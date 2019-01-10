from openmtc_app.onem2m import ResourceManagementXAE
from .connector import InfluxDBConnector


class InfluxdbApp(ResourceManagementXAE):

    def __init__(
            self,
            labels=[],
            influx_host='localhost',
            influx_port=8086,
            influx_user='root',
            influx_password='root',
            dbname='example',
            dbuser='test',
            dbuser_pw='test',
            *args,
            **kw
            ):
        super(InfluxdbApp, self).__init__(*args, **kw)
        if isinstance(labels, str):
            self.labels = {labels}
        elif hasattr(labels, '__iter__') and len(labels):
            self.labels = set(labels)
        else:
            self.labels = []
        self._entity_names = {}

        # create database
        self.connector = InfluxDBConnector(
                host=influx_host,
                port=influx_port,
                user=influx_user,
                password=influx_password,
                dbname=dbname,
                dbuser=dbuser,
                dbuser_pw=dbuser_pw)

    def _on_register(self):
        self._discover_openmtc_ipe_entities()

    def _sensor_filter(self, sensor_info):
        if self.labels:
            return len(self.labels.intersection(sensor_info['sensor_labels'])) > 0
        else:
            return True

    def _sensor_data_cb(self, sensor_info, sensor_data):
        self.connector.update(sensor_data,
                sensor_info['ID'].split('/')[3],
                sensor_info['dev_name'],
                sensor_info['dev_labels'],
                sensor_info['ID'].split('/')[-1],
                sensor_info['sensor_labels'])

