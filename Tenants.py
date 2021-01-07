from APIC import APIC

# from datetime import datetime
import maya

class Tenants():
    def __init__(self, apic_conn):
        self.token = apic_conn.apic_token()
        self.apic = APIC()
        self.apic_url = apic_conn.apic_url

    def getTenantsList(self):
        getTenantsURL = self.apic_url + '/api/class/fvTenant.json'
        token = self.token
        if token == 404:
            return 404

        tenants = self.apic.get(getTenantsURL,token)

        tenants_list = []
        for tenant in tenants['imdata']:
            modTs_date = maya.parse(tenant['fvTenant']['attributes']['modTs']).datetime()
            modTs = str(modTs_date.date())
            modTs = modTs + ' ' + str(modTs_date.time())[:8]
            tenant_tuple = None
            tenant_tuple = (
                tenant['fvTenant']['attributes']['name'],
                modTs,
                tenant['fvTenant']['attributes']['descr']
            )
            tenants_list.append(tenant_tuple)


        return tenants_list
