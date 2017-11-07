# notes:
# - adds creation of a container for devices
# - introduces function for random sensor data generation
# - introduces endless loop


from openmtc_app.onem2m import XAE
from openmtc_onem2m.model import Container


class TestIPE(XAE):
    remove_registration = True

    def _on_register(self):
        # init base structure
        label = 'devices'
        container = Container(resourceName=label)
        self._devices_container = self.create_container(None,
                                                        container,
                                                        labels=[label],
                                                        max_nr_of_instances=0)

        # create some random data for a random sensor
        self.get_random_data()

        # log message
        self.logger.debug('registered')

        # start endless loop
        self.run_forever()

    def get_random_data(self):
        pass


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:8000'
    app = TestIPE()
    Runner(app).run(host)
