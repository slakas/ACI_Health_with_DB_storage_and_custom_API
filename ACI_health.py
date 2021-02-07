#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from APIC import Connector
from models.orm_aci import DataBase, Tenant, Health, Node, App, BD, Epg, FaultSummary
from sqlalchemy import desc, exc
import sys, getopt
from loguru import logger

class ACIHealt(Connector):

    def getTenants(self, db):
        getTenantsURL = self.apic_url + '/api/class/fvTenant.json'
        logger.debug('Get tenants list from {apic}', apic=self.apic_url)
        tenants = self.get(getTenantsURL)
        tenants_dict = []
        tenants_dict_db = []

        # Get tenants from APIC and put into list of dictionaries
        for tenant in tenants['imdata']:
            name = tenant['fvTenant']['attributes']['name']
            descr = tenant['fvTenant']['attributes']['descr']
            dict = {'name':name, 'descr':descr}
            tenants_dict.append(dict)

            tn = db.session.query(Tenant).filter(Tenant.name == name).first()
            if tn:
                logger.debug(f'Update tenant {name} ({descr})', name=name, descr=descr)
                try:
                    db.session.query(Tenant).filter(Tenant.name==name).update(dict)
                except:
                    logger.exception('Unable to update table')
                    db.session.rollback()
                    raise

            elif not tn:
                logger.debug('Add tenant {name}', name=name)
                db.dynamic_add(Tenant, dict)
            db.session.commit()


        # Checking data
        db.setFlagToUnusedRow(Tenant, tenants_dict, 'name', Tenant.name)

        # Clear database
        db.dynamic_clean(Tenant)
        db.save_and_exit()

    def getNodes(self, db):
        getURL = self.apic_url + '/api/node/class/topSystem.json'
        logger.debug('Get nodes list from {apic}', apic=self.apic_url)
        nodes = self.get(getURL)
        nodes_list = []

        # Get tenants from APIC and put into list of dictionaries
        for node in nodes['imdata']:
            id = node['topSystem']['attributes']['id']
            name = node['topSystem']['attributes']['name']
            serial = node['topSystem']['attributes']['serial']
            podId = int(node['topSystem']['attributes']['podId'])
            role = node['topSystem']['attributes']['role']
            systemUpTime = node['topSystem']['attributes']['systemUpTime']
            dn = node['topSystem']['attributes']['dn']

            dict = {
                    'id' : id,
                    'name': name,
                    'serial': serial,
                    'podId': podId,
                    'role': role,
                    'systemUpTime' : systemUpTime,
                    'dn' : dn
            }
            nodes_list.append(dict)

            nd = db.session.query(Node).filter(Node.name == name).first()
            if nd:
                logger.debug('Update node {name}', name=name)
                db.session.query(Node).filter(Node.name==name).update(dict)
            elif not nd:
                logger.debug('Add node {name}', name=name)
                db.dynamic_add(Node, dict)
            db.session.commit()

        # Checking data
        db.setFlagToUnusedRow(Node, nodes_list, 'name', Node.name)

        # Clear database
        db.dynamic_clean(Node)
        db.save_and_exit()

    def getTenantHealth(self, db):
        # Get all tenants from database where del_flag is not True (1)
        tns = db.session.query(Tenant).filter(Tenant.del_flag != 1).all()
        for tn in tns:
            tenant_name = tn.name
            logger.debug('Get tenants {tn} health', tn=tenant_name)
            getTenantHealthURL = self.apic_url + '/api/mo/uni/tn-'+tenant_name+'/health.json'
            tenantHealthURL = self.get(getTenantHealthURL)

            for tenant in tenantHealthURL['imdata']:
                # Add tenant health to database table health
                db.session.add(Health(
                    healthscore=int(tenant['healthInst']['attributes']['cur']),
                    time=datetime.now(),
                    tenant_id=tn.id
                ))
                logger.debug('Save to database {tn} healthscore: {healthscore}',
                             tn=tenant['healthInst']['attributes']['dn'],
                             healthscore=tenant['healthInst']['attributes']['cur']
                             )
        db.save_and_exit()

    def getNodesHelath(self, db):
        # Get all nodes from database where del_flag is not True (1)
        nds = db.session.query(Node).filter(Node.del_flag != 1 and Node.role != 'controller').all()
        for node in nds:
            node_name = node.name
            logger.debug('Get node {nd} health', nd=node_name)
            getHealthURL = self.apic_url + '/api/mo/' + node.dn + '/health.json'
            getHealthURL = self.get(getHealthURL)

            for nodeHealth in getHealthURL['imdata']:
                db.session.add(Health(
                    healthscore=int(nodeHealth['healthInst']['attributes']['cur']),
                    time=datetime.now(),
                    node_id=node.id
                ))
                logger.debug('Save to database {tn} healthscore: {healthscore}',
                             tn=nodeHealth['healthInst']['attributes']['dn'],
                             healthscore=nodeHealth['healthInst']['attributes']['cur']
                             )
        db.save_and_exit()

    def getAppAndBDList(self, db):
        apps_list = []
        bds_list = []
        # Get tenant names and
        tenants = db.session.query(Tenant).filter(Tenant.del_flag != 1).all()
        for tenant in tenants:
            tenant_id = tenant.id
            tenant = tenant.name

            url = self.apic_url + '/api/node/mo/uni/tn-'+tenant+'.json?query-target=children'
            logger.info('Get App and BD list from tenant {tenant}',tenant=tenant)
            tenant_childrens = self.get(url)

            if tenant_childrens['totalCount'] != '0':
                for child in tenant_childrens['imdata']:
                    if 'fvAp' in child:
                        name = child['fvAp']['attributes']['name']
                        descr = child['fvAp']['attributes']['descr']
                        dn = child['fvAp']['attributes']['dn']
                        dict = {
                            'name' : name,
                            'descr' : descr,
                            'dn' : dn,
                            'tenant_id' : tenant_id
                        }
                        apps_list.append(dict)
                        app = db.session.query(App).filter(App.name == name).first()
                        if app:
                            logger.debug('Update app {name}', name=name)
                            db.session.query(App).filter(App.name == name).update(dict)
                        elif not app:
                            logger.debug('Add app {name}', name=name)
                            db.dynamic_add(App, dict)
                        db.session.commit()

                    elif 'fvBD' in child:
                        name = child['fvBD']['attributes']['name']
                        descr = child['fvBD']['attributes']['descr']
                        dn = child['fvBD']['attributes']['dn']
                        dict = {
                            'name' : name,
                            'descr' : descr,
                            'dn' : dn,
                            'tenant_id' : tenant_id
                        }
                        bds_list.append(dict)
                        bd = db.session.query(BD).filter(BD.name == name).first()
                        if bd:
                            logger.debug('Update bridge-domain {name}', name=name)
                            db.session.query(BD).filter(BD.name == name).update(dict)
                        elif not bd:
                            logger.debug('Add bridge-domain {name}', name=name)
                            db.dynamic_add(BD, dict)
                        db.session.commit()

        # Checking data
        db.setFlagToUnusedRow(App, apps_list, 'name', App.name)
        db.setFlagToUnusedRow(BD, bds_list, 'name', BD.name)
        # Clear database
        logger.debug('Clear App and BD tables, commit and exit connection to DB')
        db.dynamic_clean(App)
        db.dynamic_clean(BD)
        db.save_and_exit()

    def getAppHealth(self, db):
        logger.info('Get Apps list from DB')
        for app in db.session.query(App).all():
            tn = db.session.query(Tenant).filter(Tenant.id == app.tenant_id and Tenant.del_flag != 1).first()
            appHealthUrl = self.apic_url + '/api/node/mo/uni/tn-'+tn.name+\
                                            '/ap-'+app.name+\
                                            '.json?query-target=self&rsp-subtree-include=health'
            logger.info('Get app [{app}] health', app=app.name)
            appsHealths = self.get(appHealthUrl)

            for appHealth in appsHealths['imdata']:
                db.session.add(Health(
                    healthscore = int(appHealth['fvAp']['children'][0]['healthInst']['attributes']['cur']),
                    time = datetime.now(),
                    app_id = app.id
                ))

        db.save_and_exit()

    def getBdHealth(self, db):
        logger.info('Get BDs list from DB')
        for bd in db.session.query(BD).all():
            tn = db.session.query(Tenant).filter(Tenant.id == bd.tenant_id and Tenant.del_flag != 1).one()
            bdHealthUrl = self.apic_url + '/api/node/mo/uni/tn-'+tn.name+\
                                            '/BD-'+bd.name+\
                                            '.json?query-target=self&rsp-subtree-include=health'
            logger.info('Get BD [{bd}] health', bd=bd.name)
            bdsHealths = self.get(bdHealthUrl)

            for bdHealth in bdsHealths['imdata']:
                db.session.add(Health(
                    healthscore = int(bdHealth['fvBD']['children'][0]['healthInst']['attributes']['cur']),
                    time = datetime.now(),
                    bd_id = bd.id
                ))
        db.save_and_exit()

    def getEpgList(self,db):
        logger.debug("Getting EPGs list")

        epgs_list = []
        apps = db.session.query(App).filter(App.del_flag != 1).all()
        for app in apps:
            url = self.apic_url + '/api/node/mo/'+app.dn+'.json?query-target=children'
            apic_response = self.get(url)
            if apic_response:
                for fv in apic_response['imdata']:
                    if 'fvAEPg' in fv:
                        name = fv['fvAEPg']['attributes']['name']
                        nameAlias = fv['fvAEPg']['attributes']['nameAlias']
                        descr = fv['fvAEPg']['attributes']['descr']
                        dn = fv['fvAEPg']['attributes']['dn']
                        del_flag = False
                        app_id = app.id
                        dict = {
                            'name' : name,
                            'nameAlias' : nameAlias,
                            'descr' : descr,
                            'dn' : dn,
                            'del_flag' : del_flag,
                            'app_id' : app_id
                        }
                        epgs_list.append(dict)

                        epg = db.session.query(Epg).filter(Epg.name == name).first()
                        if epg:
                            logger.debug('Update EPG {name}', name=name)
                            db.session.query(Epg).filter(Epg.name == name).update(dict)
                        elif not epg:
                            logger.debug('Add EPG {name}', name=name)
                            db.dynamic_add(Epg, dict)
                db.session.commit()


        # Checking if data exists
        db.setFlagToUnusedRow(Epg, epgs_list, 'name', Epg.name)
        # Clear database
        logger.debug('Clear Epg tables, commit and exit connection to DB')
        db.dynamic_clean(Epg)
        db.save_and_exit()

    def getEpgHelath(self, db):
        # Get all epgs from database where del_flag is not True (1)
        epgs = db.session.query(Epg).filter(Epg.del_flag != 1).all()
        for epg in epgs:
            logger.debug('Get node {nd} health', nd=epg.name)
            getHealthURL = self.apic_url + '/api/mo/' + epg.dn + '/health.json'
            getHealthURL = self.get(getHealthURL)

            for epgHealth in getHealthURL['imdata']:
                db.session.add(Health(
                    healthscore=int(epgHealth['healthInst']['attributes']['cur']),
                    time=datetime.now(),
                    epg_id=epg.id
                ))
                logger.debug('Save to database {tn} healthscore: {healthscore}',
                             tn=epgHealth['healthInst']['attributes']['dn'],
                             healthscore=epgHealth['healthInst']['attributes']['cur']
                             )
        db.save_and_exit()

    def getFaultsSummary(self, db):
        logger.debug('Get FaultsSummary')

        url = self.apic_url + '/api/node/class/faultSummary.json?order-by=faultSummary.severity|desc'
        apic_response = self.get(url)

        if apic_response:
            logger.debug('Drop FaultSummary table')
            FaultSummary.__table__.drop(db.engine)
            logger.debug('Create new empty table faultsummary')
            db.create_tables()


            for fault in apic_response['imdata']:
                dict = {
                    'cause' : fault['faultSummary']['attributes']['cause'],
                    'code' : fault['faultSummary']['attributes']['code'],
                    'count' : int(fault['faultSummary']['attributes']['count']),
                    'descr' : fault['faultSummary']['attributes']['descr'],
                    'domain' : fault['faultSummary']['attributes']['domain'],
                    'nonAcked' : int(fault['faultSummary']['attributes']['nonAcked']),
                    'rule' : fault['faultSummary']['attributes']['rule'],
                    'severity' : fault['faultSummary']['attributes']['severity'],
                    'type' : fault['faultSummary']['attributes']['type']
                }
                logger.debug('Add data to faultsummary table')
                db.dynamic_add(FaultSummary, dict)

            db.save_and_exit()


    def tmp(self, db=None):
        # Get APP list from DB
        try:
            apps_list = db.session.query(App).all()
        except exc.SQLAlchemyError as e:
            logger.exception("Database trouble")
            sys.exit()

        for app in apps_list:
            logger.info(app.__dict__)

    def saveToFile(self, data):
        f = open('json_output.json', 'w')
        f.write(data)
        f.close()


if __name__ == "__main__":
    apic_url = 'https://sandboxapicdc.cisco.com'
    usr = 'admin'
    passwd = 'ciscopsdt'

    # Default LogLevel
    LOGLEVEL = 'WARNING'
    LOGFILE = 'logs/aci_health.log'

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hl:p:u:do:f:t:",
                                   ["help", "debug", "info"
                                    ])
    except getopt.GetoptError:
        print(str(sys.argv[0]) + ' : illegal option')
        sys.exit(2)

    for opt, arg in opts:
         if opt in ('-d', '--debug'):
            LOGLEVEL = "DEBUG"
         elif opt in ('-i', '--info'):
             LOGLEVEL = "INFO"


    logger.add(sys.stderr, format="{time} {level} {message}", filter="test" )
    logger.add(LOGFILE, level="WARNING", rotation="01:00")


    api_aci = ACIHealt(apic_url, usr, passwd)
    db = DataBase('database/aci.db')
    db.create_tables()
    api_aci.getTenants(db)
    api_aci.getNodes(db)
    api_aci.getTenantHealth(db)
    api_aci.getNodesHelath(db)
    api_aci.getAppAndBDList(db)
    api_aci.getAppHealth(db)
    api_aci.getBdHealth(db)
    api_aci.getEpgList(db)
    api_aci.getEpgHelath(db)
    api_aci.getFaultsSummary(db)
    # api_aci.tmp(db)


