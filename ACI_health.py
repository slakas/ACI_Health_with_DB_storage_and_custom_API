#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime

from APIC import Connector
from models.orm_aci import DataBase, Tenant, Health, Node, App, BD


class ApiAci(Connector):

    def getTenantsHealth(self, db):
        getTenantsURL = self.apic_url + '/api/class/fvTenant.json?rsp-subtree-include=health'
        tenants = self.get(getTenantsURL)

        for tenant in tenants['imdata']:
            tn = db.session.query(Tenant).filter(Tenant.name == tenant['fvTenant']['attributes']['name']).first()
            if tn:
                tn.descr = tenant['fvTenant']['attributes']['descr']
            else:
                db.session.add(Tenant(
                    name=tenant['fvTenant']['attributes']['name'],
                    descr=tenant['fvTenant']['attributes']['descr']
                ))
            db.session.commit()
            # Add tenant health to database table health
            tn = db.session.query(Tenant).filter(Tenant.name == tenant['fvTenant']['attributes']['name']).first()
            db.session.add(Health(
                healthscore=int(tenant['fvTenant']['children'][0]['healthInst']['attributes']['cur']),
                time=datetime.now(),
                tenant_id=tn.id
            ))
        db.save_and_exit()

    def getNodesHelath(self, db):
        nodeHealthUrl = self.apic_url + '/api/class/topSystem.json?rsp-subtree-include=health'
        nodeHealth = self.get(nodeHealthUrl)

        for nHealth in nodeHealth['imdata']:
            ndata = nHealth['topSystem']['attributes']
            node = db.session.query(Node).filter(Node.serial == ndata['serial']).first()

            if ndata['role'] != 'controller':
                if node:
                    node.id = int(ndata['id'])
                    node.name = ndata['name']
                    node.role = ndata['role']
                    node.podId = int(ndata['podId'])
                    node.systemUpTime = ndata['systemUpTime']
                else:
                    #  Add node to node table
                    db.session.add(Node(
                        id = int(ndata['id']),
                        name = ndata['name'],
                        role = ndata['role'],
                        serial = ndata['serial'],
                        podId = int(ndata['podId']),
                        systemUpTime = ndata['systemUpTime']
                        # systemUpTime = maya.parse(ndata['systemUpTime']).datetime()
                    ))
                # Add tenant health to database table health
                db.session.commit()
                node = db.session.query(Node).filter(Node.id == ndata['id']).first()
                db.session.add(Health(
                    healthscore=int(nHealth['topSystem']['children'][0]['healthInst']['attributes']['cur']),
                    time=datetime.now(),
                    node_id=node.id
                ))
                db.save_and_exit()

    def getAppAndBDList(self, db, tenant=None):
        # Get tenant names and
        if not tenant:
            tenants_names = db.session.execute('SELECT name FROM tenant')
            for tn_name in tenants_names:
                self.getAppAndBDList(db, tn_name[0])
                # print(tn_name[0])
            db.save_and_exit()
            return None

        url = self.apic_url + '/api/node/mo/uni/tn-'+tenant+'.json?query-target=children'
        tenant_childrens = self.get(url)

        tn = db.session.query(Tenant).filter(Tenant.name == tenant).first()
        for child in tenant_childrens['imdata']:
            if 'fvAp' in child:
                app = child['fvAp']['attributes']
                instance_app = db.session.query(App).filter(App.name == app['name']).first()
                if instance_app:
                    instance_app.descr = app['descr']
                    instance_app.tenant_id = tn.id
                else:
                    db.session.add(App(
                        name=app['name'],
                        descr=app['descr'],
                        tenant_id = tn.id
                    ))

            elif 'fvBD' in child:
                bd = child['fvBD']['attributes']
                instance_bd = db.session.query(BD).filter(BD.name == bd['name']).first()
                if instance_bd:
                    instance_bd.descr = bd['descr']
                else:
                    db.session.add(BD(
                        name = bd['name'],
                        descr = bd['descr'],
                        tenant_id=tn.id
                    ))

    def getAppHealth(self, db):
        for app in db.session.query(App).all():
            tn = db.session.query(Tenant).filter(Tenant.id == app.tenant_id).one()
            appHealthUrl = self.apic_url + '/api/node/mo/uni/tn-'+tn.name+\
                                            '/ap-'+app.name+\
                                            '.json?query-target=self&rsp-subtree-include=health'
            appsHealths = self.get(appHealthUrl)

            for appHealth in appsHealths['imdata']:
                db.session.add(Health(
                    healthscore = int(appHealth['fvAp']['children'][0]['healthInst']['attributes']['cur']),
                    time = datetime.now(),
                    app_id = app.id
                ))

    def getBdHealth(self, db):
        for bd in db.session.query(BD).all():
            tn = db.session.query(Tenant).filter(Tenant.id == bd.tenant_id).one()
            bdHealthUrl = self.apic_url + '/api/node/mo/uni/tn-'+tn.name+\
                                            '/BD-'+bd.name+\
                                            '.json?query-target=self&rsp-subtree-include=health'

            bdsHealths = self.get(bdHealthUrl)

            for bdHealth in bdsHealths['imdata']:
                db.session.add(Health(
                    healthscore = int(bdHealth['fvBD']['children'][0]['healthInst']['attributes']['cur']),
                    time = datetime.now(),
                    bd_id = bd.id
                ))
        db.save_and_exit()

    def tmp(self, db):
         for app in db.session.query(App).all():
            try:
                 tn = db.session.query(Tenant).filter(Tenant.id == app.tenant_id).one()
                 print(tn.name)
            except:
                print('Database structure error')
        # tenantHealthUrl = self.apic_url + '/api/class/fvTenant.json?rsp-subtree-include=health'
        # tenantHelath = self.get(tenantHealthUrl)

        # for health in tenantHelath['imdata']:
        #     print(json.dumps(health['fvTenant']['children'][0]['healthInst'], indent=2))

        # self.saveToFile(json.dumps(tenantHelath, indent=2))
        # print(json.dumps(tenantHelath, indent=2))

        # nodeHealthUrl = self.apic_url + '/api/class/topSystem.json?rsp-subtree-include=health'
        # nodeHealth = self.get(nodeHealthUrl)

        # for nHealth in nodeHealth['imdata']:
        #     ndata = nHealth['topSystem']['attributes']
        #     if ndata['role'] != 'controller':
        #         print(
        #             'ID: ', ndata['id'],
        #             "Name ",ndata['name'],
        #             'Role: ',ndata['role'],
        #             'Serial: ',ndata['serial'],
        #             'podId: ', ndata['podId'],
        #             'systemUpTime: ', ndata['systemUpTime']
        #         )
        #         # print(json.dumps(ndata['name'], indent=2))
        #
        # self.saveToFile(json.dumps(nodeHealth, indent=2))

        # appHealthUrl = self.apic_url + '/api/node/mo/uni/tn-jk3/ap-master/health.json?query-target=self'
        # appHealth = self.get(appHealthUrl)
        # print(json.dumps(appHealth, indent=2))



    def saveToFile(self, data):
        f = open('json_output.json', 'w')
        f.write(data)
        f.close()


if __name__ == "__main__":
    apic_url = 'https://sandboxapicdc.cisco.com'
    usr = 'admin'
    passwd = 'ciscopsdt'

    api_aci = ApiAci(apic_url, usr, passwd)
    db = DataBase('database/aci.db')
    db.create_tables()
    api_aci.getTenantsHealth(db)
    api_aci.getNodesHelath(db)
    api_aci.getAppAndBDList(db)
    api_aci.getAppHealth(db)
    api_aci.getBdHealth(db)
    # api_aci.tmp(db)