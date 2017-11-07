from openmtc.configuration import Configuration, SimpleOption


class OneM2MConfiguration(Configuration):
    __name__ = "onem2m configuration"
    __options__ = {"sp_id": SimpleOption(default="openmtc.org"),
                   "cse_type": SimpleOption(default="MN_CSE"),
                   "cse_id": SimpleOption(default="mn-cse-1"),
                   "cse_base": SimpleOption(default="onem2m")}
