# notes:
# - extend the handle_measurements() function to push new commands based on measurements to the actuators


from openmtc_app.onem2m import XAE


class TestGUI(XAE):
    remove_registration = True
    remote_cse = '/mn-cse-1/onem2m'

    def _on_register(self):
        # init variables
        self.actuators = []
        # start periodic discovery of 'measurements' containers
        self.periodic_discover(
            self.remote_cse,                    # start directory inside cse for discovery
            {'labels': ['measurements']},       # filter criteria (what to discover)
            1,                                  # frequency of repeated discovery (in Hz)
            self.handle_discovery_measurements  # callback function to return the result of the discovery to)
        )
        # start periodic discovery of 'commands' containers
        self.periodic_discover(
            self.remote_cse,                # start directory inside cse for discovery
            {'labels': ['commands']},       # filter criteria (what to discover)
            1,                              # frequency of repeated discovery (in Hz)
            self.handle_discovery_commands  # callback function to return the result of the discovery to)
        )

    def handle_discovery_measurements(self, discovery):
        # for each device container discovered
        for uri in discovery:
            # subscribe to device container with handler function
            print('Subscribing to Resource: %s' % uri)
            self.add_container_subscription(uri, self.handle_measurements)

    def handle_discovery_commands(self, discovery):
        # for every 'commands' container discovered
        for uri in discovery:
            print('discovered commands container: %s' % uri)
            # add discovered commands container to known actuators list
            self.actuators.append(uri)
            print('')

    def handle_measurements(self, container, data):
        print('handle_measurements...')
        print('container: %s' % container)
        print('data: %s' % data)
        # extract information from data set
        value = data['value']
        type_ = data['type']
        # simple logic to control the AirCon
        if type_ == 'temperature':
            if value >= 22:
                data = {'Power': 'ON'}
                print('Temperature = %s >= 22. Turning AirConditioning ON' % value)
            else:
                data = {'Power': 'OFF'}
                print('Temperature = %s < 22. Turning AirConditioning OFF' % value)
            # push the new command based on temperature measurements to all known AirCon actuators
            for actuator in self.actuators:
                if 'AirCon' in actuator:
                    self.push_content(actuator, data)
        # simple logic to control the Windows
        elif type_ == 'humidity':
            if value >= 65:
                data = {'State': 'OPEN'}
                print('Humidity = %s >= 65. OPEN Window' % value)
            else:
                data = {'State': 'CLOSE'}
                print('Humidity = %s < 65. CLOSE Window' % value)
            # push the new command based on humidity measurements to all known Window actuators
            for actuator in self.actuators:
                if 'Window' in actuator:
                    self.push_content(actuator, data)
        print('')


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner

    host = 'http://localhost:18000'
    app = TestGUI(
        poas=['http://localhost:21345']  # adds poas in order to receive notifications
    )
    Runner(app).run(host)
