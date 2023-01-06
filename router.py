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
            print(routers)
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
        tabla_dispositivos = child.before.decode().split("\r\n")
        tabla_dispositivos = tabla_dispositivos[2:]
        tabla_dispositivos = [x for x in tabla_dispositivos if x != '' ]
        conectados = [x.split()[0] for x in tabla_dispositivos]
        interfaces = [str(x.split()[1])+str(x.split()[2]) for x in tabla_dispositivos ]
        """ Registramos el router """
        routers[self.name] = {"ip": self.ip, "user": self.user, "password": self.password, "conectados": [x.split(".")[0] for x in conectados ], "interfaces": interfaces} # Guardamos la info del dispositivo


        """ Obtenemos la informacion de cada dispositivo conectado """
        for dispositivo in conectados:
            # Obtenemos la info del dispositivo
            child.sendline('sh cdp entry '+ dispositivo)
            child.expect(self.name+"#")
            info_dispositivo = child.before.decode().split()

            # Obtenemos la ip del dispositivo
            ip = None
            for linea in range(0, len(info_dispositivo)):
                if 'address:' == info_dispositivo[linea]:
                    ip = info_dispositivo[linea+1]

            # Examinamos los routers vecinos
            enrutador = Router(str(ip), dispositivo.split(".")[0], self.user, self.password)
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
