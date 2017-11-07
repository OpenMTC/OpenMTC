"""
Copyright (c) 2017 Fraunhofer FOKUS
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
from urlparse import urljoin
import requests
from copy import deepcopy as deepcopy

from futile.logging import get_logger
logger = get_logger(__name__)


# TODO: check if this is sufficient
def _isSenML(senml_dict):
    is_senml = True
    try:
        is_senml = is_senml and ("bn") in senml_dict.keys()
        is_senml = is_senml and ("n") in senml_dict.keys()
        is_senml = is_senml and ("u") in senml_dict.keys()
        is_senml = is_senml and ("v") in senml_dict.keys()
        is_senml = is_senml and ("t") in senml_dict.keys()
    except BaseException:
        return False
    return is_senml


def _get_type(element):
    if isinstance(element, int):
        return u"Int"
    elif isinstance(element, float):
        return u"Float"
    elif isinstance(element, bool):
        return u"Boolean"
    elif isinstance(element, (str, unicode)):
        return u"String"
    else:
        logger.error("Type of \"element\" unknown")
        return "Unknown"


class OrionAPI:

    def __init__(self, orion_host=None, api_version="v2"):
        self.host = orion_host
        self.version = api_version

    def create_entity(self, entitiy_name, entity_type="openmtc",
                      fiware_service=""):

        payload_json = {"id": entitiy_name, "type": entity_type}

        if self.version == "v2":
            logger.debug("Send Payload to Orion CB: %s", str(payload_json))
            response = self._request(
                self.host + "/v2/entities",
                method="post",
                json=payload_json,
                raw=True,
                headers={
                    "Content-type": "application/json",
                    "fiware-service": fiware_service}
            )
            logger.debug("Send Payload to Orion CB: %s", str(payload_json))
        else:
            logger.error("API version \"%s\" not supported!", self.version)

    def update_attributes(self, entity_id, data_senml, fiware_service=""):
        data_senml = data_senml[0]
        if not _isSenML(data_senml):
            logger.error("Data \"%s\" is not valid SenML", data_senml)
            return

        if data_senml["v"] == "type" or data_senml["v"] == "id":
            logger.warn(
                "SenML[v]=%s contains reserved name. Adding underscore", data_senml["v"])
            data_senml["v"] = data_senml["v"] + "_"

        payload_json = {
            data_senml["n"]: {
                "value": data_senml["v"],
                "type": _get_type(data_senml["v"]),
                "metadata": {
                    "timestamp": {"value": data_senml["t"], "type": "String"},
                    "bn": {"value": data_senml["bn"], "type": "String"},
                    "unit": {"value": data_senml["u"], "type": "String"}
                }
            }
        }

        if self.version == "v2":
            response = self._request(
                self.host + "/v2/entities/" + entity_id + "/attrs",
                method="post",
                json=payload_json,
                raw=True,
                headers={
                    "Content-type": "application/json",
                    "fiware-service": fiware_service}
            )
            logger.debug("Send Payload to Orion CB: %s", str(payload_json))
        else:
            logger.error("API version \"%s\" not supported!", self.version)

    def _request(
            self,
            url,
            method='get',
            json=None,
            params=None,
            headers=None,
            raw=False):

        joined_url = urljoin(self.host, url)
        try:
            req = requests.request(method, joined_url, json=json,
                                   params=params, headers=headers)
            logger.debug("Status Code: %s", req.status_code)
            logger.debug("Content: %s", req.content)
            if raw:
                return {"status": req.status_code, "content": req.content}
            else:
                return {"status": req.status_code, "content": req.json()}
        except requests.ConnectionError as e:
            print "Connection Error: " + str(e)
            return {"status": -1, "content": None}
