import pexpect
import getpass
import logging
import time

class Router:
    def __init__(self, ip, name, user="root", password="root"):
        self.ip = ip
        self.name = name
        self.user = user
        self.password = password

    def buscarVecinos(self, routers = {}):
        if self.name in routers.keys(): # Si ya fue obtenido, no lo volvemos a obtener
            return

        print("Conectando a " + self.name)
        #logging.debug(mensaje)

        """ Nos conectamos al router """
        child = pexpect.spawn('telnet '+ self.ip)
        child.expect('Username: ')
        child.sendline(self.user)
        child.expect('Password: ')
        child.sendline(self.password)

        """Obtenemos la tabla de dispositivos conectados """
        child.expect(self.name+">")
        child.sendline('enable')
        child.expect('Password: ')
        child.sendline('password123')
        child.expect(self.name+"#")
        child.sendline('show cdp ne | begin Device') # Obtenemos la tabla de dispositivos
        child.expect(self.name+"#")
        routersVecinos = child.before.decode().split("\r\n")
        routersVecinos = routersVecinos[2:]
        routersVecinos = [x for x in routersVecinos if x != '' ]
        conectados = [x.split()[0] for x in routersVecinos]
        interfaces = [str(x.split()[1])+str(x.split()[2]) for x in routersVecinos ]
        """ Registramos el router """
        routers[self.name] = {"ip": self.ip, "user": self.user, "password": self.password, "conectados": [x.split(".")[0] for x in conectados ], "interfaces": interfaces} # Guardamos la info del dispositivo


        """ Obtenemos la informacion de cada dispositivo conectado """
        for dispositivo in conectados:
            # Obtenemos la info del dispositivo
            child.sendline('sh cdp entry '+ dispositivo)
            child.expect(self.name+"#")
            info_dispositivo = child.before.decode().split()

            # Obtenemos la ip del dispositivo
            vecinos = {}
            for linea in range(0, len(info_dispositivo)):
                if 'address:' == info_dispositivo[linea]:
                    vecinos[str(info_dispositivo[linea+1])] =  dispositivo.split(".")[0]

        child.sendline('show ip arp')
        child.expect(self.name+"#")
        pcConectadas = child.before.decode().split("\n")
        pcConectadas = pcConectadas[2:]
        pcConectadas = [x.split()[1] for x in pcConectadas[0:-1] if x.split()[2]!= "-" and not x.split()[1] in vecinos.keys()]
        routers[self.name]["pcConectadas"] =  pcConectadas
        for vecino in vecinos.keys():
            # Examinamos los routers vecinos
            enrutador = Router(vecino, vecinos[vecino], self.user, self.password)
            enrutador.buscarVecinos(routers)

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
