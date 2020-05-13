# added this safety exception due to problems with sphinx autodoc when module
# load order is not strict. See:
# http://stackoverflow.com/questions/8774958/keyerror-in-module-threading-after-a-successful-py-test-run
import sys
import os
import gevent.monkey

if 'threading' in sys.modules and not os.environ.get('GEVENT_SUPPORT'):
    raise Exception('threading module loaded before monkey patching in '
                    'gevent_main!')

os.environ.setdefault("GEVENT_RESOLVER", "ares,thread")
gevent.monkey.patch_all()

# ssl fixes
################################################################################
import gevent.ssl

__ssl__ = __import__('ssl')

try:
    _ssl = __ssl__._ssl
except AttributeError:
    _ssl = __ssl__._ssl2


if not hasattr(_ssl, 'sslwrap'):
    import inspect

    def new_sslwrap(sock, server_side=False, keyfile=None, certfile=None,
                    cert_reqs=__ssl__.CERT_NONE,
                    ssl_version=__ssl__.PROTOCOL_SSLv23, ca_certs=None,
                    ciphers=None):
        context = __ssl__.SSLContext(ssl_version)
        context.verify_mode = cert_reqs or __ssl__.CERT_NONE
        if ca_certs:
            context.load_verify_locations(ca_certs)
        if certfile:
            context.load_cert_chain(certfile, keyfile)
        if ciphers:
            context.set_ciphers(ciphers)

        caller_self = inspect.currentframe().f_back.f_locals['self']
        return context._wrap_socket(sock, server_side=server_side,
                                    ssl_sock=caller_self)

    _ssl.sslwrap = new_sslwrap

    del inspect
    del new_sslwrap
    del __ssl__
    del _ssl

# bugfix for geventhttpclient, many thanks to kca
gevent.ssl.PROTOCOL_SSLv3 = gevent.ssl.PROTOCOL_TLSv1


# TODO: kca: look at http://www.gevent.org/servers.html

# gevent main
################################################################################
from openmtc.configuration import ConfigurationError
from openmtc_server.util.async_ import async_all

_components = []
_plugins = []

logger = None


def load_plugin(api, category, descriptor, global_config, onem2m_config,
                is_gateway):
    from re import sub as re_sub

    def convert(n):
        s1 = re_sub('(.)([A-Z][a-z]+)', r'\1_\2', n)
        return re_sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    try:
        name = descriptor["name"]
    except KeyError:
        raise ConfigurationError('"name" missing in plugin entry: %s' %
                                 (descriptor,))

    if descriptor.get("disabled"):
        logger.info("Plugin %s is disabled", name)
        return

    try:
        try:
            package = descriptor["package"]
        except KeyError:
            package = category + ".plugins." + convert(name)

        from importlib import import_module
        module_ = import_module(package)

        cls = getattr(module_, name)

        config = descriptor.get("config", {})

        if config.setdefault("global", global_config) is not global_config:
            raise ConfigurationError("Invalid (reserved) key in configuration "
                                     "for plugin %s: 'global'", name)
        if config.setdefault("onem2m", onem2m_config) is not onem2m_config:
            raise ConfigurationError("Invalid (reserved) key in configuration "
                                     "for plugin %s: 'onem2m'", name)

        try:
            if is_gateway:
                config_class = cls.__gateway_configuration__
            else:
                config_class = cls.__backend_configuration__
        except AttributeError:
            config_class = cls.__configuration__

        config = config_class(config)

        _plugins.append(cls(api, config))
    except ConfigurationError as e:
        raise ConfigurationError("Error loading plugin %s: %s" % (name, e))
    except Exception as e:
        logger.exception("Error loading plugin %s: %s", name, e)
        raise Exception("Error loading plugin %s: %s" % (name, e))


def load_plugins(api, plugins, global_config, onem2m_config, is_gateway):
    for category in plugins.values():
        for plugin in category:
            load_plugin(api, category, plugin, global_config, onem2m_config,
                        is_gateway)


def init_plugins():
    logger.info("Initializing plugins")
    async_all([plugin.initialize() for plugin in _plugins]).get()


def start_plugins():
    logger.info("Starting plugins")
    async_all([plugin.start() for plugin in _plugins]).get()


def load_config(name):
    logger.debug("Reading config file: %s", name)
    from openmtc_server.configuration import MainConfiguration, SimpleOption
    from openmtc_cse.configuration import OneM2MConfiguration

    MainConfiguration.__options__["onem2m"] = SimpleOption(OneM2MConfiguration)
    try:
        with open(name) as f:
            from json import load as j_load
            config = j_load(f)
        config = MainConfiguration(config)
    except Exception as e:
        raise ConfigurationError("Failed to load config file %s: %s" %
                                 (name, e))

    return config


def stop_component(component):
    logger.debug("Stopping component: %s", component)
    try:
        component.stop()
    except BaseException:
        logger.exception("Failed to stop component %s", component)


def stop_components():
    for c in reversed(_components):
        stop_component(c)
    logger.debug("Components stopped")


def stop_plugin(plugin):
    if plugin.started:
        stop_component(plugin)


def stop_plugins():
    # stop transport plugins after the others
    for p in [p for p in _plugins if not p.name.endswith('TransportPlugin')]:
        stop_plugin(p)
    for p in [p for p in _plugins if p.name.endswith('TransportPlugin')]:
        stop_plugin(p)


def init_component(component, api):
    logger.debug("Initializing component: %s", component)
    component.initialize(api)
    _components.append(component)


def main(default_config_file, is_gateway):
    global logger

    import futile.logging
    logger = futile.logging.get_logger(__name__)

    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

    config_locations = (".", "/etc/openmtc/gevent", "/etc/openmtc")

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f", "--configfile", default=None,
                        help="Location of the configuration file. If "
                        "unspecified the system will look for a file called %s"
                        " in these locations: %s" %
                        (default_config_file, ', '.join(config_locations)))
    parser.add_argument("-v", "--verbose", action="count", default=None,
                        help="Increase verbosity in output. This option can be"
                        " specified multiple times.")
    parser.add_argument("--profiler", action="store_true",
                        help="Use GreenletProfiler")
    args = parser.parse_args()

    configfile = args.configfile
    futile.logging.set_default_level(futile.logging.DEBUG)

    try:
        if not configfile:
            import os.path
            for d in config_locations:
                configfile = os.path.join(os.path.abspath(d),
                                          default_config_file)
                logger.debug("Trying config file location: %s", configfile)
                if os.path.isfile(configfile):
                    break
            else:
                raise ConfigurationError("Configuration file %s not found in "
                                         "any of these locations: %s" %
                                         (default_config_file, config_locations))

        config = load_config(configfile)
    except ConfigurationError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(2)

    import openmtc_cse.api
    openmtc_cse.api.config = config
    import openmtc_server.api
    openmtc_server.api.config = config

    # TODO: kca:
    # Also: set global (non-futile) level?
    if "logging" in config:  # TODO init logging
        # FIXME: This won't work, needs translation to log levels
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

    # make iso8601 logging shut up
    logger = futile.logging.get_logger(__name__)
    futile.logging.get_logger("iso8601").setLevel(futile.logging.ERROR)
    logger.debug("Running OpenMTC")

    from itertools import starmap

    import signal

    from gevent import spawn_later
    from gevent.event import Event as GEventEvent

    from openmtc_gevent.TaskRunner import GEventTaskRunner

    from openmtc_cse.methoddomain import OneM2MMethodDomain

    from openmtc_cse.transport import OneM2MTransportDomain

    from openmtc_server.platform.default.Event import (ResourceFinishEvent,
                                                       NetworkEvent)

    from .GEventNetworkManager import GEventNetworkManager

    from openmtc_server.util.db import load_db_module

    omd = OneM2MMethodDomain(config=config)

    otd = OneM2MTransportDomain(config=config)

    nm = GEventNetworkManager(config=config.get("network_manager", {}))

    task_runner = GEventTaskRunner()
    _components.append(task_runner)

    _timers = set()

    db = load_db_module(config)

    class Api(object):
        PLATFORM = "gevent"

        class events(object):
            resource_created = ResourceFinishEvent(task_runner.run_task)
            resource_deleted = ResourceFinishEvent(task_runner.run_task)
            resource_updated = ResourceFinishEvent(task_runner.run_task)
            resource_announced = ResourceFinishEvent(task_runner.run_task)

            # fired when a network interface appeared
            # called with <interface>
            interface_created = NetworkEvent(task_runner.run_task)
            # fired when a network interface was disappeared
            # called with <interface>
            interface_removed = NetworkEvent(task_runner.run_task)
            # fired when an address appeared on an existing interface
            # called with <interface>, <address>
            address_created = NetworkEvent(task_runner.run_task)
            # fired when an address disappeared on an existing interface
            # called with <interface>, <address>
            address_removed = NetworkEvent(task_runner.run_task)

        start_onem2m_session = db.start_onem2m_session
        get_shelve = db.get_shelve

        # handle request
        handle_onem2m_request = omd.handle_onem2m_request

        # send request
        send_onem2m_request = otd.send_onem2m_request
        send_notify = otd.send_notify

        register_point_of_access = otd.register_point_of_access

        # connectors and endpoints
        register_onem2m_client = otd.register_client
        get_onem2m_endpoints = otd.get_endpoints
        add_poa_list = otd.add_poa_list

        network_manager = nm

        run_task = task_runner.run_task

        @staticmethod
        def set_timer(t, f, *args, **kw):
            timer = None

            def wrapper():
                _timers.discard(timer)
                f(*args, **kw)
            timer = spawn_later(t, wrapper)
            _timers.add(timer)
            return timer

        @staticmethod
        def cancel_timer(timer):
            _timers.discard(timer)
            timer.kill()

        map = map

        @staticmethod
        def starmap(c, l):
            return tuple(starmap(c, l))

    Api.db = db

    openmtc_cse.api.api = Api
    openmtc_cse.api.events = Api.events
    openmtc_server.api.api = Api
    openmtc_server.api.events = Api.events

    shutdown_event = GEventEvent()
    signal.signal(signal.SIGTERM, shutdown_event.set)
    signal.signal(signal.SIGINT, shutdown_event.set)

    try:
        init_component(otd, Api)
        init_component(omd, Api)
        init_component(nm, Api)

        force = config["database"].get("dropDB")
        if force or not db.is_initialized():
            db.initialize(force)
            omd.init_cse_base()

        omd.start()

        load_plugins(Api, config.get("plugins", ()),
                     config["global"], config["onem2m"], is_gateway)
        init_plugins()
        start_plugins()

        logger.info("OpenMTC is running")
    except:
        logger.exception("Error during startup")
    else:
        if args.profiler:
            import GreenletProfiler
            GreenletProfiler.set_clock_type("cpu")
            GreenletProfiler.start()

        # wait for shutdown event
        shutdown_event.wait()

        if args.profiler:
            GreenletProfiler.stop()
            stats = GreenletProfiler.get_func_stats()
            stats.print_all()
            stats.save('profile.callgrind', type='callgrind')

    stop_plugins()
    stop_components()

    for timer in _timers:
        try:
            timer.kill()
        except:
            logger.exception("Failed to kill timer %s", timer)

if __name__ == "__main__":
    main()
