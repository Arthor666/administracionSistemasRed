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
routersCredentialsList = {'R1':{'ip':'192.168.0.1','nombre': 'R1','nombreU' :"r1router",'password':'secret12','enable':'password123'}}


@app.get('/router')
def registrarRouter():
    global routersCredentialsList
    return render_template('router.html',routers = routersCredentialsList)

@app.get('/protocols/<rname>')
def protocolsRouter(rname):
    global red
    return render_template('protocol-router.html',protocols = red.routers[rname].protocols,name = rname)

@app.post('/OSPF/<rname>')
def configureOSPF(rname):
    confOSPF =  request.form
    global red
    if "OSPF" not in red.routers[rname].protocols:
        red.routers[rname].protocols["OSPF"] = {}
    red.routers[rname].protocols["OSPF"]["area"] = confOSPF["area"]
    if "enable" not in confOSPF:
        red.routers[rname].protocols["OSPF"]["enable"] = False
    else:
        red.routers[rname].protocols["OSPF"]["enable"] = True
    red.routers[rname].OSPF()
    return registrarRouter()

@app.post('/RIP/<rname>')
def configureRIP(rname):
    confRIP =  request.form
    global red
    if "RIP" not in red.routers[rname].protocols:
        red.routers[rname].protocols["RIP"] = {}
    if "enable" not in confRIP:
        red.routers[rname].protocols["RIP"]["enable"] = False
    else:
        red.routers[rname].protocols["RIP"]["enable"] = True
    red.routers[rname].RIP()
    return registrarRouter()

@app.post('/EIGRP/<rname>')
def configureEIGRP(rname):
    confEIGRP =  request.form
    global red
    if "RIP" not in red.routers[rname].protocols:
        red.routers[rname].protocols["EIGRP"] = {}
    if "enable" not in confEIGRP:
        red.routers[rname].protocols["EIGRP"]["enable"] = False
    else:
        red.routers[rname].protocols["EIGRP"]["enable"] = True
    red.routers[rname].EIGRP()
    return registrarRouter()


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
    return registrarRouter()

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

@app.get('/monitorear')
def monitorear():
    """ Obtiene la pagina de monitoreo """
    return send_file('static/monitorear.html')

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

@app.route('/monitorear-interfaz/<dispositivo>/<interfaz>/<tiempo>')
def monitorearInterfaz(dispositivo, interfaz, tiempo):
    """ Realizando monitoreo en interfaz de router """
    # Obteniendo parametros desde la ip
    global red
    if not dispositivo in red.routers.keys():
        return ('No se encuentra el Dispositivo ' + dispositivo)

    r = red.routers[dispositivo]
    print(r)

    if not (interfaz.replace("-", '/') in r['interfacesActivas']):
        return "La interfaz no se encuentra activa en el dispositivo"
    else:
        return "Monitoreo"

if __name__ == '__main__':
    app.run(debug=True)
