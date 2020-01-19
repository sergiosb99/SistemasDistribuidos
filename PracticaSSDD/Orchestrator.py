#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice, IceStorm
Ice.loadSlice('trawlnet.ice')
Ice.IPv6 = 0
Ice.IPv4 = 1
import TrawlNet

class OrchestratorI(TrawlNet.Orchestrator):
  
    downloader = None
    transfer = None
    files = None
    orchestrators = []

    def downloadTask(self, link, current = None):
        if self.downloader is None:
            print("Failed to assign the download to any Downloader.")
            return 1
        else:
            try:
                print("Download request: %s" %link)
                proxyDownloader = self.downloader.create() 
                fichero = proxyDownloader.addDownloadTask(link)
                proxyDownloader.destroy()
                return fichero
            except TrawlNet.DownloadError:
                printf("Error downloading.")
                return 1

    def announce(self, other, current = None):
        print("I have received your greeting! I am:", other)
            
        if other not in self.orchestrators:
            self.orchestrators.append(other)
           
    def getFileList(self, current = None):
        fileList = []

        for fileHash in self.files:
            fileInfo = TrawlNet.FileInfo()
            fileInfo.hash = fileHash
            fileInfo.name = self.files[fileHash]
            fileList.append(fileInfo)

        return fileList

    def getFile(self, name, current = None):
        if self.transfer is None:
            print("Failed to assign the download to any Transfer.")
            return 1
        else:
            try:
                return self.transfer.create()
            except:
                print("Error.")
                return 1

class OrchestratorEventI(TrawlNet.OrchestratorEvent):

    proxy = None
    orchestrators = None
    files = None
    publisher = None

    def hello(self, me, current = None):
        if me in self.orchestrators:
            return
        print("Hello! My proxy is:", me)
        self.orchestrators.append(me)

        for fileHash in self.files:
                fileInfo = TrawlNet.FileInfo()
                fileInfo.hash = fileHash
                fileInfo.name = self.files[fileHash]
                self.publisher.newFile(fileInfo)

        other = TrawlNet.OrchestratorPrx.uncheckedCast(self.proxy) 
        me.announce(other)

class UpdateEventI(TrawlNet.UpdateEvent):

    orchestrator = None

    def newFile(self, fileInfo, current = None):
        if self.orchestrator:
            if fileInfo.hash not in self.orchestrator.files:
                self.orchestrator.files[fileInfo.hash] = fileInfo.name

class Orchestrator(Ice.Application):

    def __init__(self):
        self.files = {}
        self.orchestrators = []

    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property %s not set" % key)
            return None

        return IceStorm.TopicManagerPrx.checkedCast(proxy)

    def run(self, argv):

        broker = self.communicator()
        try:
            proxyDownloader = broker.stringToProxy(argv[1])
            print(proxyDownloader)
        except IndexError:
            print("Error, you have not indicated a proxy.")
            return 1
        except:
            print("Error, you have not indicated a valid proxy.")
            return 1

        try:
            downloader = TrawlNet.DownloaderFactoryPrx.checkedCast(proxyDownloader)
            print(downloader)
        except Ice.NoEndpointException:
            print("Error, the proxy is not valid.")
            return 1

        ### Interfaz del orchestrator para realizar la descarga mp3
        servant = OrchestratorI()
        servant.downloader = downloader
        servant.files = self.files
        servant.orchestrators = self.orchestrators

        ### Interfaz del canal de eventos UpdateEvent
        servantUpdate = UpdateEventI()
        servantUpdate.orchestrator = self 

        ### Interfaz del canal de eventos del Orchestrator
        servantOrchestrator = OrchestratorEventI()
        servantOrchestrator.orchestrators = self.orchestrators
        servantOrchestrator.files = self.files

        # Se obtiene el adaptador
        adapter = broker.createObjectAdapter("OrchestratorAdapter")

        # Ahora con el adaptador, conseguimos los proxys necesarios
        proxyOrchestrator = adapter.addWithUUID(servant)
        proxyUpdateEvent = adapter.addWithUUID(servantUpdate)
        proxyOrchestratorEvent = adapter.addWithUUID(servantOrchestrator)

        adapter.activate()

        servantOrchestrator.proxy = proxyOrchestrator

        # Imprimos el proxy del orquestador, lo necesita el cliente por parametros
        print('Orchestrator\'s proxy: %s' % proxyOrchestrator)

        ########################### SUBSCRIBER UPDATE EVENT ###########################
        # Cuando se descargue un archivo, este canal notifica a todos los orchestrators
        
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Invalid proxy')
            return 2

        topic_update_event = "UpdateEvents"
        qos_update = {}
        try:
            topic_update = topic_mgr.retrieve(topic_update_event)
        except IceStorm.NoSuchTopic:
            print("No such topic found, creating")
            topic_update = topic_mgr.create(topic_update_event)

        topic_update.subscribeAndGetPublisher(qos_update, proxyUpdateEvent)

        ###################### PUBLISHER UPDATE EVENT ################################
        # Se usa para sincronizar la lista de archivos de un orchestrator nuevo

        publisher_update_event = topic_update.getPublisher()
        publisherUpdateEvent = TrawlNet.UpdateEventPrx.uncheckedCast(publisher_update_event)
        servantOrchestrator.publisher = publisherUpdateEvent

        ####################### SUBSCRIBER ORCHESTRATOR EVENT ########################
        # Los orchestrators subscritos son informados de llegadas de nuevos

        topic_orchestrator_event = "OrchestratorSync"
        qos_orchestrator = {}
        try:
            topic_orchestrator = topic_mgr.retrieve(topic_orchestrator_event)
        except IceStorm.NoSuchTopic:
            topic_orchestrator = topic_mgr.create(topic_orchestrator_event)

        topic_orchestrator.subscribeAndGetPublisher(qos_orchestrator, proxyOrchestratorEvent)

        ####################### PUBLISHER ORCHESTRATOR EVENT #########################
        # Se notifica la llegada de un nuevo orchestrator

        publisher_event = topic_orchestrator.getPublisher()
        orchestrator_event = TrawlNet.OrchestratorEventPrx.uncheckedCast(publisher_event)
        servantOrchestrator.orchestrator = orchestrator_event
        me = TrawlNet.OrchestratorPrx.uncheckedCast(proxyOrchestrator)
        orchestrator_event.hello(me)

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        topic_update.unsubscribe(proxyUpdateEvent)
        topic_orchestrator.unsubscribe(proxyOrchestratorEvent)

        return 0

orchestrator = Orchestrator()
sys.exit(orchestrator.main(sys.argv))
