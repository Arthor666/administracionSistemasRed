import threading
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv
from datetime import datetime


class TrapListener(threading.Thread):

    def __init__(self,target,community,interface):
        self.target = target
        self.community = community
        self.interface = interface
        self.eventDict = {}
        threading.Thread.__init__(self)



    def run(self):
        snmpEngine = engine.SnmpEngine()
        port=162;
        config.addTransport(snmpEngine,udp.domainName + (1,),udp.UdpTransport().openServerMode(("192.168.0.10", port)))
        #Configuracion de comunidad V1 y V2c
        config.addV1System(snmpEngine, 'snmp-trap-listener', self.community)
        ntfrcv.NotificationReceiver(snmpEngine,  self.saveEvent)
        snmpEngine.transportDispatcher.jobStarted(1)
        try:
            snmpEngine.transportDispatcher.runDispatcher()
        except:
            snmpEngine.transportDispatcher.closeDispatcher()
            raise



    def saveEvent(self,snmpEngine, stateReference, contextEngineId, contextName,varBinds, cbCtx):
        interfaceStr = varBinds[6][1].prettyPrint()
        trap = varBinds[-1][1].prettyPrint()
        print(interfaceStr)
        self.eventDict[str(datetime.now())] = trap
