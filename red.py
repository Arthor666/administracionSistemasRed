from router import Router
import logging
import networkx as nx
import matplotlib.pyplot as plt

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

    def monitorear(router, interfaz, periodo):
        if router in self.routers:
            self.routers[router].monitorear(interfaz, periodo)
        else:
            raise Exception("Router no encontrado")
