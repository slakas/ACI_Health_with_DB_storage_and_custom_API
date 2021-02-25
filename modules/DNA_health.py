import json
from datetime import datetime

from models.orm_dnac import Node, Health, Issues, Interfaces
from modules.DNAC import Connector
from loguru import logger

logger.propagate = False

class DNAHealth(Connector):

    # API documentations:
    # https: // developer.cisco.com / docs / dna - center /  # !authentication-api


    def getDevices(self, db):
        url = self.dnac_url+'/dna/intent/api/v1/network-device'
        logger.info('Get devices from DNAC {dnac}', dnac=self.dnac_url)
        response = self.get(url)

        nodes_list = []

        if response:
            for node in response['response']:
                id = node['id']

                payload={
                    'id':id,
                    'hostname': node['hostname'],
                    'serialNumber':node['serialNumber'],
                    'instanceTenantId': node['instanceTenantId'],
                    'role': node['role'],
                    'family': node['family'],
                    'platformId' : node['platformId'],
                    'collectionStatus' : node['collectionStatus']
                }
                nodes_list.append(payload)

                nd = db.session.query(Node).filter(Node.id == id).first()
                if nd:
                    logger.debug('Update node {name}', name=node['hostname'])
                    db.session.query(Node).filter(Node.id == id).update(payload)
                elif not nd:
                    logger.debug('Add node {name}', name=node['hostname'])
                    db.dynamic_add(Node, payload)
                db.session.commit()

                # Get all interfaces of device
                logger.info('Get interfaces of {x}', x=node['hostname'])
                self.getInterfaces(db, id)

        # Checking data
        rows = db.session.query(Node).all()
        for row in rows:
            db.setFlagToUnusedRow(row, row.hostname, 'hostname', nodes_list)

        # Clear database
        db.dynamic_clean(Node)
        db.save_and_exit()

    def getNodesHelath(self, db):
        # Get all nodes from database where del_flag is not True (1)
        nds = db.session.query(Node).filter(Node.del_flag != 1 and Node.role != 'controller').all()

        # Get nodes health
        nodesHealth = self.get(self.dnac_url + '/dna/intent/api/v1/device-health')

        nodesHelath_list = nodesHealth['response']

        for node in nds:
            node_name = node.hostname
            logger.debug('Get node {nd} health', nd=node_name)
            for nodeHealth in nodesHelath_list:
                if node_name == nodeHealth['name']:
                    db.session.add(Health(
                        overallHealth = nodeHealth['overallHealth'],
                        issueCount = nodeHealth['issueCount'],
                        interfaceLinkErrHealth = nodeHealth['interfaceLinkErrHealth'],
                        cpuUlitilization = nodeHealth['cpuUlitilization'],
                        cpuHealth = nodeHealth['cpuHealth'],
                        memoryUtilizationHealth = nodeHealth['memoryUtilizationHealth'],
                        memoryUtilization = nodeHealth['memoryUtilization'],
                        interDeviceLinkAvailHealth = nodeHealth['interDeviceLinkAvailHealth'],
                        interDeviceLinkAvailFabric = nodeHealth['interDeviceLinkAvailFabric'],
                        reachabilityHealth = nodeHealth['reachabilityHealth'],
                        node_id = node.id
                    ))
                    logger.debug('Save health of {node} to database', node=node_name)
                    nodesHelath_list.remove(nodeHealth)
                    break

        db.save_and_exit()

    def getInterfaces(self, db, deviceId):
        url = self.dnac_url+'/dna/intent/api/v1/interface/network-device/'+deviceId
        response = self.get(url)

        interfaces_list = []

        if response:
            for interface in response['response']:
                payload={
                    "adminStatus": interface["adminStatus"],
                    "className": interface["className"],
                    "description": interface["description"],
                    "deviceId": interface["deviceId"],
                    "duplex": interface["duplex"],
                    "id": interface["id"],
                    "ifIndex": interface["ifIndex"],
                    "instanceTenantId": interface["instanceTenantId"],
                    "instanceUuid": interface["instanceUuid"],
                    "interfaceType": interface["interfaceType"],
                    "ipv4Address": interface["ipv4Address"],
                    "ipv4Mask": interface["ipv4Mask"],
                    "isisSupport": interface["isisSupport"],
                    "lastUpdated": interface["lastUpdated"],
                    "macAddress": interface["macAddress"],
                    "mappedPhysicalInterfaceId": interface["mappedPhysicalInterfaceId"],
                    "mappedPhysicalInterfaceName": interface["mappedPhysicalInterfaceName"],
                    "mediaType": interface["mediaType"],
                    "nativeVlanId": interface["nativeVlanId"],
                    "ospfSupport": interface["ospfSupport"],
                    "pid": interface["pid"],
                    "portMode": interface["portMode"],
                    "portName": interface["portName"],
                    "portType": interface["portType"],
                    "serialNo": interface["serialNo"],
                    "series": interface["series"],
                    "speed": interface["speed"],
                    "status": interface["status"],
                    "vlanId": interface["vlanId"],
                    "voiceVlan": interface["voiceVlan"]
                }

                interfaces_list.append(payload)
                inf = db.session.query(Interfaces).filter(Interfaces.id == interface["id"]).first()
                print(inf)
                if inf:
                    logger.debug('Update interface {name}', name=interface['portName'])
                    db.session.query(Interfaces).filter(Interfaces.id == interface["id"]).update(payload)
                elif not inf:
                    logger.debug('Add node {name}', name=interface['portName'])
                    db.dynamic_add(Interfaces, payload)
                db.session.commit()

        # Checking data
        rows = db.session.query(Interfaces).filter_by(deviceId = interface['id']).all()
        for row in rows:
            db.setFlagToUnusedRow(row, row.id, 'id', interfaces_list)


        # Clear database
        db.dynamic_clean(Interfaces)
        db.save_and_exit()

    def getIssues(self,db):
        logger.debug('Get DNA Issues')

        url = self.dnac_url + '/dna/intent/api/v1/issues'
        response = self.get(url)

        MILLISECONDS = 1000

        if response:
            logger.debug('Drop Issues table')
            Issues.__table__.drop(db.engine)
            logger.debug('Create new empty table Issues')
            db.create_tables()

            for issue in response['response']:

                payload = {
                    'name' : issue['name'],
                    'deviceRole' : issue['deviceRole'],
                    'status' : issue['status'],
                    'priority' : issue['priority'],
                    'category' : issue['category'],
                    'issue_occurence_count' : issue['issue_occurence_count'],
                    'last_occurence_time'  : datetime.fromtimestamp(issue['last_occurence_time'] / MILLISECONDS)
                }
                logger.debug('Add data to faultsummary table')
                # db.dynamic_add(Issues, payload)

            # db.save_and_exit()