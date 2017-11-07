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
        self.api.register_onem2m_client(portmap.keys(), get_client)
        interface = self.config.get('interface', '127.0.0.1')
        port = self.config.get('port', 1883)
        try:
            scheme = portmap.keys()[portmap.values().index(port)]
        except (KeyError, ValueError):
            scheme = 'mqtt'
        self._client = get_client(
            ''.join([
                scheme,
                '://',
                interface,
                ':',
                str(port),
            ]),
            handle_request_func=self.api.handle_onem2m_request,
            client_id=self.config['onem2m'].get('cse_id'),
        )
        self._started()

    def _stop(self):
        self._client.stop()
        self._stopped()
