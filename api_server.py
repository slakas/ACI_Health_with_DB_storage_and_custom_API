# -*- encoding: utf-8 -*-
import configparser, json
from flask import Flask, render_template, jsonify
from models.orm_aci import DataBase,Tenant, Health, Node, App, BD, Epg, FaultSummary, FaultDetail

app = Flask(__name__)



@app.route("/epg", methods=['GET'])
def epg():
    payload = db.dynamic_get(Epg, 'name', 'nameAlias', 'descr', 'dn')
    return jsonify(payload)

@app.route("/epg/health", methods=['GET'])
def epg_health():
    payload = db.dynamic_get_with_health(Epg, 'name', 'nameAlias', 'descr', 'dn')
    return jsonify(payload)

@app.route("/bd", methods=['GET'])
def bd():
    payload = db.dynamic_get(BD, 'name', 'descr', 'dn')
    return jsonify(payload)

@app.route("/bd/health", methods=['GET'])
def bd_health():
    payload = db.dynamic_get_with_health(BD, 'name', 'descr', 'dn')
    return jsonify(payload)

@app.route("/tenant", methods=['GET'])
def tenant():
    payload = db.dynamic_get(Tenant, 'name', 'descr')
    return jsonify(payload)

@app.route("/tenant/health", methods=['GET'])
def tenant_health():
    payload = db.dynamic_get_with_health(Tenant, 'name', 'descr')
    return jsonify(payload)

@app.route("/node/health", methods=['GET'])
def node_health():
    payload = db.dynamic_get_with_health(Node, 'name', 'serial', 'podId', 'role', 'systemUpTime', 'dn')
    return jsonify(payload)

@app.route("/node", methods=['GET'])
def node():
    payload = db.dynamic_get(Node, 'name', 'serial', 'podId', 'role', 'systemUpTime', 'dn')
    return jsonify(payload)

@app.route("/app", methods=['GET'])
def aci_apps():
    payload = db.dynamic_get(App, 'name', 'descr', 'dn')
    return jsonify(payload)

@app.route("/app/health", methods=['GET'])
def app_health():
    payload = db.dynamic_get_with_health(App, 'name', 'descr', 'dn')
    return jsonify(payload)

@app.route("/faults", methods=['GET'])
def faults():
    payload = db.getFaults('code', 'cause', 'count', 'descr', 'domain', 'nonAcked', 'rule')
    return jsonify(payload)

@app.route("/")
def index():
    return jsonify({'service_ver':'0.1.0'})

if __name__ == "__main__":
    # Load configuration form conf.cnf file
    cnf_file = 'conf.cnf'

    config_path = cnf_file
    config = configparser.ConfigParser()
    config.readfp(open(config_path))

    db_path = config.get('database', 'db_path')
    db = DataBase(db_path)
    # db.dynamic_get((Node, 'name', 'serial', 'role'))

    app.run(host='0.0.0.0', port=8080)