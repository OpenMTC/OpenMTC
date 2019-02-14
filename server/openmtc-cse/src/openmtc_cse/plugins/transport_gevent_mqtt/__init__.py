from openmtc_cse import OneM2MEndPoint
from openmtc_cse.methoddomain.filtercriteria import parse_filter_criteria
from openmtc_onem2m.model import get_long_member_name
from openmtc_server.Plugin import Plugin
from openmtc_server.configuration import Configuration
from openmtc_onem2m.client.mqtt import get_client, portmap


class MQTTTransportPluginConfiguration(Configuration):
    __name__ = "MQTTTransportPluginConfiguration configuration"


class MQTTTransportPlugin(Plugin):
    __configuration__ = MQTTTransportPluginConfiguration

    def _init(self):
        self._initialized()

    def _start(self):
        self.api.register_onem2m_client(list(portmap.keys()), get_client)
        interface = self.config.get('interface', '127.0.0.1')
        port = self.config.get('port', 1883)
        try:
            scheme = list(portmap.keys())[list(portmap.values()).index(port)]
        except (KeyError, ValueError):
            scheme = 'mqtt'

        def handle_request_func(onem2m_request):
            if onem2m_request.fc:
                onem2m_request.fc = parse_filter_criteria({
                    get_long_member_name(k): v for k, v in onem2m_request.fc.items()
                })

            return self.api.handle_onem2m_request(onem2m_request)

        self._client = get_client(
            ''.join([
                scheme,
                '://',
                interface,
                ':',
                str(port),
            ]),
            handle_request_func=handle_request_func,
            client_id=self.config['onem2m'].get('cse_id'),
        )

        self.api.register_point_of_access(
            OneM2MEndPoint(scheme=scheme, server_address=interface, port=port))

        self._started()

    def _stop(self):
        self._client.stop()
        self._stopped()
