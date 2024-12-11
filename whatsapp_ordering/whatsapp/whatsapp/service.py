import json
import requests
from . message import message

class whatsapp:

    meta_api_url = None
    meta_version = 'v20.0'
    meta_access_token = None
    meta_phone_number = None
    meta_path = ""
    meta_payload = {}

    # message objects
    meta_message = None


    def __init__(self, meta_path=None, meta_version=None) -> None:
        self.meta_api_url = 'https://graph.facebook.com/'
        if meta_version:
            self.meta_version = meta_version

        self.meta_message = message()
        self.meta_path = meta_path

    def do_request(self):
        response = requests.request("POST", url=self.get_url_request(), headers=self.get_header_request(), data=json.dumps(self.get_payload()))
        return response

    def get_header_request(self):
        headers = {
                    'Authorization': str('Bearer ') + str(self.meta_access_token),
                    'Content-Type':'application/json'
                  }
        return headers
    
    def get_payload(self):
        return self.meta_payload

    def get_url_request(self):
        return self.meta_api_url + str(self.meta_version) + str('/') + str(self.meta_phone_number) + str('/') + str(self.meta_path)