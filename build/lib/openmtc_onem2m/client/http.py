import urllib
import ssl
from socket import (
    gaierror,
    error as socket_error,
)
from time import time
from urlparse import urlparse
from aplus import Promise
from futile.caching import LRUCache
from geventhttpclient.client import HTTPClient
from geventhttpclient.response import HTTPResponse
from openmtc.exc import (
    OpenMTCNetworkError,
    ConnectionFailed,
)
from openmtc_onem2m.exc import (
    get_error_class,
    get_response_status,
    ERROR_MIN,
)
from openmtc_onem2m.model import (
    ResourceTypeE,
    get_short_attribute_name,
    get_short_member_name,
)
from openmtc_onem2m.serializer.util import (
    decode_onem2m_content,
    encode_onem2m_content,
)
from openmtc_onem2m.transport import (
    OneM2MOperation,
    OneM2MResponse,
    OneM2MErrorResponse,
)
from . import (
    OneM2MClient,
    normalize_path,
)

_method_map_to_http = {
    OneM2MOperation.create:     'POST',
    OneM2MOperation.retrieve:   'GET',
    OneM2MOperation.update:     'PUT',
    OneM2MOperation.delete:     'DELETE',
    OneM2MOperation.notify:     'POST',
}

_clients = LRUCache(threadsafe=False)

_query_params = frozenset(['rt', 'rp', 'rcn', 'da', 'drt'])

_header_to_field_map = {
    'X-M2M-ORIGIN': 'originator',
    'X-M2M-RI':     'rqi',
    'X-M2M-GID':    'gid',
    'X-M2M-OT':     'ot',
    'X-M2M-RST':    'rset',
    'X-M2M-RET':    'rqet',
    'X-M2M-OET':    'oet',
    'X-M2M-EC':     'ec',
}


def get_client(m2m_ep, use_xml=False, ca_certs=None, cert_file=None, key_file=None,
               insecure=False):
    try:
        return _clients[(m2m_ep, use_xml)]
    except KeyError:
        # TODO: make connection_timeout and concurrency configurable
        client = _clients[(m2m_ep, use_xml)] = OneM2MHTTPClient(
            m2m_ep, use_xml, ca_certs, cert_file, key_file, insecure)
        return client


class OneM2MHTTPClient(OneM2MClient):
    # defaults
    DEF_SSL_VERSION = ssl.PROTOCOL_TLSv1_2

    def __init__(self, m2m_ep, use_xml, ca_certs=None, cert_file=None, key_file=None,
                 insecure=False):
        super(OneM2MHTTPClient, self).__init__()

        self.parsed_url = urlparse(m2m_ep)
        is_https = self.parsed_url.scheme[-1].lower() == "s"
        port = self.parsed_url.port or (is_https and 443 or 80)
        host = self.parsed_url.hostname
        self.path = self.parsed_url.path.rstrip('/')
        if self.path and not self.path.endswith('/'):
            self.path += '/'

        # TODO(rst): handle IPv6 host here
        # geventhttpclient sets incorrect host header
        # i.e "host: ::1:8000" instead of "host: [::1]:8000
        if (is_https and ca_certs is not None and cert_file is not None and
                key_file is not None):
            ssl_options = {
                "ca_certs": ca_certs,
                "certfile": cert_file,
                "keyfile": key_file,
                "ssl_version": self.DEF_SSL_VERSION
            }
        else:
            ssl_options = None

        client = HTTPClient(host, port, connection_timeout=120.0,
                            concurrency=50, ssl=is_https,
                            ssl_options=ssl_options, insecure=insecure)
        self.request = client.request

        self.content_type = 'application/' + ('xml' if use_xml else 'json')

    def _handle_network_error(self, exc, p, http_request, t,
                              exc_class=OpenMTCNetworkError):
        error_str = str(exc)
        if error_str in ("", "''"):
            error_str = repr(exc)
        method = http_request["method"]
        path = http_request["request_uri"]
        log_path = "%s://%s/%s" % (self.parsed_url.scheme, self.parsed_url.netloc, path)
        error_msg = "Error during HTTP request: %s. " \
                    "Request was: %s %s (%.4fs)" % (error_str, method, log_path, time() - t)
        p.reject(exc_class(error_msg))

    def map_onem2m_request_to_http_request(self, onem2m_request):
        """
        Maps a OneM2M request to a HTTP request
        :param onem2m_request: OneM2M request to be mapped
        :return: request: the resulting HTTP request
        """
        self.logger.debug("Mapping OneM2M request to generic request: %s", onem2m_request)

        params = {
            param: getattr(onem2m_request, param) for param in _query_params
            if getattr(onem2m_request, param) is not None
        }

        if onem2m_request.fc is not None:
            filter_criteria = onem2m_request.fc
            params.update({
                (get_short_attribute_name(name) or get_short_member_name(name)): val
                for name, val in filter_criteria.get_values(True).iteritems()
            })

        path = normalize_path(onem2m_request.to)

        if params:
            path += '?' + urllib.urlencode(params, True)

        content_type, data = encode_onem2m_content(onem2m_request.content, self.content_type, path=path)

        # TODO(rst): check again
        # set resource type
        if onem2m_request.operation == OneM2MOperation.create:
            content_type += '; ty=' + str(ResourceTypeE[onem2m_request.resource_type.typename])

        headers = {
            header: getattr(onem2m_request, field) for header, field in _header_to_field_map.iteritems()
            if getattr(onem2m_request, field) is not None
        }
        headers['content-type'] = content_type

        self.logger.debug("Added request params: %s", params)

        return {
            'method':       _method_map_to_http[onem2m_request.operation],
            'request_uri':  self.path + path,
            'body':         data,
            'headers':      headers,
        }

    def map_http_response_to_onem2m_response(self, onem2m_request, response):
        """
        Maps HTTP response to OneM2M response
        :param onem2m_request: the OneM2M request that created the response
        :param response: the HTTP response
        :return: resulting OneM2MResponse or OneM2MErrorResponse
        """
        if not isinstance(response, HTTPResponse):
            self.logger.error("Not a valid response: %s", response)
            # return OneM2MErrorResponse(STATUS_INTERNAL_SERVER_ERROR)
        self.logger.debug("Mapping HTTP response for OneM2M response: %s", response)
        rsc = response.get("x-m2m-rsc", 5000)
        if int(rsc) >= ERROR_MIN:
            return OneM2MErrorResponse(
                get_error_class(rsc).response_status_code, onem2m_request)

        return OneM2MResponse(
            get_response_status(rsc),
            request=onem2m_request,
            rsc=rsc,
            pc=decode_onem2m_content(response.read(), response.get("content-type"))
        )

    def send_onem2m_request(self, onem2m_request):
        with Promise() as p:
            http_request = self.map_onem2m_request_to_http_request(onem2m_request)
            t = time()

            try:
                response = self.request(**http_request)
            except (socket_error, gaierror) as exc:
                self._handle_network_error(exc, p, http_request, t, ConnectionFailed)
            except Exception as exc:
                self.logger.exception("Error in HTTP request")
                self._handle_network_error(exc, p, http_request, t)
            else:
                try:
                    onem2m_response = self.map_http_response_to_onem2m_response(onem2m_request, response)
                    if isinstance(onem2m_response, OneM2MErrorResponse):
                        p.reject(onem2m_response)
                    else:
                        p.fulfill(onem2m_response)
                finally:
                    response.release()

        return p
