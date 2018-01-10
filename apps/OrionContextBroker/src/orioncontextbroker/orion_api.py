try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import requests

from futile.logging import LoggerMixin


class OrionAPI(LoggerMixin):

    def __init__(self, orion_host=None, api_version="v2"):
        super(OrionAPI, self).__init__()
        self.host = orion_host
        self.version = api_version

    # TODO: check if this is sufficient
    @staticmethod
    def _is_senml(senml_dict):
        try:
            return (all(key in senml_dict for key in ('bn', 'n', 'u', 't')) and
                    any(key in senml_dict for key in ('v', 'vs', 'vb')))
        except TypeError:
            return False

    def _get_type(self, element):
        if isinstance(element, int):
            return u"Int"
        elif isinstance(element, float):
            return u"Float"
        elif isinstance(element, bool):
            return u"Boolean"
        elif isinstance(element, (str, unicode)):
            return u"String"
        else:
            self.logger.error("Type of \"element\" unknown")
            return "Unknown"

    def create_entity(self, entity_name, entity_type="openmtc", fiware_service=""):
        payload_json = {"id": entity_name, "type": entity_type}

        if self.version == "v2":
            self.logger.debug("Send Payload to Orion CB: %s", str(payload_json))
            self._request(
                self.host + "/v2/entities",
                method="post",
                json=payload_json,
                raw=True,
                headers={
                    "Content-type": "application/json",
                    "fiware-service": fiware_service}
            )
            self.logger.debug("Send Payload to Orion CB: %s", str(payload_json))
        else:
            self.logger.error("API version \"%s\" not supported!", self.version)

    def update_attributes(self, entity_id, data_senml, fiware_service=""):
        if not self._is_senml(data_senml):
            self.logger.error("Data \"%s\" is not valid SenML", data_senml)
            return

        if data_senml["v"] == "type" or data_senml["v"] == "id":
            self.logger.warn(
                "SenML[v]=%s contains reserved name. Adding underscore", data_senml["v"])
            data_senml["v"] = data_senml["v"] + "_"

        payload_json = {
            data_senml["n"]: {
                "value": data_senml["v"],
                "type": self._get_type(data_senml["v"]),
                "metadata": {
                    "timestamp": {"value": data_senml["t"], "type": "String"},
                    "bn": {"value": data_senml["bn"], "type": "String"},
                    "unit": {"value": data_senml["u"], "type": "String"}
                }
            }
        }

        if self.version == "v2":
            self._request(
                self.host + "/v2/entities/" + entity_id + "/attrs",
                method="post",
                json=payload_json,
                raw=True,
                headers={
                    "Content-type": "application/json",
                    "fiware-service": fiware_service}
            )
            self.logger.debug("Send Payload to Orion CB: %s", str(payload_json))
        else:
            self.logger.error("API version \"%s\" not supported!", self.version)

    def _request(self, url, method='get', json=None, params=None, headers=None, raw=False):
        joined_url = urljoin(self.host, url)
        try:
            req = requests.request(method, joined_url, json=json,
                                   params=params, headers=headers)
            self.logger.debug("Status Code: %s", req.status_code)
            self.logger.debug("Content: %s", req.content)
            if raw:
                return {"status": req.status_code, "content": req.content}
            else:
                return {"status": req.status_code, "content": req.json()}
        except requests.ConnectionError as e:
            self.logger.error("Connection Error: " + str(e))
            return {"status": -1, "content": None}
