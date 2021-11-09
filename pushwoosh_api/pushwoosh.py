import requests
import logging
import json
import time

from tenacity import retry
from .pushwoosh_exceptions import *
from json.decoder import JSONDecodeError

OK_STATUSES = [200, 210]
WAIT_TIME = 5.0

logger = logging.getLogger(__name__)


class Pushwoosh:
    api_key = ""
    api_endpoint = "https://cp.pushwoosh.com/json/1.3"
    _last_request_url = None
    _last_request_data = None
    _last_request_response = None
    _last_request_json = None
    _last_request_error = None
    _last_request_text = None

    def __init__(self, api_endpoint, api_key=None):
        self.api_key = api_key
        self.api_endpoint = api_endpoint

    @retry
    def _send_request(self, uri, request):
        # noinspection SpellCheckingInspection
        """
        :param uri: relative URI of the request, e.g. "getPushHistory"
        :param request: object with request body as dict, e.g. { "app_code": "AAAAA-BBBBB"}
        :return: dict with JSON response, e.g. {"status_code":200, "status": "OK", "response": {...}}
        """
        r = {
            "request": request
        }

        if self.api_key is not None:
            r["request"]["auth"] = self.api_key
        self._last_request_data = r

        url = "{}/{}".format(self.api_endpoint, uri)
        self._last_request_url = url

        logger.debug("Url: {}".format(url))
        logger.debug("Data JSON: {}".format(json.dumps(r)))

        response = requests.post(url, data=json.dumps(r))
        self._last_request_response = response
        logger.debug("Response code: {}".format(response.status_code))
        logger.debug("Response content: {}".format(response.content))

        if response.status_code in OK_STATUSES:
            try:
                json_result = response.json()
                if json_result is not None:
                    self._last_request_json = json_result
                    logger.debug("Response json: {}".format(response.json()))
                    return json_result
            except JSONDecodeError:
                self._last_request_text = response.text
                logger.debug("Response text: {}".format(response.text))
                logger.warning("No JSON in response from Pushwoosh API. Content: {}".format(response.content))
                raise (EmptyJsonResponse(response,
                                         "No JSON in Response from Pushwoosh. Response text: {}".format(response.text)))

        else:
            logger.error("Error in response from Pushwoosh. Code: {} Reason: {}".format(response.status_code,
                                                                                        response.reason))
            logger.error("Headers from response: {}".format(response.headers))
            raise (HttpError(response.status_code, response.text,
                             "Pushwoosh API returned code {}. Reason: {}".format(response.status_code,
                                                                                 response.reason)))

    def get_push_history(self, source=None, search_by=None, value=None, last_notification_id=0):
        """
        https://docs.pushwoosh.com/platform-docs/api-reference/messages#getpushhistory
        :param source: None, "CP", "API", "GeoZone", "Beacon", "RSS", "AutoPush", "Twitter", "A/B Test".
        :param search_by: None, "notificationID", "notificationCode", "applicationCode", "campaignCode".
        :param value: Search value set according to the "searchBy" field.
        :param last_notification_id: Used for pagination. Last messageId from the previous /getPushHistory call.
        :return: tuple (#messages, lastNotificationId, rows)
        """
        uri = "getPushHistory"
        request = {
            "source": source,
            "searchBy": search_by,
            "value": value,
            "lastNotificationID": last_notification_id
        }
        logger.debug("Called with params: source: {}, "
                     "searchBy: {}, "
                     "value: {}, "
                     "lastNotificationId: {}".format(source, search_by, value, last_notification_id))

        response = self._send_request(uri=uri, request=request)
        length = response["response"]["rows"].__len__()
        last = 0

        if length:
            last = response["response"]["rows"][-1]["id"]

        return length, last, response["response"]["rows"]

    def get_all_push_history(self, source=None, search_by=None, value=None):
        """
        Obtains all records from push history, that match the provided search criteria (not only 1000)
        :param source: None, "CP", "API", "GeoZone", "Beacon", "RSS", "AutoPush", "Twitter", "A/B Test".
        :param search_by: None, "notificationID", "notificationCode", "applicationCode", "campaignCode".
        :param value: Search value set according to the "searchBy" field.
        :return: tuple (#messages, lastNotificationId, rows)
        """
        last_notification_id = 0
        result = []
        while True:
            num, last_notification_id, rows = self.get_push_history(source=source,
                                                                    search_by=search_by,
                                                                    value=value,
                                                                    last_notification_id=last_notification_id)

            logger.debug("Received {} messages, lastNotificationID: {}".format(num, last_notification_id))

            result += rows

            if not last_notification_id:
                break

        return result

    def push_history_generator(self, source=None, search_by=None, value=None):
        """
        Same as get_all_push_history(), but it uses generator and can be used in for statements like that:
        for message in Pushwoosh.get_all_push_history():
        :param source: None, "CP", "API", "GeoZone", "Beacon", "RSS", "AutoPush", "Twitter", "A/B Test".
        :param search_by: None, "notificationID", "notificationCode", "applicationCode", "campaignCode".
        :param value: Search value set according to the "searchBy" field.
        :return: tuple (#messages, lastNotificationId, rows)
        """
        last_notification_id = 0
        while True:
            num, last_notification_id, rows = self.get_push_history(source=source,
                                                                    search_by=search_by,
                                                                    value=value,
                                                                    last_notification_id=last_notification_id)

            logger.debug("Received {} messages, lastNotificationID: {}".format(num, last_notification_id))

            for row in rows:
                try:
                    yield row
                except StopIteration:
                    return

            if not last_notification_id:
                return

    def get_applications(self, page=0):
        """
        https://docs.pushwoosh.com/platform-docs/api-reference/applications#getapplications
        :param page: The page number for pagination.
        :return: total pages, current page, applications dict
        """
        uri = "getApplications"
        request = {
            "page": page
        }

        response = self._send_request(uri=uri, request=request).get("response")
        return response.get("total", 0), response.get("page", 0), response.get("applications", {})

    def get_all_applications(self):
        """
        Obtains the list of all applications. same as get_applications, but goes through all pages.
        :return:
        """
        page = 0
        result = {}
        while True:
            total, current, applications = self.get_applications(page=page)
            result = {**result, **applications}

            if page == total:
                break

            page += 1

        return result

    def applications_generator(self):
        """
        Same as get_all_applications, but generator to use it like that:
        for app in Pushwoosh.applications_generator()
        :return:
        """
        page = 0
        while True:
            total, current, applications = self.get_applications(page=page)

            for app in applications.keys():
                try:
                    yield app, applications[app]
                except StopIteration:
                    return
            if page == total:
                return
            page += 1

    def delete_message(self, message_code):
        """
        https://docs.pushwoosh.com/platform-docs/api-reference/messages#deletemessage
        :param message_code – message code, obtained from /createMessage request
        :return: result
        """

        uri = "deleteMessage"
        request = {
            "message": message_code
        }

        return self._send_request(uri=uri, request=request)

    def get_results(self, request_id):
        """
        Get results of an asynchronous call, such as exportSegment, bulkSetTags and other (see docs/api_reference.md)
        https://docs.pushwoosh.com/platform-docs/api-reference/messages#getresults
        :param request_id: ID of a scheduled task
        :return:
        """
        uri = "getResults"
        request = {
            "request_id": request_id
        }
        return self._send_request(uri=uri, request=request)

    def wait_for_result(self, request_id, wait_sec=30):
        """
        Same as get_results, but instead of one attempt it waits for a successful completion
        :param request_id: a job ID like "nue_1231231231231231" to check results for
        :param wait_sec: optional, how long to wait between checks. Default: 30 sec.
        :return:
        """
        while True:
            try:
                result = self.get_results(request_id)
                status_code = result.get("status_code")
                if status_code == 200:
                    return result

                logger.info("Request {} is not ready yet. Status: {}. Retrying in {} seconds".format(
                    request_id,
                    status_code,
                    wait_sec))
                time.sleep(wait_sec)
            except KeyError:
                pass

    def export_segment(self, devices_filter):
        """
        Calculate the predefined segment and obtain a link to download a CSV with devices that fall into the segment.
        https://docs.pushwoosh.com/platform-docs/api-reference/filters#exportsegment
        :param devices_filter: Filter string (see the above doc for the syntax reference)
        :return:
        """
        uri = "exportSegment"
        request = {
            "devices_filter": devices_filter
        }
        return self._send_request(uri=uri, request=request)

    def get_inbox_messages(self, application, user_id, hwid, last_code=None, count=0):
        """
        https://docs.pushwoosh.com/platform-docs/api-reference/message-inbox#getinboxmessages
        Method to obtain messages stored in inbox for the user/device
        :param application: -- app code
        :param user_id: -- user id, if there is no custom user ID, then it must be equal to hwid
        :param hwid: -- hwid
        :param last_code: -- Code of the last message retrieved in the previous response.
        :param count: The number of messages to be showed in a single response; used for pagination.
        :return:
        """
        uri = "getInboxMessages"
        request = {
            "application": application,
            "userId": user_id,
            "hwid": hwid,
            "last_code": last_code,
            "count": count
        }
        return self._send_request(uri=uri, request=request).get("response")

    def register_device(self, application, hwid, push_token, device_type, language=None, timezone=None):
        """
        Register device as per https://docs.pushwoosh.com/platform-docs/api-reference/device-api#registerdevice
        :param application: application_code (AAAAA-BBBBB)
        :param hwid: unique ID for the device, could be uuid64
        :param push_token: a valid push token
        :param device_type: type 1 - iOS, 3 - Android, 10 - Safari, 11 - Chrome, 12 - Firefox
        :param language: optional, string in ISO 639-1|639-2 language code
        :param timezone: optional, timezone offset in seconds
        :return: response object
        """
        uri = "registerDevice"
        request = {
            "application": application,
            "hwid": hwid,
            "push_token": push_token,
            "device_type": device_type,
            "language": language,
            "timezone": timezone
        }
        return self._send_request(uri=uri, request=request)

    def unregister_device(self, application, hwid):
        """
        Unregisters the device as per
        https://docs.pushwoosh.com/platform-docs/api-reference/device-api#unregisterdevice
        :param application: - application code
        :param hwid: - hardware ID
        :return:
        """
        uri = "unregisterDevice"
        request = {
            "application": application,
            "hwid": hwid
        }
        return self._send_request(uri=uri, request=request)

    def delete_device(self, application, hwid):
        """
        Unregisters the device as per
        https://docs.pushwoosh.com/platform-docs/api-reference/device-api#unregisterdevice
        :param application: - application code
        :param hwid: - hardware ID
        :return:
        """
        uri = "deleteDevice"
        request = {
            "application": application,
            "hwid": hwid
        }
        return self._send_request(uri=uri, request=request)

    def get_unregistered_devices(self, application):
        """
        :return: array
        """
        uri = "getUnregisteredDevices"
        request = {
            "application": application
        }
        return self._send_request(uri=uri, request=request)

    def create_message(self, application, notifications):
        uri = "createMessage"
        request = {
            "application": application,
            "notifications": notifications
        }
        return self._send_request(uri=uri, request=request)

    def get_tracking_log(self, date):
        uri = "getTrackingLog"
        request = {
            "date": date
        }
        return self._send_request(uri=uri, request=request)

    def list_filters(self):
        uri = "listFilters"
        request = {}
        return self._send_request(uri=uri, request=request)

    def delete_filter(self, name):
        uri = "deleteFilter"
        request = {
            "name": name
        }
        return self._send_request(uri=uri, request=request)

    def create_filter(self, name, conditions=None, operator='AND', application=None, expiration_date=None):
        uri = "createFilter"
        request = {
            "name": name,
            "conditions": conditions,
            "operator": operator,
            "application": application,
            "expiration_date": expiration_date
        }
        return self._send_request(uri=uri, request=request)

    def list_tags(self):
        uri = "listTags"
        request = {}
        return self._send_request(uri=uri, request=request)

    def delete_tag(self, name):
        uri = "deleteTag"
        request = {
            "tag": {
                "name": name
            }
        }
        return self._send_request(uri=uri, request=request)

    def add_tag(self, name, tag_type, application_specific=False, user_specific=False):
        """
        :param name:
        :param tag_type:
                        1 - Integer
                        2 - String
                        3 - List
                        4 - Date
                        5 - Boolean
                        6 - Decimal. Ex: 19.95
                        7 - Version. Ex: "1.0.0.0"
        :param application_specific:
        :param user_specific:
        :return:
        """
        uri = "addTag"
        request = {
            "tag": {
                "name": name,
                "type": tag_type,
                "application_specific": application_specific,
                "user_specific": user_specific
            }
        }
        return self._send_request(uri=uri, request=request)

    def register_user(self, user_id, application, hwid, tz_offset=None, device_type=1):
        uri = "registerUser"
        request = {
            "userId": user_id,
            "application": application,
            "hwid": hwid,
            "tz_offset": tz_offset,
            "device_type": device_type
        }
        return self._send_request(uri=uri, request=request)

    def list_presets(self, application):
        """
        List Push presets as per https://docs.pushwoosh.com/platform-docs/api-reference/presets#listpresets
        :param application:  application code (AAAAA-BBBBB)
        :return: list of preset objects or request object in case of error
        """
        uri = "listPresets"
        request = {
            "application": application
        }
        return self._send_request(uri=uri, request=request).get("response")

    def get_preset(self, preset_code):
        """
        Get preset configuration by its code as per
        https://docs.pushwoosh.com/platform-docs/api-reference/presets#getpreset
        :param preset_code: preset code (AAAAA-BBBBB)
        :return: preset dictionary or request object in case of error
        """
        uri = "getPreset"
        request = {
            "preset_code": preset_code
        }
        return self._send_request(uri=uri, request=request).get("response")

    def create_preset(self, name, application, content, scheduling=None, segmentation=None, campaign_code=None):
        """
        Create preset https://docs.pushwoosh.com/platform-docs/api-reference/presets#createpreset
        :param name: name of the preset to be displayed in control panel
        :param application: application code (AAAAA-BBBBB)
        :param content: content dictionary. IMPORTANT: read the API description for the content structure
        :param scheduling: (optional) scheduling parameters dictionary
        :param segmentation: (optional) segmentation parameters dictionary
        :param campaign_code: (optional) campaign code
        :return: response object
        """
        uri = "createPreset"
        request = {
            "name": name,
            "applicationCode": application,
            "campaignCode": campaign_code,
            "content": content,
            "scheduling": scheduling,
            "segmentation": segmentation
        }
        return self._send_request(uri=uri, request=request)

    def delete_preset(self, preset_code):
        """
        Delete preset as per https://docs.pushwoosh.com/platform-docs/api-reference/presets#deletepreset
        :param preset_code: preset code (AAAAA-BBBBB) to be deleted
        :return: response object
        """
        uri = "deletePreset"
        request = {
            "preset_code": preset_code
        }
        return self._send_request(uri=uri, request=request)

    def get_campaigns(self, application, cursor=None, limit=None):
        """
        Get a list of campaigns as per https://docs.pushwoosh.com/platform-docs/api-reference/campaigns#getcampaigns
        :param application: application code (AAAAA-BBBBB) to retrieve campaigns for
        :param cursor: (optional) the ID of the last campaign from the previous request (works as paginator)
        :param limit: (optional) the number of campaigns to return in one response, by default all are returned.
                    May be used together with cursor parameter.
        :return: list of presets or response object
        """
        uri = "getCampaigns"
        request = {
            "application": application,
            "cursor": cursor,
            "limit": limit
        }
        return self._send_request(uri=uri, request=request).get("response")

    def create_campaign(self, application, name, description=None):
        """й
        Creates campaign as per https://docs.pushwoosh.com/platform-docs/api-reference/campaigns#createcampaign
        :param application: application code (AAAAA-BBBBB) to create campaign for.
        :param name: name for the campaign.
        :param description: (optional) human-readable description to be displayed in PW interface
        :return: response object with campaign ID
        """
        uri = "createCampaign"
        request = {
            "application": application,
            "name": name,
            "description": description
        }
        return self._send_request(uri=uri, request=request)

    def delete_campaign(self, campaign):
        """
        Deletes campaign as per https://docs.pushwoosh.com/platform-docs/api-reference/campaigns#deletecampaign
        :param campaign: ID of the campaign to be deleted
        :return: response object
        """
        uri = "deleteCampaign"
        request = {
            "campaign": campaign
        }
        return self._send_request(uri=uri, request=request)

    def set_tags(self, application, tags, hwid=None, user_id=None):
        """
        Set device or user tags as per https://docs.pushwoosh.com/platform-docs/api-reference/device-api#set-tags
        :param application: application code (AAAAA-BBBBB)
        :param tags: dictionary with tag values to be set. For list tags "operation" is supported as well.
        :param hwid: HWID for the device where tags have to be set. Used for device-specific tags only.
        :param user_id: User ID for the user-specific tag setting.
        :return: response object
        """
        if hwid is None and user_id is None:
            raise(RequiredParametersError([hwid, user_id], "Either hwid or user id have to be provided"))

        uri = "setTags"
        request = {
            "application": application,
            "tags": tags
        }

        if hwid is not None:
            request["hwid"] = hwid
        if user_id is not None:
            request["userId"] = user_id

        return self._send_request(uri=uri, request=request)

    """
    Hidden API method to bulk register devices
    """
    def bulk_register_device(self, application, devices):
        uri = "bulkRegisterDevice"
        request = {
            "application": application,
            "devices": devices
        }

        return self._send_request(uri=uri, request=request)