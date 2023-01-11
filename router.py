import pexpect
import getpass
import logging
import time
from ipaddress import IPv4Address

class Router:
    def __init__(self, ip, name, user="root", password="root",enable = "",protocols = {},conectados = None,interfaces = None,pcConectadas = {}):
        self.ip = ip
        self.name = name
        self.user = user
        self.password = password
        self.enable = enable
        self.protocols = protocols
        self.conectados = conectados
        self.interfaces = interfaces
        self.pcConectadas = pcConectadas

    def buscarVecinos(self, red):
        if self.name in red.routers.keys(): # Si ya fue obtenido, no lo volvemos a obtener
            return
        if self.name not in red.routersCredentialsList.keys():
            red.routers[self.name] = Router(self.ip,None,None,None,None,None)
            return
        credenciales = red.routersCredentialsList[self.name]
        #logging.debug(mensaje)

        """ Nos conectamos al router """
        child = pexpect.spawn('telnet '+ self.ip)
        child.expect('Username: ')
        child.sendline(credenciales["nombreU"])
        child.expect('Password: ')
        child.sendline(credenciales["password"])

        """Obtenemos la tabla de dispositivos conectados """
        child.expect(self.name+">")
        child.sendline('enable')
        child.expect('Password: ')
        child.sendline(credenciales["enable"])
        child.expect(self.name+"#")
        child.sendline('show cdp ne | begin Device') # Obtenemos la tabla de dispositivos
        child.expect(self.name+"#")
        routersVecinos = child.before.decode().split("\r\n")
        routersVecinos = routersVecinos[2:]
        routersVecinos = [x for x in routersVecinos if x != '' ]
        conectados = [x.split()[0] for x in routersVecinos]
        interfaces = [str(x.split()[1])+str(x.split()[2]) for x in routersVecinos ]
        """ Registramos el router """
        red.routers[self.name] = Router(self.ip,self.name,self.user,self.password,credenciales["enable"],{},[x.split(".")[0] for x in conectados ],interfaces)

        """ Obtenemos la informacion de cada dispositivo conectado """
        for dispositivo in conectados:

            child.sendline('sh cdp entry '+ dispositivo)
            child.expect(self.name+"#")
            info_dispositivo = child.before.decode().split()

            vecinos = {}
            for linea in range(0, len(info_dispositivo)):
                if 'address:' == info_dispositivo[linea]:
                    vecinos[str(info_dispositivo[linea+1])] =  dispositivo.split(".")[0]

        child.sendline('show ip arp')
        child.expect(self.name+"#")
        pcConectadas = child.before.decode().split("\n")
        pcConectadas = pcConectadas[2:]
        pcConectadas = [x.split()[1] for x in pcConectadas[0:-1] if x.split()[2]!= "-" and not x.split()[1] in vecinos.keys()]
        red.routers[self.name].pcConectadas =  pcConectadas
        for vecino in vecinos.keys():
            enrutador = Router(vecino, vecinos[vecino], self.user, self.password)
            enrutador.buscarVecinos(red)

    def configurarSNMP(self):
        mensaje = "Conectando a " + self.name
        logging.debug(mensaje)

        """ Nos conectamos al router """
        child = pexpect.spawn('telnet '+ self.ip)
        child.expect('Username: ')
        child.sendline(self.user)
        child.expect('Password: ')
        child.sendline(self.password)

        """ Configuramos el snmp"""
        child.expect(self.name+"#")
        child.sendline("snpm-server comunity | i snmp");
        child.expect(self.name+"#")
        child.sendline("snmp-server enable traps snmp linkdown linkup");
        child.expect(self.name+"#")
        child.sendline("snmp-server host 10.0.1.1 version 2c comun_pruebas");
        child.expect(self.name+"#")



    def getConnectedNetworks(self):
        child = pexpect.spawn('telnet '+ self.ip)
        child.expect('Username: ')
        child.sendline(self.user)
        child.expect('Password: ')
        child.sendline(self.password)
        child.expect(self.name+">")
        child.sendline('enable')
        child.expect('Password: ')
        child.sendline(self.enable)
        child.expect(self.name+"#")
        child.sendline("sh ip route c")
        child.expect(self.name+"#")
        sout = child.before.decode().split("\n")[1:-1]
        sout = [x.split(" ")[4:6] for x in sout if "" != x.split(" ")[4:6]]
        sout = [[z for z in x if "." in z ] for x in sout ]
        sout = [x[0] for x in sout  if len(x) > 0]
        ips = []
        for ip in sout:
            wildCard = str(IPv4Address(int(IPv4Address._make_netmask(ip.split("/")[1])[0])^(2**32-1)))
            idNet = str(ip.split("/")[0].split(".")[0])+"."+str(ip.split("/")[0].split(".")[1])+"."+str(ip.split("/")[0].split(".")[2])+"."+str((255-int(wildCard.split(".")[-1])))
            ips.append([idNet,wildCard])
        child.close()
        return ips

    def EIGRP(self):
        child = pexpect.spawn('telnet '+ self.ip)
        child.expect('Username: ')
        child.sendline(self.user)
        child.expect('Password: ')
        child.sendline(self.password)
        child.expect(self.name+'>')
        child.sendline('enable')
        child.expect('Password: ')
        child.sendline(self.enable)
        child.expect(self.name+'#')
        child.sendline("conf t")
        child.expect_exact(self.name+'(config)#')
        if not self.protocols["EIGRP"]["enable"]:
            child.sendline("no router eigrp 1")
            child.expect_exact(self.name+'(config)#')
            return
        child.sendline("router eigrp 1")
        child.expect_exact(self.name+'(config-router)#')
        child.sendline("address-family ipv4")
        child.expect_exact(self.name+'(config-router-af)#')
        for protocol in ["ospf 100","rip"]:
            child.sendline("do sh ip route "+protocol)
            child.expect_exact(self.name+"(config-router-af)#")
            line = child.before.decode().split("\n")[1]
            if len(line) > 3:
                child.sendline("redistribute "+protocol)
                child.expect_exact(self.name+'(config-router-af)#')
        networks = self.getConnectedNetworks()
        for network in networks:
            child.sendline("network "+network[0]+" "+network[1])
            child.expect_exact(self.name+'(config-router-af)#')
        child.sendline("end")
        child.expect(self.name+'#')
        child.close()
        return


    def RIP(self):
        child = pexpect.spawn('telnet '+ self.ip)
        child.expect('Username: ')
        child.sendline(self.user)
        child.expect('Password: ')
        child.sendline(self.password)
        child.expect(self.name+'>')
        child.sendline('enable')
        child.expect('Password: ')
        child.sendline(self.enable)
        child.expect(self.name+'#')
        child.sendline("conf t")
        child.expect_exact(self.name+'(config)#')
        if not self.protocols["RIP"]["enable"]:
            child.sendline("no router rip")
            child.expect_exact(self.name+'(config)#')
            return
        child.sendline("router rip")
        child.expect_exact(self.name+'(config-router)#')
        child.sendline("version 2")
        child.expect_exact(self.name+'(config-router)#')
        for protocol in ["ospf 100","eigrp 1"]:
            child.sendline("do sh ip route "+protocol)
            child.expect_exact(self.name+"(config-router)#")
            line = child.before.decode().split("\n")[1]
            if len(line) > 3:
                child.sendline("redistribute "+protocol)
                child.expect_exact(self.name+'(config-router)#')
        networks = self.getConnectedNetworks()
        for network in networks:
            child.sendline("network "+network[0])
            child.expect_exact(self.name+'(config-router)#')
        child.sendline("end")
        child.expect(self.name+'#')
        child.close()
        print("Rip Iniciado")
        return

    def OSPF(self):
        child = pexpect.spawn('telnet '+ self.ip)
        child.expect('Username: ')
        child.sendline(self.user)
        child.expect('Password: ')
        child.sendline(self.password)
        child.expect(self.name+'>')
        child.sendline('enable')
        child.expect('Password: ')
        child.sendline(self.enable)
        child.expect(self.name+'#')
        child.sendline('configure terminal')
        child.expect_exact(self.name+'(config)#')
        if not self.protocols["OSPF"]["enable"]:
            child.sendline("no router ospf 100")            
            child.expect_exact(self.name+'(config)#')
            return
        child.sendline('router ospf 100')
        child.expect_exact(self.name+'(config-router)#')
        for protocol in ["rip","eigrp 1"]:
            child.sendline("do sh ip route "+protocol)
            child.expect_exact(self.name+"(config-router)#")
            line = child.before.decode().split("\n")[1]
            if len(line) > 3:
                child.sendline("redistribute "+protocol+" metric 1 subnets")
                child.expect_exact(self.name+"(config-router)#")
        networks = self.getConnectedNetworks()
        print(networks)
        for network in networks:
            child.sendline("network "+network[0]+" "+network[1]+" area "+self.protocols["OSPF"]["area"])
            child.expect_exact(self.name+"(config-router)#")
        child.sendline("end")
        child.expect(self.name+"#")
        child.close()
        return

    def monitorear(self,intefaz, periodo):
        pass
