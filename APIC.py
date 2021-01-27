import requests
import sys

class Connector():
    def __init__(self, apic_url, usr, passw):
        self.apic_url = apic_url
        self.usr = usr
        self.passwd = passw
        self.token = None
        self.apic_token()

    def apic_token(self):
        print("\tConnecting to ", self.apic_url, '...')

        login_url = self.apic_url + '/api/aaaLogin.json'

        #body
        login_body = {
            "aaaUser":{
                "attributes":{
                    "name": self.usr,
                    "pwd": self.passwd
                }
            }
        }

        try:
            post_response = requests.post(login_url, json=login_body, timeout=5)
        except requests.exceptions.RequestException as e:
            print("Error with APIC connection... \n", e)
            sys.exit("Error with APIC connection... \n")

        #get json response
        auth_resp = post_response.json()

        try:
            print('Pobieram Token')
            auth_token = auth_resp['imdata'][0]['aaaLogin']['attributes']['token']

        except (KeyError, TypeError):
            print("Authenication error or bad response: ", auth_resp)
            sys.exit("Authenication error or bad response")


        # create cookie array from token
        self.token = {'APIC-Cookie': auth_token}

    def get(self, uri):
        url = uri

        try:
            response = requests.get(url, cookies=self.token)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print("Http error: ", e)
            sys.exit("Http error ")

    def __del__(self):
        del Connector.apic_token
