import requests
from requests.auth import HTTPBasicAuth
import sys
from loguru import logger


class Connector():
    def __init__(self, url, usr, passw):
        self.dnac_url = url
        self.usr = usr
        self.passwd = passw
        self.token = None
        self.dnac_token()
        self.errors_counter = 0

    def dnac_token(self):
        logger.info("Connecting to ", self.dnac_url, '...')
        login_url = self.dnac_url + '/api/system/v1/auth/token'

        try:
            post_response = requests.post(url=login_url, auth=HTTPBasicAuth(self.usr, self.passwd), verify=False, timeout=5)
        except requests.exceptions.RequestException as e:
            logger.critical("Error with DNAC connection... \n")
            logger.exception("Error with DNAC connection")
            sys.exit("Error with DNAC connection... \n")


        #get json response
        auth_resp = post_response.json()

        try:
            logger.info('Get Token')
            if 'Token' in auth_resp:
                self.token = auth_resp['Token']
                logger.success('Got token and created cookie')
            else:
                logger.critical('Cannot get token. Details: {x}', x=auth_resp)

        except (KeyError, TypeError):
            print("Authenication error or bad response: ", auth_resp)
            sys.exit("Authenication error or bad response")

    def get(self, uri):
        # self.refresh_token()
        url = uri

        headers = {
            'content-type': "application/json",
            'x-auth-token': self.token
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()


        except requests.exceptions.RequestException as e:
            if 'errorCode' in response.json()['response']:
                logger.critical(response.json()['response']['message'] + " | " + response.json()['response']['detail'])
            logger.exception("Http error")

            if 'exp' in response.json():
                self.dnac_token()

            return None
