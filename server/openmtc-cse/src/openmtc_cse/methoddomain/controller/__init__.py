import string
from datetime import datetime
from itertools import chain
from operator import attrgetter
from random import choice
from urlparse import urlparse
import binascii
import base64

from iso8601.iso8601 import parse_date, ParseError
from fyzz import parse
from rdflib import Graph

import openmtc_cse.api as api
from futile import uc
from futile.logging import LoggerMixin
from openmtc.exc import OpenMTCError
from openmtc.model import FlexibleAttributesMixin
from openmtc.util import datetime_now, datetime_the_future
from openmtc_cse.methoddomain.filtercriteria import check_match
from openmtc_onem2m.exc import (CSEOperationNotAllowed, STATUS_OK, CSETypeError,
                                CSEMissingValue, CSEValueError, STATUS_CREATED,
                                CSEError, CSESyntaxError, CSEBadRequest,
                                CSEPermissionDenied, STATUS_NOT_FOUND, CSEConflict,
                                CSEContentsUnacceptable, CSETargetNotReachable,
                                STATUS_UPDATED, STATUS_DELETED)
from openmtc_onem2m.model import (ExpiringResource, Notification,
                                  AccessControlOperationE, ResourceTypeE,
                                  NotificationContentTypeE, FilterUsageE,
                                  get_short_resource_name, URIList,
                                  DiscResTypeE, Container, AccessControlPolicy,
                                  AccessControlPolicyIDHolder, AccessControlRuleC,
                                  DynAuthDasRequestC, SecurityInfo, SecurityInfoTypeE,
                                  AE, ContentInstance)
from openmtc_onem2m.transport import (OneM2MResponse, OneM2MRequest,
                                      OneM2MOperation, OneM2MErrorResponse)
from openmtc_onem2m.util import split_onem2m_address
from openmtc_server.db import DBError
from openmtc_server.db.exc import DBNotFound
from openmtc_server.util import match_now_cron
from openmtc_server.util import uri_safe
from openmtc_server.util.async import async_all


_resource_id_counter = {}


class OneM2MDefaultController(LoggerMixin):
    RANDOM_SOURCE = string.letters + string.digits

    result_content_type = None

    def __init__(self, db_session, resource_type, handle_onem2m_request):
        super(OneM2MDefaultController, self).__init__()
        self.resource_type = resource_type
        self.handle_onem2m_request = handle_onem2m_request

        # DB wrapper

        def _update(resource, fields=None):
            if isinstance(resource, (Container, ContentInstance)):
                resource.stateTag += 1
            return db_session.update(resource, fields)
        self._create = db_session.store
        self._get = db_session.get
        self._update = _update
        self._delete = db_session.delete
        self._get_collection = db_session.get_collection
        self._get_latest_content_instance = db_session.get_latest_content_instance
        self._get_oldest_content_instance = db_session.get_oldest_content_instance

    def __call__(self, request, target_resource):
        self.logger.debug("%s servicing request", type(self).__name__)

        self.request = request
        self.resource = target_resource

        self.global_config = api.config["global"]
        self.onem2m_config = api.config["onem2m"]
        self.api = api.api
        self.events = api.events

        self.values = None

        self._require_auth = self.global_config.get("require_auth", True)

        # TODO(rkr): maybe make subjectAltName as mandatory in the certificate,
        # TODO          before handling it to the WSGI application
        # differentiate between authN and impersonation
        # authN: a valid ssl handshake was performed, but the subjectAltName may not provided
        # impersonation: which means that subjectAltName exists in cert and matches the request
        #  originator id
        self.is_authenticated = getattr(request, "_authenticated", None)
        self.remote_ip_addr = getattr(request, "_remote_ip_addr", None)

        self._sp_id = "//" + self.onem2m_config["sp_id"]  # //openmtc.org
        self._rel_cse_id = "/" + self.onem2m_config["cse_id"]  # /mn-cse-1
        self._abs_cse_id = self._sp_id + self._rel_cse_id  # //openmtc.org/mn-cse-1

        # default policies
        self._default_privileges = map(lambda x: AccessControlRuleC(**x),
                                       self.onem2m_config.get("default_privileges", []))

        # dynamic authorization
        dynamic_authorization = self.onem2m_config.get("dynamic_authorization", {})
        self._dynamic_authorization_supported = dynamic_authorization.get('enabled', False)
        self._dynamic_authorization_poa = dynamic_authorization.get('poa', [])

        return self._handle_request()

    def _handle_request(self):
        try:
            handler = getattr(self, "_handle_" + self.request.operation.name)
        except AttributeError as e:
            raise CSEOperationNotAllowed(e)
        return handler()

    # AUTHORIZATION

    def _check_authorization(self, resource=None):
        """This method performs the access control decision (TS-0003 7.1.4).
         The result should be "res_acrs= TRUE || FALSE" for "Permit" or "Deny".

        :return: True or False
        """

        if not self._require_auth:
            return

        # ==========================================
        # Part I: Getting the accessControlPolicyIDs
        # ==========================================
        # 1. get accessControlPolicyIDs of target resource
        # 2. if not exist, get from parent resource
        # 3. some resources specific handling => TS-0001 clause 9.6 for <container>,
        #        <m2mServiceSubscriptionProfile>, <serviceSubscribedNode>
        #   =>> get from parent
        # 4. apply system default policies, if accessControlPolicyIDs attribute is:
        #       - not set
        #       - not point to valid resource
        #       - not reachable

        # =====================================================================
        # Part II: Get Rules (acrs) from selfPrivileges or privileges attribute
        # =====================================================================
        # 1. if target is the <accessControlPolicy> resource
        #   =>> get rules from "selfPrivileges"
        # 2. if target is another resource:
        #   =>> get accessControlRules (acr) from "privilege" attribute of the
        #       <accessControlPolicy> which is linked in the accessControlPolicyIDs

        # ====================================
        # Part III: Evaluate against the rules
        # ====================================
        # Check the following conditions:
        # 1. check if accessControlOriginators of the rule includes the originator of the request
        #    ==>> evaluate fr parameter of request vs. acor
        # 2. check if accessControlOperations of the rule includes the operation type of the request
        #   ==>> evaluate op parameter of request vs. acop
        # 3. check if accessControlContexts of the rule includes the request context

        self.logger.debug("checking authorization...")

        try:
            urlparse(self.request.originator)
        except AttributeError:
            raise CSEPermissionDenied("No or not a valid originator given!")

        # cse is authorized: needed to perform actions like sending DAS response, otherwise loop
        if self.request.originator == self._abs_cse_id:
            return

        if not resource:
            resource = self.parent if self.request.op == OneM2MOperation.create else self.resource

        # AE is allowed on own resources
        if isinstance(resource, AE):
            _, _, ae_id = split_onem2m_address(self.request.originator)
            if ae_id == resource.resourceID:
                return
        elif getattr(resource, 'creator', '') == self.request.originator:
            return

        # if the resource is a policy, check selfPrivileges
        if isinstance(resource, AccessControlPolicy):
            self._check_auth_acp(resource)
        elif isinstance(resource, AccessControlPolicyIDHolder):
            self._check_auth_acp_holder(resource)
        else:
            self._check_auth_other(resource)

    def _check_auth_acp(self, resource):
        self.logger.debug("resource is AccessControlPolicy, checking selfPrivileges '%s'" %
                          resource.selfPrivileges)

        # TODO(rst): check if default policies are also valid for selfPrivileges
        if self._perform_evaluation([resource], "selfPrivileges"):
            return

        raise CSEPermissionDenied("Authentication failed. Cause: selfPrivileges")

    def _check_auth_acp_holder(self, resource):
        self.logger.debug("Resource is AccessControlPolicyIDHolder, getting policies...")

        self._check_privileges(resource)

    def _check_auth_other(self, resource):
        self.logger.debug("Resource has no attribute 'accessControlPolicyIDs'. Checking parent...")
        parent = self._get_parent_of_resource(resource)

        if not isinstance(parent, AccessControlPolicyIDHolder):
            self.logger.debug("Parent is not an AccessControlPolicyIDHolder")
            raise CSEPermissionDenied("Authorization failed.")

        self._check_privileges(parent)

    def _get_parent_of_resource(self, resource):
        return self._get(resource.parentID)

    def _check_privileges(self, resource):
        # get all ACPs
        policies = []   # acpi, accessControlPolicyIDs
        if resource.accessControlPolicyIDs:
            policies = self._get_policies(resource.accessControlPolicyIDs)
        elif isinstance(resource, Container):
            policies = self._get_parent_policies_of_container(resource)

        # perform evaluation based on policies/default policies
        if self._perform_evaluation(policies, "privileges"):
            return

        if self._dynamic_authorization_supported:
            self.logger.debug("Notifying DAS Server...")
            if self._notify_das_server(resource):
                return

        raise CSEPermissionDenied("Authorization failed.")

    def _get_parent_policies_of_container(self, resource):
        policies = []
        parent_resource = self._get_parent_of_resource(resource)
        if parent_resource.accessControlPolicyIDs:
            policies = self._get_policies(parent_resource.accessControlPolicyIDs)
            return policies
        else:
            if isinstance(parent_resource, Container):
                return self._get_parent_policies_of_container(parent_resource)
            else:
                return policies

    def _get_policies(self, access_control_policy_ids):

        def get_policy(aid):
            try:
                return self.api.handle_onem2m_request(
                    OneM2MRequest(
                        OneM2MOperation.retrieve, aid, fr=self._abs_cse_id
                    )
                ).get().content
            except OneM2MErrorResponse as error:
                if error.response_status_code == STATUS_NOT_FOUND:
                    self.logger.debug("Policy '%s' NOT FOUND.", aid)
                else:
                    self.logger.debug("Error getting policy: %s:", error)
                return None

        return filter(None, map(get_policy, access_control_policy_ids))

    # def _notify_das_server(self, notify_uri, payload):
    def _notify_das_server(self, resource):
        # 7.5.1.2.10 Notification for Dynamic Authorization
        # When the Originator(i.e. Hosting CSE) is triggered to perform dynamic authorization for
        # an incoming request that it receives, then it performs the following steps in order:
        #   1) Configure the To parameter with the address of the corresponding DAS Server
        #       associated with the resource targeted by the received request. The Hosting CSE
        #       shall use the DAS Server address information configured within the
        #       dynamicAuthorizationPoA attribute of the < dynamicAuthorizationConsultation >
        #       resource associated with the targeted resource. The Hosting CSE shall determine the
        #       corresponding < dynamicAuthorizationConsultation > resource using the
        #       dynamicAuthorizationConsultationIDs attribute of the targeted resource. If the
        #       attribute is not supported by the targeted resource, or it is not set, or it has a
        #       value that does not correspond to a valid < dynamicAuthorizationConsultation >
        #       resource(s), or it refers to a < dynamicAuthorizationConsultation > resource(s)
        #       that is not reachable, then based on system policies, the
        #       dynamicAuthorizationConsultationIDs associated with the parent may apply to the
        #       child resource if present, or a system default < dynamicAuthorizationConsultation >
        #       may apply if present. If a dynamicAuthorizationConsultationID attribute and
        #       corresponding < dynamicAuthorizationConsultation > resource can not be found or if
        #       the dynamicAuthorizationEnabled of a < dynamicAuthorizationConsultation > has a
        #       value of FALSE, the Hosting CSE shall reject the request by returning an
        #       "ORIGINATOR_HAS_NO_PRIVILEGE" Response Status Code to the Originator of the
        #       received request and no additional steps shall be performed.

        dac = self._get_dynamic_authorization_consultation(resource)

        if dac is None:
            dyn_auth_poa = self._dynamic_authorization_poa
        else:
            dyn_auth_poa = dac.dynamicAuthorizationPoA

        if not dyn_auth_poa:
            return False

        #   2) Configure the From parameter with the ID of the Hosting CSE which hosts the resource
        #       targeted by the received request.
        #   3) Configure the mandatory sub-elements of the securityInfo element of the notification
        #       data
        #       a. The securityInfoType element shall be configured as "1" (Dynamic Authorization
        #           Request) in the Notify request primitive.
        #       b.The originator element shall be configured with the ID of the Originator of the
        #           received request.
        #       c. The targetedResourceType element shall be configured with the type of resource
        #           targeted by the received request.
        #       d. The operation element shall be configured with the type of operation targeted by
        #           the received request.
        #   4) Optionally configure one or more optional sub-elements of the securityInfo element
        #       of the notification data
        #       ...

        das_req = DynAuthDasRequestC(
            originator=self.request.originator,
            operation=self.request.operation,
            targetedResourceType=resource.resourceType,
            targetedResourceID=self._rel_cse_id + '/' + resource.resourceID
        )
        content = SecurityInfo(
            dasRequest=das_req,
            securityInfoType=SecurityInfoTypeE.DynamicAuthorizationRequest
        )

        request = OneM2MRequest(OneM2MOperation.notify, '', fr=self._abs_cse_id,
                                ty=SecurityInfo, pc=content)

        #   5) The Hosting CSE shall send the notification request for dynamic authorization to the
        #       targeted DAS Server.
        try:
            resp = self.api.send_notify(request, dyn_auth_poa).get()
        except (OneM2MErrorResponse, CSETargetNotReachable):
            return False

        # Originator:
        # When the Hosting CSE receives a notification response for dynamic authorization, it
        # performs the following steps in order:
        #   1) The Hosting CSE shall verify that the securityInfoType element of the securityInfo
        #       element of the notification is configured as "2" (Dynamic Authorization Response).
        #       If it is not, the Hosting CSE shall not grant privileges to the Originator of the
        #       request for which the Hosting CSE was attempting dynamic authorization. The Hosting
        #       CSE shall reject the request by returning an "ORIGINATOR_HAS_NO_PRIVILEGE" Response
        #       Status Code to the Originator of the received request and no additional steps shall
        #       be performed.

        sec_info_resp = resp.content

        try:
            if sec_info_resp.securityInfoType != SecurityInfoTypeE.DynamicAuthorizationResponse:
                return False
        except AttributeError:
            return False

        #   2) The Hosting CSE shall check whether the response contains a dynamicACPInfo element.
        #       If present, the Hosting CSE shall create a <accessControlPolicy> child resource
        #       under the targeted resource and configure its privileges using the dynamicACPInfo.
        #       In this case, the Hosting CSE shall configure the privileges attribute with the
        #       grantedPrivileges and the expirationTime attribute with the privilegesLifetime. The
        #       Hosting CSE shall also configure the selfPrivileges attribute to allow itself to
        #       perform Update/Retrieve/Delete operations on the newly created <accessControlPolicy>
        #       resource.

        if not sec_info_resp.dasResponse:
            return False

        acp_info = sec_info_resp.dasResponse.dynamicACPInfo
        # disabled for debug
        # if acp_info:
        #     self._create_dynamic_policy(resource, acp_info)

        #   3) The Hosting CSE shall check whether the response contains a tokens element. If
        #       present the Hosting CSE shall perform verification and caching of the token as
        #       specified in clause 7.3.2 in TS-0003 [7].

        # Not implemented yet.

        #   NOTE: The Hosting CSE uses the information in the DAS response for authorization,
        #       see clause 7.3.3.15.

        return self._perform_evaluation([acp_info], "grantedPrivileges")

    def _get_dynamic_authorization_consultation(self, resource):
        try:
            for dac_id in resource.dynamicAuthorizationConsultationIDs:
                try:
                    dac = self._get(dac_id)
                    if dac.dynamicAuthorizationEnabled:
                        return dac
                except DBNotFound:
                    pass

            pid = resource.parentID
        except AttributeError:
            return None
        else:
            return self._get_dynamic_authorization_consultation(self._get(pid))

    def _create_dynamic_policy(self, resource, acp_info):
        acp = AccessControlPolicy(
            selfPrivileges=[AccessControlRuleC(
                accessControlOriginators=[self._abs_cse_id],
                accessControlOperations=[
                    AccessControlOperationE.retrieve,
                    AccessControlOperationE.update,
                    AccessControlOperationE.delete
                ]
            )],
            privileges=acp_info.grantedPrivileges,
            expirationTime=acp_info.privilegesLifetime or datetime_the_future(3600)
        )

        req = OneM2MRequest(OneM2MOperation.create, resource.resourceID,
                            pc=acp,
                            fr=self._abs_cse_id,
                            ty=AccessControlPolicy)
        resp = self.api.handle_onem2m_request(req).get()
        dyn_acp_id = resp.content.resourceID
        resource.accessControlPolicyIDs.append(dyn_acp_id)
        self._update(resource, ['accessControlPolicyIDs'])

    def _perform_evaluation(self, policies, privilege_type):

        def _perform_access_decision(access_control_rules):
            for acr in access_control_rules:
                if self._is_authorized(self.request, acr):
                    self.logger.debug("SUCCESS: At least one match in accessControlRules.")
                    return True
            return False

        if policies:
            self.logger.debug("Performing evaluation of resource policies...")
            privileges = list(chain.from_iterable(map(attrgetter(privilege_type), policies)))
            return _perform_access_decision(privileges)
        elif self._default_privileges:
            self.logger.debug("Performing evaluation using default privileges...")
            return _perform_access_decision(self._default_privileges)
        return False

    def _is_authorized(self, request, acr):
        """This method performs access control decision (TS-0003 7.1.5) for a single acr.
        res_acr(k) = res_authn(k) AND res_origs(k) AND res_ops(k) AND res_ctxts(k).

        :param request:
        :param acr:
        :return:
        """
        self.logger.debug("_is_authorized -> keys: %s", acr.__dict__)

        # get enum value of requested operation name
        request_op_val = getattr(AccessControlOperationE, request.op)

        # discover operation is indicated by op = retrieve AND fc and Discrestype parameters
        # therefore set request operation value to 32 and check it against acop
        if request.op == OneM2MOperation.retrieve and request.drt and request.fc:
            try:
                if request.drt in ["1", "2"] and request.fc.filterUsage == 1:
                    request_op_val = 32
            except AttributeError:
                pass

        # results for each part in the acr
        res_origs = False
        res_ops = False
        res_authn = False
        res_ctxts = False

        # 1st - request originator in acor?
        #   TS-0001, p.119, Table 9.6.2.1-1: possible parameters
        #   acr.accessControlOriginators = ["all" || "<originatorID>" (CSE-ID, AE-ID, Group-ID
        #                                   || Role-ID (optional?)(TS0001 - 7.1.14) ]

        def orig_matches(orig, to_match):
            if to_match == 'all':
                self.logger.debug("all originators are valid for this acr")
                return True

            def get_cse_relative_originator(o):
                if o.startswith(self._sp_id):
                    return o[len(self._sp_id):]
                return o

            if get_cse_relative_originator(orig) == get_cse_relative_originator(to_match):
                self.logger.debug("request originator matches originator/domain")
                return True

            self.logger.debug("invalid originator: '%s' != '%s'", orig, to_match)
            return False

        if hasattr(acr, "accessControlOriginators") and acr.accessControlOriginators:
            res_origs = any(orig_matches(request.fr, o) for o in acr.accessControlOriginators)
            if not res_origs:
                return False
        else:
            # the set of acor is empty (or not available) => fr is not member of it => False
            self.logger.debug("no accessControlOriginators to check")
            return False

        # 2nd - op allowed?
        #   acr.accessControlOperations e.g. [1, 2, 4] <- intEnums type AccessControlOperation
        #       acop vs. op: for create, delete, request, update, notify
        #       acop vs. op AND fc (Disrestype parameters): for discover
        if hasattr(acr, "accessControlOperations") and acr.accessControlOperations:
            # check request operation value against acop and check combined values (like 3, 7, etc.)
            for v in acr.accessControlOperations:
                if (request_op_val & v) != 0:
                    res_ops = True
                    break
            if res_ops:
                self.logger.debug("request operation '%s' is part of allowed operations '%s'",
                                  request.op,
                                  acr.accessControlOperations)
            else:
                self.logger.debug("request operation '%s' is not part of allowed operations '%s'",
                                  request.op,
                                  acr.accessControlOperations)
                return False
        else:
            self.logger.debug("no accessControlOperations to check")

        # 3rd - request matches authenticationFlag
        if hasattr(acr, "accessControlAuthenticationFlag"):
            if acr.accessControlAuthenticationFlag:
                if self.is_authenticated:
                    res_authn = True
                else:
                    self.logger.debug("accessControlAuthenticationFlag is set True, "
                                      "but originator is not authenticated")
                    res_authn = False
            else:
                res_authn = True

        # 4th - request matches context criteria? (time window || location || ipAddress)
        # TODO(rkr): future implementation: location
        if hasattr(acr, "accessControlContexts") and acr.accessControlContexts:
            for context in acr.accessControlContexts:
                if hasattr(context, "accessControlWindow") and context.accessControlWindow:
                    window_match = False
                    for window in context.accessControlWindow:
                        if match_now_cron(window):
                            window_match = True
                            break

                    if window_match:
                        self.logger.debug("time window is open for request")
                    else:
                        self.logger.debug("time window closed for request")
                        return False

                if hasattr(context, "accessControlIpAddresses") and context.accessControlIpAddresses:
                    if hasattr(context.accessControlIpAddresses, "ipv4Addresses") and \
                            context.accessControlIpAddresses.ipv4Addresses:
                        ip_match = False
                        for ipv4 in context.accessControlIpAddresses.ipv4Addresses:
                            remote_ipv4_addr = self.remote_ip_addr[7:]
                            if remote_ipv4_addr == ipv4:
                                ip_match = True
                                break
                        if ip_match:
                            self.logger.debug("ip match for request")
                        else:
                            self.logger.debug("no ip match for request")
                            return False

        # went through all stages -> success, return True
        if res_origs and res_ops and res_authn:
            return True
        else:
            return False

    def _is_authenticated(self, request_originator):
        # TODO(rkr): implement 1st and 2nd; the 3rd is not a currently needed use case in our
        # TODO       deployments
        # TODO(rkr): see TS-0003 p.33; 7.1.2-3
        # rq_authn = TRUE || FALSE

        # 1st - Originator = AE registered to Hosting CSE
        # if originator is AE registered to the Hosting CSE then this decision is
        # deployment/implementation specific. In some cases it is appropriate to expect TLS or DTLS
        # to be used. In other cases, TLS or DTLS may be un-necessary.

        # 2nd - Originator = CSE registered to Hosting CSE
        # If originator is CSE registered with the Hosting CSE, originator shall always be
        # considered authenticated, because the Mcc is always required to be protected by TLS or
        # DTLS. (according to an SAEF like described in TS-0003 8.2)

        # 3rd - AE/CSE registered with an other CSE that is not the Hosting CSE
        # If the Originator is an AE or CSE registered with a CSE other than the Hosting CSE, then
        # the Originator is considered authenticated by the Hosting CSE if and only if the request
        # primitive is protected using End - to - End Security of Primitives(ESPrim) as described
        # in clause 8.4.

        # TODO(rkr): AE Impersonation Prevention - TS-0003 p.37; 7.2.1
        # 0. Security association establishment may be performed.Clause 6.1.2.2.1 describes the
        # scenarios when security association establishment between an AE and CSE is mandatory, and
        # describes the scenarios when security association establishment between an AE and CSE is
        # recommended.The subsequent procedures shall be performed if a security association has
        # been established.
        #
        # 1. The AE shall send a request to Hosting CSE via its Registrar CSE(Hosting CSE is not
        # represented on this figure and can either be the Registrar CSE or another CSE).
        #
        # 2. The Registrar CSE shall check if the value in the From parameter is the same as the ID
        # associated in security association.
        #
        # 3. If the value is not the same, the Registrar CSE shall send a response with error
        # response code '6101' (Security error - impersonation error).
        #
        # 4. If the values is the same, the Registrar CSE performs procedures specified in clause
        # 8.2 of oneM2M TS - 0001[1].Depending on the number of Transit CSEs, the Registrar CSE
        # shall either process the request or forward it to the Hosting CSE or to another Transit
        # CSE.

        # defaults
        AE_TLS_DTLS_connected = False
        CSE_TLS_DTLS_connected = False

        # TODO(rkr): implement
        # AE_TLS_DTLS_connected = True
        # CSE_TLS_DTLS_connected = True

        if AE_TLS_DTLS_connected or CSE_TLS_DTLS_connected:
            self.request.rq_authn = True
            return True
        else:
            self.request.rq_authn = False
            return False

    # NOTIFY

    def _handle_notify(self):
        raise CSEOperationNotAllowed()

    # CREATE

    def _handle_create(self):
        self.parent = self.resource
        del self.resource

        self.now = datetime_now()
        self.fields = []

        self._check_authorization()
        self._check_create_representation()
        self._create_resource()
        self._finalize_create()
        return self._send_create_response()

    def _check_create_representation(self):
        rt = self.resource_type
        if not self.parent.has_child_type(rt):
            raise CSEBadRequest()

        # TODO(rst): change controller to work on resource itself
        values = self.request.content.get_values(True)

        self.logger.debug("_check_create_representation: %s", values)

        # TODO: move this to expiration time handler plugin
        # but needs to be set to a value even if plugin is disabled
        if issubclass(self.resource_type, ExpiringResource):
            expiration_time = values.get("expirationTime")
            if not expiration_time:
                expiration_time = self.now + self.global_config[
                    "default_lifetime"]
                self.fields.append("expirationTime")
            else:
                if not isinstance(expiration_time, datetime):
                    try:
                        expiration_time = parse_date(expiration_time)
                    except ParseError as e:
                        raise CSEValueError(
                            "Illegal value for expirationTime: %s" % (e,))
                if expiration_time < self.now + self.global_config["min_lifetime"]:
                    self.logger.warn("expirationTime is too low. Adjusting")
                    expiration_time = self.now + self.global_config["min_lifetime"]
                    self.fields.append("expirationTime")
                elif expiration_time > self.now + self.global_config["max_lifetime"]:
                    self.logger.warn("expirationTime is too high. Adjusting")
                    expiration_time = self.now + self.global_config["max_lifetime"]
                    self.fields.append("expirationTime")

            values["expirationTime"] = expiration_time

        rt_attributes = rt.attributes
        ignore_extra = True  # todo(rst): check this later with flexContainer
        is_flex = ignore_extra and issubclass(self.resource_type,
                                              FlexibleAttributesMixin)

        # TODO: optimize
        if ignore_extra and not is_flex:
            names = rt.attribute_names
            for k in values.keys():
                if k not in names:
                    values.pop(k)

        for attribute in rt_attributes:
            have_attr = (attribute.name in values and
                         values[attribute.name] is not None)
            # TODO(rkr): check mandatory attributes
            if not have_attr and attribute.mandatory:
                raise CSEMissingValue("Missing attribute: %s" % (attribute.name,))
            if have_attr and attribute.accesstype == attribute.RO:
                self._handle_ro_attribute(attribute)

        self.values = values

    def _handle_ro_attribute(self, attribute):
        if not self.request.internal:
            raise CSETypeError("Attribute must not be specified: %s" %
                               (attribute.name,))

    def _create_resource(self):
        # TODO(rst): change controller to work on resource itself
        if not self.values:
            values = self.request.content.get_values(True)
        else:
            values = self.values

        self._set_mandatory_create_attributes(values)

        self.logger.debug("Creating resource of type '%s' with values: %s",
                          self.resource_type, values)

        resource_type = self.resource_type

        if "stateTag" in resource_type.attribute_names:
            values["stateTag"] = 0

        resource = resource_type(**values)
        resource.path = self._get_resource_path()

        self.logger.info("Created resource of type '%s' at %s",
                         resource.typename, resource.path)

        self.resource = resource

        return self._create(resource)

    def _set_resource_id(self, values):
        short_name = get_short_resource_name(self.resource_type.typename)
        try:
            _resource_id_counter[short_name] += 1
        except KeyError:
            _resource_id_counter[short_name] = 0
        values["resourceID"] = short_name + str(
            _resource_id_counter[short_name])

    def _set_mandatory_create_attributes(self, values):
        # time attributes
        values["creationTime"] = values["lastModifiedTime"] = self.now

        # set values for parentID and resourceID
        values["parentID"] = self.parent.resourceID
        self._set_resource_id(values)

        # resource name
        try:
            name = uc(values["resourceName"])
        except KeyError:
            name = "%s-%s" % (self.resource_type.typename, self._create_id())
        self.name = values["resourceName"] = name

        # resource type
        values["resourceType"] = ResourceTypeE[self.resource_type.typename]

    def _create_id(self):
        return ''.join([choice(self.RANDOM_SOURCE) for _ in range(16)])

    def _get_resource_path(self):
        try:
            return self.__resource_path
        except AttributeError:
            # TODO: current uri_safe is insufficient. need a better strategy
            rp = self.__resource_path = self.parent.path + "/" + uri_safe(
                self.name)
            return rp

    def _finalize_create(self):
        events = self.api.events
        events.resource_created.fire(self.resource,
                                     self.request)
        if self.parent is not None:
            events.resource_updated.fire(self.parent,
                                         self.request)

    def _send_create_response(self):
        return OneM2MResponse(STATUS_CREATED, pc=self.resource,
                              request=self.request)

    # RETRIEVE

    def _prepare_fields(self):
        """
        Make sure fields is a list
        :return:
        """

        self.fields = self.request.content and self.request.content.values

    def _handle_retrieve(self):
        try:
            fu = self.request.filter_criteria.filterUsage
        except AttributeError:
            fu = None
        self._prepare_fields()
        if fu == FilterUsageE.Discovery:
            self._prepare_discovery()
        else:
            self._check_authorization()
            # TODO(rkr): if authorization from accessControlPolicies failed || False
            # TODO          perform Dynamic Authorization if the Hosting CSE does support it
            self._prepare_resource()
        return self._send_retrieve_response()

    def _prepare_discovery(self):
        self.limit = None
        self.truncated = False

        try:
            self.drt = DiscResTypeE(int(self.request.drt))
        except TypeError:
            self.drt = DiscResTypeE.structured
        except ValueError:
            raise CSEBadRequest()

        if hasattr(self.request.filter_criteria, 'limit'):
            self.limit = self.request.filter_criteria.limit

        self.logger.debug("_prepare_resource -> _handle_result: %s" %
                          self.resource)

        self.discovered = []
        self.result = URIList(self.discovered)
        self._discovery()

    def _discovery(self):
        try:
            return self._do_discovery(self.resource)
        except OpenMTCError:
            self.logger.exception("Error during discovery")
            raise CSEError("Error during discovery")

    def _do_discovery(self, node):
        self.logger.debug("_do_discovery: %s", node)

        if self.limit and len(self.discovered) >= self.limit:
            self.logger.debug("stopping discovery: limit reached")
            self.truncated = True
            return True

        if check_match(node, self.request.filter_criteria):
            try:
                self._check_authorization(node)
                if self.drt == DiscResTypeE.unstructured:
                    self.discovered.append(node.resourceID)
                else:
                    self.discovered.append(node.path)
            except CSEPermissionDenied:
                pass

        if not self.truncated:
            self._retrieve_children_for_resource(node)
            self.logger.debug("checking sub resources of: %s", node)
            self.logger.debug("childResource: %s", node.childResource)
            for s in node.childResource:
                self.logger.debug("is resource '%s' virtual? -> %s", s.name,
                                  s.virtual)
                if not s.virtual:
                    sub_node = self._get(s.path)
                    self._do_discovery(sub_node)

    def _prepare_resource(self):
        self.logger.debug("preparing resource.")
        res = self.result = self.resource
        try:
            res.resourceType = getattr(ResourceTypeE,
                                       type(res).__name__)
        except AttributeError:
            self.logger.debug("no resourceType for %s", res)

        if self.fields and isinstance(self.fields, list):
            res.set_values({k: v if k in self.fields else None for
                            k, v in res.get_values().items()})
        return self._retrieve_children()

    def _send_retrieve_response(self):
        return OneM2MResponse(STATUS_OK, pc=self.result, request=self.request)

    def _retrieve_children(self):
        return self._retrieve_children_for_resource(self.resource)

    def _retrieve_children_for_resource(self, resource):
        self.logger.debug("getting children of: %s", resource)
        children = self._get_collection(None, resource)
        resource.childResource = children

    # UPDATE

    def _handle_update(self):
        self.now = datetime_now()
        self.fields = []

        self._check_authorization()
        self._check_update_representation()
        self._update_resource()
        self._finalize_update()
        return self._send_update_response()

    def _check_update_representation(self):
        rt = self.resource_type

        # TODO(rst): change controller to work on resource itself
        values = self.request.content.get_values(True)

        self.logger.debug("_check_update_representation: %s", values)

        for k in ("lastModifiedTime", "stateTag", "childResource"):
            values.pop(k, None)

        # TODO: move this to expiration time handler plugin
        # but needs to be set to a value even if plugin is disabled
        if issubclass(self.resource_type, ExpiringResource):
            expiration_time = values.get("expirationTime")
            if not expiration_time:
                expiration_time = self.now + self.global_config[
                    "default_lifetime"]
                self.fields.append("expirationTime")
            else:
                if not isinstance(expiration_time, datetime):
                    try:
                        expiration_time = parse_date(expiration_time)
                    except ParseError as e:
                        raise CSEValueError(
                            "Illegal value for expirationTime: %s" % (e,))
                if expiration_time < self.now + self.global_config[
                        "min_lifetime"]:
                    self.logger.warn("expirationTime is too low. Adjusting")
                    expiration_time = self.now + self.global_config[
                        "min_lifetime"]
                    self.fields.append("expirationTime")
                elif expiration_time > self.now + self.global_config[
                        "max_lifetime"]:
                    self.logger.warn("expirationTime is too high. Adjusting")
                    expiration_time = self.now + self.global_config[
                        "max_lifetime"]
                    self.fields.append("expirationTime")

            values["expirationTime"] = expiration_time

        rt_attributes = rt.attributes
        ignore_extra = True  # todo(rst): check this later with flexContainer
        is_flex = ignore_extra and issubclass(self.resource_type,
                                              FlexibleAttributesMixin)

        # TODO: optimize
        if ignore_extra and not is_flex:
            names = rt.attribute_names
            for k in values.keys():
                if k not in names:
                    values.pop(k)

        for attribute in rt_attributes:
            have_attr = attribute.name in values
            if have_attr and attribute.accesstype == attribute.WO:
                self._handle_wo_attribute(attribute)

    def _handle_wo_attribute(self, attribute):
        if not self.request.internal:
            raise CSETypeError("Attribute must not be specified: %s" %
                               (attribute.name,))

    def _update_resource(self):
        # TODO(rst): change controller to work on resource itself (partly done)
        values = self.request.content.get_values(True)

        self._set_mandatory_update_attributes(values)

        self.logger.debug("Updating resource of type '%s' with values: %s",
                          self.resource_type, values)

        resource_type = self.resource_type

        if "stateTag" in resource_type.attribute_names:
            values["stateTag"] = 0

        resource = resource_type(**values)

        for v in values.keys():
            setattr(self.resource, v, values[v])

        # resource.path = self.resource.path

#        self.logger.info("Updated resource of type '%s' at %s",
#                        resource.typename, resource.path)
        self.logger.info("Updated resource of type '%s' at %s",
                         self.resource.typename, self.resource.path)

        # self.resource = resource

        return self._update(self.resource)
        # return self._update(resource, values.keys())

    def _set_mandatory_update_attributes(self, values):
        values["lastModifiedTime"] = self.now

    def _finalize_update(self):
        events = self.api.events
        events.resource_updated.fire(self.resource,
                                     self.request)

    def _send_update_response(self):
        return OneM2MResponse(STATUS_UPDATED, pc=self.resource,
                              request=self.request)

    # DELETE

    def _handle_delete(self):
        self._check_authorization()
        self._delete_resource()
        if not self.request.cascading:
            self._get_parent()
        self._finalize_delete()
        return self._send_delete_response()

    def _get_parent(self):
        self.parent = self._get(self.resource.parent_path)

    def _delete_resource(self):
        self._delete_children()
        self._do_delete_resource()

    def _do_delete_resource(self):
        return self._delete(self.resource)

    def _delete_children(self):
        self._retrieve_children()
        self._do_delete_children()

    def _do_delete_children(self):
        child_promises = []

        for child in self.resource.childResource:
            request = OneM2MRequest(OneM2MOperation.delete, child.path, fr=self._abs_cse_id,
                                    rqi=self.request.rqi)
            request.cascading = True
            child_promises.append(self.handle_onem2m_request(request))

        async_all(child_promises, fulfill_with_none=True).get()

    def _finalize_delete(self):
        if not self.request.cascading:
            self.events.resource_updated.fire(self.parent,
                                              self.request)
        self.events.resource_deleted.fire(self.resource, self.request)

    def _send_delete_response(self):
        return OneM2MResponse(STATUS_DELETED, request=self.request)


# see TS-0004 7.4.4
class CSEBaseController(OneM2MDefaultController):
    def _handle_create(self):
        raise CSEOperationNotAllowed()

    def _prepare_resource(self):
        super(CSEBaseController, self)._prepare_resource()
        self.resource.pointOfAccess = self.api.get_onem2m_endpoints()

    def _handle_update(self):
        raise CSEOperationNotAllowed()

    def _handle_delete(self):
        raise CSEOperationNotAllowed()


# see TS-0004 7.4.5
class RemoteCSEController(OneM2MDefaultController):
    # TODO(rst): add Mca check -> 7.4.5.2.1 Create

    def _handle_create(self):
        self.parent = self.resource
        del self.resource

        self.now = datetime_now()
        self.fields = []

        self._check_create_representation()
        self._create_resource()
        self._finalize_create()
        return self._send_create_response()


class AEController(OneM2MDefaultController):
    def _handle_notify(self):
        return self.api.send_notify(self.request, self.resource.pointOfAccess).get()

    def _handle_create(self):
        self.parent = self.resource
        del self.resource

        self.now = datetime_now()
        self.fields = []

        self._check_create_representation()
        self._create_resource()
        self._finalize_create()
        return self._send_create_response()

    def _set_resource_id(self, values):

        def get_generic_ae_id():
            try:
                _resource_id_counter["ae"] += 1
            except KeyError:
                _resource_id_counter["ae"] = 0
            return "CAE" + str(_resource_id_counter["ae"])

        try:
            _, _, ae_id = split_onem2m_address(self.request.originator)
        except TypeError:
            ae_id = get_generic_ae_id()

        if not ae_id.startswith('C'):
            ae_id = get_generic_ae_id()

        try:
            self._get(ae_id)
        except DBNotFound:
            pass
        else:
            raise CSEConflict()

        values["resourceID"] = ae_id

    def _set_mandatory_create_attributes(self, values):
        super(AEController, self)._set_mandatory_create_attributes(values)

        values["AE-ID"] = values["resourceID"]

        # TODO(rst): set nodeLink
        values["nodeLink"] = "dummy"


class SubscriptionController(OneM2MDefaultController):
    def _handle_create(self):
        self.parent = self.resource
        del self.resource

        self.now = datetime_now()
        self.fields = []

        self._check_authorization()
        self._check_originator_access()
        self._check_notification_uri()
        self._check_create_representation()
        self._create_resource()
        self._finalize_create()
        return self._send_create_response()

    # def _check_syntax_create(self):
    #     super(SubscriptionController, self)._check_syntax_create()
    #     try:
    #         criterias = self.request.pc["eventNotificationCriteria"]
    #         if criterias:
    #             from openmtc_cse.methoddomain.filtercriteria import filters
    #
    #             self.logger.debug("validating filter criterias: %s", criterias)
    #             for crit in criterias:
    #                 if crit != "attribute":
    #                     if hasattr(filters, crit):
    #                         self.logger.debug("criterion '%s' is valid", crit)
    #                         pass  # valid filter
    #                     else:
    #                         self.logger.error("criterion '%s' is invalid", crit)
    #                         raise CSESyntaxError("unknown criterion: %s", crit)
    #     except KeyError as e:
    #         pass
    #         # self.logger.warn(e)

    def _check_originator_access(self):
        # TODO(rst): TS-004 7.3.8.2.1
        # 3. Check if the subscribed-to resource, addressed in To parameter in
        # the Request, is subscribable. Subscribable resource types are defined
        # in TS-0001 Functional Architecture [6], they have <subscription>
        # resource types as their child resources.
        # If it is not subscribable, the Hosting CSE shall return the Notify
        # response primitive with a Response Status Code indicating
        # "TARGET_NOT_SUBSCRIBABLE" error.

        # 4. Check if the Originator has privileges for retrieving the
        # subscribed-to resource.
        # If the Originator does not have the privilege, the Hosting CSE shall
        # return the Notify response primitive with Response Status Code
        # indicating "NO_PRIVILEGE" error.
        return

    def _check_notification_uri(self):
        # TODO(rst): TS-004 7.3.8.2.1
        # 5. If the notificationURI is not the Originator, the Hosting CSE
        # should send a Notify request primitive to the notificationURI with
        # verificationRequest parameter set as TRUE (clause 7.4.1.2.2).

        # debug only
        if self.request.originator is None:
            return

        try:
            self.logger.debug("Checking notificationURI: %s",
                              self.request.content.notificationURI)
            uris = [uri for uri in
                    self.request.content.notificationURI if
                    not uri.startswith(self.request.originator)]
            # TODO(rst): change the check that it should be a valid AE-ID
            # for uri in uris:
            #     if not urlparse(uri).scheme:
            #         raise CSESyntaxError("Invalid notificationURI")
        except KeyError:
            raise CSESyntaxError("Invalid notificationURI")

        # a. If the Hosting CSE cannot send the Notify request primitive, the
        # Hosting CSE shall return the Notify response primitive with a Response
        # Status Code indicating "SUBSCRIPTION_VERIFICATION_INITIATION_FAILED"
        # error.

        def send_verification(notify_uri):
            notification = Notification(
                verificationRequest=True,
                creator=self.request.originator
            )

            send_notify_request = OneM2MRequest(OneM2MOperation.notify, notify_uri,
                                                self.request.originator, pc=notification)
            return self.api.send_onem2m_request(send_notify_request)

        # b. If the Hosting CSE sent the primitive, the Hosting CSE shall
        # check if the Notify response primitive contains a Response Status Code
        # indicating "SUBSCRIPTION_CREATOR_HAS_NO_PRIVILEGE" or
        # "SUBSCRIPTION_HOST_HAS_NO_PRIVILEGE" error. If so, the Hosting CSE
        # shall return the Create response primitive with a Response Status Code
        # indicating the same error from the Notify response primitive to the
        # Originator.

        def handle_error(error):
            self.logger.info("Subscription verification failed: %s", error)
            raise CSEError
            # TODO(rst): check subscription error
            # if error.status_code in [
            #     STATUS_REQUEST_TIMEOUT,
            #     STATUS_BAD_GATEWAY,
            #     STATUS_SERVICE_UNAVAILABLE,
            #     STATUS_GATEWAY_TIMEOUT
            # ]:
            #     raise CannotInitiateSubscriptionVerification(error)
            # elif error.status_code == STATUS_SUBSCRIPTION_VERIFICATION_FAILED:
            #     raise SubscriptionVerificationFailed(error)
            # else:
            #     raise CSEBadGateway(error)

        # TODO(rst): verification request needs to be checked
        # try:
        #     async_all(map(send_verification, uris),
        #               fulfill_with_none=True).get()
        # except Exception as error:
        #     handle_error(error)

    def _set_mandatory_create_attributes(self, values):
        super(SubscriptionController,
              self)._set_mandatory_create_attributes(values)
        # TODO(rst): TS-004 7.3.8.2.1
        # 7. If the notificationURI is not the Originator, the Hosting CSE shall
        # store Originator ID to creator attribute.
        if (self.request.originator not in
                values["notificationURI"]):
            values["creator"] = self.request.originator

        # set notificationContentType if not set
        if "notificationContentType" not in values:
            values["notificationContentType"] = \
                NotificationContentTypeE.allAttributes


class ContainerController(OneM2MDefaultController):
    def _set_mandatory_create_attributes(self, values):
        super(ContainerController,
              self)._set_mandatory_create_attributes(values)
        values["creator"] = self.request.originator or 'nobody'
        values["currentNrOfInstances"] = 0
        values["currentByteSize"] = 0


class ContentInstanceController(OneM2MDefaultController):
    def _create_resource(self):
        super(ContentInstanceController, self)._create_resource()

        # handle_old_instances
        max_nr_of_instances = self.parent.maxNrOfInstances
        current_nr_of_instances = self.parent.currentNrOfInstances
        if 0 < max_nr_of_instances <= current_nr_of_instances:
            self.parent.currentNrOfInstances -= 1
            self.parent.currentByteSize -= self.parent.oldest.contentSize

            self._delete(self.parent.oldest)

            if self.parent.currentNrOfInstances >= 1:
                oldest = self._get_oldest_content_instance(
                    self.parent)
                self.logger.debug("Setting new oldest: %s", oldest)
                self.parent.oldest = oldest
            else:
                self.logger.debug("Setting oldest to None")
                self.parent.oldest = None

        # handle_new_instance
        self.parent.currentNrOfInstances += 1
        self.parent.currentByteSize += self.resource.contentSize
        if self.parent.oldest is None:
            self.logger.debug("Setting new resource as oldest: %s",
                              self.resource)
            self.parent.oldest = self.resource
        self.parent.latest = self.resource
        self._update(self.parent)

    def _set_mandatory_create_attributes(self, vals):
        self.request.name = None
        super(ContentInstanceController,
              self)._set_mandatory_create_attributes(vals)

        vals["contentSize"] = len(vals["content"].encode('utf-8'))
        if not vals.get("contentInfo"):
            vals["contentInfo"] = 'text/plain:0'

    def _delete_resource(self):
        super(ContentInstanceController, self)._delete_resource()

        cnt = self._get(self.resource.parentID)
        # TODO(rst): handle byte size
        try:
            ci_l = self._get_latest_content_instance(cnt)
            ci_o = self._get_oldest_content_instance(cnt)
        except (DBError, KeyError):
            cnt.latest = None
            cnt.oldest = None
            cnt.currentNrOfInstances = 0
        else:
            cnt.latest = ci_l
            cnt.oldest = ci_o
            cnt.currentNrOfInstances -= 1

        return self._update(cnt)


class AccessControlPolicyController(OneM2MDefaultController):
    def _set_mandatory_create_attributes(self, vals):
        super(AccessControlPolicyController,
              self)._set_mandatory_create_attributes(vals)

        if vals.get("selfPrivileges") is None:
            vals["selfPrivileges"] = [{
                "accessControlOperations": [
                    AccessControlOperationE.create,
                    AccessControlOperationE.retrieve,
                    AccessControlOperationE.update,
                    AccessControlOperationE.delete,
                    AccessControlOperationE.notify,
                    AccessControlOperationE.discover
                ],
                "accessControlOriginators": ["/mn-cse-1"]
            }]


class DynamicAuthorizationConsultationController(OneM2MDefaultController):
    def _set_mandatory_create_attributes(self, values):
        super(DynamicAuthorizationConsultationController,
              self)._set_mandatory_create_attributes(values)

        # TODO(rkr): values is set here, but it's not set in the resource at the end when resource
        # TODO(rkr): is created
        if not values.get("dynamicAuthorizationPoA"):
            values["dynamicAuthorizationPoA"] = []
            # if not values.get("dynamicAuthorizationLifetime"):
            #     values["dynamicAuthorizationLifetime"] = ""


class SemanticDescriptorController(OneM2MDefaultController):

    @staticmethod
    def _check_descriptor_data(descriptor_data):
        try:
            data = base64.b64decode(descriptor_data)
        except binascii.Error:
            raise CSEContentsUnacceptable("The descriptor was not correctly base64 encoded.")

        try:
            g = Graph()
            g.parse(data=data, format="application/rdf+xml")
        except Exception:
            raise CSEContentsUnacceptable("The descriptor attribute does not conform to the "
                                          "RDF/XML syntax as defined in RDF 1.1 XML Syntax.")

    def _check_create_representation(self):
        super(SemanticDescriptorController, self)._check_create_representation()
        self._check_descriptor_data(self.values["descriptor"])

    def _prepare_resource(self):
        super(SemanticDescriptorController, self)._prepare_resource()
        res = self.result

        # delete "semanticOpExec" from the response.
        del res.attribute_values["semanticOpExec"]
        setattr(res, "semanticOpExec", None)

    def _check_update_representation(self):
        super(SemanticDescriptorController, self)._check_update_representation()

        values = self.request.content.get_values(True)
        if all(k in values for k in ("semanticOpExec", "descriptor")):
            # check if both attribute exist at the same time
            raise CSEContentsUnacceptable("bad request: both semanticOpExec and descriptor exist")
        elif "descriptor" in values:
            # verify if the descriptor conform to the RDF syntax or not
            self._check_descriptor_data(self.values["descriptor"])
        elif "semanticOpExec" in values:
            # verify if the semanticOpExec has a correct SPAROL syntax
            try:
                parse(values["semanticOpExec"])
            except Exception:
                raise CSEContentsUnacceptable("The semanticOpExec attribute does not conform to "
                                              "the SPARQL query syntax.")
        else:
            raise CSESyntaxError("Please provide an updated descriptor or a semanticOpExec")
