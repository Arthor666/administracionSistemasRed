from pysnmp.hlapi import *
from pysnmp.entity.rfc3413.oneliner import cmdgen
import pysnmp
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv
from pysnmp.entity.rfc3413.oneliner import cmdgen
import threading
import time
import matplotlib.pyplot as plt
cmdGen = cmdgen.CommandGenerator()

class Hilo(threading.Thread):

    def __init__(self,ip,intervalo,interfaz):
        threading.Thread.__init__(self)
        self.ip = ip
        self.intervalo = intervalo
        self.interfaz = interfaz
        self.killed = False

    def kill(self):
        self.killed = True

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

    def run(self):
        oidIn= '1.3.6.1.2.1.2.2.1.10.'
        oidOut='1.3.6.1.2.1.2.2.1.16.'
        oidErroInr='1.3.6.1.2.1.2.2.1.14.'
        oidErrorOut='1.3.6.1.2.1.2.2.1.20.'

        opcion=''
        inter = int(self.intervalo)
        match self.interfaz:
            case '0/0':
                oidIn= '1.3.6.1.2.1.2.2.1.10.1'
                oidOut='1.3.6.1.2.1.2.2.1.16.1'
                oidErroInr='1.3.6.1.2.1.2.2.1.14.1'
                oidErrorOut='1.3.6.1.2.1.2.2.1.20.1'
            case '1/0':
                oidIn= '1.3.6.1.2.1.2.2.1.10.2'
                oidOut='1.3.6.1.2.1.2.2.1.16.2'
                oidErroInr='1.3.6.1.2.1.2.2.1.14.2'
                oidErrorOut='1.3.6.1.2.1.2.2.1.20.2'
            case '2/0':
                oidIn='1.3.6.1.2.1.2.2.1.10.3'
                oidOut='1.3.6.1.2.1.2.2.1.16.3'
                oidErroInr='1.3.6.1.2.1.2.2.1.14.3'
                oidErrorOut='1.3.6.1.2.1.2.2.1.20.3'
            case '3/0':
                oidIn='1.3.6.1.2.1.2.2.1.10.4'
                oidOut='1.3.6.1.2.1.2.2.1.16.4'
                oidErroInr='1.3.6.1.2.1.2.2.1.14.4'
                oidErrorOut='1.3.6.1.2.1.2.2.1.20.4'
            case _:                
                return None


        host = self.ip
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



        while not self.killed :#cont < int(intervalo):
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
            time.sleep(int(self.intervalo))

        print("Monitoreo Finalizado")
