import random
import string

from enum import Enum, unique

from futile.logging import get_logger
from openmtc.model import StrEnum
from openmtc_onem2m.exc import OneM2MError, STATUS, get_response_status


@unique
class RequestMethod(Enum):
    create = "create"
    retrieve = "retrieve"
    update = "update"
    delete = "delete"
    notify = "notify"
    execute = "execute"
    observe = "observe"


_logger = get_logger(__name__)


class MetaInformation(object):
    def __init__(self, ri=None, ot=None, rqet=None, rset=None, rt=None, rd=None,
                 rc=None, rp=None, oet=None, ls=None, ec=None, da=None,
                 gid=None, role=None):
        """Meta info about request, contains:
           ri (Request Identifier),
           ot (optional originating timestamp),
           rqet (optional request expiration timestamp),
           rset (optional result expiration timestamp),
           rt (optional response type),
           rd (optional result destination),
           rc (optional result content),
           rp (optional response persistence),
           oet (optional operational execution time),
           ls (optional lifespan),
           ec (optional event category),
           da (optional delivery aggregation),
           gid (optional group request identifier)
           role ()
        """

    @property
    def ri(self):
        return self.identifier

    @ri.setter
    def ri(self, ri):
        self.identifier = ri

    @property
    def ot(self):
        return self.originating_timestamp

    @ot.setter
    def ot(self, ot):
        self.originating_timestamp = ot

    @property
    def rqet(self):
        return self.request_expiration_timestamp

    @rqet.setter
    def rqet(self, rqet):
        self.request_expiration_timestamp = rqet

    @property
    def rset(self):
        return self.result_expiration_timestamp

    @rset.setter
    def rset(self, rset):
        self.result_expiration_timestamp = rset

    @property
    def rt(self):
        return self.response_type

    @rt.setter
    def rt(self, rt):
        self.response_type = rt

    @property
    def rd(self):
        return self.result_destination

    @rd.setter
    def rd(self, rd):
        self.result_destination = rd

    @property
    def rc(self):
        return self.result_content

    @rc.setter
    def rc(self, rc):
        self.result_content = rc

    @property
    def rp(self):
        return self.response_persistence

    @rp.setter
    def rp(self, rp):
        self.response_persistence = rp

    @property
    def oet(self):
        return self.operational_execution_time

    @oet.setter
    def oet(self, oet):
        self.operational_execution_time = oet

    @property
    def ec(self):
        return self.event_category

    @ec.setter
    def ec(self, ec):
        self.event_category = ec

    @property
    def ls(self):
        return self.lifespan

    @ls.setter
    def ls(self, ls):
        self.lifespan = ls

    @property
    def da(self):
        return self.delivery_aggregation

    @da.setter
    def da(self, da):
        self.delivery_aggregation = da

    @property
    def gid(self):
        return self.group_request_identifier

    @gid.setter
    def gid(self, gid):
        self.group_request_identifier = gid

    @property
    def ro(self):
        return self.role

    @ro.setter
    def ro(self, ro):
        self.role = ro

    def __str__(self):
        s = ''
        for k in self.__dict__:
            if getattr(self, k):
                s = s + ' | mi.' + str(k) + ': ' + str(self.__dict__[k])
        return s


MI = MetaInformation


class AdditionalInformation(object):
    def __init__(self, cs=None, ra=None):
        """Optional additional information about the request, contains:
            cs (optional, status codes),
            ra (optional, address for the temporary storage of end node Responses)
        """
        self.cs = cs
        self.ra = ra

    def __str__(self):
        s = ''
        for k in self.__dict__:
            if getattr(self, k):
                s = s + ' | ai.' + str(k) + ': ' + str(self.__dict__[k])
        return s


AI = AdditionalInformation


class OneM2MOperation(StrEnum):
    create = "create"
    retrieve = "retrieve"
    update = "update"
    delete = "delete"
    notify = "notify"


class OneM2MRequest(object):
    internal = False
    cascading = False
    ae_notifying = False

    """Class representing a OneM2M request"""

    def __init__(self, op, to, fr=None, rqi=None, ty=None, pc=None, rids=None,
                 ot=None, rqet=None, rset=None, oet=None, rt=None, rp=None,
                 rcn=None, ec=None, da=None, gid=None, filter_criteria=None,
                 fc=None, drt=None, tids=None, ltids=None, tqi=None, rvi=None,
                 vsi=None):
        # Operation
        self.operation = op
        # Target uri
        self.to = to
        # Originator ID
        self.originator = fr  # original long name is from
        self.request_identifier = rqi or ''.join(
            random.sample(string.ascii_letters + string.digits, 16)
        )
        # Type of a created resource
        self.resource_type = ty
        # Resource content to be transferred.
        self.content = pc
        self.role_ids = rids
        self.originating_timestamp = ot
        self.request_expiration_timestamp = rqet
        self.result_expiration_timestamp = rset
        self.operation_execution_time = oet
        self.response_type = rt
        self.result_persistence = rp
        self.result_content = rcn
        self.event_category = ec
        self.delivery_aggregation = da
        self.group_request_identifier = gid
        self.filter_criteria = filter_criteria or fc
        # Optional Discovery result type
        self.discovery_result_type = drt
        self.token_ids = tids
        self.local_token_ids = ltids
        self.token_request_identifier = tqi
        self.release_version_indicator = rvi
        self.vendor_information = vsi

    @property
    def op(self):
        return self.operation

    @op.setter
    def op(self, op):
        self.operation = op

    @property
    def fr(self):
        return self.originator

    @fr.setter
    def fr(self, fr):
        self.originator = fr

    @property
    def rqi(self):
        return self.request_identifier

    @rqi.setter
    def rqi(self, rqi):
        self.request_identifier = rqi

    @property
    def ty(self):
        return self.resource_type

    @ty.setter
    def ty(self, ty):
        self.resource_type = ty

    @property
    def pc(self):
        return self.content

    @pc.setter
    def pc(self, pc):
        self.content = pc

    @property
    def rids(self):
        return self.role_ids

    @rids.setter
    def rids(self, rids):
        self.role_ids = rids

    @property
    def ot(self):
        return self.originating_timestamp

    @ot.setter
    def ot(self, ot):
        self.originating_timestamp = ot

    @property
    def rqet(self):
        return self.request_expiration_timestamp

    @rqet.setter
    def rqet(self, rqet):
        self.request_expiration_timestamp = rqet

    @property
    def rset(self):
        return self.result_expiration_timestamp

    @rset.setter
    def rset(self, rset):
        self.result_expiration_timestamp = rset

    @property
    def oet(self):
        return self.operation_execution_time

    @oet.setter
    def oet(self, oet):
        self.operation_execution_time = oet

    @property
    def rt(self):
        return self.response_type

    @rt.setter
    def rt(self, rt):
        self.response_type = rt

    @property
    def rp(self):
        return self.result_persistence

    @rp.setter
    def rp(self, rp):
        self.result_persistence = rp

    @property
    def rcn(self):
        return self.result_content

    @rcn.setter
    def rcn(self, rcn):
        self.result_content = rcn

    @property
    def ec(self):
        return self.event_category

    @ec.setter
    def ec(self, ec):
        self.event_category = ec

    @property
    def da(self):
        return self.delivery_aggregation

    @da.setter
    def da(self, da):
        self.delivery_aggregation = da

    @property
    def gid(self):
        return self.group_request_identifier

    @gid.setter
    def gid(self, gid):
        self.group_request_identifier = gid

    @property
    def fc(self):
        return self.filter_criteria

    @fc.setter
    def fc(self, fc):
        self.filter_criteria = fc

    @property
    def drt(self):
        return self.discovery_result_type

    @drt.setter
    def drt(self, drt):
        self.discovery_result_type = drt

    @property
    def tids(self):
        return self.token_ids

    @tids.setter
    def tids(self, tids):
        self.token_ids = tids

    @property
    def ltids(self):
        return self.local_token_ids

    @ltids.setter
    def ltids(self, rvi):
        self.local_token_ids = ltids

    @property
    def tqi(self):
        return self.token_request_identifier

    @tqi.setter
    def tqi(self, tqi):
        self.token_request_identifier = tqi

    @property
    def rvi(self):
        return self.release_version_indicator

    @rvi.setter
    def rvi(self, rvi):
        self.release_version_indicator = rvi

    @property
    def vsi(self):
        return self.vendor_information

    @vsi.setter
    def vsi(self, vsi):
        self.vendor_information = vsi

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, ' | '.join([
            '%s: %s' % (str(k), str(v)) for k, v in self.__dict__.items()
        ]))


class OneM2MResponse(object):
    """Class representing a OneM2M response"""

    def __init__(self, status_code, request=None, rqi=None, pc=None, to=None,
                 fr=None, rsc=None, ot=None, rset=None, ec=None, cts=None,
                 cto=None, rvi=None, vsi=None, fields=None):
        # Operation result
        if isinstance(status_code, STATUS):
            self.response_status_code = status_code
        else:
            self.response_status_code = get_response_status(status_code)
        if request:
            self.request_identifier = request.rqi
            # Target uri
            self.to = request.to
            # Originator ID
            self.originator = request.fr
            self.originating_timestamp = request.ot
            self.result_expiration_timestamp = request.rset
            self.event_category = request.ec
            self.release_version_indicator = request.rvi
            self.vendor_information = request.vsi
        else:
            self.request_identifier = rqi
            # Target uri
            self.to = to
            # Originator ID
            self.originator = fr
            self.originating_timestamp = ot
            self.release_version_indicator = rvi
            self.vendor_information = vsi
        self.result_expiration_timestamp = rset
        self.event_category = ec
        # Resource content to be transferred.
        self.content = pc
        self.content_status = cts
        self.content_offset = cto
        self.fields = fields

    @property
    def status_code(self):
        return self.response_status_code.http_status_code

    @property
    def rsc(self):
        return self.response_status_code.numeric_code

    @property
    def rqi(self):
        return self.request_identifier

    @rqi.setter
    def rqi(self, rqi):
        self.request_identifier = rqi

    @property
    def pc(self):
        return self.content

    @pc.setter
    def pc(self, pc):
        self.content = pc

    @property
    def fr(self):
        return self.originator

    @fr.setter
    def fr(self, fr):
        self.originator = fr

    @property
    def ot(self):
        return self.originating_timestamp

    @ot.setter
    def ot(self, ot):
        self.originating_timestamp = ot

    @property
    def rset(self):
        return self.result_expiration_timestamp

    @rset.setter
    def rset(self, rset):
        self.result_expiration_timestamp = rset

    @property
    def ec(self):
        return self.event_category

    @ec.setter
    def ec(self, ec):
        self.event_category = ec

    @property
    def cts(self):
        return self.content_status

    @cts.setter
    def cts(self, cts):
        self.content_status = cts

    @property
    def cto(self):
        return self.content_offset

    @cto.setter
    def cto(self, cto):
        self.content_offset = cto

    @property
    def rvi(self):
        return self.release_version_indicator

    @rvi.setter
    def rvi(self, rvi):
        self.release_version_indicator = rvi

    @property
    def vsi(self):
        return self.vendor_information

    @vsi.setter
    def vsi(self, vsi):
        self.vendor_information = vsi

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, ' | '.join([
            '%s: %s' % (str(k), str(v)) for k, v in self.__dict__.items()
        ]))


class OneM2MErrorResponse(OneM2MResponse, OneM2MError):
    pass
