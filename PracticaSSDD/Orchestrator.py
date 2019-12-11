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
            try:
                print("Peticion de descarga: %s" %link)
                return self.downloader.addDownloadTask(link)
            except TrawlNet.DownloadError: 
                printf("Error al llevar a cabo la descarga")
                return 1

    def announce(self, other, current = None): ## no se como hacerlo
        pass

    def getFileList(): ## OJALA PUDIERA PROBARLO
        lista = []
        
        for fileHash in self.files:
            fileInfo = TrawlNet.FileInfo()
            fileInfo.hash = fileHash
            fileInfo.name = self.files[fileHash]
            lista.append(fileInfo)

        return lista

class OrchestratorEventI (TrawlNet.OrchestratorEvent):     
    #def __init__(self):        
    #    self.orchestrator = None
    #    self.lista
    #    self.anunciador = None
    #    self.proxy = None
    orchestrator = None
    anunciador = None
    proxy = None
    lista = None

    def hello(self, me, current = None):
        if me.ice_toString() in self.lista:
            return
        print("Se ha registrado un nuevo orchestrator: ", me)
        self.lista.append(me)
        # Mandamos la referencia al nuevo orquestador
        other = TrawlNet.OrchestratorPrx.uncheckedCast(self.proxy)
        self.anunciador.announce(other) # ¿checked en vez de unchecked?

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
        self.orchestrators = []

    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property %s not set" % key)
            return None
        
        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    
    def run(self, argv):
         
        broker = self.communicator()

        # Se obtiene el proxy del Downloader al que conectarse por parametros
        proxyDownloader = broker.stringToProxy(argv[1])
        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyDownloader)

        if not downloader:
            return ValueError("Proxy invalido: %s" %argv[1])
        
        ### Interfaz del orchestrator para realizar la descarga mp3
        sirviente = OrchestratorI()
        sirviente.downloader = downloader
        
        ### Interfaz del canal de eventos UpdateEvent
        sirvienteUpdate = UpdateEventI()
        sirvienteUpdate.orchestrator = self # El orchestrator soy "yo"
        
        ### Interfaz del canal de eventos del Orchestrator
        sirvienteOrchestrator = OrchestratorEventI()
        sirvienteOrchestrator.orchestrator = self # soy yo mismo ##### AQUÍ PODRIA ESTAR EL FALLO OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOJO
        sirvienteOrchestrator.lista = self.orchestrators
        sirvienteOrchestrator.anunciador = sirviente ##### DUDAS
        # Se obtiene el adaptador
        adaptador = broker.createObjectAdapter("OrchestratorAdapter")

        # Ahora con el adaptador, conseguimos los proxys necesarios
        proxyOrchestrator = adaptador.addWithUUID(sirviente) # Proxy del Orchestrator
        subscriberUpdateEvent = adaptador.addWithUUID(sirvienteUpdate) # Proxy del UpdateEvent
        publisherOrchestratorEvent = adaptador.addWithUUID(sirvienteOrchestrator) # Proxy del publicador del evento de orchestrator

        ######### NO ESTOY SEGURO DE ESTO
        sirvienteOrchestrator.proxy = proxyOrchestrator

        # Imprimos el proxy del orquestador, lo necesita el cliente por parametros
        print('Proxy orchestrator: %s' % proxyOrchestrator)
               
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

        topic_update.subscribeAndGetPublisher(qos_update,subscriberUpdateEvent)
        
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

        topic_orchestrator.subscribeAndGetPublisher(qos_orchestrator,publisherOrchestratorEvent) # REVISAR ULTIMA VARIABLE
        
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
        sirvienteOrchestrator.orchestrator = orchestratorEvent
        me = TrawlNet.OrchestratorPrx.uncheckedCast(proxyOrchestrator)
        orchestratorEvent.hello(me)
        ####################################################################

        adaptador.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        topic_update.unsubscribe(subscriberUpdateEvent)
        topic_orchestrator.unsubscribe(publisherOrchestratorEvent) # REVISAR VARIABLE

        return 0

orchestrator = Orchestrator()
sys.exit(orchestrator.main(sys.argv))
