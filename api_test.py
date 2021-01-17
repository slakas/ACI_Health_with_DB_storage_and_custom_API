#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from APIC import Connector


class ApiAci(Connector):
    # def __init__(self):
    #     self.apic_token()

    def getTenantsList(self):
        getTenantsURL = self.apic_url + '/api/class/fvTenant.json'

        tenants = self.get(getTenantsURL)
        self.saveToFile(json.dumps(tenants, indent=2))
        # print(json.dumps(tenants, indent=2))

    def saveToFile(self, data):
        f = open('json_output.json', 'w')
        f.write(data)
        f.close()


if __name__ == "__main__":
    apic_url = 'https://sandboxapicdc.cisco.com'
    usr = 'admin'
    passwd = 'ciscopsdt'


    api_aci = ApiAci(apic_url, usr, passwd)
    api_aci.getTenantsList()