from abc import abstractmethod
from collections import namedtuple
from openmtc_server import Component


Interface = namedtuple("Interface", ("name", "addresses", "hw_address"))
Address = namedtuple("Address", ("address", "family"))


class NetworkManager(Component):

    @abstractmethod
    def get_interfaces(self):
        """Returns all known network interfaces

        :return Promise([Interface]): a promise for a list of interfaces
        """

    @abstractmethod
    def get_interface(self, name):
        """Returns an Interface object identified by name

        :param name: name of interface
        :return Promise(Interface): a promise for an interface
        :raise UnknownInterface: if interface was not found
        """

    @abstractmethod
    def get_addresses(self, interface=None):
        """Get addresses of a given interface or all addresses if :interface: is None

        :param interface: name of interface
        :return: Promise([Address]): a promise for a list of addresses
        """
