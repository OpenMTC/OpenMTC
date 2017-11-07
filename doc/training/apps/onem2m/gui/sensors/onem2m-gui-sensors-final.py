# notes:
# - complete example


from openmtc_app.onem2m import XAE


class TestGUI(XAE):
    remove_registration = True
    remote_cse = '/mn-cse-1/onem2m'

    def _on_register(self):
        # start periodic discovery of 'measurements' containers
        self.periodic_discover(
            self.remote_cse,                    # start directory inside cse for discovery
            {'labels': ['measurements']},       # filter criteria (what to discover)
            1,                                  # frequency of repeated discovery (in Hz)
            self.handle_discovery_measurements  # callback function to return the result of the discovery to)
        )

    def handle_discovery_measurements(self, discovery):
        # for each device container discovered
        for uri in discovery:
            # subscribe to device container with handler function
            print('Subscribing to Resource: %s' % uri)
            self.add_container_subscription(uri, self.handle_measurements)

    def handle_measurements(self, container, data):
        # this function handles the new data from subscribed measurements containers
        print('handle measurements..')
        print('container: %s' % container)
        print('data: %s' % data)
        print('')


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:18000'
    app = TestGUI(
        poas=['http://localhost:21345'],          # adds poas in order to receive notifications
        # SSL options
        originator_pre='//openmtc.org/in-cse-1',  # originator_pre, needs to match value in cert
        ca_certs='../../openmtc-gevent/certs/ca-chain.cert.pem',
        cert_file='certs/test-gui.cert.pem',      # cert file, pre-shipped and should match name
        key_file='certs/test-gui.key.pem'
    )
    Runner(app).run(host)
