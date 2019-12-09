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
    orchestrator = None
    def hello(self, me, current = None):
            if self.orchestrator:
                self.orchestrator.saludar(me) # Por pulir

class UpdateEventI (TrawlNet.UpdateEvent):   
    orchestrator = None
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
        
        ### Interfaz del orchestrator para realizar la descarga mp3
        self.sirviente = OrchestratorI()
        self.sirviente.downloader = self.downloader
        
        ### Interfaz del canal de eventos UpdateEvent
        self.sirvienteUpdate = UpdateEventI()
        self.sirvienteUpdate.orchestrator = self # El orchestrator soy "yo"
        
        # Se obtiene el adaptador
        self.adaptador = self.broker.createObjectAdapter("OrchestratorAdapter")

        # Ahora con el adaptador, conseguimos los proxys necesarios
        self.subscriberUpdateEvent = self.adaptador.addWithUUID(self.sirvienteUpdate) # Proxy del UpdateEvent
        self.proxyOrchestrator = self.adaptador.addWithUUID(self.sirviente) # Proxy del Orchestrator
        

        if not self.downloader:
            return ValueError("Proxy invalido: %s" %argv[1])
       
        # CODIGO SUBSCRIBER
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Proxy invalido')
            return 2

        topic_name = "UpdateEvents"
        qos = {}
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)

        topic.subscribeAndGetPublisher(qos,self.subscriberUpdateEvent)

        # Imprimos el proxy del orquestador, lo necesita el cliente por parametros
        print('Proxy orchestrator: %s' % self.proxyOrchestrator)

        self.adaptador.activate()
        self.shutdownOnInterrupt()
        self.broker.waitForShutdown()

        topic.unsubscribe(self.subscriberUpdateEvent) 

        return 0

orchestrator = Orchestrator()
sys.exit(orchestrator.main(sys.argv))
