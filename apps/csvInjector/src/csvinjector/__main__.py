from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from openmtc_app.util import prepare_app, get_value
from openmtc_app.runner import AppRunner as Runner
from .csv_injector import csvInjector

# defaults
default_name = "csvInjector"
default_ep = "http://localhost:8000"
default_csv_path = "~/test.csv"
default_csv_delim = ","
default_csv_quotechar = "|"
default_device_classifier = ""
default_date_classifier = "DATE"
default_time_format = "%d/%m/%Y-%H:%M"
default_duration = 300
default_repeat = False

# args parser
parser = ArgumentParser(
    description="An IPE called csvInjector",
    prog="csvInjector",
    formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument("-n", "--name", help="Name used for the AE.")
parser.add_argument("-s", "--ep", help="URL of the local Endpoint.")
parser.add_argument("-f", "--csv-path", help="Path to CSV File")
parser.add_argument("--csv-delim", help="Delimiter used for the provided csv")
parser.add_argument(
    "--csv-quotechar", help="Quotechar used for the provided csv")
parser.add_argument(
    "--device-classifier", help="Column used to specify different devices in csv")
parser.add_argument(
    "--date-classifier", help="Column used to specify where dates are defined in csv")
parser.add_argument(
    "--time-format", help="Format of the date column in csv (see https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior)")
parser.add_argument(
    "--duration", help="Time to inject the csv (if csv time data does not fit, it will be scaled)")
parser.add_argument(
    "--repeat", help="Repeat after csv is injected")

# args, config and logging
args, config = prepare_app(parser, __loader__, __name__, "config.json")

# variables
nm = get_value("name", (unicode, str), default_name, args, config)
cb = config.get("cse_base", "onem2m")
ep = get_value("ep", (unicode, str), default_ep, args, config)
poas = config.get("poas", ["http://auto:28300"])
originator_pre = config.get("originator_pre", "//openmtc.org/mn-cse-1")
ssl_certs = config.get("ssl_certs", {})
csv_path = get_value("csv_path", (unicode, str), default_csv_path, args,
                     config)
csv_delim = get_value("csv_delim", (unicode, str), default_csv_delim, args,
                      config)
csv_quotechar = get_value("csv_quotechar", (unicode, str),
                          default_csv_quotechar, args, config)
device_classifier = get_value("device_classifier", (unicode, str),
                          default_device_classifier, args, config)
date_classifier = get_value("date_classifier", (unicode, str, list),
                          default_date_classifier, args, config)
time_format = get_value("time_format", (unicode, str, list),
                          default_time_format, args, config)
duration = get_value("duration", (int, float),
                          default_duration, args, config)
repeat = get_value("repeat", (unicode, str),
                          default_repeat, args, config)

# start
app = csvInjector(
    name=nm,
    cse_base=cb,
    poas=poas,
    originator_pre=originator_pre,
    csv_path=csv_path,
    csv_delim=csv_delim,
    csv_quotechar=csv_quotechar,
    device_classifier=device_classifier,
    date_classifier=date_classifier,
    time_format=time_format,
    csv_inject_duration=duration,
    repeat=repeat,
    **ssl_certs)
Runner(app).run(ep)

print("Exiting....")
