import time
from openmtc_app.onem2m import XAE
from openmtc_onem2m.model import Container
from collections import namedtuple
from cul_868_coordinator import CUL868Coordinator

BAUD_RATE = 9600
NODE_DISCOVER_INTERVAL = 6
SLEEP_INTERVAL = 0.1

CULDevice = namedtuple("CULDevice", ("type", "device_id"))


class CUL868IPE(XAE):
    max_nr_of_instances = 30
    default_access_right = False

    def __init__(self, cul_devices, device="/dev/ttyACM0",
                 sim=False, sim_period=3, device_mappings={}, *args, **kw):
        super(CUL868IPE, self).__init__(*args, **kw)
        self.device = device

        self.fs20 = []
        self.em1000em = []
        self.s300th = []
        self.fs20_sender = []
        self.fs20_brightness = []
        self.fs20_door = []
        self.fs20_window = []
        self.fs20_motion = []
        self.hms100t = []
        self.hms100tf = []

        self.containers = {}
        self.dev_containers = {}

        self.sim = sim
        self.sim_period = sim_period

        self.device_mappings = device_mappings

        self._old_fs20_values = {}

        self.cul = CUL868Coordinator(device=device)

        for d in map(lambda s: CULDevice(*s.split(":")[:2]), cul_devices):
            if d.type == "fs20":
                house_code, device_code = d.device_id.split("-")
                self.fs20.append((house_code, device_code))
            elif d.type == "em1000em":
                self.em1000em.append(d.device_id)
            elif d.type == "s300th":
                self.s300th.append(d.device_id)
            elif d.type == "fs20_sender":
                self.fs20_sender.append(d.device_id)
            elif d.type == "fs20_brightness":
                self.fs20_brightness.append(d.device_id)
            elif d.type == "fs20_door":
                self.fs20_door.append(d.device_id)
            elif d.type == "fs20_window":
                self.fs20_window.append(d.device_id)
            elif d.type == "fs20_motion":
                self.fs20_motion.append(d.device_id)
            elif d.type == "hms100t":
                self.hms100t.append(d.device_id)
            elif d.type == "hms100tf":
                self.hms100tf.append(d.device_id)
            else:
                raise ValueError("Unknown device type: %s" % (d.type,))

    def _on_shutdown(self):
        self.cul.shutdown()

    def add_device(self, cnt_id, labels, sub_containers):
        labels += ["openmtc:device", "openmtc:device:cul868"]
	cse_id = self.get_resource(self.cse_base).CSE_ID[1:]
        try:
            tenant_id, instance_id = cse_id.split('~')
        except ValueError:
            tenant_id = cse_id
            instance_id = 'None'
        context = (self.device_mappings[cnt_id] 
                if cnt_id in self.device_mappings.keys() else None)

        dev_cnt = Container(resourceName=cnt_id, maxNrOfInstances=0,
                            labels=labels)
        dev_cnt = self.create_container(None, dev_cnt)
        self.dev_containers[cnt_id] = dev_cnt

        for c_id, l, func in sub_containers:
            s_id = cnt_id + '_' + c_id.upper()
            
            if func:
                l = (map(lambda x: "openmtc:actuator_data:%s" % x, l)
                     if l else [])
                l.append('openmtc:actuator_data')
                l.append('openmtc:sensor_data')
                # if in device mappings, add smart orchestra labels
                if context:
                    l.extend((
                            '{}'.format(tenant_id),
                            '{}/{}'.format(tenant_id, instance_id),
                            '{}/{}/{}'.format(tenant_id, instance_id, context),
                            '{}/{}/{}/{}'.format(tenant_id, instance_id, context, c_id)
                            ))
                sub_cnt = Container(resourceName=c_id, maxNrOfInstances=0,
                                    labels=l)
            else:
                l = map(lambda x: "openmtc:sensor_data:%s" % x, l) if l else []
                l.append('openmtc:actuator_data')
                l.append('openmtc:sensor_data')
                # if in device mappings, add smart orchestra labels
                if context:
                    l.extend((
                            '{}'.format(tenant_id),
                            '{}/{}'.format(tenant_id, instance_id),
                            '{}/{}/{}'.format(tenant_id, instance_id, context),
                            '{}/{}/{}/{}'.format(tenant_id, instance_id, context, c_id)
                            ))
                sub_cnt = Container(resourceName=c_id, labels=l)

            self.containers[s_id] = s_cnt = self.create_container(dev_cnt,
                                                                  sub_cnt)

            if func:
                self.add_container_subscription(s_cnt, func)

        return dev_cnt

    def _on_register(self):
        for house_code, device_code in self.fs20:
            d = "%s_%s" % (house_code, device_code)
            handle_switch = self._get_handle_switch(house_code, device_code)
            self.add_device('FS20_ST3_%s' % d, ["FS20_ST3", "ST3", "PowerPlug"],
                            (("switch", ["switch"], handle_switch),))

        self.cul.add_handler(self.cul.PROTOCOL_S300TH, self._handle_s300th_data)
        self.cul.add_handler(self.cul.PROTOCOL_FS20,
                             self._handle_fs20_sender_data)
        self.cul.add_handler(self.cul.PROTOCOL_EM1000EM,
                             self._handle_em1000em_data)
        self.cul.add_handler(self.cul.PROTOCOL_HMS, self._handle_hms_data)

        if self.sim:
            self.cul.start_simulation(self.run_forever, self.sim_period)
        else:
            self.cul.start()

    def _get_handle_switch(self, house_code, device_code):

        def handle_switch(container, content):
            if isinstance(content, (str, unicode)):  # fallback to old behavior
                if content == 'TOGGLE':
                    self.cul.toggle(house_code, device_code)
                elif content == 'ON':
                    self.cul.switch_on(house_code, device_code)
                elif content == 'OFF':
                    self.cul.switch_off(house_code, device_code)
            elif isinstance(content, list):  # senml
                try:
                    value = round(float(content[0]['v']))
                    if value == 1.0:
                        self.cul.switch_on(house_code, device_code)
                    elif value == 0.0:
                        self.cul.switch_off(house_code, device_code)
                except (KeyError, ValueError):
                    pass

        return handle_switch

    @staticmethod
    def _time():
        return format(round(time.time(), 3), '.3f')

    def _get_sensor_data(self, dev_name, measure, unit, value):
        entry = {
            "bn": "urn:dev:" + dev_name,    # basename
            "n": measure,                   # name
            "t": self._time()               # timestamp
        }

        if unit:                            # unit
            entry['u'] = unit

        try:
            entry['v'] = float(value)       # value
        except ValueError:
            if isinstance(value, bool):
                entry['vb'] = value
            elif value.lower() == "true":
                entry['vb'] = True
            elif value.lower() == "false":
                entry['vb'] = False
            else:
                entry['vs'] = str(value)

        return [entry]

    def _handle_em1000em_data(self, dev_id, data):
        self.logger.debug("Handling EM1000EM data: %s", data)

        cnt_id = "EM1000EM_%s" % dev_id
        dev_name = "em100em:%s" % dev_id

        try:
            self.dev_containers[cnt_id]
        except KeyError:
            if dev_id in self.em1000em or len(self.em1000em) == 0:
                self.add_device(cnt_id, ["EM1000EM"],
                                (("load", False, None),
                                 ("work", False, None)))
            else:
                return

        # Load
        container_id = cnt_id + "_LOAD"
        ci = self._get_sensor_data(dev_name, "load", "W", data.last)
        self.push_content(self.containers[container_id], ci)

        # Work
        container_id = cnt_id + "_WORK"
        ci = self._get_sensor_data(dev_name, "work", "kWh", data.cumulated)
        self.push_content(self.containers[container_id], ci)

    def _handle_s300th_data(self, dev_id, data):
        self.logger.debug("Handling S300TH data: %s", data)

        cnt_id = "S300TH_%s" % dev_id
        dev_name = "s300th:%s" % dev_id

        try:
            self.dev_containers[cnt_id]
        except KeyError:
            if dev_id in self.s300th or len(self.s300th) == 0:
                self.add_device(cnt_id,  ["S300TH"],
                                (("temperature", ["temperature"], None),
                                 ("humidity", ["humidity"], None)))
            else:
                return

        # Temperature
        container_id = cnt_id + "_TEMPERATURE"
        ci = self._get_sensor_data(dev_name, "temperature", "Cel",
                                   data.temperature)
        self.push_content(self.containers[container_id], ci)

        # Humidity
        container_id = cnt_id + "_HUMIDITY"
        ci = self._get_sensor_data(dev_name, "humidity", "%RH", data.humidity)
        self.push_content(self.containers[container_id], ci)

    def _get_fs20_value(self, dev_id, value):
        # TODO(rst): handle more command strings (toggle, dim_*, timer)
        try:
            old_fs20_value = self._old_fs20_values[dev_id]
        except KeyError:
            old_fs20_value = ''

        if value == 'off':
            fs20_value = '0.0'
        elif value == 'on_old':
            if old_fs20_value.startswith('-'):
                fs20_value = old_fs20_value[1:]
            else:
                fs20_value = old_fs20_value or '1.0'
        elif value.startswith('on_'):
            fs20_value = str(int(value[3:]) / 16.0)
        else:
            fs20_value = None

        if fs20_value is not None:
            if value == 'off':
                self._old_fs20_values[dev_id] = '-' + old_fs20_value
            else:
                self._old_fs20_values[dev_id] = fs20_value

        return fs20_value

    def _handle_fs20_sender_data(self, dev_id, data):
        self.logger.debug("Handling FS20_sender data: %s", data)
        self.logger.debug("data is of type" + str(type(data)))

        # motion
        if (len(self.fs20_motion) > 0 or len(self.fs20_brightness) > 0 or
                len(self.fs20_door) > 0 or len(self.fs20_window) > 0):
            if dev_id in self.fs20_motion:
                self._handle_fs20_motion_data(dev_id, data)
            elif dev_id in self.fs20_brightness:
                self._handle_fs20_brightness_data(dev_id, data)
            elif dev_id in self.fs20_door:
                self._handle_fs20_door_data(dev_id, data)
            elif dev_id in self.fs20_window:
                self._handle_fs20_window_data(dev_id, data)
        else:
            cnt_id = "FS20_sender_%s" % dev_id
            dev_name = "fs20:%s" % dev_id

            try:
                self.dev_containers[cnt_id]
            except KeyError:
                if dev_id in self.fs20_sender or len(self.fs20_sender) == 0:
                    self.add_device(cnt_id, ["FS20_sender"],
                                    (("command", ["command"], None),))
                else:
                    return

            # Command
            container_id = cnt_id + "_COMMAND"
            value = self._get_fs20_value(dev_id, data.command)
            if value is not None:
                ci = self._get_sensor_data(dev_name, "command", "%", value)
                self.push_content(self.containers[container_id], ci)

    def _handle_fs20_motion_data(self, dev_id, data):
        self.logger.debug("Handling FS20_motion data: %s", data)

        cnt_id = "FS20_motion_%s" % (dev_id,)
        dev_name = "fs20:%s" % dev_id

        try:
            self.dev_containers[cnt_id]
        except KeyError:
            if dev_id in self.fs20_motion:
                self.add_device(cnt_id, ["FS20_sender", "FS20_motion"],
                                (("motion", ["motion", "command"], None),))
            else:
                return

        # Motion
        container_id = cnt_id + "_MOTION"
        value = self._get_fs20_value(dev_id, data.command)
        if value is not None:
            ci = self._get_sensor_data(dev_name, "command", "%", value)
            self.push_content(self.containers[container_id], ci)

    def _handle_fs20_brightness_data(self, dev_id, data):
        self.logger.debug("Handling FS20_brightness data: %s", data)

        cnt_id = "FS20_brightness_%s" % dev_id
        dev_name = "fs20:%s" % dev_id

        try:
            self.dev_containers[cnt_id]
        except KeyError:
            if dev_id in self.fs20_brightness or len(self.fs20_brightness) == 0:
                self.add_device(cnt_id, ["FS20_sender", "FS20_brightness"],
                                (("brightness", ["brightness", "command"],
                                  None),))
            else:
                return

        # Brightness
        container_id = cnt_id + "_BRIGHTNESS"
        value = self._get_fs20_value(dev_id, data.command)
        if value is not None:
            ci = self._get_sensor_data(dev_name, "command", "%", value)
            self.push_content(self.containers[container_id], ci)

    def _handle_fs20_door_data(self, dev_id, data):
        self.logger.debug("Handling FS20_door data: %s", data)

        cnt_id = "FS20_door_%s" % dev_id
        dev_name = "fs20:%s" % dev_id

        try:
            self.dev_containers[cnt_id]
        except KeyError:
            if dev_id in self.fs20_door or len(self.fs20_door) == 0:
                self.add_device(cnt_id,
                                ["FS20_sender", "FS20_door"],
                                (("door", ["door", "command"], None),))
            else:
                return

        # Door
        container_id = cnt_id + "_DOOR"
        value = self._get_fs20_value(dev_id, data.command)
        if value is not None:
            ci = self._get_sensor_data(dev_name, "command", "%", value)
            self.push_content(self.containers[container_id], ci)

    def _handle_fs20_window_data(self, dev_id, data):
        self.logger.debug("Handling FS20_window data: %s", data)

        cnt_id = "FS20_window_%s" % dev_id
        dev_name = "fs20:%s" % dev_id

        try:
            self.dev_containers[cnt_id]
        except KeyError:
            if dev_id in self.fs20_window or len(self.fs20_window) == 0:
                self.add_device(cnt_id, ["FS20_sender", "FS20_window"],
                                (("window", ["window", "command"], None),))
            else:
                return

        # Window
        container_id = cnt_id + "_WINDOW"
        value = self._get_fs20_value(dev_id, data.command)
        if value is not None:
            ci = self._get_sensor_data(dev_name, "command", "%", value)
            self.push_content(self.containers[container_id], ci)

    def _handle_hms_data(self, dev_id, data):
        if data.device == "HMS100T":
            self._handle_hms100t_data(dev_id, data)
        elif data.device == " HMS100TF":
            self._handle_hms100tf_data(dev_id, data)

    def _handle_hms100t_data(self, dev_id, data):
        self.logger.debug("Handling HMS100T data: %s", data)

        cnt_id = "HMS100T_%s" % dev_id
        dev_name = "hms100t:%s" % dev_id

        try:
            self.dev_containers[cnt_id]
        except KeyError:
            if dev_id in self.hms100t or len(self.hms100t) == 0:
                self.add_device(cnt_id, ["HMS100T"],
                                (("temperature", ["temperature"], None),
                                 ("battery", False, None)))
            else:
                return

        # Temperature
        container_id = cnt_id + "_TEMPERATURE"
        ci = self._get_sensor_data(dev_name, "temperature", "Cel",
                                   data.temperature)
        self.push_content(self.containers[container_id], ci)

        # TODO(rst): handle battery
        pass

    def _handle_hms100tf_data(self, dev_id, data):
        self.logger.debug("Handling HMS100TF data: %s", data)

        cnt_id = "HMS100TF_%s" % dev_id
        dev_name = "hms100tf:%s" % dev_id

        try:
            self.dev_containers[cnt_id]
        except KeyError:
            if dev_id in self.hms100t or len(self.hms100t) == 0:
                self.add_device(cnt_id, ["HMS100TF"],
                                (("temperature", ["temperature"], None),
                                 ("humidity", ["humidity"], None),
                                 ("battery", True, None)))
            else:
                return

        # Temperature
        container_id = cnt_id + "_TEMPERATURE"
        ci = self._get_sensor_data(dev_name, "temperature", "Cel",
                                   data.temperature)
        self.push_content(self.containers[container_id], ci)

        # Humidity
        container_id = cnt_id + "_HUMIDITY"
        ci = self._get_sensor_data(cnt_id, "humidity", "%RH", data.humidity)
        self.push_content(self.containers[container_id], ci)

        # TODO(rst): handle battery
        pass
