# notes:
# - initial app base structure
# - starts periodic discovery on registration
# - the discovery result is printed as a whole
# - this will discover EVERY new container


from openmtc_app.onem2m import XAE


class TestGUI(XAE):
    remove_registration = True
    remote_cse = '/mn-cse-1/onem2m'

    def _on_register(self):
        # start periodic discovery of EVERY container
        self.periodic_discover(
            self.remote_cse,  # start directory inside cse for discovery
            None,  # no filter criteria
            1,  # frequency of repeated discovery (in Hz)
            self.handle_discovery  # callback function to return the result of the discovery to
        )

    def handle_discovery(self, discovery):
        # print the discovery
        print('New discovery:')
        print(discovery)
        print(' ')


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:18000'
    app = TestGUI()
    Runner(app).run(host)
