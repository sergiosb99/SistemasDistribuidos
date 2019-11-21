#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
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

class Orchestrator (Ice.Application):
    def run(self, argv):
        
        broker = self.communicator()

        proxyDownloader = broker.stringToProxy(argv[1])
        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyDownloader)

        if not downloader:
            return ValueError("Proxy invalido: %s" %argv[1])

        adaptador = broker.createObjectAdapter("OrchestratorAdapter")
        sirviente = OrchestratorI()
        sirviente.downloader = downloader
        proxy = adaptador.addWithUUID(sirviente)
        print(proxy)
        sys.stdout.flush()
        adaptador.activate()
	
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

orchestrator = Orchestrator()
sys.exit(orchestrator.main(sys.argv))
