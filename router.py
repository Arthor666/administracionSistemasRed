import pexpect
import getpass
import logging
import time
from ipaddress import IPv4Address
import paramiko
from pysnmp.hlapi import *
from pysnmp.entity.rfc3413.oneliner import cmdgen
from netmiko import ConnectHandler


class Router:
    def __init__(self, ip, name, user="root", password="root",enable = "",protocols = {},conectados = None,interfaces = {},pcConectadas = {},usuariosSsh={}):
        self.ip = ip
        self.name = name
        self.user = user
        self.password = password
        self.enable = enable
        self.conectados = conectados
        self.interfaces = interfaces
        self.pcConectadas = pcConectadas
        self.protocols = protocols
        self.usuariosSsh = usuariosSsh
        if(self.password != None):
            self.obtenerInterfaces()
            self.obtenerProtocolosActivos()

    def obtenerProtocolosActivos(self):
        child = self.getChild()
        child.sendline('show ip protocols summary')
        child.expect(self.name+"#")
        protocols = child.before.decode().split("\n")[4:-1]
        protocols = [x.split()[1].upper() for x in protocols if x != []]
        for p in protocols:
            self.protocols[p] = {"enable": True}
        child.close()

    def getSsh(self):
        router = {
        'device_type': 'cisco_ios',
        'ip': self.ip,
        'username': self.user,
        'password': self.password,
        'secret': self.enable
        }

        device_conn = ConnectHandler(**router)
        device_conn.enable()
        return device_conn

    def obtenerUsuariosSsh(self):
        device_conn = self.getSsh()
        output = device_conn.send_command('show running-config | include user')
        UsersInLines = output.splitlines()
        users=[]
        for userLine in UsersInLines:
            #print(userLine)
            userDicAux={}
            userLineList= userLine.split()            
            userDicAux['username']=userLineList[1]
            userDicAux['privilage']=userLineList[3]
            userDicAux['password']=userLineList[4]
            users.append(userDicAux)
        self.usuariosSsh=users

        device_conn.disconnect()

    def CrearUsuarioSsh(self,user,password):
            print("Crea Usuario")
            device_conn = self.getSsh()
            config_commands =['username '+user+' privilege 15 password '+password]
            setConfig = device_conn.send_config_set(config_commands)
            #print('{}\n'.format(setConfig))
            device_conn.disconnect()




    def getChild(self):
        child = pexpect.spawn('telnet '+ self.ip)
        child.expect('Username: ')
        child.sendline(self.user)
        child.expect('Password: ')
        child.sendline(self.password)
        if(self.enable != ""):
            child.expect(self.name+">")
            child.sendline('enable')
            child.expect('Password: ')
            child.sendline(self.enable)
        child.expect(self.name+"#")
        return child

    def buscarVecinos(self, red,revisados):
        if self.name in revisados: # Si ya fue obtenido, no lo volvemos a obtener
            return
        credenciales = red.routersCredentialsList[self.name]
        #logging.debug(mensaje)

        """ Nos conectamos al router """
        child = self.getChild()
        child.sendline('show cdp ne | begin Device') # Obtenemos la tabla de dispositivos
        child.expect(self.name+"#")
        routersVecinos = child.before.decode().split("\r\n")
        routersVecinos = routersVecinos[2:]
        routersVecinos = [x for x in routersVecinos if x != '' ]
        conectados = [x.split()[0] for x in routersVecinos]
        interfaces = [str(x.split()[1])+str(x.split()[2]) for x in routersVecinos ]
        self.obtenerUsuariosSsh()
        """ Obtenemos la informacion de cada dispositivo conectado """
        red.routers[self.name].conectados = [x.split(".")[0] for x in conectados ]
        vecinos = {}
        for dispositivo in conectados:

            child.sendline('sh cdp entry '+ dispositivo)
            child.expect(self.name+"#")
            info_dispositivo = child.before.decode().split()

            for linea in range(0, len(info_dispositivo)):
                if 'address:' == info_dispositivo[linea]:
                    vecinos[str(info_dispositivo[linea+1])] =  dispositivo.split(".")[0]

        child.sendline('show ip arp')
        child.expect(self.name+"#")
        pcConectadas = child.before.decode().split("\n")
        pcConectadas = pcConectadas[2:]
        pcConectadas = [x.split()[1] for x in pcConectadas[0:-1] if x.split()[2]!= "-" and not x.split()[1] in vecinos.keys()]
        red.routers[self.name].pcConectadas =  pcConectadas
        revisados.append(self.name)
        for vecino in vecinos.keys():
            if vecinos[vecino] not in red.routersCredentialsList.keys():
                red.routers[vecinos[vecino]] = Router(vecino, vecinos[vecino],None,None,None,None,None)
                continue
            if vecinos[vecino] not in revisados:
                red.routers[vecinos[vecino]] = Router(vecino, vecinos[vecino],red.routersCredentialsList[vecinos[vecino]]["nombreU"],red.routersCredentialsList[vecinos[vecino]]["password"],red.routersCredentialsList[vecinos[vecino]]["enable"])
                red.routers[vecinos[vecino]].buscarVecinos(red,revisados)

    def configurarSNMP(self):
        mensaje = "Conectando a " + self.name
        logging.debug(mensaje)

        """ Nos conectamos al router """
        child = self.getChild()




        child.sendline("snmp-server community secreta ro 10");
        child.expect(self.name+"#")
        child.sendline("snmp-server host 192.168.0.10 secreta");
        child.expect(self.name+"#")
        child.sendline("snmp-server enable traps");
        child.expect(self.name+"#")




    def getConnectedNetworks(self):
        child = self.getChild()
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
        child = self.getChild()
        child.sendline("conf t")
        child.expect_exact(self.name+'(config)#')
        if not self.protocols["EIGRP"]["enable"]:
            if self.validateProtocols("EIGRP"):
                child.sendline("no router eigrp 1")
                child.expect_exact(self.name+'(config)#')
                child.close()
                return
            self.protocols["EIGRP"]["enable"] = True
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
        child = self.getChild()
        child.sendline("conf t")
        child.expect_exact(self.name+'(config)#')
        if not self.protocols["RIP"]["enable"]:
            if self.validateProtocols("RIP"):
                child.sendline("no router rip")
                child.expect_exact(self.name+'(config)#')
                child.close()
                return
            self.protocols["RIP"]["enable"] = True
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

    def validateProtocols(self,protocol):
        protocols = {"RIP","OSPF","EIGRP"}
        protocols.discard(protocol)
        for p in protocols:
            if(p in self.protocols):
                if(self.protocols[p]["enable"]):
                    return True
        return False

    def OSPF(self):
        child = self.getChild()
        child.sendline('configure terminal')
        child.expect_exact(self.name+'(config)#')
        if not self.protocols["OSPF"]["enable"]:
            if self.validateProtocols("OSPF"):
                child.sendline("no router ospf 100")
                child.expect_exact(self.name+'(config)#')
                child.close()
                return
            self.protocols["OSPF"]["enable"] = True
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
        for network in networks:
            child.sendline("network "+network[0]+" "+network[1]+" area "+self.protocols["OSPF"]["area"])
            child.expect_exact(self.name+"(config-router)#")
        child.sendline("end")
        child.expect(self.name+"#")
        child.close()
        return

    def monitorear(self,intefaz, periodo):
        pass



    def obtenerInterfaces(self):
        child = self.getChild()

        """ Configuramos el snmp"""
        child.sendline("show interfaces accounting");
        child.expect(self.name + "#")
        r = child.before
        child.close()

        r = str(r).replace('''b'show interfaces accounting''', '')
        r = str(r).split('FastEthernet')
        r.pop(0)
        l = []
        for x in r:
            n = x.split('\\r\\n')
            n.pop(1)
            l.append(n)
        nuevaLista = []
        for j in l:
            nuevaLista.append(j[0].strip())

        interfacess = {}
        for n in nuevaLista:
            estatus = {}
            if not (' is disabled' in n):
                 estatus.setdefault('status', True)
                 interfacess.setdefault(n, estatus)
        self.interfaces = interfacess
