# notes:
# - adds random
# - spawns run_forever with get_random_data function every one second
# - prints some random value operations


from random import random

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

        # trigger periodically new data generation
        self.run_forever(1, self.get_random_data)

        # log message
        self.logger.debug('registered')

    def get_random_data(self):
        print('---------')
        random_value = random()
        print(random_value)
        print(random_value * 10)
        print(int(random_value * 10))


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:8000'
    app = TestIPE()
    Runner(app).run(host)
