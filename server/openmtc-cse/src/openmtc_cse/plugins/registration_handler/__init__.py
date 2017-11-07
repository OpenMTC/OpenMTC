from openmtc_onem2m.exc import (CSENotFound, CSEError, STATUS_CONFLICT,
                                CSETargetNotReachable, CSEConflict)
from openmtc_onem2m.model import RemoteCSE, CSETypeIDE, CSEBase, Subscription
from openmtc_onem2m.transport import (OneM2MRequest, OneM2MOperation,
                                      OneM2MErrorResponse)
from openmtc_server.Plugin import Plugin
from openmtc_server.exc import ConfigurationError

from openmtc_cse.util import ExpTimeUpdater


class RegistrationHandler(Plugin):
    """ Plugin to register this CSE with other CSEs.
    """
    # defaults:
    DEF_INTERVAL = 60 * 60
    DEF_OFFSET = 60 * 60

    DEF_INTERVAL = 5
    DEF_OFFSET = 10

    @property
    def remote_cses(self):
        return self.config.get("remote_cses") or ()

    @property
    def get_interval(self):
        """ ExpirationTime update interval.
        """
        return self.config.get("interval", self.DEF_INTERVAL)

    @property
    def originator(self):
        return self.cse_id

    @property
    def get_offset(self):
        """ Offset added to ExpirationTime to ensure it can be met early.
        """
        return self.config.get("offset", self.DEF_OFFSET)

    def _init(self):
        try:
            onem2m_config = self.config["onem2m"]
        except KeyError:
            raise ConfigurationError("No onem2m config part!")

        # cse id
        try:
            self.cse_id = "/" + onem2m_config["cse_id"]
        except KeyError:
            raise ConfigurationError("Missing configuration key: cse_id")

        # cse type
        cse_type = onem2m_config.get("cse_type")
        try:
            cse_type = getattr(CSETypeIDE,
                               str(cse_type).replace("-", "_").upper())
        except (AttributeError, TypeError, ValueError):
            raise ConfigurationError("Invalid value for 'cse_type': %s" %
                                     (cse_type,))
        self.cse_type = CSETypeIDE(cse_type)

        self.cse_base = onem2m_config.get("cse_base", "onem2m")
        self.labels = self.config.get("labels", [])

        self.__registrations = []
        self._initialized()

    def _start(self):
        """ Creates the CSE resource on the registered-to CSE.
            Starts an ExpTimeUpdater for this resource.
        """
        self.refresher = None
        self._registered = False
        self._register()
        self._started()

    def _handle_registration_error(self, error):
        self.logger.warn("Could not register: %s", error)
        self.__timer = self.api.set_timer(12000, self._register)

    def _register(self):
        try:    # todo: put this into own method
            self.refresher = ExpTimeUpdater(interval=self.get_interval,
                                            offset=self.get_offset)
        except Exception as e:
            self.logger.warn("The refresher was not started: %s", e)

        try:
            self._handle_remote_cses()
        except CSEError as e:
            self._handle_registration_error(e)

    def _handle_remote_cses(self, handle_remote_cse_method=None):
        remote_cses = self.remote_cses

        # default handle method like it used to be
        if not handle_remote_cse_method:
            handle_remote_cse_method = self._handle_remote_cse

        if not remote_cses:
            self.logger.info("No remote CSEs configured")
            return

        # add poa information
        for remote_cse in remote_cses:
            remote_cse_id = remote_cse.get("cse_id")
            if remote_cse_id:
                remote_cse_poa = remote_cse.get("poa", [])
                self.api.add_poa_list(remote_cse_id, remote_cse_poa)

        return map(handle_remote_cse_method, remote_cses)

    def _handle_remote_cse_delete(self, remote_cse):
        """ Sends a delete request for the RemoteCSE resource.
        """
        try:
            remote_cse_id = "/" + remote_cse["cse_id"]
        except KeyError:
            raise ConfigurationError('Missing parameter (cse_id) in %s' %
                                     remote_cse)
        remote_cse_base = remote_cse.get("cse_base", "onem2m")

        def _delete_remote_cse_base():
            to = remote_cse_id + '/' + remote_cse_base + self.cse_id
            request = OneM2MRequest(OneM2MOperation.delete, to,
                                    self.originator)
            return self.api.send_onem2m_request(request)

        _delete_remote_cse_base()

    def _handle_remote_cse(self, remote_cse):
        """ Sends a create request for the RemoteCSE resource.
            Retrieves resource data afterwards.

            @return: RemoteCSE instance representing the created resource.
        """

        try:
            remote_cse_id = "/" + remote_cse["cse_id"]
        except KeyError:
            raise ConfigurationError('Missing parameter (cse_id) in %s' %
                                     remote_cse)

        # cse type
        remote_cse_type = remote_cse.get("cse_type")
        try:
            remote_cse_type = getattr(CSETypeIDE, str(
                remote_cse_type).replace("-", "_").upper())
        except (AttributeError, TypeError, ValueError):
            raise ConfigurationError("Invalid value for 'cse_type': %s" %
                                     (remote_cse_type,))
        remote_cse_type = CSETypeIDE(remote_cse_type)

        remote_cse_base = remote_cse.get("cse_base", "onem2m")

        remote_cse_uri = remote_cse_id + '/' + remote_cse_base

        self.logger.info("registering %s at %s", self.cse_id, remote_cse_id)

        def _create_own_remote_cse_remotely():
            endpoints = self.api.get_onem2m_endpoints()

            from openmtc.util import datetime_the_future

            # init RemoteCSE object
            cse = RemoteCSE(resourceName=self.cse_id[1:],
                            labels=self.labels,
                            cseType=self.cse_type,
                            pointOfAccess=endpoints,
                            CSEBase=self.cse_base,
                            CSE_ID=self.cse_id,
                            requestReachability=bool(len(endpoints)),
                            expirationTime=datetime_the_future(self.get_offset)
                            )
            if remote_cse.get('own_poa'):
                cse.pointOfAccess = remote_cse.get('own_poa')

            request = OneM2MRequest(OneM2MOperation.create, remote_cse_uri,
                                    self.originator,
                                    ty=RemoteCSE,
                                    pc=cse)

            return self.api.send_onem2m_request(request)

        def _retrieve_remote_cse_base():
            request = OneM2MRequest(OneM2MOperation.retrieve, remote_cse_uri,
                                    self.originator,
                                    ty=CSEBase)
            return self.api.send_onem2m_request(request)

        def _create_remote_cse_locally(cse_base):
            cse = RemoteCSE(resourceName=remote_cse_id[1:],
                            CSEBase=remote_cse_base,
                            CSE_ID=remote_cse_id,
                            cseType=remote_cse_type,
                            pointOfAccess=cse_base.pointOfAccess)
            cse.pointOfAccess = remote_cse.get('poa')

            request = OneM2MRequest(OneM2MOperation.create, self.cse_base,
                                    self.originator,
                                    ty=RemoteCSE,
                                    pc=cse)

            return self.api.handle_onem2m_request(request)

        try:
            instance = _create_own_remote_cse_remotely().get().content

            def _update_function(updated_instance):
                self._handle_remote_cse_update_expiration_time(remote_cse,
                                                               updated_instance)

            self.refresher.start(instance, send_update=_update_function)
        except CSETargetNotReachable as e_not_reachable:
            # TODO(rst): print error message
            raise e_not_reachable
        except OneM2MErrorResponse as error_response:
            if error_response.response_status_code == STATUS_CONFLICT:
                # TODO(rst): handle conflict here
                raise CSEConflict()
        else:
            retrieved_cse_base = _retrieve_remote_cse_base().get().content
            if retrieved_cse_base is None:
                raise CSENotFound()
            _create_remote_cse_locally(retrieved_cse_base).get()

    def _handle_remote_cse_update_expiration_time(self, remote_cse,
                                                  instance=None):
        """ Sends a update request for the RemoteCSE resource.
            Retrieves resource data afterwards.

            @return: RemoteCSE instance representing the created resource.
        """
        try:
            remote_cse_id = "/" + remote_cse["cse_id"]
        except KeyError:
            raise ConfigurationError('Missing parameter (cse_id) in %s' %
                                     remote_cse)
        # cse type
        remote_cse_type = remote_cse.get("cse_type")
        try:
            remote_cse_type = getattr(CSETypeIDE, str(
                remote_cse_type).replace("-", "_").upper())
        except (AttributeError, TypeError, ValueError):
            raise ConfigurationError("Invalid value for 'cse_type': %s" %
                                     (remote_cse_type,))

        def _update_own_remote_cse_remotely():
            cse = RemoteCSE(
                expirationTime=instance.expirationTime
            )
            # todo: need to check format here?
            to = remote_cse_id + "/" + instance.resourceID
            request = OneM2MRequest(OneM2MOperation.update, to,
                                    fr=self.originator,
                                    ty=RemoteCSE,
                                    pc=cse
                                    )
            return self.api.send_onem2m_request(request)

        try:
            _update_own_remote_cse_remotely().get()
        except CSETargetNotReachable as e_not_reachable:
            raise e_not_reachable
        except OneM2MErrorResponse as error_response:
            if error_response.response_status_code == STATUS_CONFLICT:
                raise CSEConflict()
        else:
            pass

    def _handle_remote_cse_update_endpoints(self, remote_cse, instance):
        self.logger.debug("Updating endpoints in remote cse: %s", remote_cse)
        self.logger.warn("Not implemented yet")
        # todo: implement this

    def _handle_endpoint_change(self, csebase, req):
        self._handle_remote_cses(self._handle_endpoint_change)

    def _register_events(self):
        self.events.resource_updated.register_handler(
            self._handle_endpoint_change, CSEBase)

    def _subscribe_remote_endpoints(self):
        """ subscribe to the remote basecse resources, to get notified if
            something changes
            todo: fix and activate, needs notification server
        """
        def __subscribe(remote_cse):
            try:
                remote_cse_id = "/" + remote_cse["cse_id"]
            except KeyError:
                raise ConfigurationError('Missing parameter (cse_id) in %s' %
                                         remote_cse)
            subs = Subscription(notificationURI=self.api.get_onem2m_endpoints())
            to = remote_cse_id + "/" + remote_cse.get("cse_base", "onem2m")
            request = OneM2MRequest(OneM2MOperation.create, to,
                                    self.originator,
                                    ty=Subscription,
                                    pc=subs)
            return self.api.send_onem2m_request(request)

        self._handle_remote_cses(handle_remote_cse_method=__subscribe)

    def _start_refresher(self, instance):
        self.refresher.start(instance)

    def _stop(self):
        """ Stops the plugin.
            DELETES CSE resource.
        """
        self._handle_remote_cses(
            handle_remote_cse_method=self._handle_remote_cse_delete)

        try:
            self.api.cancel_timer(self.__timer)
        except AttributeError:
            pass

        try:
            self.refresher.stop()
        except AttributeError:
            pass

        if self._registered:
            pass

        self._stopped()
