from urllib.parse import urlparse

from openmtc.mapper import BasicMapper, MapperError
from openmtc_onem2m import OneM2MRequest
from openmtc_onem2m.transport import OneM2MOperation


def _is_persistent(instance):
    return bool(instance.path)


class OneM2MMapper(BasicMapper):
    def __init__(self, cse, originator=None, ca_certs=None, cert_file=None, key_file=None,
                 *args, **kw):
        super(OneM2MMapper, self).__init__(*args, **kw)

        scheme = urlparse(cse).scheme.lower()
        if scheme in ("", "https", "http"):
            from openmtc_onem2m.client.http import get_client
            self._send_request = get_client(
                cse, use_xml=False, ca_certs=ca_certs, cert_file=cert_file, key_file=key_file
            ).send_onem2m_request
        elif scheme in ("mqtt", "mqtts", "secure-mqtt"):
            from openmtc_onem2m.client.mqtt import get_client
            self._send_request = get_client(
                cse, use_xml=False, client_id=originator, ca_certs=ca_certs, cert_file=cert_file,
                key_file=key_file
            ).send_onem2m_request
        elif scheme == "coap":
            raise NotImplementedError
        else:
            raise ValueError(
                "Unsupported URL scheme: %s" % (scheme,)
            )
        self.originator = originator

    def create(self, path, instance):
        instance.__dict__.update({
            attribute.name: None for attribute in type(instance).attributes
            if attribute.accesstype == attribute.RO
        })

        # TODO(rst): add resource_type
        response = self._send_request(OneM2MRequest(
            OneM2MOperation.create,
            path,
            self.originator,
            ty=type(instance),
            pc=instance,
            rvi='2a'
        )).get()

        try:
            instance.__dict__.update(response.content.values)
            instance.path = path + '/' + response.content.resourceName
        except (AttributeError, ):
            instance.path = path

        self.logger.debug("Set instance path: %s" % (instance.path, ))
        instance._synced = False
        return instance

    def update(self, instance, fields=None):
        if not _is_persistent(instance):
            raise MapperError("Instance is not yet stored")
        return self._do_update(instance, fields)

    def _do_update(self, instance, fields=None):
        try:
            fields = list(fields or [])
        except TypeError:
            fields = []
        attributes = type(instance).attributes
        values_to_clear = {a.name: None if a.type is not list else [] for a in attributes
                           if a.accesstype in (a.WO, a.RO) or a.name not in fields and len(fields)}

        # remove NP attributes
        instance.set_values(values_to_clear)

        response = self._send_request(OneM2MRequest(
            OneM2MOperation.update,
            instance.path,
            self.originator,
            pc=instance,
            rvi='2a'
        )).get()

        try:
            response.content.path = instance.path
        except AttributeError:
            pass

        return response.content

    def get(self, path, fc=None, **request_options):
        response = self._get_data(path, fc, **request_options)
        response.content.path = path
        self.logger.debug("Received response: %s", response.content)
        return response.content

    def _get_data(self, path, fc=None, **request_options):
        return self._send_request(OneM2MRequest(
            OneM2MOperation.retrieve,
            path,
            self.originator,
            filter_criteria=fc,
            rvi='2a',
            rcn=5,
            **request_options
        )).get()

    def delete(self, instance):
        self._send_request(OneM2MRequest(
            OneM2MOperation.delete,
            getattr(instance, "path", instance),
            self.originator,
            rvi='2a'
        ))

    # TODO(rst): check if this can be removed in parent class
    @classmethod
    def _patch_model(cls):
        pass

    def _fill_resource(self, res, data):
        pass

    def _map(self, path, typename, data):
        pass
