import json
import requests

class Connector():
    def __init__(self, apic_url, usr, passw):
        self.apic_url = apic_url
        self.usr = usr
        self.passwd = passw

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
            return 404

        #get json response
        auth_resp = post_response.json()

        try:
            print('Pobieram Token')
            auth_token = auth_resp['imdata'][0]['aaaLogin']['attributes']['token']

        except (KeyError, TypeError):
            print("Authenication error or bad response: ", auth_resp)
            return 404

        # create cookie array from token
        return {'APIC-Cookie': auth_token}

    def __del__(self):
        del self.CookieToken
        del self.usr
        del self.passwd

class APIC():
    def get(self, uri, token):
        url = uri
        try:
            response = requests.get(url, cookies=token)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print("Http error: ", e)
            return 404

# if __name__ == "__main__":
#     apic_url = 'https://sandboxapicdc.cisco.com'
#     usr = 'admin'
#     passwd = 'ciscopsdt'
#
#     apic = APIC(apic_url,usr,passwd)
#
#     getTenantsURL = '/api/class/fvTenant.json'
#     print("Auth Token: {}\n".format(json.dumps(apic.get(getTenantsURL), indent=2, sort_keys=True)))
#
#     del Connector