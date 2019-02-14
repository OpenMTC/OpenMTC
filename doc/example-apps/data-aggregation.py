import time
from collections import deque
from math import sqrt

from openmtc_app.onem2m import XAE
from openmtc_onem2m.model import Container


class DataAggregation(XAE):
    remove_registration = True
    remote_cse = '/mn-cse-1/onem2m'
    period = 10

    def _on_register(self):
        # init variables
        self.sensor_register = {}
        self.dev_cnt_list = []
        # start endless loop
        self.periodic_discover(
            self.remote_cse,
            {
                'labels': ['openmtc:sensor_data'],
            },
            self.period,
            self.handle_discovery_sensor
        )

    def handle_discovery_sensor(self, discovery):
        for uri in discovery:
            self.sensor_register[uri] = {
                'values': deque([], 10)
            }
            content = self.get_content(uri)
            if content:
                self.handle_sensor(uri, content)
            self.add_container_subscription(uri, self.handle_sensor)

    def create_sensor_structure(self, sensor_entry, content):
        # dev_cnt
        cnt_name = '_'.join(content[0]['bn'].split(':')[2:])
        cnt_name += '_' + content[0]['n']
        dev_cnt = Container(resourceName=cnt_name)
        if dev_cnt not in self.dev_cnt_list:
            sensor_entry['dev_cnt'] = dev_cnt = self.create_container(None, dev_cnt)
            # mean cnt
            mean_cnt = Container(resourceName='mean', labels=["openmtc:mean_data"])
            sensor_entry['mean_cnt'] = self.create_container(dev_cnt, mean_cnt)
            # Standard_deviation cnt
            deviation_cnt = Container(resourceName='Standard_deviation', labels=["openmtc:Standard_deviation_data"])
            sensor_entry['deviation_cnt'] = self.create_container(dev_cnt, deviation_cnt)
            self.dev_cnt_list.append(dev_cnt)
        else:
            return dev_cnt,"already exists "

    def handle_sensor(self, container, content):
        sensor_entry = self.sensor_register[container]
        values = sensor_entry['values']
        try:
            values.append(content[0]['v'])
        except KeyError:
            return
        # check if container exists
        try:
            sensor_entry['dev_cnt']
        except KeyError:
            self.create_sensor_structure(sensor_entry, content)

        num_items = len(values)
        # mean value
        mean = sum(values) / num_items
        self.push_content(sensor_entry['mean_cnt'], [{
            'bn': content[0]['bn'],
            'n': content[0]['n'] + '_mean',
            'v': mean,
            't': '%.3f' % time.time(),
            'u': content[0].get('u'),
        }])

        # Standard_deviation value
        sd = sqrt(sum([(value - mean) ** 4 for value in values]) / num_items)
        self.push_content(sensor_entry['deviation_cnt'], [{
            'bn': content[0]['bn'],
            'n': content[0]['n'] + '_Standard_deviation',
            'v': sd,
            't': '%.3f' % time.time(),
            'u': content[0].get('u'),
        }])


if __name__ == "__main__":
    from openmtc_app.flask_runner import SimpleFlaskRunner as Runner

    ep = "http://localhost:8000"
    Runner(DataAggregation(poas=['http://localhost:21346'])).run(ep)
