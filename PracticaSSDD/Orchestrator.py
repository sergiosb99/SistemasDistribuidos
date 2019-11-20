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
            return self.downloader.addDownloadTask(link)

class Orchestrator (Ice.Application):
    def run(self, argv):
        
        broker = self.communicator()

        proxyDownloader = broker.stringToProxy(argv[1]) # Se obtiene un objeto proxy
        downloader = TrawlNet.DownloaderPrx.checkedCast(proxyDownloader)

        if not downloader:
            return ValueError("Proxy invalido: %s" %argv[1])

        adaptador = broker.createObjectAdapter("OrchestratorAdapter") # El adaptador requiere un endpoint, un host y un puerto, están en orchestrator.config
        sirviente = OrchestratorI()
        sirviente.downloader = downloader
        proxy = adaptador.addWithUUID(sirviente)
        print(proxy)
        sys.stdout.flush()

        adaptador.activate() # El adaptador se ejecuta en otro hilo
		
		#A partir de este momento el servidor escucha peticiones
	
        self.shutdownOnInterrupt() # Ctrl + C, fin de la aplicación (SIGQUIT)
        broker.waitForShutdown() # Bloquea el hilo principal hasta que el comunicador sea terminado

        return 0

orchestrator = Orchestrator()
sys.exit(orchestrator.main(sys.argv))
