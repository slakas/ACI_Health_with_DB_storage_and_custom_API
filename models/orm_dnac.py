#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import Column, ForeignKey, Integer, String, Text, create_engine, DateTime, schema, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from loguru import logger
from pathlib import Path
import configparser, sys

'''
MySQL helper docs:
https://mysql.wisborg.dk/2019/03/03/using-sqlalchemy-with-mysql-8/#installing-mysql-server

'''

# Base class
dbModel = declarative_base()

class Node(dbModel):
    __tablename__ = 'node'
    id = Column(String(100), primary_key=True)
    hostname = Column(String(50), unique=True)
    serialNumber = Column(String(50))
    instanceTenantId = Column(String(50))
    role = Column(String(100))
    family = Column(String(50))
    platformId = Column(String(50))
    del_flag = Column(Boolean(), default=False)
    collectionStatus = Column(String(50))
    # interfacesCount = Column(Integer()) #https://{{dnac}}:{{port}}/dna/intent/api/v1/interface/network-device/183ed3e6-3472-405c-a1ce-26d07987a140/count
    # systemUpTime = Column(DateTime())
    health = relationship('Health', backref='node')
    interfaces = relationship('Interfaces', backref='node')

class Interfaces(dbModel):
    __tablename__ = 'interfaces'
    id = Column(String(100), primary_key=True)
    adminStatus = Column(String(250))
    className = Column(String(100))
    description = Column(String(100))
    duplex = Column(String(100))
    ifIndex = Column(String(100))
    instanceTenantId = Column(String(100))
    instanceUuid = Column(String(100))
    interfaceType = Column(String(100))
    ipv4Address = Column(String(100))
    ipv4Mask = Column(String(100))
    isisSupport = Column(String(100))
    lastUpdated = Column(String(100))
    macAddress = Column(String(100))
    mappedPhysicalInterfaceId = Column(String(100))
    mappedPhysicalInterfaceName = Column(String(100))
    mediaType = Column(String(100))
    nativeVlanId = Column(String(100))
    ospfSupport = Column(String(100))
    pid = Column(String(100))
    portMode = Column(String(100))
    portName = Column(String(100))
    portType = Column(String(100))
    serialNo = Column(String(100))
    series = Column(String(100))
    speed = Column(String(100))
    status = Column(String(100))
    vlanId = Column(String(100))
    voiceVlan = Column(String(100))
    del_flag = Column(Boolean(), default=False)
    deviceId = Column(String(100), ForeignKey('node.id'), nullable=True)

class Issues(dbModel):
    __tablename__ = 'issues'
    id = Column(String(100), primary_key=True)
    name = Column(Text())
    deviceRole = Column(String(100))
    status = Column(String(100))
    priority = Column(String(10))
    category = Column(String(100))
    issue_occurence_count = Column(Integer())
    last_occurence_time = Column(DateTime())

class Health(dbModel):
    __tablename__ = 'health'
    id = Column(Integer, primary_key=True, unique=True)
    overallHealth = Column(Integer)
    issueCount = Column(Integer)
    interfaceLinkErrHealth = Column(Integer)
    cpuUlitilization = Column(Integer)
    cpuHealth = Column(Integer)
    memoryUtilizationHealth = Column(Integer)
    memoryUtilization = Column(Float())
    interDeviceLinkAvailHealth = Column(Integer)
    interDeviceLinkAvailFabric = Column(Integer)
    reachabilityHealth = Column(String(50))
    # clientCount = Column(Text())
    # "freeTimerScore": -1,
    # "packetPoolHealth": -1,
    # "wqePoolsHealth": -1,
    # "wanLinkUtilization": -1,
    # "interferenceHealth": {},
    # "noiseHealth": {},
    # "airQualityHealth": {},
    # "utilizationHealth": {}
    node_id = Column(String(100), ForeignKey('node.id'), nullable=True)

class DataBase():
    def __init__(self, db_file):
        # Load configuration form conf.cnf file
        cnf_file = Path(__file__).resolve().parent.parent.joinpath('conf.cnf')
        config = configparser.ConfigParser()
        config.readfp(open(cnf_file))
        # Create instance of Engine class to manage the database
        # SQLite
        # self.engine = create_engine('sqlite:///'+db_file)
        # MySQL
        self.engine = create_engine(
            'mysql+mysqlconnector://'
                +config.get('dna_database', 'user')+':'
                +config.get('dna_database', 'passwd')+'@'+db_file)
        self.session = self.create_session()
        self.con = self.engine.connect()

    def create_tables(self):
        # Create table
        dbModel.metadata.create_all(self.engine)

    def drop_table(self, table):
        # drop table
        # self.engine._exec(schema.DropTable(table))
        table.__table__.drop(self.engine)

    def create_session(self):
        # Create database session
        BDSession = sessionmaker(bind=self.engine)
        return BDSession()

    def dynamic_get(self,table, *args):
        '''
            Get all rows from table /table/ and returns columns selected in *args
        '''

        rows = self.session.query(table).all()
        list = []
        for row in rows:
            dict = {}
            row_dict = row.__dict__
            for arg in args:
                dict.update({arg : row_dict[arg]})
            list.append(dict)

        return list

    def dynamic_get_with_health(self,table, *args):
        '''
            Get all rows from table /table/ and returns columns selected in *args
        '''

        rows = self.session.query(table).all()
        list = []
        for row in rows:
            dict = {}
            # h_dict = {}
            h_list = []
            row_dict = row.__dict__
            for arg in args:
                dict.update({arg : row_dict[arg]})

            for health in row.health:
                h_list.append({
                    'healthscore' : health.healthscore,
                    'time' : health.time
                })


            list.append((dict,h_list))

        return list

    def dynamic_add(self,table, payload):
        add_data = None
        if type(payload) is list:
            for row in payload:
                logger.debug('Add data {x}', x=row)
                add_data = table(**row)
                self.session.add(add_data)
                self.session.flush()
                self.session.refresh(add_data)
            # self.session.commit()
        else:
            logger.debug('Add data {x}', x=payload)
            add_data = table(**payload)
            self.session.add(add_data)
            self.session.flush()
            self.session.refresh(add_data)

        return add_data.id

    def setFlagToUnusedRow(self,row, compare_obj, compare_obj_str, compare_dict):
            if not any(t[compare_obj_str] == compare_obj for t in compare_dict):
                logger.warning('Missing item {name}', name=compare_obj)
                row.del_flag = True

    def dynamic_clean(self, table, recursive=False):

        del_list = []
        del_rows = self.session.query(table).filter_by(del_flag=1).all()

        for element in del_rows:
            # clean health rows
            if hasattr(element, 'health') and callable(getattr(element, 'health')):
                del_list.append(element.health)
            # Recursive clean
            if table.__tablename__ == 'tenant':
                # relationship: health, app, bd
                del_list.append( element.health)
                del_list.append( element.app)
                del_list.append( element.bd)

            elif table.__tablename__ == 'app':
                # relationship :    tenant_id ,   health
                del_list.append(element.health)
                del_list.append(element.epg)


        del_list.append(del_rows)

        if len(del_list) == 0:
            logger.info('Nothing to remove ')
            return None
        else:
            for list in del_list:
                for row in list:
                    logger.warning('Try do remove {y}: {x}', y=row.__tablename__, x=row.__dict__)
                    self.session.delete(row)

    def save_and_exit(self):
        # Save and exit database
        self.session.commit()
        self.session.close()

