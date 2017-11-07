from abc import abstractmethod
from collections import namedtuple
import random
from futile.logging import LoggerMixin
from random import choice

S300THData = namedtuple("S300THData", ("temperature", "humidity"))
EM1000EMData = namedtuple("EM1000EMData",
                          ("counter", "cumulated", "last", "top"))
FS20Data = namedtuple("FS20Data", ("command", "duration"))
HMSData = namedtuple("HMSData",
                     ("device", "temperature", "humidity", "battery"))


class Parser(LoggerMixin):
    def __call__(self, line):
        self.logger.debug("Parsing: %s", line)
        result = self._parse(line)

        self.logger.debug("Parse result: %s", result)
        return result

    @abstractmethod
    def _parse(self, line):
        pass


class SIMParser(Parser):
    def _parse(self, line):
        if line == 'K':
            dev_id = '1'
            temperature = random.uniform(0, 30)
            humidity = random.uniform(0, 30)
            return dev_id, S300THData(temperature, humidity)
        elif line == 'F':
            dev_id = '21111111-132' + choice(['1', '2'])
            duration = ''
            command = choice(['11', '12', '14'])
            return dev_id, FS20Data(command, duration)
            # elif line == 'E':
            #     dev_id = line
            #     counter = random.uniform(0,30)
            #     cumulated = random.uniform(0,30)
            #     last =random.uniform(0,30)
            #     top = random.uniform(0,30)
            #
            #     return dev_id, EM1000EMData(counter, cumulated, last, top)
            # elif line == 'H':
            #     dev_id = ''
            #     temperature = random.uniform(0,30)
            #     humidity = random.uniform(0,30)
            #     battery = random.uniform(0,100)
            #     return dev_id, HMSData(temperature, humidity, battery)


class S300THParser(Parser):
    def _parse(self, line):
        l1 = int(line[1])
        dev_id = str(int(line[2]) + (l1 & 7))

        temp = float(line[6] + line[3] + "." + line[4])

        if l1 > 8:  # TODO: Check if this works
            temp *= -1

        humidity = float(line[7] + line[8] + "." + line[5])

        return dev_id, S300THData(temp, humidity)


class EM1000EMParser(Parser):
    def _parse(self, line):
        dev_id = str(int(line[3:5], 16))

        counter = int(line[5:7], 16)
        cumulated = int(line[9:11] + line[7:9], 16) / 1000.0
        last = int(line[13:15] + line[11:13], 16) * 10
        top = int(line[17:19] + line[15:17], 16) * 10

        return dev_id, EM1000EMData(counter, cumulated, last, top)


class FS20Parser(Parser):
    @staticmethod
    def int2base(x, base):
        import string

        digs = string.digits + string.lowercase
        if x < 0:
            sign = -1
        elif x == 0:
            return '0'
        else:
            sign = 1
        x *= sign
        digits = []
        while x:
            digits.append(digs[x % base])
            x /= base
        if sign < 0:
            digits.append('-')
        digits.reverse()
        return ''.join(digits)

    def base_convert(self, value, from_base, to_base):
        return self.int2base(int(value, from_base), to_base)

    @staticmethod
    def base4_digit_increaser(base4):
        base4_i = base4.replace("3", "4")
        base4_i = base4_i.replace("2", "3")
        base4_i = base4_i.replace("1", "2")
        base4_i = base4_i.replace("0", "1")
        return base4_i

    def _parse(self, line):
        # from http://fhz4linux.info/tiki-index.php?page=FS20%20Protocol

        commands = [
            'off',                  # 00
            'on_1',                 # 01
            'on_2',                 # 02
            'on_3',                 # 03
            'on_4',                 # 04
            'on_5',                 # 05
            'on_6',                 # 06
            'on_7',                 # 07
            'on_8',                 # 08
            'on_9',                 # 09
            'on_10',                # 10
            'on_11',                # 11
            'on_12',                # 12
            'on_13',                # 13
            'on_14',                # 14
            'on_15',                # 15
            'on_16',                # 16
            'on_old',               # 17
            'toggle',               # 18
            'dim_up',               # 19
            'dim_down',             # 20
            'dim_up_down',          # 21
            'time_set',             # 22
            'send_state'            # 23
            'off_for_timer',        # 24
            'on_16_for_timer',      # 25
            'on_old_for_timer',     # 26
            'reset',                # 27
            'free',                 # 28
            'free',                 # 29
            'on_16_for_timer_pre',  # 30
            'on_old_for_timer_pre'  # 31
        ]

        line = line.rstrip()
        # convert hex string (minus identifier "F") to elv String (base4
        # with digits 1-4)
        elv = self.base4_digit_increaser(
            self.base_convert(line[1:7], 16, 4).zfill(6 * 2))

        # grab data
        hc1 = elv[0:4]
        hc2 = elv[4:8]
        address = elv[8:10]
        sub_address = elv[10:12]
        command = int(line[7:9], 16)
        extended = command & 0x20
        command &= ~0xE0
        if extended:
            duration = ((2 ** min(int(line[9:10], 16), 12)) *
                        int(line[10:11], 16) * 0.25)
        else:
            duration = ''

        # make sensor ID consist of house_code and address
        dev_id = str(hc1) + str(hc2) + "-" + str(address) + str(sub_address)

        return dev_id, FS20Data(commands[command], duration)


class HMSParser(Parser):
    devices = {
        "0": "HMS100TF",
        "1": "HMS100T",
        "2": "HMS100WD",
        "3": "RM100-2",
        "4": "HMS100TFK",  # Depending on the onboard jumper it is 4 or 5
        "5": "HMS100TFK",
        "6": "HMS100MG",
        "8": "HMS100CO",
        "e": "HMS100FIT"
    }

    def _parse(self, line):
        dev_id = line[1:5]
        val = line[5:]

        device = self.devices.get(val[1])
        status = int(val[0], 16)
        sign = -1 if (status & 8) else 1

        if device == "HMS100T":
            temperature = sign * float(val[5] + val[2] + '.' + val[3])
            humidity = None
            battery = 0
            if status & 2:
                battery = 1
            if status & 4:
                battery = 2
        elif device == "HMS100TF":
            temperature = sign * float(val[5] + val[2] + '.' + val[3])
            humidity = sign * float(val[6] + val[7] + '.' + val[4])
            battery = 0
            if status & 2:
                battery = 1
            if status & 4:
                battery = 2
        else:
            temperature = None
            humidity = None
            battery = None

        return dev_id, HMSData(device, temperature, humidity, battery)
