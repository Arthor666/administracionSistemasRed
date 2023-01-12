from router import Router
import logging
import networkx as nx
import matplotlib.pyplot as plt
from pysnmp.entity.rfc3413.oneliner import cmdgen
import threading
import datetime
import time
cmdGen = cmdgen.CommandGenerator()

class Red():

    def __init__(self,routersCredentialsList):
        self.routersCredentialsList = routersCredentialsList
        self.routers = {}

    def leerTopologia(self):
        if(self.routersCredentialsList == [] or self.routersCredentialsList == None):
            return None
        gatewayCredentials = list(self.routersCredentialsList.values())[0]
        router_cercano = Router(gatewayCredentials["ip"],gatewayCredentials["nombre"],gatewayCredentials["nombreU"],gatewayCredentials["password"],gatewayCredentials["enable"])
        router_cercano.buscarVecinos(self)
        # Generando gráfico
        G = nx.Graph()
        for router in self.routers:
            if(self.routers[router]["user"] != None):
                G.add_node(router, name=router,color = "green")
                for pc in self.routers[router]["pcConectadas"]:
                    G.add_node(router, name=pc)
                    G.add_edge(router, pc)
            else:
                G.add_node(router, name=router,color = "yellow")
        for r1 in self.routers:
            if( self.routers[r1]["conectados"] != None):
                for r2 in self.routers[r1]["conectados"]:
                    G.add_edge(r1, r2)
        return G
        #nx.draw_networkx(G, with_labels=True, node_color="g") # Creando gráfico
        #plt.savefig("static/topologia.jpg")

    def obtenerRouters(self):
        return self.routers

    def configurarSNMP(self, router):
        if router in self.routers:
            enrutador = Router(self.routers[router]["ip"], router, self.routers[router]["user"], self.routers[router]["password"])
            enrutador.configurarSNMP()
        else:
            raise Exception("Router no encontrado")

    def snmp_query(self,host, community, oid):
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
    

    def grafica(self,x,y,rectas):
        print("Haciendo grafica")
        plt.scatter(x, y)
        plt.plot(x, y)
        plt.xlabel('Tiempo')
        plt.ylabel('No. Paquetes')
        plt.ylim([0, 1000])
        
        for n in rectas:
            plt.vlines(x=n, ymin=0, ymax=1000)
        
        plt.savefig("static/grafica.jpg", bbox_inches='tight')
        plt.close()
        
    def clear(self):
        plt.clf()

    def monitoreo(self,ip,interfaz,intervalo):

        print(ip,interfaz,intervalo)
	# Interface OID

        oid=''
        match interfaz:
            case '0/0':
                oid= '1.3.6.1.2.1.2.2.1.10.1'
            case '0/1':
                oid= '1.3.6.1.2.1.2.2.1.10.2'
            case '0/2':
                oid='1.3.6.1.2.1.2.2.1.10.2'
            case '0/3':
                oid='1.3.6.1.2.1.2.2.1.10.2'
            case _:
                return None
       

        host = ip
        community = 'secreta'
        suma=0
        
        puntosx=[]
        puntosy=[]
        rectas=[]  

        cont=1
        bandera=True            
            
        while True :#cont < int(intervalo):
            if(cont==1):
                result = int(self.snmp_query(host, community, oid))
                
            else:
                aux = result
                result = int(self.snmp_query(host, community, oid))
                #print(result)
                paquetes =  result - aux
                if paquetes <300 :
                    if bandera:
                        rectas.append(cont*5)
                        bandera = False
                else:
                    if bandera == False:
                        rectas.append(cont*5)
                        bandera = True
                
                
                puntosy.append(paquetes)
                puntosx.append(cont*5)
            cont = cont+1
            
            
            print(puntosx)
            print(puntosy)
            if cont>2:
                self.grafica(puntosx,puntosy,rectas)
            time.sleep(int(intervalo))
            
        print("Monitoreo Finalizado")

    

