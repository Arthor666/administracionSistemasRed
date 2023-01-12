from flask import Flask, request, jsonify, send_file, render_template
from wtforms import SelectField
from flask_wtf import FlaskForm 
from red import Red
import logging
import networkx as nx
import json
from scapy.all import conf
import os
import threading

SECRET_KEY = os.urandom(32)


# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', handlers=[logging.FileHandler('app.log')])
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

app = Flask(__name__)
red = None
routersCredentialsList = {}
app.config['SECRET_KEY'] = SECRET_KEY

class Form(FlaskForm):
	router = SelectField('router', choices=[])
	interfaz = SelectField('interfaz', choices=[])
	intervalo = SelectField('intervalo', choices=[])

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

@app.route('/monitorear',methods=['GET','POST'])
def monitorearInterfaz():
    """ Realizando monitoreo en interfaz de router """
    form = Form()
    routers=[]
    for r in red.routers.keys():
    	routers.append((r,r))
    
    form.router.choices = routers
    
    form.intervalo.choices = [('5','5'),('10','10'),('15','15'),('30','30'),('40','40'),('60','60')]
    
    r = list(red.routers.keys())[0]
    
    interfaces=[]
    
    for i in red.routers[r]['interfacesActivas']:
    	interfaces.append((i,i))
    
    form.interfaz.choices=interfaces
    
    if request.method=="POST":
      
       
        router = red.routers[r]['ip']

        monitoreoHilo= threading.Thread(target=red.monitoreo,args=(red.routers[form.router.data]['ip'],form.interfaz.data,form.intervalo.data,))
        monitoreoHilo.start()
        return render_template('monitoreo.html',router=form.router.data,interfaz= form.interfaz.data)
    
    return render_template('interfaz.html',form=form)
    
@app.route('/interfaz/<router>')
def interfaz(router):
	interfaces = red.routers[router]['interfacesActivas']
	
	interArr =[]
	
	for inter in interfaces:
		intObt={}
		intObt['id']= inter
		intObt['name'] =inter
		interArr.append(intObt)
	
	return jsonify({'Interfaces':interArr})
		
	


@app.post('/monitorear')
def monitorearInterfazView():
    credenciales = request.form
    print(credenciales)
    InterfazCredentialsList={}
    InterfazCredentialsList['inferfaz'] = credenciales
    return render_template('monitoreo.html',intefaz = InterfazCredentialsList)

if __name__ == '__main__':
    app.run(debug=True)
    

	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
