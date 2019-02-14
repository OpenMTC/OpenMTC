from openmtc_app.onem2m import XAE


class SimpleDecision(XAE):
    remove_registration = True
    remote_cse = '/mn-cse-1/onem2m'
    period = 10

    def _on_register(self):
        # init variables
        self.switchContainers = []
        # start endless loop
        self.periodic_discover(self.remote_cse,
                               {'labels': ["openmtc:actuator_data"]},
                               self.period, self.handle_discovery_switch)
        self.periodic_discover(self.remote_cse,
                               {'labels': ["openmtc:sensor_data:command"]},
                               self.period, self.handle_discovery_command)
        self.periodic_discover(self.remote_cse,
                               {'labels': ["openmtc:sensor_data:brightness"]},
                               self.period, self.handle_discovery_brightness)

    def handle_discovery_switch(self, discovery):
        for uri in discovery:
            self.switchContainers.append(uri)

    def handle_discovery_command(self, discovery):
        for uri in discovery:
            self.add_container_subscription(uri, self.handle_command)

    def handle_discovery_brightness(self, discovery):
        for uri in discovery:
            self.add_container_subscription(uri, self.handle_brightness)

    def handle_command(self, container, content):
        command = "ON" if content[0]['v'] == 1 else "OFF"
        for switch in self.switchContainers:
            self.push_content(switch, command)

    def handle_brightness(self, container, content):
        command = "ON" if content[0]['v'] < 500.0 else "OFF"
        for switch in self.switchContainers:
            self.push_content(switch, command)


if __name__ == "__main__":
    from openmtc_app.flask_runner import SimpleFlaskRunner as Runner

    ep = "http://localhost:8000"
    Runner(SimpleDecision(poas=['http://localhost:22245'])).run(ep)
