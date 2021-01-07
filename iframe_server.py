# -*- encoding: utf-8 -*-
from flask import Flask, render_template
from APIC import Connector
from Tenants import Tenants
app = Flask(__name__)

token = ''

def getTenants():
    tenants = Tenants(ACIconnect)
    tenants_list = tenants.getTenantsList()

    return(tenants_list)

@app.route("/tenants")
def tenants():
    headers = ['#','name','modTs','descr']
    Tlist = getTenants()
    if Tlist == 404:
        return render_template('error.html', error_msg='Błąd połączenia')
    else:
        return render_template('tenants.html', headers=headers, tenants=Tlist)

@app.route("/int")
def int_details():
    return render_template('interface.html')
    
@app.route("/")
def hello():
    return render_template('index.html' , card_name='index_var')

if __name__ == "__main__":
    apic_url = 'https://sandboxapicdc.cisco.com'
    usr = 'admin'
    passwd = 'ciscopsdt'

    ACIconnect = Connector(apic_url, usr, passwd)

    app.run(host='0.0.0.0', port=80)