"""
Copyright (c) 2017 Fraunhofer FOKUS
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from futile.logging import get_logger
from openmtc_app.onem2m import XAE
from openmtc_onem2m.model import CSETypeIDE, RemoteCSE

from orion_api import OrionAPI

logger = get_logger(__name__)


class OrionContextBroker(XAE):

    def __init__(self, labels=[""], interval=10,
                 orion_host="http://localhost:1026", orion_api="v2",
                 *args, **kw):
        super(OrionContextBroker, self).__init__(*args, **kw)
        self.labels = labels
        self.remove_registration = True
        self.interval = interval
        self.orion_api = OrionAPI(orion_host=orion_host, api_version=orion_api)

    def _on_register(self):
        # init variables
        self._known_remote_cses = {}
        self._discovered_devices = {}
        self._discovered_sensors = {}

        # connected to backend or gateway?
        cse_base = self.get_resource(self.cse_base)
        logger.debug("CSE_BASE: %s", cse_base)

        if (cse_base.cseType == CSETypeIDE.MN_CSE or
                cse_base.cseType == CSETypeIDE.AEN_CSE):
            logger.debug("CSE_BASE identified as gateway")
            # discover gateway
            self._discover_cse(cse_base.CSE_ID + '/' + self.cse_base)
        else:
            logger.debug("CSE_BASE identified as backend")
            # discover backend
            self._discover_cse(cse_base.CSE_ID + '/' + self.cse_base)
            # discover remote gateways
            self._get_remote_cses(cse_base)

    # get remote CSEs

    def _get_remote_cses(self, cse_base):

        def get_cse_base():
            handle_cse_base(self.get_resource(self.cse_base))

        def handle_cse_base(cb):
            for resource in cb.childResource:
                if (isinstance(resource, RemoteCSE) and
                        resource.path not in self._known_remote_cses):
                    remote_cse = self.get_resource(resource.id)
                    self._known_remote_cses[resource.path] = remote_cse
                    remote_cse_base = (remote_cse.CSE_ID + '/' +
                                       remote_cse.CSEBase)
                    self._discover_cse(remote_cse_base)

        handle_cse_base(cse_base)
        self.run_forever(self.interval, get_cse_base)

    # discover CSE
    def _discover_cse(self, cse_base):

        def err_cb(errror_response):
            try:
                del self._known_remote_cses[remote_cse_id]
            except KeyError:
                pass
        # discover devices
        self.periodic_discover(cse_base, {'labels': ['openmtc:device']},
                               self.interval,
                               self._discover_devices)
        self.periodic_discover(cse_base, {'labels': ['openmtc:sensor_data',
                                                     'openmtc:actuator_data']},
                               self.interval,
                               self._discover_sensors, err_cb)

    def _discover_devices(self, discovery):
        for device_path in discovery:
            self._discovered_devices[device_path] = 0
        logger.debug("Discovered devices: %s", self._discovered_devices)

    def _handle_sensor_data(self, container, data):
        logger.debug("Got Sensor \"%s\" data: %s", container, data)
        # XXX if a label contains 3x '/' assume that we need smart orchestra
        # naming
        try:
            entity_name = next(lbl for lbl in self.get_resource(
                container).labels if lbl.count('/') == 3)
            tenant_name = entity_name.split('/')[0]
            entity_name = '-'.join(entity_name.split('/')[1:3])
        except Exception as e:
            entity_name = container.split('/')[-2]
            tenant_name = ""

        self.orion_api.create_entity(entity_name, fiware_service=tenant_name)
        self.orion_api.update_attributes(
            entity_name,
            data,
            fiware_service=tenant_name)

    def _handle_new_sensor(self, sensor_path):

        # check labels of openmtc:device
        device_labels = self.get_resource(
            "/".join(sensor_path.split('/')[0:-1])).labels
        # if label configured
        if not ((len(self.labels) == 0) or
                (len(self.labels) == 1 and self.labels[0] == "")):
            # if no matching label
            if len(set(self.labels) & set(device_labels)) == 0:
                # no matching label no subscription
                logger.debug("no matching label for %s", sensor_path)
                return

        logger.debug("Subscription added for %s", sensor_path)
        self.add_container_subscription(sensor_path, self._handle_sensor_data)

    def _discover_sensors(self, discovery):
        for sensor_path in discovery:
            try:
                dev_path = [x for x in self._discovered_devices.keys()
                            if sensor_path.startswith(x)][0]
            except IndexError as e:  # todo(rst): ignore, but should not happen
                logger.debug("%s", e)
                logger.debug("%s", sensor_path)
                continue
            self._discovered_sensors[sensor_path] = {
                'ID': sensor_path,
                'dev_name': dev_path.split('/')[-1],
                'cse_id': sensor_path.split('/')[1],
                'data': None,
                'type': 'sensor',
                'n': None,
                'u': None
            }
            self._handle_new_sensor(sensor_path)
