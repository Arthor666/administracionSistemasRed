from flask import Flask, request, jsonify, send_file, render_template
from red import Red
import logging
import networkx as nx
import json

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', handlers=[logging.FileHandler('app.log')])
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

app = Flask(__name__)
red = None

@app.get('/')
def index():
    # Obteniendo credenciales desde la petición
    #credenciales = request.get_json()
    ip = "192.168.0.1"#credenciales['ip']
    name = "R1"#credenciales['name']
    user = "r1router"#credenciales['user']
    password = "secret12"#credenciales['password']

    # Asignando crecentiales a la red
    global red
    red = Red(ip, name, user, password)
    # Leyendo la topologia
    G = red.leerTopologia() # almacena en el archivo topologia.jpg
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

@app.post('/monitorear-interfaz')
def monitorearInterfaz():
    """ Realizando monitoreo en interfaz de router """
    # Obteniendo parametros desde la ip
    credenciales = request.get_json()
    router = credenciales['router']
    interfaz = credenciales['interfaz']
    periodo = credenciales['periodo']

    try:
        # Realizando monitoreo
        red.monitorear(router, intefaz, periodo)
        return jsonify({"status": "ok"})
    except:
        return jsonify({"status": "Error monitoreando"}), 500

if __name__ == '__main__':
    app.run(debug=True)
