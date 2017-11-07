import netifaces
import time
from collections import namedtuple

from aplus import Promise
from openmtc_server.exc import InterfaceNotFoundException
from openmtc_server.NetworkManager import NetworkManager

Interface = namedtuple("Interface", ("name", "addresses", "hwaddress"))
Address = namedtuple("Address", ("address", "family"))


class GEventNetworkManager(NetworkManager):
    def __init__(self, config, *args, **kw):
        super(GEventNetworkManager, self).__init__(*args, **kw)

        self._api = None

        self.config = config

        self.polling = True

        self.logger.info("GEventNetworkManager loaded")

    def initialize(self, api):
        self._api = api
        self.logger.info("GEventNetworkManager initialized")
        self.start()

    def start(self):
        # self.api.register_connectivity_handler(self.connectivity_request)
        self.polling = True
        self._api.run_task(self.start_polling)
        self.logger.info("GEventNetworkManager started")

    def stop(self):
        self.polling = False
        self.logger.info("GEventNetworkManager stopped")

    def connectivity_request(self):
        """Handles connectivity requests"""
        # please note: normally we get an rcat argument, default: rcat=0
        with Promise() as p:
            blacklist = ['lo']
            interfaces = netifaces.interfaces()

            interface = next((x for x in interfaces if (x not in blacklist)),
                             None)

            if interface is None:
                p.reject(InterfaceNotFoundException(
                    "No interfaces found matching request"))
            else:
                p.fulfill((self._get_interface(interface), 0))

        return p

    def start_polling(self, timeout=1):
        """Poll netifaces information and check for differences, for as long as
        self.polling == True.

        :param timeout: Amount of time to wait between polling
        """
        last_interfaces = cur_interfaces = netifaces.interfaces()
        cur_interfaces_copy = list(cur_interfaces)

        last_ifaddresses = {}
        for iface in last_interfaces:
            last_ifaddresses[iface] = netifaces.ifaddresses(iface)

        self.logger.debug("polling started")
        while self.polling:
            try:
                cur_interfaces = netifaces.interfaces()
                cur_interfaces_copy = list(cur_interfaces)

                intersection = set(last_interfaces) ^ set(cur_interfaces)
                if len(intersection) > 0:
                    self.logger.debug("difference detected")
                    self.logger.debug("last interfaces: %s", last_interfaces)
                    self.logger.debug("current interfaces: %s", cur_interfaces)

                    for isetface in intersection:
                        if isetface in cur_interfaces:
                            # new interface
                            self.logger.debug("Firing %s event for %s",
                                              "interface_created", isetface)
                            self._api.events.interface_created.fire(
                                self._create_interface(
                                    isetface, netifaces.ifaddresses(isetface)))
                        else:
                            # removed interface
                            self.logger.debug("Firing %s event for %s",
                                              "interface_removed", isetface)
                            self._api.events.interface_removed.fire(
                                self._create_interface(
                                    isetface, last_ifaddresses[isetface]))

                for iface in cur_interfaces:
                    cur_ifaddresses = netifaces.ifaddresses(iface)
                    if (iface in last_ifaddresses and
                                last_ifaddresses[iface] != cur_ifaddresses):
                        self._check_ifaddresses_diff(last_ifaddresses[iface],
                                                     cur_ifaddresses, iface)

                    last_ifaddresses[iface] = cur_ifaddresses
            except Exception as e:
                self.logger.exception("Something went wrong during polling: %s",
                                      e)
            finally:
                # updating last stuff to current stuff
                last_interfaces = cur_interfaces_copy
                time.sleep(timeout)

        self.logger.debug("polling done")

    def get_interfaces(self):
        """Returns all known network interfaces

        :return Promise([Interface]): a promise for a list of interfaces
        """
        with Promise() as p:
            interfaces = []
            for iface in netifaces.interfaces():
                interfaces.append(self._get_interface(iface))

            # check if array has duplicates
            # does this even work with namedtuple(s)?
            # interfaces = list(set(interfaces))
            p.fulfill(interfaces)
        return p

    def get_interface(self, name):
        """Returns an Interface object identified by name

        :param name: name of interface
        :return Promise(Interface): a promise for an interface
        :raise InterfaceNotFoundException: if interface was not found
        """
        with Promise() as p:

            if name not in netifaces.interfaces():
                p.reject(InterfaceNotFoundException("%s was not found" % name))
            else:
                p.fulfill(self._get_interface(name))
        return p

    def get_addresses(self, interface=None):
        """Get addresses of a given interface or all addresses if :interface: is
        None

        :param interface: name of interface
        :return: Promise([Address]): a promise for a list of addresses
        """
        with Promise() as p:
            p.fulfill(self._get_addresses(interface))

        return p

    def _get_addresses_from_ifaddresses(self, ifaddresses):
        """Get addresses of a given interface

        :param ifaddresses: raw addresses of interface (from netifaces)
        :return: list of addresses
        """
        addresses = []
        for family in ifaddresses:
            if family != netifaces.AF_LINK:  # no hwaddr
                for addr in ifaddresses[family]:
                    a = addr["addr"]
                    if family == netifaces.AF_INET6:
                        a = self._remove_ipv6_special_stuff(a)
                    addresses.append(
                        Address(address=a, family=family))

        return addresses

    def _get_addresses(self, iface=None):
        """Get addresses of a given interface

        :param iface: name of interface
        :return: list of addresses
        """

        if iface is None:
            interfaces = netifaces.interfaces()
        else:
            interfaces = [iface]

        addresses = []

        for interface in interfaces:
            n_addresses = netifaces.ifaddresses(interface)
            addresses += self._get_addresses_from_ifaddresses(n_addresses)

        # check if array has duplicates
        # addresses = list(set(addresses))

        return addresses

    def _create_interface(self, name, ifaddresses):
        """Create Interface tuple based on given interfaces addresses. (function
        independent of netifaces)

        :param name:
        :param ifaddresses:
        :return:
        """
        addresses = self._get_addresses_from_ifaddresses(ifaddresses)
        try:
            hwaddress = ifaddresses[netifaces.AF_LINK][0]["addr"]
        except (IndexError, KeyError):
            self.logger.debug("No hardware address found for %s!", name)
            hwaddress = None

        return Interface(name=name,
                         addresses=addresses,
                         hwaddress=hwaddress)

    def _get_interface(self, name):
        """Returns an Interface object identified by name

        :param name: name of interface
        :return Interface: interface
        :raise UnknownInterface: if interface was not found
        """
        if name not in netifaces.interfaces():
            raise InterfaceNotFoundException("%s was not found" % name)
        else:
            ifaddresses = netifaces.ifaddresses(name)
            addresses = self._get_addresses_from_ifaddresses(ifaddresses)
            try:
                hwaddress = ifaddresses[netifaces.AF_LINK][0]["addr"]
            except (IndexError, KeyError):
                self.logger.debug("No hardware address found for %s!", name)
                hwaddress = None
            return Interface(name=name,
                             addresses=addresses,
                             hwaddress=hwaddress)

    def _check_ifaddresses_diff(self, lifaddr, cifaddr, iface):
        """parses last and current interface addresses of a given interface and
        fires events for discovered differences

        :param lifaddr: dict of family:addresses (last addresses)
        :param cifaddr: dict of family:addresses (curr addresses)
        :param iface: str name of interface (needed only to create interface for
                      event firing)
        """
        self.logger.debug("checking difference of \r\n%s vs \r\n%s", lifaddr,
                          cifaddr)

        intersection = set(lifaddr.keys()) ^ set(cifaddr.keys())
        if len(intersection) > 0:
            self.logger.debug(
                "Sensing a change in address families of interface %s", iface)
            # first check if new address family
            self.logger.debug("Iterating through %s", intersection)
            for isectkey in intersection:
                if isectkey in cifaddr.keys():
                    for addr in cifaddr.get(isectkey, []):
                        self.logger.debug("Firing %s event for %s of %s",
                                          "address_created", addr, iface)
                        a = Address(address=addr["addr"], family=isectkey)
                        self._api.events.address_created.fire(iface, a)
                elif isectkey in lifaddr.keys():
                    for addr in lifaddr.get(isectkey, []):
                        self.logger.debug("Firing %s event for %s of %s",
                                          "address_removed", addr, iface)
                        a = Address(address=addr["addr"], family=isectkey)
                        self._api.events.address_removed.fire(iface, a)

        else:
            for key in lifaddr.keys():
                # check for removed addresses (contained only in lifaddr)
                removed_addr = []
                for laddr in lifaddr.get(key):
                    for caddr in cifaddr.get(key):
                        d = DictDiffer(caddr, laddr)

                        if len(d.changed()) == 0:
                            # this means both addresses are the same -> remove
                            # from removed_addr list
                            if laddr in removed_addr:
                                removed_addr.remove(laddr)
                            break

                        else:
                            # else add address to unknown/removed addresses
                            if laddr not in removed_addr:
                                removed_addr.append(laddr)

                if len(removed_addr) > 0:
                    self.logger.debug("removed addresses found: %s",
                                      removed_addr)
                    for raddr in removed_addr:
                        self.logger.debug("Firing %s event for %s of %s",
                                          "address_removed", raddr, iface)
                        a = Address(address=raddr["addr"], family=key)
                        self._api.events.address_removed.fire(iface, a)

                # now check for added addresses (contained only in cifaddr)
                added_addr = []
                for caddr in cifaddr.get(key):
                    for laddr in lifaddr.get(key):
                        d = DictDiffer(caddr, laddr)

                        if len(d.changed()) == 0:
                            # this means both addresses are the same -> remove
                            # from added_addr list
                            if caddr in added_addr:
                                added_addr.remove(caddr)
                            break

                        else:
                            # else add address to unknown/added addresses
                            if caddr not in added_addr:
                                added_addr.append(caddr)

                if len(added_addr) > 0:
                    self.logger.debug("added addresses found: %s", added_addr)
                    for aaddr in added_addr:
                        self.logger.debug("Firing %s event for %s of %s",
                                          "address_created", aaddr, iface)
                        a = Address(address=aaddr["addr"], family=key)
                        self._api.events.address_created.fire(iface, a)

    @staticmethod
    def _remove_ipv6_special_stuff(address):
        return address.split("%")[0]


class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """

    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(
            past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        return set(o for o in self.intersect if
                   self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect if
                   self.past_dict[o] == self.current_dict[o])
