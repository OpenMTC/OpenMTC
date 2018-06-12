from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from openmtc_app.util import prepare_app, get_value
from openmtc_app.runner import AppRunner as Runner
from .mqtt_connector import mqttConnector

# defaults
default_name = "mqttConnector"
default_ep = "http://localhost:8000"
default_topic_pre = "exampleTopic"
default_topic_index_location = 1
default_topic_index_device = -1
default_fiware_service = None
default_broker_user = "foo"
default_broker_user_pw = "bar"
default_mqtts_ca_certs = None
default_mqtts_certfile = None
default_mqtts_keyfile = None

# args parser
parser = ArgumentParser(
    description="An IPE called mqttConnector",
    prog="mqttConnector",
    formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-n", "--name", help="Name used for the AE.")
parser.add_argument("-s", "--ep", help="URL of the local Endpoint.")
parser.add_argument("--topic_pre", help="Topic you want to be subscribed to")
parser.add_argument(
    "--topic_index_location", help="Index of location in topic string")
parser.add_argument(
    "--topic_index_device", help="Index of device name in topic string")
parser.add_argument("--broker_user", help="credentials for MQTT broker")
parser.add_argument("--broker_user_pw", help="credentials for MQTT broker")
parser.add_argument("--mqtts", dest='mqtts_enabled', action='store_true')
parser.add_argument("--no-mqtts", dest='mqtts_enabled', action='store_false')
parser.set_defaults(mqtts_enabled=False)
parser.add_argument(
    "--mqtts_ca_certs", help="Path to CA certs or tuple of paths")
parser.add_argument("--mqtts_certfile", help="Path to own mqtts cert")
parser.add_argument("--mqtts_keyfile", help="Path to own mqtts key")
# args, config and logging
args, config = prepare_app(parser, __loader__, __name__, "config.json")

# variables
nm = get_value("name", (unicode, str), default_name, args, config)
cb = config.get("cse_base", "onem2m")
ep = get_value("ep", (unicode, str), default_ep, args, config)
poas = config.get("poas", ["http://auto:21753"])
originator_pre = config.get("originator_pre", "//openmtc.org/mn-cse-1")
ssl_certs = config.get("ssl_certs", {})

broker_ep = config.get("broker_ep", "openmtc.smartorchestra.de:8883")

topic_pre = get_value("topic_pre", (unicode, str), default_topic_pre, args,
                      config)
topic_index_location = get_value("topic_index_location", (int),
                                 default_topic_index_location, args, config)
topic_index_device = get_value("topic_index_device", (int),
                               default_topic_index_device, args, config)
fiware_service = get_value("fiware_service", (unicode, str),
                           default_fiware_service, args, config)
broker_user = get_value("broker_user", (unicode, str), default_broker_user,
                        args, config)
broker_user_pw = get_value("broker_user_pw", (unicode, str),
                           default_broker_user_pw, args, config)
user_pw = get_value("broker_user_pw", (unicode, str), default_broker_user_pw,
                    args, config)
mqtts_enabled = get_value("mqtts_enabled", (bool), False, args, config)
mqtts_ca_certs = get_value("mqtts_ca_certs", (unicode, str),
                           default_mqtts_ca_certs, args, config)
mqtts_certfile = get_value("mqtts_certfile", (unicode, str),
                           default_mqtts_certfile, args, config)
mqtts_keyfile = get_value("mqtts_keyfile", (unicode, str),
                          default_mqtts_keyfile, args, config)
# start
app = mqttConnector(
    broker_ep=broker_ep,
    topic_pre=topic_pre,
    broker_user=broker_user,
    broker_user_pw=broker_user_pw,
    topic_index_location=topic_index_location,
    topic_index_device=topic_index_device,
    fiware_service=fiware_service,
    mqtts_enabled=mqtts_enabled,
    mqtts_ca_certs=mqtts_ca_certs,
    mqtts_certfile=mqtts_certfile,
    mqtts_keyfile=mqtts_keyfile,
    name=nm,
    cse_base=cb,
    poas=poas,
    originator_pre=originator_pre,
    **ssl_certs)
Runner(app).run(ep)

print("Exiting....")
