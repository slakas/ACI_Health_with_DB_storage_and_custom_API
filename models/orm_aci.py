#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import Column, ForeignKey, Integer, String, Text, create_engine, DateTime, schema, Boolean
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

class Health(dbModel):
    __tablename__ = 'health'
    id = Column(Integer, primary_key=True)
    healthscore = Column(Integer)
    time = Column(DateTime())
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=True)
    tenant = relationship('Tenant', back_populates='health')
    node_id = Column(Integer, ForeignKey('node.id'), nullable=True)
    app_id = Column(Integer, ForeignKey('app.id'), nullable=True)
    bd_id = Column(Integer, ForeignKey('bd.id'), nullable=True)
    epg_id = Column(Integer, ForeignKey('epg.id'), nullable=True)

class App(dbModel):
    __tablename__ = 'app'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    descr = Column(String(250))
    dn = Column(String(250))
    del_flag = Column(Boolean(), default=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=True)
    epg = relationship('Epg', backref='app')
    health = relationship('Health', backref='app')

class BD(dbModel):
    __tablename__ = 'bd'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    descr = Column(String(250))
    dn = Column(String(250))
    del_flag = Column(Boolean(), default=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=True)
    health = relationship('Health', backref='bd')

class Epg(dbModel):
    __tablename__ = 'epg'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    nameAlias = Column(String(250))
    descr = Column(String(250))
    dn = Column(String(250))
    del_flag = Column(Boolean(), default=False)
    app_id = Column(Integer, ForeignKey('app.id'), nullable=True)
    health = relationship('Health', backref='epg')

class Tenant(dbModel):
    __tablename__ = 'tenant'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    descr = Column(String(250))
    del_flag = Column(Boolean(), default=False)
    health = relationship('Health', back_populates='tenant')
    app = relationship('App', backref='app')
    bd = relationship('BD', backref='bd')

class Node(dbModel):
    __tablename__ = 'node'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    serial = Column(String(50))
    podId = Column(Integer)
    role = Column(String(100))
    systemUpTime = Column(String(100))
    dn = Column(String(250))
    # systemUpTime = Column(DateTime())
    del_flag = Column(Boolean(), default=False)
    health = relationship('Health', backref='node')

class FaultSummary(dbModel):
    __tablename__ = 'faultsummary'
    id = Column(Integer, primary_key=True)
    cause = Column(String(50))
    code = Column(String(50))
    count = Column(Integer)
    descr = Column(Text())
    domain = Column(String(50))
    nonAcked = Column(Integer)
    rule = Column(String(150))
    severity = Column(String(50))
    type = Column(String(50))
    faultdetail = relationship('FaultDetail', backref='faultdetail')


class FaultDetail(dbModel):
    __tablename__ = 'faultdetail'
    id = Column(Integer, primary_key=True)
    code = Column(String(50))
    ack = Column(String(50))
    descr = Column(Text())
    dn = Column(Text())
    created = Column(DateTime())
    lastTransition = Column(DateTime())
    domain = Column(String(50))
    rule = Column(String(150))
    severity = Column(String(50))
    type = Column(String(50))
    faultsummary_id = Column(Integer, ForeignKey('faultsummary.id'), nullable=True)
    # faultsummary = relationship('faultsummary', backref='faultdetail')

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
                +config.get('database', 'user')+':'
                +config.get('database', 'passwd')+'@'+db_file)
        self.session = self.create_session()
        self.con = self.engine.connect()

    def create_tables(self):
        # Create table
        dbModel.metadata.create_all(self.engine)

    def drop_table(self, table):
        # drop table
        self._exec(schema.DropTable(table))

    def create_session(self):
        # Create database session
        BDSession = sessionmaker(bind=self.engine)
        return BDSession()

    def getFaults(self, *args):
        '''
            Get all rows from table /table/ and returns columns selected in *args
        '''

        rows = self.session.query(FaultSummary).all()
        list = []
        for row in rows:
            dict = {}
            detail_list = []
            row_dict = row.__dict__
            for arg in args:
                dict.update({arg: row_dict[arg]})

            for detail in row.faultdetail:
                detail_list.append({
                    'code': detail.code,
                    'ack': detail.ack,
                    'descr': detail.dn,
                    'created': detail.created,
                    'lastTransition': detail.lastTransition,
                    'domain': detail.domain,
                    'rule': detail.rule,
                    'severity': detail.severity,
                    'type': detail.type
                })

            list.append((dict, detail_list))

        return list

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

    def setFlagToUnusedRow(self,table, compare_dict, key_str, key_obj):
        tab = self.session.query(table).all()
        for row in tab:
            if not any(t[key_str] == row.name for t in compare_dict):
                logger.warning('Missing item {name}', name=row.name)
                row.del_flag = True

    def dynamic_clean(self, table, recursive=False):

        del_list = []
        del_rows = self.session.query(table).filter_by(del_flag=1).all()

        for element in del_rows:
            # clean health rows
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

