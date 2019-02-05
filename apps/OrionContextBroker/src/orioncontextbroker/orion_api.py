from urllib.parse import urljoin
import logging
from datetime import datetime

import requests

from futile.logging import LoggerMixin

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class OrionAPI(LoggerMixin):
    def __init__(self,
                 orion_host=None,
                 api_version="v2",
                 accumulate_endpoint="http://localhost:8080"):
        super(OrionAPI, self).__init__()
        self.host = orion_host
        self.version = api_version
        self.accumulate_endpoint = accumulate_endpoint

    @staticmethod
    def _is_senml(senml_dict):
        try:
            return (all(key in senml_dict for key in ('bn', 'n', 'u', 't'))
                    and any(key in senml_dict for key in ('v', 'vs', 'vb')))
        except TypeError:
            return False

    def _get_type(self, element):
        if isinstance(element, int):
            return "Int"
        elif isinstance(element, float):
            return "Float"
        elif isinstance(element, bool):
            return "Boolean"
        elif isinstance(element, str):
            return "String"
        else:
            self.logger.error('Type of "{}" unknown'.format(element))
            return "Unknown"

    def is_host_alive(self):
        req = self._request(
            "{}/v2/entities".format(self.host),
            method="get"
        )
        return req['status'] >= 0

    def create_entity(self,
                      entity_name,
                      entity_type="openmtc",
                      fiware_service=""):
        payload_json = {"id": entity_name, "type": entity_type}

        if self.version == "v2":
            self.logger.debug(
                "Send Payload to Orion CB: {}".format(payload_json))
            self._request(
                "{}/v2/entities".format(self.host),
                method="post",
                json=payload_json,
                raw=True,
                headers={
                    "Content-type": "application/json",
                    "fiware-service": fiware_service
                })
            self.logger.debug(
                "Send Payload to Orion CB: {}".format(payload_json))
        else:
            self.logger.error('API version "{}" not supported!'.format(
                self.version))

    def update_attributes(self, entity_id, data_senml, fiware_service=""):
        if not self._is_senml(data_senml):
            self.logger.error(
                'Data "{}" is not valid SenML'.format(data_senml))
            return

        if data_senml["v"] in ("type", "id"):
            self.logger.warn(
                "SenML[v]={} contains reserved name. Adding underscore".format(
                    data_senml["v"]))
            data_senml["v"] = "{}_".format(data_senml["v"])

        payload_json = {
            data_senml["n"]: {
                "value": data_senml["v"],
                "type": self._get_type(data_senml["v"]),
                "metadata": {
                    "timestamp": {
                        "value": datetime.fromtimestamp(float(data_senml["t"])).replace(microsecond=0).isoformat()
                        if data_senml["t"] != "none" else data_senml["t"],
                        "type": "String"
                    },
                    "bn": {
                        "value": data_senml["bn"],
                        "type": "String"
                    },
                    "unit": {
                        "value": data_senml["u"],
                        "type": "String"
                    }
                }
            }
        }

        if self.version == "v2":
            self._request(
                self.host + "/v2/entities/{}/attrs".format(entity_id),
                method="post",
                json=payload_json,
                raw=True,
                headers={
                    "Content-type": "application/json",
                    "fiware-service": fiware_service
                })
            self.logger.debug(
                "Send Payload to Orion CB: {}".format(payload_json))
        else:
            self.logger.error('API version "{}" not supported!'.format(
                self.version))

    def subscribe(self, entity_id, entity_type="openmtc", fiware_service=""):
        payload_json = {
            "description":
            'OpenMTC Actuator Subscription for Entitiy {}'.format(entity_id),
            "subject": {
                "entities": [{
                    "id": entity_id,
                    "type": entity_type
                }],
                "condition": {
                    "attrs": ["cmd"]
                }
            },
            "notification": {
                "http": {
                    "url": self.accumulate_endpoint
                },
                "attrs": ["cmd"]
            }
        }
        if self.version == "v2":
            response = self._request(
                self.host + "/v2/subscriptions",
                method="post",
                json=payload_json,
                raw=True,
                headers={
                    "Content-type": "application/json",
                    "fiware-service": fiware_service
                })
            self.logger.debug(
                "Add Subscription for {} on Fiware Service {}".format(
                    entity_id, fiware_service))
        else:
            self.logger.error('API version "{}" not supported!'.format(
                self.version))
        # return the subscriptionId
        return response["headers"]["Location"].split('/')[3]

    def unsubscribe(self, subscription_id, fiware_service=""):
        self._request(self.host + "/v2/subscriptions/" + subscription_id,
                      method='delete',
                      headers={"fiware-service": fiware_service},
                      raw=True)

    def _request(self,
                 url,
                 method='get',
                 json=None,
                 params=None,
                 headers=None,
                 raw=False):
        joined_url = urljoin(self.host, url)
        try:
            req = requests.request(
                method, joined_url, json=json, params=params, headers=headers)
            self.logger.debug('Got "{}" with Status Code {}'.format(
                req.status_code, req.content))
            if raw:
                return {
                    "status": req.status_code,
                    "content": req.content,
                    "headers": req.headers
                }
            else:
                return {
                    "status": req.status_code,
                    "content": req.json(),
                    "headers": req.headers
                }
        except requests.ConnectionError as e:
            self.logger.error("Connection Error: {}".format(e))
            return {"status": -1, "content": None}
