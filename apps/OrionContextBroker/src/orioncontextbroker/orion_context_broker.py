import re

from openmtc_app.onem2m import ResourceManagementXAE
from orion_api import OrionAPI


class OrionContextBroker(ResourceManagementXAE):

    def __init__(self, orion_host="http://localhost:1026", orion_api="v2", labels=None,
                 *args, **kw):
        super(OrionContextBroker, self).__init__(*args, **kw)
        if isinstance(labels, basestring):
            self.labels = {labels}
        elif hasattr(labels, '__iter__'):
            self.labels = set(labels)
        else:
            self.labels = None
        self._entity_names = {}
        self.orion_api = OrionAPI(orion_host=orion_host, api_version=orion_api)

    def _on_register(self):
        self._discover_openmtc_ipe_entities()

    def _sensor_filter(self, sensor):
        if self.labels:
            return len(self.labels.intersection(sensor.labels)) > 0
        else:
            return True

    def _sensor_data_cb(self, sensor_info, sensor_data):

        def get_entity_name():
            try:
                id_label = filter(lambda x: (x.startswith('openmtc:id:')),
                                  sensor_info['sensor_labels']).pop()
                cse_id, dev_id = re.sub('^openmtc:id:', '', id_label).split('/')[:2]
            except (IndexError, ValueError):
                cse_id = sensor_info['cse_id']
                dev_id = sensor_info['dev_name']
            try:
                f_s, e_pre = cse_id.split('~', 1)
            except ValueError:
                f_s = ''
                e_pre = cse_id
            return re.sub('[\W]', '_', f_s), '%s-%s' % (e_pre, dev_id)

        try:
            fiware_service, entity_name = self._entity_names[sensor_info['ID']]
        except KeyError:
            fiware_service, entity_name = self._entity_names[sensor_info['ID']] = get_entity_name()
            self.orion_api.create_entity(entity_name, fiware_service=fiware_service)

        self.orion_api.update_attributes(entity_name, sensor_data, fiware_service=fiware_service)
