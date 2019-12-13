#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice, IceStorm
Ice.loadSlice('trawlnet.ice')
import TrawlNet

class OrchestratorI (TrawlNet.Orchestrator):
    downloader = None
    files = None
    orchestrators = []
    publisher = None
    orchestrator = None #

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
        print("Respuesta orchestrator: ", other)
            
        if other not in self.orchestrators:
            self.orchestrators.append(other)
           
        #canciones = other.getFileList()
        #canciones.append("HOLA")

        #for i in range(len(canciones)):
        #    print(canciones[i])

            #print(canciones)
            #self.files.update(canciones)
        '''
            print("HOLA")
            print(self.files)
            for fileHash in self.files.values():
                #fileInfo = TrawlNet.FileInfo()
                print("CACA")
                #fileInfo.hash = fileHash
                #fileInfo.name = other.files[fileHash]
                self.publisher.newFile(filoInfo)
        '''
    def getFileList(self, current = None):
        lista = []

        for fileHash in self.files:
            fileInfo = TrawlNet.FileInfo()
            fileInfo.hash = fileHash
            fileInfo.name = self.files[fileHash]
            lista.append(fileInfo)

        return lista

class OrchestratorEventI (TrawlNet.OrchestratorEvent):

    orchestrator = None
    proxy = None
    lista = None
    files = None
    publisher = None

    def hello(self, me, current = None):
        if me in self.lista:
            return
        print("Se ha registrado un nuevo orchestrator: ", me)
        self.lista.append(me)

        for fileHash in self.files:
                fileInfo = TrawlNet.FileInfo()
                print("estoy recopilando los fileInfo en el hello")
                fileInfo.hash = fileHash
                fileInfo.name = self.files[fileHash]
                self.publisher.newFile(fileInfo)

        # Mandamos la referencia al nuevo orquestador
        other = TrawlNet.OrchestratorPrx.uncheckedCast(self.proxy) 
        me.announce(other)

class UpdateEventI (TrawlNet.UpdateEvent):

    orchestrator = None

    def newFile(self, fileInfo, current = None):
        print("Nuevo evento registrado")
        if self.orchestrator:
            if fileInfo.hash not in self.orchestrator.files:
                self.orchestrator.files[fileInfo.hash] = fileInfo.name
            else:
                print("El archivo descargado ya estaba con anterioridad")


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
        sirviente.files = self.files
        sirviente.orchestrators = self.orchestrators
        sirviente.orchestrator = self #

        ### Interfaz del canal de eventos UpdateEvent
        sirvienteUpdate = UpdateEventI()
        sirvienteUpdate.orchestrator = self # El orchestrator soy "yo"

        ### Interfaz del canal de eventos del Orchestrator
        sirvienteOrchestrator = OrchestratorEventI()
        sirvienteOrchestrator.orchestrator = self
        sirvienteOrchestrator.lista = self.orchestrators #
        sirvienteOrchestrator.files = self.files #

        # Se obtiene el adaptador
        adaptador = broker.createObjectAdapter("OrchestratorAdapter")

        # Ahora con el adaptador, conseguimos los proxys necesarios
        proxyOrchestrator = adaptador.addWithUUID(sirviente) # Proxy del Orchestrator
        subscriberUpdateEvent = adaptador.addWithUUID(sirvienteUpdate) # Proxy del UpdateEvent
        publisherOrchestratorEvent = adaptador.addWithUUID(sirvienteOrchestrator) # Proxy del publicador del evento de orchestrator

        adaptador.activate()

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

        ################# CÓDIGO PUBLISHER UPDATE EVENT ####################
        topic_mgr_update_publisher = self.get_topic_manager()
        if not topic_mgr_update_publisher:
            print('Proxy invalido')
            return 2

        topic_name_update_publisher = "UpdateEvents"
        try:
            topic_update_publisher = topic_mgr_update_publisher.retrieve(topic_name_update_publisher)
        except IceStorm.NoSuchTopic:
            print("No such topic found, creating")
            topic_update_publisher = topic_mgr_update_publisher.create(topic_name_update_publisher)

        publisher_update_event = topic_update_publisher.getPublisher() # Se obtiene un publicador
        publisherUpdateEvent = TrawlNet.UpdateEventPrx.uncheckedCast(publisher_update_event)
        sirvienteOrchestrator.publisher = publisherUpdateEvent
        # El publisher de OrchestratorI sera publisherUpdateEvent, ya que luego invoca al método newFile.

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        topic_update.unsubscribe(subscriberUpdateEvent)
        topic_orchestrator.unsubscribe(publisherOrchestratorEvent)

        return 0

orchestrator = Orchestrator()
sys.exit(orchestrator.main(sys.argv))
