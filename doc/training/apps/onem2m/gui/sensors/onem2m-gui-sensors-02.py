# notes:
# - adds filter criteria, to specify what to discover
# - detailed print of every uri from the discovery
# - this will only discover new container with the specific label 'measurements'
# - renamed function handle_discovery() to handle_discovery_measurements()


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
        print('New discovery:')
        # for each device container discovered
        for uri in discovery:
            # print content of discovery
            print('uri from discovery: %s' % uri)


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:18000'
    app = TestGUI()
    Runner(app).run(host)
