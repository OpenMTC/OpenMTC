# IPE-sensors demo app


The [ipe-sensors demo applications](./apps/onem2m/ipe/sensors/) generates data from (virtual) sensors and sends them to the CSE. The demo application is extended incrementally from the basic app frame to the complete IPE-sensors demo application.


## Step 1: [onem2m-ipe-sensors-01.py](./apps/onem2m/ipe/sensors/onem2m-ipe-sensors-01.py)

* added base structure

``` py
from openmtc_app.onem2m import XAE


class TestIPE(XAE):
    remove_registration = True

    def _on_register(self):
        # log message
        self.logger.debug('registered')


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:8000'
    app = TestIPE()
    Runner(app).run(host)
```


## Step 2: [onem2m-ipe-sensors-02.py](./apps/onem2m/ipe/sensors/onem2m-ipe-sensors-02.py)

* adds creation of a container for devices
* introduces function for random sensor data generation
* introduces endless loop

``` py
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
```


## Step 3: [onem2m-ipe-sensors-03.py](./apps/onem2m/ipe/sensors/onem2m-ipe-sensors-03.py)

* adds random
* spawns run_forever with get_random_data function every one second
* prints some random value operations

``` py
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
```


## Step 4: [onem2m-ipe-sensors-04.py](./apps/onem2m/ipe/sensors/onem2m-ipe-sensors-04.py)

* introducing list of sensors to create
* introducing settings for random sensor data generation
* adding code for random time intervals
* adding code for random sensor selection
* adding code for random sensor data generation

``` py
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
```


## Step 5: [onem2m-ipe-sensors-05.py](./apps/onem2m/ipe/sensors/onem2m-ipe-sensors-05.py)

* adds different range and offset for temperature and humidity value generation
* introducing self._recognized_sensors variable
* completing get_random_data() function
* introducing handle_sensor_data() function
* introducing create_sensor_structure() function
* introducing push_sensor_data() function

``` py
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
    threshold = 0.2
    temp_range = 25
    temp_offset = 10
    humi_range = 50
    humi_offset = 30

    def _on_register(self):

        # init variables
        self._recognized_sensors = {}

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

        # at random time intervals
        if random() > self.threshold:

            # select a random sensor
            sensor = self.sensors[int(random() * len(self.sensors))]

            # set parameters depending on sensor type
            if sensor.startswith('Temp'):
                value_range = self.temp_range
                value_offset = self.temp_offset
            else:
                value_range = self.humi_range
                value_offset = self.humi_offset

            # generate random sensor data
            value = int(random() * value_range + value_offset)
            self.handle_sensor_data(sensor, value)

    def handle_sensor_data(self, sensor, value):

        # initialize sensor structure if never done before
        if sensor not in self._recognized_sensors:
            self.create_sensor_structure(sensor)
        self.push_sensor_data(sensor, value)

    def create_sensor_structure(self, sensor):
        print('I need to create a structure for the sensor %s.' % sensor)
        self._recognized_sensors[sensor] = 'something useful'

    def push_sensor_data(self, sensor, value):
        print('I would push the content %i of %s to the gateway.' % (value, sensor))


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:8000'
    app = TestIPE()
    Runner(app).run(host)
```


## Step 6: [onem2m-ipe-sensors-06.py](./apps/onem2m/ipe/sensors/onem2m-ipe-sensors-06.py)

* added create sensor container to function create_sensor_structure()
* add sensor to _recognized_sensors
* build data set with value and metadata
* printing out the new data set

``` py
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
    threshold = 0.2
    temp_range = 25
    temp_offset = 10
    humi_range = 50
    humi_offset = 30

    def _on_register(self):

        # init variables
        self._recognized_sensors = {}

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

        # at random time intervals
        if random() > self.threshold:

            # select a random sensor
            sensor = self.sensors[int(random() * len(self.sensors))]

            # set parameters depending on sensor type
            if sensor.startswith('Temp'):
                value_range = self.temp_range
                value_offset = self.temp_offset
            else:
                value_range = self.humi_range
                value_offset = self.humi_offset

            # generate random sensor data
            value = int(random() * value_range + value_offset)
            self.handle_sensor_data(sensor, value)

    def handle_sensor_data(self, sensor, value):

        # initialize sensor structure if never done before
        if sensor not in self._recognized_sensors:
            self.create_sensor_structure(sensor)
        self.push_sensor_data(sensor, value)

    def create_sensor_structure(self, sensor):
        print('initializing sensor: %s' % sensor)

        # create sensor container
        device_container = Container(resourceName=sensor)
        device_container = self.create_container(self._devices_container.path,
                                                 device_container,
                                                 labels=['sensor'],
                                                 max_nr_of_instances=0)

        # add sensor to _recognized_sensors
        self._recognized_sensors[sensor] = device_container

    def push_sensor_data(self, sensor, value):

        # build data set with value and metadata
        if sensor.startswith('Temp'):
            data = {
                'value': value,
                'type': 'temperature',
                'unit': 'degreeC'
            }
        else:
            data = {
                'value': value,
                'type': 'humidity',
                'unit': 'percentage'
            }

        # print the new data set
        print('%s: %s' % (sensor, data))


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:8000'
    app = TestIPE()
    Runner(app).run(host)
```


## Step 7: [onem2m-ipe-sensors-07.py](./apps/onem2m/ipe/sensors/onem2m-ipe-sensors-07.py)

* introduced self._measurement_containers variable
* added creation of measurements container in function create_sensor_structure()
* added push of data to measurements_container of the sensor in function push_sensor_data()

``` py
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
    threshold = 0.2
    temp_range = 25
    temp_offset = 10
    humi_range = 50
    humi_offset = 30

    def _on_register(self):

        # init variables
        self._recognized_sensors = {}
        self._recognized_measurement_containers = {}

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

        # at random time intervals
        if random() > self.threshold:

            # select a random sensor
            sensor = self.sensors[int(random() * len(self.sensors))]

            # set parameters depending on sensor type
            if sensor.startswith('Temp'):
                value_range = self.temp_range
                value_offset = self.temp_offset
            else:
                value_range = self.humi_range
                value_offset = self.humi_offset

            # generate random sensor data
            value = int(random() * value_range + value_offset)
            self.handle_sensor_data(sensor, value)

    def handle_sensor_data(self, sensor, value):

        # initialize sensor structure if never done before
        if sensor not in self._recognized_sensors:
            self.create_sensor_structure(sensor)
        self.push_sensor_data(sensor, value)

    def create_sensor_structure(self, sensor):
        print('initializing sensor: %s' % sensor)

        # create sensor container
        device_container = Container(resourceName=sensor)
        device_container = self.create_container(self._devices_container.path,
                                                 device_container,
                                                 labels=['sensor'],
                                                 max_nr_of_instances=0)

        # add sensor to _recognized_sensors
        self._recognized_sensors[sensor] = device_container

        # create measurements container
        labels = ['measurements']
        if sensor.startswith('Temp'):
            labels.append('temperature')
        else:
            labels.append('humidity')
        measurements_container = Container(resourceName='measurements')
        measurements_container = self.create_container(device_container.path,
                                                       measurements_container,
                                                       labels=labels,
                                                       max_nr_of_instances=3)

        # add measurements_container from sensor to _recognized_measurement_containers
        self._recognized_measurement_containers[sensor] = measurements_container

    def push_sensor_data(self, sensor, value):

        # build data set with value and metadata
        if sensor.startswith('Temp'):
            data = {
                'value': value,
                'type': 'temperature',
                'unit': 'degreeC'
            }
        else:
            data = {
                'value': value,
                'type': 'humidity',
                'unit': 'percentage'
            }

        # print the new data set
        print ('%s: %s' % (sensor, data))

        # finally, push the data set to measurements_container of the sensor
        self.push_content(self._recognized_measurement_containers[sensor], data)


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:8000'
    app = TestIPE()
    Runner(app).run(host)
```

