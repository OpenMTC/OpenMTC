
import urllib.request
import urllib.parse
import urllib.error
from openmtc_app.onem2m import XAE
import uuid


class DataVisualization(XAE):
    remove_registration = True
    remote_cse = '/mn-cse-1/onem2m'
    period = 10

    def _on_register(self):
        # init variables
        self.sensor_register = {}
        self.sensor_register = []
        self.sensor_values = []
        self.name = uuid.uuid1()
        self.things_name = urllib.request.urlopen("https://dweet.io/follow/%s" % self.name)
        print("Thing name :", self.name)
        print("link for the current data type and values :", self.things_name.geturl())
        # start endless loop
        self.periodic_discover(self.remote_cse,
                               {'labels': ["openmtc:sensor_data"]},
                               self.period, self.handle_discovery_sensor)

    def handle_discovery_sensor(self, discovery):
        for uri in discovery:
            self.add_container_subscription(uri, self.handle_sensor_data)

    def handle_sensor_data(self, container, content):
        data = {}
        self.sensor_register.append(content[0]['n'])
        self.sensor_values.append(content[0]['v'])
        for i, k in zip(self.sensor_register, self.sensor_values):
            data.update({i: k})
            params = urllib.parse.urlencode(data)
        urllib.request.urlopen("https://dweet.io/dweet/for/%s?%s" % (self.name, params))


if __name__ == "__main__":
    from openmtc_app.flask_runner import SimpleFlaskRunner as Runner

    ep = "http://localhost:8000"
    Runner(DataVisualization(poas=['http://localhost:21345'])).run(ep)


