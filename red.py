from router import Router
import logging
import networkx as nx
import matplotlib.pyplot as plt
from pysnmp.entity.rfc3413.oneliner import cmdgen
import threading
import datetime
import time
from pysnmp.hlapi import *
from pysnmp.entity.rfc3413.oneliner import cmdgen
import pysnmp
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv
import netmiko
from email.message import EmailMessage
import ssl
import smtplib

cmdGen = cmdgen.CommandGenerator()


class Red():

    def __init__(self,routersCredentialsList):
        self.routersCredentialsList = routersCredentialsList
        self.routers = {}
        self.password = 'cymhfkjbpyotpzkn'
        self.email = 'asr574039@gmail.com'


    def leerTopologia(self):
        if(self.routersCredentialsList == [] or self.routersCredentialsList == None):
            return None
        gatewayCredentials = list(self.routersCredentialsList.values())[0]
        self.routers[gatewayCredentials["nombre"]] = Router(gatewayCredentials["ip"],gatewayCredentials["nombre"],gatewayCredentials["nombreU"],gatewayCredentials["password"],gatewayCredentials["enable"])
        self.routers[gatewayCredentials["nombre"]].buscarVecinos(self,[])
        # Generando gráfico
        G = nx.Graph()
        for router in self.routers:
            if(self.routers[router].user != None):
                G.add_node(router, name=router,color = "green")
                for pc in self.routers[router].pcConectadas:
                    G.add_node(router, name=pc)
                    G.add_edge(router, pc)
            else:
                G.add_node(router, name=router,color = "yellow")
        for r1 in self.routers:
            if( self.routers[r1].conectados != None):
                for r2 in self.routers[r1].conectados:
                    G.add_edge(r1, r2)
        return G
        #nx.draw_networkx(G, with_labels=True, node_color="g") # Creando gráfico
        #plt.savefig("static/topologia.jpg")

    def obtenerRouters(self):
        return self.routers

    def configurarSNMP(self, router):
        if router in self.routers:
            enrutador = Router(self.routers[router].ip, router, self.routers[router].user, self.routers[router].password)
            enrutador.configurarSNMP()
        else:
            raise Exception("Router no encontrado")

    def configurarSSh(self, router,u,p):
        if router in self.routers:
            self.routers[router].CrearUsuarioSsh(u,p)            
        else:
            raise Exception("Router no encontrado")


    def getEstado(self):
        return self.estado

    def enviaCorreo(self,mensaje):

        to = 'asr574039@gmail.com'
        subject = 'Trap'
        body = 'mensaje'

        em=EmailMessage()
        em['From'] = email
        em['To']=to
        em['Subject']=subject
        em.set_content(mensaje)

        conexion = smtplib.SMTP(host='smtp.gmail.com',port=587)
        conexion.ehlo()
        conexion.starttls()
        conexion.login(user=self.email,password=self.password)
        conexion.sendmail(from_addr=email,to_addrs=to,msg=em.as_string())
        conexion.quit

    def cbFun(self,snmpEngine, stateReference, contextEngineId, contextName,varBinds, cbCtx):
        print("Mensaje nuevo de traps recibido");
        logging.info("Mensaje nuevo de traps recibido")
        for name, val in varBinds:
            logging.info('%s = %s' % (name.prettyPrint(), val.prettyPrint()))
            mensaje='%s = %s' % (name.prettyPrint(), val.prettyPrint())
            print(mensaje)
            self.enviaCorreo(mensaje)





    def snmp_get(self,host, community, oid):
        errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(cmdgen.CommunityData(community),cmdgen.UdpTransportTarget((host, 161)),oid)

        if errorIndication:
            print(errorIndication)
        else:
            if errorStatus:
                print('%s at %s' % (
                    errorStatus.prettyPrint(),
		            errorIndex and varBinds[int(errorIndex)-1] or '?'
		            )
		        )
            else:
                for name, val in varBinds:
                    return(str(val))
    def snmp_set(self,host, community, oid,value):
        g = setCmd(SnmpEngine(),CommunityData(community),UdpTransportTarget((host, 161)),ContextData(),ObjectType(ObjectIdentity('SNMPv2-MIB', oid, 0),value))
        next(g)


    def modificarMib(self,host,name,desc,cont,local,comunity):
        print(host,name,desc,cont,local,comunity)
        if(name!=None):
            self.snmp_set(host,comunity,'sysName',name)

        if(desc!=None):
            self.snmp_set(host,comunity,'sysDescr',desc)

        if(cont!=None):
            self.snmp_set(host,comunity,'sysContact',cont)

        if(local!=None):
            self.snmp_set(host,comunity,'sysLocation',local)

    def grafica(self,x,y,rectas,id,titulo):
        print("Haciendo grafica")
        plt.scatter(x, y)
        plt.plot(x, y)
        plt.xlabel('Tiempo')
        plt.ylabel('No. Paquetes')
        plt.ylim([0, 1000])
        plt.title(titulo)

        for n in rectas:
            plt.vlines(x=n, ymin=0, ymax=1000)

        plt.savefig("static/grafica"+str(id)+".jpg", bbox_inches='tight')
        plt.clf()
        plt.close()

    def clear(self):
        plt.clf()

    def monitoreo(self,ip,interfaz,intervalo):

        print(ip,interfaz,intervalo)
	# Interface OID
        inter=int(intervalo)
        oidIn= '1.3.6.1.2.1.2.2.1.10.'
        oidOut='1.3.6.1.2.1.2.2.1.16.'
        oidErroInr='1.3.6.1.2.1.2.2.1.14.'
        oidErrorOut='1.3.6.1.2.1.2.2.1.20.'

        opcion=''

        match interfaz:
            case '0/0':
                oidIn= '1.3.6.1.2.1.2.2.1.10.1'
                oidOut='1.3.6.1.2.1.2.2.1.16.1'
                oidErroInr='1.3.6.1.2.1.2.2.1.14.1'
                oidErrorOut='1.3.6.1.2.1.2.2.1.20.1'
            case '0/1':
                oidIn= '1.3.6.1.2.1.2.2.1.10.2'
                oidOut='1.3.6.1.2.1.2.2.1.16.2'
                oidErroInr='1.3.6.1.2.1.2.2.1.14.2'
                oidErrorOut='1.3.6.1.2.1.2.2.1.20.2'
            case '0/2':
                oidIn='1.3.6.1.2.1.2.2.1.10.3'
                oidOut='1.3.6.1.2.1.2.2.1.16.3'
                oidErroInr='1.3.6.1.2.1.2.2.1.14.3'
                oidErrorOut='1.3.6.1.2.1.2.2.1.20.3'
            case '0/3':
                oidIn='1.3.6.1.2.1.2.2.1.10.4'
                oidOut='1.3.6.1.2.1.2.2.1.16.4'
                oidErroInr='1.3.6.1.2.1.2.2.1.14.4'
                oidErrorOut='1.3.6.1.2.1.2.2.1.20.4'
            case _:
                return None


        host = ip
        community = 'public'
        suma=0

        puntosx=[]
        puntosy=[]

        puntosx1=[]
        puntosy1=[]

        puntosx2=[]
        puntosy2=[]

        puntosx3=[]
        puntosy3=[]

        rectas=[]
        rectas1=[]
        rectas2=[]
        rectas3=[]

        cont=1

        bandera=True
        bandera1=True
        bandera2=True
        bandera3=True



        while True :#cont < int(intervalo):
            if(cont==1):
                result = int(self.snmp_get(host, community, oidIn))
                result1 = int(self.snmp_get(host, community, oidOut))
                result2 = int(self.snmp_get(host, community, oidErroInr))
                result3 = int(self.snmp_get(host, community, oidErrorOut))
            else:
                aux = result
                aux1= result1
                aux2= result2
                aux3= result3
                result = int(self.snmp_get(host, community, oidIn))
                result1 = int(self.snmp_get(host, community, oidOut))
                result2 = int(self.snmp_get(host, community, oidErroInr))
                result3 = int(self.snmp_get(host, community, oidErrorOut))
                #print(result)
                paquetes =  result - aux
                paquetes1 =  result1 - aux1
                paquetes2 =  result2 - aux2
                paquetes3 =  result3 - aux3

                if paquetes <300 :
                    if bandera:
                        rectas.append(cont*inter)
                        bandera = False
                else:
                    if bandera == False:
                        rectas.append(cont*inter)
                        bandera = True
                if paquetes1 <300 :
                    if bandera1:
                        rectas1.append(cont*inter)
                        bandera1 = False
                else:
                    if bandera1 == False:
                        rectas1.append(cont*inter)
                        bandera1 = True

                if paquetes2 <300 :
                    if bandera2:
                        rectas2.append(cont*inter)
                        bandera2 = False
                else:
                    if bandera2== False:
                        rectas2.append(cont*inter)
                        bandera2 = True

                if paquetes3 <300 :
                    if bandera3:
                        rectas3.append(cont*inter)
                        bandera3 = False
                else:
                    if bandera3 == False:
                        rectas3.append(cont*inter)
                        bandera3 = True

                puntosy.append(paquetes)
                puntosx.append(cont*inter)

                puntosy1.append(paquetes1)
                puntosx1.append(cont*inter)

                puntosy2.append(paquetes2)
                puntosx2.append(cont*inter)

                puntosy3.append(paquetes3)
                puntosx3.append(cont*inter)

            cont = cont+1
            if cont>2:
                self.grafica(puntosx,puntosy,rectas,1,'Paquetes de Entrada')
                self.grafica(puntosx1,puntosy1,rectas1,2,'Paquetes de Salida')
                self.grafica(puntosx2,puntosy2,rectas2,3,'Paquetes de Entrada Daniados')
                self.grafica(puntosx3,puntosy3,rectas3,4,'Paquetes de Salida  Daniados')
            time.sleep(int(intervalo))

        print("Monitoreo Finalizado")
