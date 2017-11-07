import ssl
from socket import getservbyname

from openmtc_cse import OneM2MEndPoint
from openmtc_onem2m.client.http import get_client
from openmtc_server.Plugin import Plugin
from openmtc_server.configuration import Configuration, SimpleOption
from openmtc_server.platform.gevent.ServerRack import GEventServerRack
from .wsgi import OpenMTCWSGIServer, OpenMTCWSGIApplication, OpenMTCWSGIHandler


class HTTPTransportPluginConfiguration(Configuration):
    __name__ = "HTTPTransportPluginConfiguration configuration"
    __options__ = {
        "port": SimpleOption(int, default=8000)
    }


class HTTPTransportPlugin(Plugin):
    __configuration__ = HTTPTransportPluginConfiguration

    def _init(self):
        self._initialized()

    def _start_server_rack(self):
        servers = []

        interface = self.config.get("interface", "")

        ssl_certs = self.config.get("onem2m", {}).get("ssl_certs")
        key_file = ssl_certs.get("key")
        cert_file = ssl_certs.get("crt")
        ca_file = ssl_certs.get("ca")
        enable_https = self.config.get("enable_https", False)
        require_cert = self.config.get("require_cert", True)

        is_https = enable_https and key_file and cert_file and ca_file

        scheme = "https" if is_https else "http"

        port = self.config.get("port", getservbyname(scheme))

        default_content_type = self.config.get("global", {}).get(
            "default_content_type", False)

        pretty = self.config.get("global", {}).get("pretty", False)

        # the __call__ of the OpenMTCWSGIApplication should return a function,
        #   which is given to the WSGIServer as
        # the function that is called by the server for each incoming request
        application = OpenMTCWSGIApplication(
            self.api.handle_onem2m_request, server_address=interface,
            default_content_type=default_content_type, pretty=pretty,
            require_cert=require_cert
        )

        if is_https:
            # in WSGI the application consists of a single function
            # this function is called by the server for each request that the
            #   server has to handle
            servers.append(OpenMTCWSGIServer((interface, port), application,
                                             keyfile=key_file, certfile=cert_file,
                                             ca_certs=ca_file, cert_reqs=ssl.CERT_OPTIONAL,
                                             environ={'SERVER_NAME': 'openmtc.local'},
                                             handler_class=OpenMTCWSGIHandler,
                                             ssl_version=ssl.PROTOCOL_TLSv1_2
                                             ))
        else:
            servers.append(OpenMTCWSGIServer((interface, port), application,
                                             environ={'SERVER_NAME': 'openmtc.local'},
                                             handler_class=OpenMTCWSGIHandler))

        rack = self.__rack = GEventServerRack(servers)

        rack.start()

        return scheme, interface, port

    def _start(self):
        self.api.register_onem2m_client(("http", "https"), get_client)

        scheme, interface, port = self._start_server_rack()

        self.api.register_point_of_access(
            OneM2MEndPoint(scheme=scheme, server_address=interface, port=port))

        self._started()

    def _stop(self):
        self.__rack.stop()
        self._stopped()
