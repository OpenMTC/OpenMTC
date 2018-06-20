from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from openmtc_app.util import prepare_app, get_value
from openmtc_app.runner import AppRunner as Runner
from .influxdb_app import InfluxdbApp

# defaults
default_name = "InfluxdbApp"
default_ep = "http://localhost:8000"
default_labels = []

# args parser
parser = ArgumentParser(
    description="An IPE called InfluxdbApp",
    prog="InfluxdbApp",
    formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-n", "--name", help="Name used for the AE.")
parser.add_argument("-s", "--ep", help="URL of the local Endpoint.")
parser.add_argument("--influx-host", help="Host of InfluxDB")
parser.add_argument("--influx-port", help="Port of InfluxDB")
parser.add_argument("--influx-user", help="Root User of InfluxDB")
parser.add_argument('--labels', type=str, help='just subscribe to those '
                                               'labels', nargs='+')
parser.add_argument("--influx-password", help="Root Password of InfluxDB")
parser.add_argument("--db-name", help="InfluxDB name")
parser.add_argument("--db-user", help="InfluxDB User")
parser.add_argument("--db-pw", help="InfluxDB User password")

# args, config and logging
args, config = prepare_app(parser, __loader__, __name__, "config.json")

# variables
nm = get_value("name", (unicode, str), default_name, args, config)
cb = config.get("cse_base", "onem2m")
ep = get_value("ep", (unicode, str), default_ep, args, config)
poas = config.get("poas", ["http://auto:23706"])
originator_pre = config.get("originator_pre", "//openmtc.org/mn-cse-1")
ssl_certs = config.get("ssl_certs", {})
lbl = get_value("labels", list, default_labels, args, config)

influx_host = get_value("influx_host", (unicode, str), "localhost", args, config)
influx_port = get_value("influx_port", (unicode, str), "8086", args, config)
influx_user = get_value("influx_user", (unicode, str), "root", args, config)
influx_password = get_value("influx_password", (unicode, str), "root", args, config)
db_name = get_value("db_name", (unicode, str), "example", args, config)
db_user = get_value("db_user", (unicode, str), "test", args, config)
db_pw = get_value("db_pw", (unicode, str), "test", args, config)

# start
app = InfluxdbApp(
    name=nm, cse_base=cb, poas=poas,
    labels=lbl,
    originator_pre=originator_pre, 
    influx_host=influx_host,
    influx_port=influx_port,
    influx_user=influx_user,
    influx_password=influx_password,
    dbname=db_name,
    dbuser=db_user,
    dbuser_pw=db_pw,
    **ssl_certs
)
Runner(app).run(ep)

print ("Exiting....")
