from openmtc_app.onem2m import XAE
from openmtc_onem2m.model import Container
from csv_process import csvProcessor
import sched
import time
import datetime


class csvInjector(XAE):
    def __init__(self,
                 csv_path,
                 csv_delim,
                 csv_quotechar,
                 device_classifier,
                 date_classifier,
                 time_format,
                 csv_inject_duration=0,
                 repeat=False,
                 *args,
                 **kw):

        super(csvInjector, self).__init__(*args, **kw)
        self._recognized_sensors = {}
        self._recognized_measurement_containers = {}
        # csv key to differ between devices
        self.device_classifier = device_classifier
        self.date_classifier = date_classifier
        self.csv_path = csv_path
        self.csv_delim = csv_delim
        self.csv_quotechar = csv_quotechar
        self.time_format = time_format
        self.csv_inject_duration = csv_inject_duration
        self.repeat = repeat

    def _on_register(self):
        # start endless loop
        self._init_scheduler()
        self.scheduler.run()
        if self.repeat:
            while True:
                self._init_scheduler()
                self.scheduler.run()

    def _init_scheduler(self):
        # read csv
        self.csv_data_list = csvProcessor(self.csv_path, self.csv_delim,
                                          self.csv_quotechar, self.time_format,
                                          self.csv_inject_duration,
                                          self.date_classifier).csv_data
        # setup scheduler
        self.scheduler = sched.scheduler(time.time, time.sleep)
        for event in self.csv_data_list:
            if isinstance(self.date_classifier, list):
                self.scheduler.enter(event["timestamp_schedule"], 1,
                                     self.push_data, (event, ))
            else:
                self.scheduler.enter(event[self.date_classifier], 1,
                                     self.push_data, (event, ))

    def _create_measurement_container(self, device_name, name):
        measurement_container = self.create_container(
            self._recognized_sensors[device_name].path,
            Container(resourceName=name),
            max_nr_of_instances=0,
            labels=[
                'openmtc:sensor_data:{}'.format(name), 'openmtc:sensor_data'
            ])
        self._recognized_measurement_containers[device_name][
            name] = measurement_container

    def _create_sensor_structure(self, event):
        device_container = self.create_container(
            None,
            Container(resourceName=event[self.device_classifier]),
            labels=['openmtc:device'],
            max_nr_of_instances=0)

        self._recognized_sensors[event[
            self.device_classifier]] = device_container
        self._recognized_measurement_containers[event[
            self.device_classifier]] = {}

        for k in event.keys():
            if k == "Date" or k == self.device_classifier or k in ("", None):
                continue
            self._create_measurement_container(event[self.device_classifier],
                                               k)

    def push_data(self, event):
        sensor = event[self.device_classifier]
        if not sensor in self._recognized_sensors:
            self._create_sensor_structure(event)
        device_container = self._recognized_sensors[sensor]
        for k in event.keys():
            if k == "Date" or k == self.device_classifier or event[k] in (
                    "", None):
                continue
            if not k in self._recognized_measurement_containers[sensor].keys():
                self._create_measurement_container(sensor, k)
            timestamp = time.mktime(datetime.datetime.now().timetuple())
            senml = {
                "bn": "csv_extracted",
                "n": k,
                "u": "None",
                "t": timestamp,
                "v": event[k]
            }
            self.logger.debug("sensor {} sends data: {}".format(sensor, senml))
            self.push_content(
                self._recognized_measurement_containers[sensor][k], [senml])
