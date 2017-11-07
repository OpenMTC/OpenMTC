# gui-sensors demo app


The [gui-sensors demo applications](/doc/training/apps/onem2m/gui/sensors/) receives data from the (virtual) sensors from the ipe-demo-apps and prints it to the console. The demo application is extended incrementally from the basic app frame to the complete gui-sensors demo application.


## Step 1: [onem2m-gui-sensors-01.py](/doc/training/apps/onem2m/gui/sensors/onem2m-gui-sensors-01.py)

* initial app base structure
* starts periodic discovery on registration
* the discovery result is printed as a whole
* this will discover EVERY new container

``` py
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
```


## Step 2: [onem2m-gui-sensors-02.py](/doc/training/apps/onem2m/gui/sensors/onem2m-gui-sensors-02.py)

* adds filter criteria, to specify what to discover
* detailed print of every uri from the discovery
* this will only discover new container with the specific label 'measurements'
* renamed function handle_discovery() to handle_discovery_measurements()

``` py
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
```


## Step 3: [onem2m-gui-sensors-03.py](/doc/training/apps/onem2m/gui/sensors/onem2m-gui-sensors-03.py)

* adds subscription to discovered containers via returned uri
* adds content handler for subscribed containers
* this will only discover and subscribe to new containers with the specific label
* whenever a child is created in the subscribed containers, the content handler is called

``` py
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
        # for each device container discovered
        for uri in discovery:
            # subscribe to device container with handler function
            print('Subscribing to Resource: %s' % uri)
            self.add_container_subscription(uri, self.handle_measurements)

    def handle_measurements(self, container, data):
        # this function handles the new data from subscribed measurements containers
        print('handle measurements..')
        print('container: %s' % container)
        print('data: %s' % data)
        print('')


if __name__ == '__main__':
    from openmtc_app.runner import AppRunner as Runner
    host = 'http://localhost:18000'
    app = TestGUI(
        poas=['http://localhost:21345']  # adds poas in order to receive notifications
    )
    Runner(app).run(host)
```

