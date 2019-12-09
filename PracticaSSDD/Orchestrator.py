#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice, IceStorm
Ice.loadSlice('trawlnet.ice')
import TrawlNet

class OrchestratorI (TrawlNet.Orchestrator):
    downloader = None
    def downloadTask(self, link, current = None):
        if self.downloader is None:
            print("No se conseguido asignar la descarga a un downloader")
            return 1
        else:
            print("Peticion de descarga: %s" %link)
            return self.downloader.addDownloadTask(link)

    def announce(self, other, current = None): 
        pass

    def getFileList():
        pass

class OrchestratorEventI (TrawlNet.OrchestratorEvent):
    
    def __init__(self):
        self.publisher = None

    def hello(self, me, current = None):
            print("HE LLEGAO PAYO")
            #if self.publisher:
                #self.publisher.saludar(me) # Por pulir

class UpdateEventI (TrawlNet.UpdateEvent):   
    orchestrator = None # A lo mejor meterlo en un init
    def newFile(self, fileInfo, current = None):
        print("Nuevo evento registrado")
        if self.orchestrator:
            if fileInfo.hash not in self.orchestrator.files:
                self.orchestrator.files[fileInfo.hash] = fileInfo.name

class Orchestrator (Ice.Application):

    def __init__(self):
        self.files = {}
        self.orchestrator = {}

    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property %s not set" % key)
            return None
        
        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    
    def run(self, argv):
         
        self.broker = self.communicator()

        # Se obtiene el proxy del Downloader al que conectarse por parametros
        self.proxyDownloader = self.broker.stringToProxy(argv[1])
        self.downloader = TrawlNet.DownloaderPrx.checkedCast(self.proxyDownloader)

        if not self.downloader:
            return ValueError("Proxy invalido: %s" %argv[1])
        
        ### Interfaz del orchestrator para realizar la descarga mp3
        self.sirviente = OrchestratorI()
        self.sirviente.downloader = self.downloader
        
        ### Interfaz del canal de eventos UpdateEvent
        self.sirvienteUpdate = UpdateEventI()
        self.sirvienteUpdate.orchestrator = self # El orchestrator soy "yo"
        
        ### Interfaz del canal de eventos del Orchestrator
        self.sirvienteOrchestrator = OrchestratorEventI()
        self.sirvienteOrchestrator.orchestrator = self # soy yo mismo
        
        # Se obtiene el adaptador
        self.adaptador = self.broker.createObjectAdapter("OrchestratorAdapter")

        # Ahora con el adaptador, conseguimos los proxys necesarios
        self.proxyOrchestrator = self.adaptador.addWithUUID(self.sirviente) # Proxy del Orchestrator
        self.subscriberUpdateEvent = self.adaptador.addWithUUID(self.sirvienteUpdate) # Proxy del UpdateEvent
        self.publisherOrchestratorEvent = self.adaptador.addWithUUID(self.sirvienteOrchestrator) # Proxy del publicador del evento de orchestrator
        ###### ¿HACE FALTA UN PROXY PARA EL SUBSCRIBER DEL EVENTOS DE ORQUESTADORES?

        # Imprimos el proxy del orquestador, lo necesita el cliente por parametros
        print('Proxy orchestrator: %s' % self.proxyOrchestrator)
               
        #################### SUBSCRIBER UPDATE EVENT ######################
        topic_mgr_update = self.get_topic_manager()
        if not topic_mgr_update:
            print('Proxy invalido')
            return 2

        topic_name_update = "UpdateEvents"
        qos_update = {}
        try:
            topic_update = topic_mgr_update.retrieve(topic_name_update)
        except IceStorm.NoSuchTopic:
            topic_update = topic_mgr_update.create(topic_name_update)

        topic_update.subscribeAndGetPublisher(qos_update,self.subscriberUpdateEvent)

        ################## PUBLISHER ORCHESTRATOR EVENT ###################
        topic_mgr_publisher = self.get_topic_manager()
        if not topic_mgr_publisher:
            print('Proxy invalido')
            return 2

        topic_name_publisher = "OrchestratorSync"
        try:
            topic_publisher = topic_mgr_publisher.retrieve(topic_name_publisher)
        except IceStorm.NoSuchTopic:
            print("No such topic found, creating")
            topic_publisher = topic_mgr_publisher.create(topic_name_publisher)

        publisher_event = topic_publisher.getPublisher()
        orchestratorEvent = TrawlNet.OrchestratorEventPrx.uncheckedCast(publisher_event)
        
        orchestratorEvent.hello(self.sirvienteOrchestrator.orchestrator) # CREO QUE SELF SOY YO
        #self.sirvienteOrchestrator.publisher = orchestratorEvent

        ################# SUBSCRIBER ORCHESTRATOR EVENT ###################
        topic_mgr_subscriber = self.get_topic_manager()
        if not topic_mgr_subscriber:
            print('Proxy invalido')
            return 2

        topic_name_orchestrator = "OrchestratorSync"
        qos_orchestrator = {}
        try:
            topic_orchestrator = topic_mgr_update.retrieve(topic_name_orchestrator)
        except IceStorm.NoSuchTopic:
            topic_orchestrator = topic_mgr_update.create(topic_name_orchestrator)

        topic_orchestrator.subscribeAndGetPublisher(qos_orchestrator,self.publisherOrchestratorEvent) # REVISAR ULTIMA VARIABLE

        ####################################################################

        self.adaptador.activate()
        self.shutdownOnInterrupt()
        self.broker.waitForShutdown()

        topic_update.unsubscribe(self.subscriberUpdateEvent)
        topic_orchestrator.unsubscribe(self.publisherOrchestratorEvent) # REVISAR VARIABLE

        return 0

orchestrator = Orchestrator()
sys.exit(orchestrator.main(sys.argv))
