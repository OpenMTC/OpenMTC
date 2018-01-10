import select
from collections import defaultdict
from os import system
from random import choice

from gevent import spawn

from futile.logging import LoggerMixin
from .parsers import (EM1000EMParser, S300THParser, FS20Parser, HMSParser, SIMParser)


def _hex(n):
    s = hex(n)[2:]
    len_s = len(s)
    return s.zfill(len_s + len_s % 2)


class CUL868Coordinator(LoggerMixin):
    COMMAND_ON = "11"
    COMMAND_OFF = "00"
    COMMAND_TOGGLE = "12"

    PROTOCOL_S300TH = "K"
    PROTOCOL_EM1000EM = "E"
    PROTOCOL_FS20 = "F"
    PROTOCOL_HMS = "H"

    def __init__(self, device="/dev/ttyACM1"):
        super(CUL868Coordinator, self).__init__()
        self.running = False
        self.device = device
        self.handlers = defaultdict(lambda: defaultdict(list))
        self.parsers = {
            "K": S300THParser(),
            "E": EM1000EMParser(),
            "F": FS20Parser(),
            "H": HMSParser()
        }

        self.sim_parsers = {
            "K": SIMParser(),
            # "E": SIMParser(),
            # "F": SIMParser(),
            # "H": SIMParser()
        }

        self.write_handle = self.device_handle = None

    def start(self):
        self.device_handle = open(self.device, "r", 0)
        self.write_handle = open(self.device, "w", 0)
        self.write_handle.write("X01\r\n")
        self.running = True

        spawn(self._listener)

    def start_simulation(self, run_forever, period):
        run_forever(period, self._generate_simulated_data)

    def _generate_simulated_data(self):
        p = choice(self.sim_parsers.keys())
        fake_parser = self.sim_parsers[p]
        dev_id, data = fake_parser(p)
        handler = self.handlers[p]

        try:
            handler(dev_id, data)
        except Exception:
            self.logger.exception("Error in data handler.")

    def _listener(self):
        system("stty -echo -echok -echoke -echoe -echonl < %s" %
               (self.device,))
        while self.running:
            try:
                rlist, _, _ = select.select([self.device_handle], [], [], 0.25)
                if not rlist:
                    continue
                line = self.device_handle.readline()  # TODO: Make this interruptable
            except Exception:
                self.logger.exception("Error reading from %s.", self.device)
                return
            if len(line) == 0:
                self.logger.info("Received empty line. Aborting")
                return

            if len(line) == 1:
                continue
            self.logger.debug("Read CUL data: %r", line)

            protocol = line[0]

            if protocol in "*X":
                continue

            try:
                parser = self.parsers[protocol]
            except KeyError:
                self.logger.warn("No parser for %s", line)
                continue

            self.logger.debug("Have parser for %s: %s", protocol, parser)

            try:
                dev_id, data = parser(line)
            except Exception:
                self.logger.exception("Error parsing line: %s", line)
                continue

            self.logger.debug("Parsed data: %s %s", dev_id, data)

            self.logger.debug("%s %s %s", self.handlers,
                              self.handlers[protocol])

            handler = self.handlers[protocol]
            self.logger.debug("Calling handler: %s", handler)
            try:
                handler(dev_id, data)
            except Exception:
                self.logger.exception("Error in data handler.")

    def shutdown(self):
        self.logger.info("Shutting down.")
        self.running = False
        if self.device_handle is not None:
            self.device_handle.close()
        if self.write_handle is not None:
            self.write_handle.close()

    def add_handler(self, protocol, handler):
        self.handlers[protocol] = handler

    def _send_fs20(self, house_code, device_code, command):
        self.logger.debug("Send FS20: house_code=%s device_code=%s command=%s",
                          house_code, device_code, command)
        s = ''.join(
            ("F", _hex(int(house_code)), _hex(int(device_code)), command))
        self.logger.debug("Sending FS20 command: %s", s)
        self.write_handle.write(s + "\r\n")
        self.logger.debug("Command sent")

    def switch_on(self, house_code, device_code):
        self._send_fs20(house_code, device_code, self.COMMAND_ON)

    def switch_off(self, house_code, device_code):
        self._send_fs20(house_code, device_code, self.COMMAND_OFF)

    def toggle(self, house_code, device_code):
        self._send_fs20(house_code, device_code, self.COMMAND_TOGGLE)
