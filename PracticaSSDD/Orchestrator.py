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
                self.orchestrator.sayhello(me)

class UpdateEventI (TrawlNet.UpdateEvent):   

    n = 0

    def write(self, message, current=None):
        print("{0}: {1}".format(self.n, message))
        sys.stdout.flush()
        self.n += 1
        
    orchestrator = None
    def newFile(self, fileInfo, current = None):
        if self.orchestrator:
            if fileInfo.hash not in self.orchestrator.files:
                self.orchestrator.files[fileInfo.hash] = fileInfo.name

class Orchestrator (Ice.Application):
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print("property %s not set" % key)
            return None
        
        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    
    def run(self, argv):
        # PARTE CLIENTE 
        self.broker = self.communicator()
        self.proxyDownloader = self.broker.stringToProxy(argv[1])
        self.downloader = TrawlNet.DownloaderPrx.checkedCast(self.proxyDownloader)
        
        if not self.downloader:
            return ValueError("Proxy invalido: %s" %argv[1])
       
        # CODIGO SUBSCRIBER
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('Proxy invalido')
            return 2

        # PARTE SERVIDOR
        self.adaptador = self.broker.createObjectAdapter("OrchestratorAdapter")
        self.sirviente = OrchestratorI()
        self.sirviente.downloader = self.downloader
        self.subscriber = self.adaptador.addWithUUID(self.sirviente)
        #self.subscriber = self.adaptador.add(self.sirviente,self.broker.stringToIdentity("orchestrator1"))

        topic_name = "UpdateEvents"
        qos = {}
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)

        topic.subscribeAndGetPublisher(qos,self.subscriber)
        print('Waiting events... %s' % self.subscriber)

        self.adaptador.activate()
        self.shutdownOnInterrupt()
        self.broker.waitForShutdown()

        topic.unsubscribe(self.subscriber) 

        return 0

orchestrator = Orchestrator()
sys.exit(orchestrator.main(sys.argv))
