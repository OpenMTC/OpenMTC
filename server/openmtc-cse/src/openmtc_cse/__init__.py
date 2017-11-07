from collections import namedtuple


OneM2MEndPoint = namedtuple("OneM2MEndPointBase",
                            ("scheme", "server_address", "port"))
