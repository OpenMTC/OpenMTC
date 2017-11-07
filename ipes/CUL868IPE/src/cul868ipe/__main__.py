import sys
import os
if 'threading' in sys.modules and not os.environ.get('SUPPORT_GEVENT'):
    raise Exception('threading module loaded before monkey patching!')
os.environ.setdefault("GEVENT_RESOLVER", "thread")
import gevent.monkey
gevent.monkey.patch_all()

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from openmtc_app.util import prepare_app, get_value
from openmtc_app.runner import AppRunner as Runner
from .cul_868_ipe import CUL868IPE

# defaults
default_name = "CUL868IPE"
default_device = "/dev/ttyACM0"
default_ep = "http://localhost:8000"

# args parser
parser = ArgumentParser(
    description="An IPE for the FS20 device connected on a CUL868",
    prog="CUL868IPE",
    formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-n", "--name", help="Name used for the AE.")
parser.add_argument("-s", "--ep", help="URL of the local Endpoint.")
parser.add_argument("-d", "--cul-device", help="Device Node of the CUL868.")
parser.add_argument("devices", nargs="*")

# args, config and logging
args, config = prepare_app(parser, __loader__, __name__, "config.json")

# variables
nm = get_value("name", (unicode, str), default_name, args, config)
cb = config.get("cse_base", "onem2m")
ep = get_value("ep", (unicode, str), default_ep, args, config)
poas = config.get("poas", ["http://auto:28728"])
originator_pre = config.get("originator_pre", "//openmtc.org/mn-cse-1")
ssl_certs = config.get("ssl_certs", {})

s = config.get("sim", False)
p = int(config.get("sim_period"))
cul_device = get_value('cul_device', (unicode, str), default_device, args, config)
device_mappings = get_value('device_mappings', dict, {}, args, config) 
devices = get_value('devices', list, [], args, config)

# start
app = CUL868IPE(
    devices, device=cul_device, sim=s, sim_period=p,
    device_mappings=device_mappings,
    name=nm, cse_base=cb, poas=poas,
    originator_pre=originator_pre, **ssl_certs
)
Runner(app).run(ep)

print ("Exiting....")
