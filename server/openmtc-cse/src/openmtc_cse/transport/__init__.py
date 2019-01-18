from urllib.parse import urlparse
from netifaces import AF_INET, AF_INET6

from aplus import Promise
from openmtc.exc import OpenMTCNetworkError
from openmtc_onem2m.model import RemoteCSE
from futile.collections import get_iterable
from openmtc_onem2m.transport import OneM2MErrorResponse
from openmtc_server import Component
from openmtc_onem2m.exc import CSETargetNotReachable, CSENotImplemented
from openmtc_onem2m.util import split_onem2m_address


class OneM2MTransportDomain(Component):
    def __init__(self, config, *args, **kw):
        super(OneM2MTransportDomain, self).__init__(*args, **kw)

        self._api = None
        self.events = None

        self.config = config

        self.sp_id = self.config.get("onem2m", {}).get("sp_id", "")
        self.cse_id = self.config.get("onem2m", {}).get("cse_id", "")

        do_overwrite = (self.config.get("onem2m", {}).get("overwrite_originator", {})
                        .get("enabled", False))
        orig_overwrite = (self.config.get("onem2m", {}).get("overwrite_originator", {})
                          .get("originator", ""))
        if do_overwrite:
            self.originator = orig_overwrite
        else:
            self.originator = "//" + self.sp_id + "/" + self.cse_id

        ssl_certs = self.config.get("onem2m", {}).get("ssl_certs", {})
        self.key_file = ssl_certs.get("key")
        self.cert_file = ssl_certs.get("crt")
        self.ca_file = ssl_certs.get("ca")
        self.accept_insecure_certs = self.config.get("onem2m", {}).get("accept_insecure_certs")

        self._addresses = {}

        self._poa_templates = []

        self._endpoints = []

        self._poa_lists = {}

        self._get_clients = {}

    def initialize(self, api):
        self._api = api
        self.events = api.events

        # addresses
        self._api.events.interface_created.register_handler(self._handle_interface_created)
        self._api.events.interface_removed.register_handler(self._handle_interface_removed)
        self._api.events.address_created.register_handler(self._handle_address_created)
        self._api.events.address_removed.register_handler(self._handle_address_removed)

        # remote CSEs
        self.events.resource_created.register_handler(self._handle_cse_created, RemoteCSE)
        self.events.resource_updated.register_handler(self._handle_cse_updated, RemoteCSE)
        self.events.resource_deleted.register_handler(self._handle_cse_deleted, RemoteCSE)

        interfaces = self._api.network_manager.get_interfaces().get()
        self._addresses = {i.name: list(filter(self._filter_out_link_local, i.addresses))
                           for i in interfaces}

    @staticmethod
    def _filter_out_link_local(address):
        return not address.address.startswith("fe80:")

    def _get_address_list(self):
        return [i for s in self._addresses.values() for i in s]

    def _create_endpoints(self):
        self._endpoints = []

        for poa_t in self._poa_templates:
            if poa_t.scheme.startswith("mqtt"):
                self._endpoints.append(poa_t.scheme + '://' + poa_t.server_address +
                                       ':' + str(poa_t.port))
            else:
                def map_func(address):
                    if address.family == AF_INET6:
                        a = '[' + address.address + ']'
                    else:
                        a = address.address
                    return poa_t.scheme + '://' + a + ':' + str(poa_t.port)

                if poa_t.server_address == "::":
                    def filter_func(x):
                        return x
                elif poa_t.server_address in ("", "0.0.0.0"):
                    def filter_func(x):
                        return x.family == AF_INET
                else:
                    def filter_func(x):
                        return x.address == poa_t.server_address

                self._endpoints += map(map_func, filter(filter_func,
                                                        self._get_address_list()))

    # interface handling
    def _handle_interface_created(self, interface):
        self._addresses[interface.name] = list(filter(self._filter_out_link_local, interface.addresses))
        self._create_endpoints()

    def _handle_interface_removed(self, interface):
        del self._addresses[interface.name]
        self._create_endpoints()

    def _handle_address_created(self, interface_name, address):
        if self._filter_out_link_local(address):
            self._addresses[interface_name].append(address)
            self._create_endpoints()

    def _handle_address_removed(self, interface_name, address):
        if self._filter_out_link_local(address):
            try:
                self._addresses[interface_name].remove(address)
            except ValueError:
                pass
            self._create_endpoints()

    # cse handling
    # TODO(rst): find out if IDs starting with slash or not
    def _handle_cse_created(self, instance, req=None):
        self.logger.debug("_handle_cse_created(instance=%s, req=%s)", instance, req)
        self.add_poa_list(instance.CSE_ID.lstrip('/'), instance.pointOfAccess)

    def _handle_cse_updated(self, instance, req=None):
        self.logger.debug("_handle_cse_updated(instance=%s, req=%s)", instance, req)
        self.add_poa_list(instance.CSE_ID.lstrip('/'), instance.pointOfAccess)

    def _handle_cse_deleted(self, instance, req):
        self.logger.debug("_handle_cse_deleted(req=%s)", req)
        self.remove_poa_list(instance.CSE_ID.lstrip('/'))

    # api functions
    def register_client(self, schemes, get_client):
        """Registers a specific client for the given schemes."""
        schemes = set(map(str.lower, get_iterable(schemes)))

        for scheme in schemes:
            self._get_clients[scheme] = get_client

    def register_point_of_access(self, poa):
        """Registers a point of access."""
        self._poa_templates.append(poa)
        self._create_endpoints()

    def _send_request_to_endpoints(self, onem2m_request, poa_list):
        with Promise() as p:
            if not poa_list:
                p.reject(CSETargetNotReachable())

            onem2m_request.originator = self.originator

            for poa in poa_list:
                use_xml = False  # TODO(rst): check how this needs to be handled
                ssl_certs = {
                    'ca_certs': self.ca_file,
                    'cert_file': self.cert_file,
                    'key_file': self.key_file
                }
                # TODO(hve): add scheme test.
                try:
                    client = self._get_clients[urlparse(poa).scheme](
                        poa, use_xml, insecure=self.accept_insecure_certs, **ssl_certs)
                except KeyError:
                    self.logger.error("Scheme %s not configured" % urlparse(poa).scheme)
                    continue
                try:
                    response = client.send_onem2m_request(onem2m_request).get()
                    p.fulfill(response)
                    break
                except OpenMTCNetworkError:
                    continue
                except OneM2MErrorResponse as error_response:
                    p.reject(error_response)

            if p.isPending():
                p.reject(CSETargetNotReachable())
        return p

    def send_notify(self, notify_request, poa_list=None):
        notify_request.ae_notifying = True
        return self._send_request_to_endpoints(notify_request, poa_list)

    def send_onem2m_request(self, onem2m_request):
        path = onem2m_request.to

        sp_id, cse_id, _ = split_onem2m_address(path)

        if not cse_id:
            poa_list = []
        else:
            if sp_id and sp_id[2:] != self.sp_id:
                # inter-domain routing
                raise CSENotImplemented()
            else:
                # intra-domain routing
                poa_list = self._poa_lists.get(cse_id[1:], [])

        return self._send_request_to_endpoints(onem2m_request, poa_list)

    # TODO(rst): add here more options to retrieve only non-local addresses etc.
    def get_endpoints(self):
        return self._endpoints

    def add_poa_list(self, identifier, poa_list):
        self._poa_lists[identifier] = poa_list

    def remove_poa_list(self, identifier):
        try:
            del self._poa_lists[identifier]
        except KeyError:
            pass
