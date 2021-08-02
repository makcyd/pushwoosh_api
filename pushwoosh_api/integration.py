import requests
import logging
import json

logger = logging.getLogger(__name__)
"""
Implementation for Integrations API:
https://integrations.pushwoosh.com/api/v1/#/
"""


class IntegrationAPI:
    api_key = ""
    api_endpoint = "https://integrations.pushwoosh.com/api/v1"
    headers = {}

    _last_request_url = None
    _last_request_data = None
    _last_request_response = None
    _last_request_json = None
    _last_request_error = None
    _last_request_text = None

    def __init__(self, api_key, api_endpoint=None):
        self.api_key = api_key
        self.headers["Authorization"] = api_key
        if not api_endpoint:
            self.api_endpoint = "https://integrations.pushwoosh.com/api/v1"
        else:
            self.api_endpoint = api_endpoint

    def _send_request(self, uri, request, method="POST"):
        self._last_request_data = request

        url = "{}/{}".format(self.api_endpoint, uri)
        self._last_request_url = url

        logger.debug("Url: {}".format(url))
        logger.debug("Data JSON: {}".format(json.dumps(request)))

        response = requests.post(url, data=json.dumps(request), headers=self.headers)
        self._last_request_response = response
        logger.debug("Response code: {}".format(response.status_code))
        logger.debug("Response content: {}".format(response.content))

        self._last_request_text = response.text
        self._last_request_json = response.json()

        return response.json()

    def touch(self, body, method="POST"):
        uri = "touch"
        return self._send_request(uri=uri, request=body, method=method)
