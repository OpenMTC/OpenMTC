from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from openmtc_app.util import prepare_app, get_value
from openmtc_app.runner import AppRunner as Runner
from .orion_context_broker import OrionContextBroker

# defaults
default_name = "OrionContextBroker"
default_ep = "http://localhost:8000"
default_labels = [""]
default_interval = 10  # interval(s) to check status updates
default_orion_host = "http://localhost:1026"
default_orion_api = "v2"

# args parser
parser = ArgumentParser(
    description="Stores OpenMTC Date in an\
      instance of the Orion Context Broker",
    prog="OrionContextBroker",
    formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-n", "--name", help="Name used for the AE.")
parser.add_argument("-s", "--ep", help="URL of the local Endpoint.")
parser.add_argument("--orion_host", help="URL of Orion CB")
parser.add_argument("--orion_api", help="Orion CB Api version (possible\
    values: \"v2\")")
parser.add_argument('--labels', type=str, help='just subscribe to those\
    labels', nargs='+')
parser.add_argument('--interval', type=int, help='update interval (s)')

# args, config and logging
args, config = prepare_app(parser, __loader__, __name__, "config.json")

# variables
nm = get_value("name", (unicode, str), default_name, args, config)
cb = config.get("cse_base", "onem2m")
ep = get_value("ep", (unicode, str), default_ep, args, config)
poas = config.get("poas", ["http://auto:25396"])
originator_pre = config.get("originator_pre", "//openmtc.org/mn-cse-1")
ssl_certs = config.get("ssl_certs", {})
interval = get_value("interval", (int), default_ep, args, config)
lbl = get_value("labels", (list), default_labels, args, config)
orion_host = get_value("orion_host", (unicode, str),
                       default_orion_host, args, config)
orion_api = get_value("orion_api", (unicode, str),
                      default_orion_api, args, config)

# start
app = OrionContextBroker(
    labels=lbl, interval=interval, orion_host=orion_host, orion_api=orion_api,
    name=nm, cse_base=cb, poas=poas,
    originator_pre=originator_pre, **ssl_certs
)
Runner(app).run(ep)

print ("Exiting....")
