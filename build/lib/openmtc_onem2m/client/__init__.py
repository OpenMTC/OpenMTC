from abc import abstractmethod
from futile import LoggerMixin


def normalize_path(path):
    if not path:
        return ''
    if path.startswith('//'):
        # abs CSE
        return '/_' + path[1:]
    elif path.startswith('/'):
        # sp rel CSE
        return '/~' + path
    return path


class OneM2MClient(LoggerMixin):
    def __init__(self):
        super(OneM2MClient, self).__init__()

    @abstractmethod
    def send_onem2m_request(self, onem2m_request):
        pass
