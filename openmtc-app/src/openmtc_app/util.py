import sys
from json import load as json_load
from operator import getitem

import futile
from functools import reduce


def prepare_app(parser, loader, name, default_config_file):
    parser.add_argument("-v", "--verbose", action="count", default=None,
                        help="Increase verbosity in output. This option can be"
                             " specified multiple times.")
    args = parser.parse_args()

    module_ = loader.name.split("." + name).pop(0)

    futile.logging.set_default_level(futile.logging.DEBUG)
    logger = futile.logging.get_logger(name)

    config_locations = (".", "/etc/openmtc/" + module_)

    try:
        import os.path
        for d in config_locations:
            config_file = os.path.join(os.path.abspath(d),
                                       default_config_file)
            logger.debug("Trying config file location: %s", config_file)
            if os.path.isfile(config_file):
                break
        else:
            raise Exception("Configuration file %s not found in any of these "
                            "locations: %s" % default_config_file,
                            config_locations)
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(2)

    try:
        with open(config_file) as f:
            logger.info("Reading configuration file %s.", config_file)
            config = json_load(f)
    except IOError as e:
        logger.warning("Failed to read configuration file %s: %s",
                       config_file, e)
        config = {}
    except Exception as e:
        logger.critical("Error reading configuration file %s: %s",
                        config_file, e)
        sys.exit(2)

    if "logging" in config:  # TODO init logging
        log_conf = config["logging"]
        if args.verbose is None:
            futile.logging.set_default_level(log_conf.get("level") or
                                             futile.logging.WARNING)
        elif args.verbose >= 2:
            futile.logging.set_default_level(futile.logging.DEBUG)
        else:
            futile.logging.set_default_level(futile.logging.INFO)
        logfile = log_conf.get("file")
        if logfile:
            futile.logging.add_log_file(logfile)
    else:
        futile.logging.set_default_level(futile.logging.DEBUG)

    return args, config


def get_value(name, value_type, default_value, args, config):
    try:
        value = (getattr(args, name.replace(".", "_"), None) or
                 reduce(getitem, name.split("."), config))
    except KeyError:
        value = None
    value = value if isinstance(value, value_type) else default_value
    return value
