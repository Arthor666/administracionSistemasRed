from flask import Flask, request, jsonify, send_file, render_template
from red import Red
import logging
import networkx as nx
import json
from scapy.all import conf

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', handlers=[logging.FileHandler('app.log')])
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

app = Flask(__name__)
red = None
routersCredentialsList = {}


@app.get('/router')
def registrarRouter():
    global routersCredentialsList
    return render_template('router.html',routers = routersCredentialsList)

@app.post('/router')
def guardarRouter():
    credenciales = request.form
    ip = credenciales['ip']
    name = credenciales['nombre']
    user = credenciales['nombreU']
    password = credenciales['password']
    enable = credenciales['enable']
    global routersCredentialsList
    routersCredentialsList[name] = {"ip":ip,"nombre":name,"nombreU":user,"password":password,"enable":enable}
    return render_template('router.html',routers = routersCredentialsList)

@app.get('/')
def index():
    global red
    global routersCredentialsList
    red = Red(routersCredentialsList)
    G = red.leerTopologia()
    d = nx.json_graph.node_link_data(G)  # node-link format to serialize
    # write json
    json.dump(d, open("static/json/force.json", "w"))
    return render_template('index.html')

@app.post('/topologia')
def obtenerTopologia():
    """ Obetener la topologia de la red e inicializa los
    datos del router al que primero se conecta """
    # Obteniendo credenciales desde la petición
    credenciales = request.get_json()
    ip = credenciales['ip']
    name = credenciales['name']
    user = credenciales['user']
    password = credenciales['password']

    # Asignando crecentiales a la red
    global red
    red = Red(ip, name, user, password)
    # Leyendo la topologia
    G = red.leerTopologia() # almacena en el archivo topologia.jpg
    d = nx.json_graph.node_link_data(G)  # node-link format to serialize
    # write json
    json.dump(d, open("static/scripts/json/force.json", "w"))
    return send_file('static/index.html')

@app.get('/info-topologia')
def obtenerInfoTopologia():
    """ Obetener la topologia de la red e inicializa los
    datos del router al que primero se conecta """

    # Obteniendo la infomración de la topologia
    infoTopologia = red.obtenerRouters()

    return jsonify(infoTopologia)

@app.post('/snmp/<router>')
def levantarSNMP(router):
    """ Levantando procolo SNMP en router """
    # Levantando protocolo SNMP
    red.configurarSNMP(router)

    return jsonify({"status": "ok"})

@app.get('/monitorear')
def monitorearInterfaz():
    """ Realizando monitoreo en interfaz de router """
    # Obteniendo parametros desde la ip
    #print(red.routers)
    return render_template('interfaz.html',routers = red.routers)

@app.post('/monitorear')
def monitorearInterfazView():
    credenciales = request.form
    print(credenciales)
    InterfazCredentialsList={}
    InterfazCredentialsList['inferfaz'] = credenciales
    return render_template('monitoreo.html',intefaz = InterfazCredentialsList)

if __name__ == '__main__':
    app.run(debug=True)
