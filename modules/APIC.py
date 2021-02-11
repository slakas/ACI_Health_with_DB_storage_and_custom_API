import requests
import sys
from loguru import logger


class Connector():
    def __init__(self, apic_url, usr, passw):
        self.apic_url = apic_url
        self.usr = usr
        self.passwd = passw
        self.token = None
        self.apic_token()
        self.errors_counter = 0


    def apic_token(self):
        logger.info("Connecting to ", self.apic_url, '...')
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
            logger.critical("Error with APIC connection... \n")
            logger.exception("Error with APIC connection")
            sys.exit("Error with APIC connection... \n")


        #get json response
        auth_resp = post_response.json()

        try:
            logger.info('Get Token')
            if 'imdata' in auth_resp:
                auth_token = auth_resp['imdata'][0]['aaaLogin']['attributes']['token']
            else:
                logger.critical('Cannot get token. Details: {x}', x=auth_resp)

        except (KeyError, TypeError):
            print("Authenication error or bad response: ", auth_resp)
            sys.exit("Authenication error or bad response")


        # create cookie array from token
        self.token = {'APIC-Cookie': auth_token}

    def refresh_token(self):
        response = requests.get(self.apic_url + '/api/aaaRefresh-token.json', cookies=self.token)
        if 'error' in response.json()['imdata'][0]:
            logger.error(response.json()['imdata'][0]['error']['attributes']['text'])
            self.apic_token()

    def logout(self):
        logger.info('Logout from apic')
        logout_url = self.apic_url + '/api/aaaLogout.json'
        requests.delete(logout_url)

    def get(self, uri):
        # self.refresh_token()
        url = uri

        try:
            response = requests.get(url, cookies=self.token)
            response.raise_for_status()
            # Check token and renew if needed
            if response.json()['totalCount'] == '0':
                logger.error('TotalCount is 0 for {uri}', uri=uri)
                return None

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.exception("Http error")


