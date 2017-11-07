# notes:
# - introducing list of sensors to create
# - introducing settings for random sensor data generation
# - adding code for random time intervals
# - adding code for random sensor selection
# - adding code for random sensor data generation


from random import random

from openmtc_app.onem2m import XAE
from openmtc_onem2m.model import Container


class TestIPE(XAE):
    remove_registration = True

    # sensors to create
    sensors = [
        'Temp-1',
        'Temp-2',
        'Humi-1',
        'Humi-2'
    ]

    # settings for random sensor data generation
    threshold = 0.5
    value_range = 25
    value_offset = 10

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
        print('')

        # for random time intervals
        if random() > self.threshold:
            print('got some data')

            # select a random sensor
            print('available sensors: %s' % self.sensors)
            print('number of available sensors: %s' % len(self.sensors))
            print('some random sensor: %s' % self.sensors[int(random() * len(self.sensors))])

            # generate random sensor data
            print('random sensor data: %s' % int(random() * self.value_range + self.value_offset))

        else:
            print('no data')


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:8000'
    app = TestIPE()
    Runner(app).run(host)
