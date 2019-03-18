import requests
import json
from base64 import b64encode


# Classes
# Define a custom exception to avoid hiding bugs
class UnexpectedResponseCodeException(Exception):
    pass


# API class for making API calls
class ApiInstance:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.api_base_url = "https://ns1.pervasivenation.com/rest/"

    # Some internal helpers for requests
    # Params should be a list in the order that they are expected by the API
    def __get_request(self, endpoint, url_params=[]):
        params_str = ""
        for param in url_params:
            params_str += "/" + str(param)

        r = requests.get(self.api_base_url + endpoint + params_str, auth=(self.username, self.password))
        if r.status_code is not 200:
            raise UnexpectedResponseCodeException("Expected status code 200 but got: %s" % r.status_code)
        else:
            return r.json()

    def __put_request(self, endpoint, url_params=[], body=None):
        if body is None:
            body = {}
        params_str = ""
        for param in url_params:
            params_str += "/" + str(param)
        r = requests.put(self.api_base_url + endpoint + params_str, auth=(self.username, self.password),
                         data=json.dumps(body))
        if r.status_code is not 200:
            raise UnexpectedResponseCodeException("Expected status code 200 but got: %s" % r.status_code)
        else:
            try:
                return r.json()
            except ValueError:
                # Sometimes requests return an empty value, which causes a JSONDecodeError to be raised - handled here
                return {}

    def __get_basic_auth(self, username=None, password=None):
        if username is None:
            username = self.username

        if password is None:
            password = self.password

        b64str = b64encode(bytes("%s:%s" % (username, password), "utf-8"))
        b64str = b64str.decode("utf-8")
        return "Basic " + b64str

    # Public API functions for use externally
    # Nodes - currently only GET operations implemented
    # Get a list of all nodes' details registered to user on orbiwise
    def get_nodes(self):
        return self.__get_request("nodes")

    # Get a single node's details
    def get_node(self, dev_eui):
        return self.__get_request("nodes", [dev_eui])

    # Payloads - Note: These endpoints are NOT for polling/real time data. For that see callbacks
    # Again only get operations implemented for now
    # Get a list of UL payloads to date for a node
    def get_ul_payloads(self, dev_eui):
        return self.__get_request("nodes", [dev_eui, "payloads", "ul"])

    # Get the latest UL payload for a device
    def get_latest_ul_payload(self, dev_eui):
        return self.__get_request("nodes", [dev_eui, "payloads", "ul", "latest"])

    # Send a downlink from server to device, data in base64 format
    def send_downlink(self, dev_eui, data, port=2, confirmed=None):
        confirmed = "" if confirmed is None else "&confirmed=" + str(confirmed)
        url = self.api_base_url + "nodes/" + dev_eui + "/payloads/dl?port=" + str(port) + confirmed
        b64data = b64encode(data)
        r = requests.post(url, auth=(self.username, self.password), data=b64data, headers={"Content-Type": "application/base64"})
        if r.status_code != 200:
            print(vars(r))
            raise UnexpectedResponseCodeException("Expected status code 200 but got: %s" % r.status_code)
        else:
            try:
                return r.json()
            except ValueError:
                # Sometimes requests return an empty value, which causes a JSONDecodeError to be raised - handled here
                return {}

    # Callback registering - Both methods implemented; all others from docs are callbacks sent to server
    def register_callback_url(self, callback_api_ip, port=80, path_prefix="", retry_policy=0, data_format="base64",
                              callback_api_username=None, callback_api_password=None):
        if callback_api_username is not None and callback_api_password is not None:
            auth_string = self.__get_basic_auth(username=callback_api_username, password=callback_api_password)
        else:
            auth_string = None

        body = {
            "host": callback_api_ip,
            "port": port,
            "path_prefix": path_prefix,
            # I assume this is the auth for the callback api but never explicitly explained in orbiwise docs..
            "auth_string": auth_string if auth_string else "",
            "retry_policy": retry_policy,
            "data_format": data_format
        }
        return self.__put_request("pushmode", ["start"], body=body)

    def deregister_callback_url(self, app_id=None):
        params = ["stop"]
        if app_id is not None:
            params.append(app_id)
        return self.__put_request("pushmode", params)
