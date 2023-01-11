import pexpect
import getpass
import logging
import time

class Router:
    def __init__(self, ip, name, user="root", password="root",enable = ""):
        self.ip = ip
        self.name = name
        self.user = user
        self.password = password
        self.enable = enable
        self.interfaces = {}
        self.obtenerInterfaces()

    def buscarVecinos(self, red):
        if self.name in red.routers.keys(): # Si ya fue obtenido, no lo volvemos a obtener
            return
        if self.name not in red.routersCredentialsList.keys():
            red.routers[self.name] = {"ip": self.ip, "user": None, "password": None, "conectados": None, "interfaces": None}
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
       # child.expect(self.name+">")
        #child.sendline('enable')
        #child.expect('Password: ')
        #child.sendline(credenciales["enable"])
        child.expect(self.name+"#")
        child.sendline('show cdp ne | begin Device') # Obtenemos la tabla de dispositivos
        child.expect(self.name+"#")
        routersVecinos = child.before.decode().split("\r\n")
        routersVecinos = routersVecinos[2:]
        routersVecinos = [x for x in routersVecinos if x != '' ]
        conectados = [x.split()[0] for x in routersVecinos]
        interfaces = [str(x.split()[1])+str(x.split()[2]) for x in routersVecinos ]
        """ Registramos el router """
        red.routers[self.name] = {"ip": self.ip, "user": self.user, "password": self.password, "conectados": [x.split(".")[0] for x in conectados ], "interfaces": interfaces}
        red.routers[self.name]["interfacesActivas"] = self.interfaces
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
        red.routers[self.name]["pcConectadas"] =  pcConectadas
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



    def monitorear(self,intefaz, periodo):
        pass

    def obtenerInterfaces(self):
        mensaje = "Conectando a " + self.name
        logging.debug(mensaje)

        """ Nos conectamos al router """
        child = pexpect.spawn('telnet ' + self.ip)
        child.expect('Username: ')
        child.sendline(self.user)
        child.expect('Password: ')
        child.sendline(self.password)

        """ Configuramos el snmp"""
        child.expect(self.name + "#")
        child.sendline("show interfaces accounting");
        child.expect(self.name + "#")
        r = child.before

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
