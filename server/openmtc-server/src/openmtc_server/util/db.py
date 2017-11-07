from openmtc_server.exc import ConfigurationError
from importlib import import_module


def load_db_module(config, **override_params):
    try:
        dbconfig = config["database"]
    except KeyError:
        raise ConfigurationError("db configuration is missing")

    try:
        db_fq_name = dbconfig["driver"]
    except KeyError:
        raise ConfigurationError("db configuration is missing a 'driver' entry")

    package, _, clsname = db_fq_name.rpartition(".")

    if not package or not clsname:
        raise ConfigurationError("Invalid DB driver string")

    module = import_module(package)

    cls = getattr(module, clsname)

    dbconfig.update(override_params)

    return cls(dbconfig)
