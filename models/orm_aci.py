#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime


# Base class
dbModel = declarative_base()

class Health(dbModel):
    __tablename__ = 'health'
    id = Column(Integer, primary_key=True)
    healthscore = Column(Integer)
    time = Column(DateTime())
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=True)
    node_id = Column(Integer, ForeignKey('node.id'), nullable=True)
    app_id = Column(Integer, ForeignKey('app.id'), nullable=True)
    bd_id = Column(Integer, ForeignKey('bd.id'), nullable=True)

class App(dbModel):
    __tablename__ = 'app'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    descr = Column(String(250))
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=True)
    health = relationship('Health', backref='app')

class BD(dbModel):
    __tablename__ = 'bd'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    descr = Column(String(250))
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=True)
    health = relationship('Health', backref='bd')

class Tenant(dbModel):
    __tablename__ = 'tenant'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    descr = Column(String(250))
    health = relationship('Health', backref='tenant')
    app = relationship('App', backref='app')
    bd = relationship('BD', backref='bd')

class Node(dbModel):
    __tablename__ = 'node'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    role = Column(String(100))
    serial = Column(String(50))
    podId = Column(Integer)
    systemUpTime = Column(String(100))
    # systemUpTime = Column(DateTime())
    health = relationship('Health', backref='node')


class DataBase():
    def __init__(self, db_file):
        # Create instance of Engine class to manage the database
        self.engine = create_engine('sqlite:///'+db_file)
        self.session = self.create_session()

    def create_tables(self):
        # Create table
        dbModel.metadata.create_all(self.engine)

    def create_session(self):
        # Create database session
        BDSession = sessionmaker(bind=self.engine)
        return BDSession()

    def save_and_exit(self):
        # Save and exit database
        self.session.commit()
        self.session.close()

