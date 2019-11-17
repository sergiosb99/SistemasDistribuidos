#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet


class Client(Ice.Application):
    def run(self,argv):
        try:
            proxy = self.communicator().stringToProxy(argv[1]) # se obtiene un objeto proxy
        except IndexError:
            print("No has indicado el proxy de un orchestrator valido")
            return 1
        try:
            link = argv[2]
        except IndexError:
            print("No has indicado un link de descarga valido")
            return 1

        orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy)
        # OrchestratorPrx -> para invocar los metodos de la interfaz, proxy a un obj remoto
        
        if not orchestrator:
            raise RuntimeError("Proxy invalido: %s" %argv[1])
        
        print("Link de descarga: %s" % link)
        archivo = orchestrator.downloadTask(url) # metodo del orquestador
        printf("Archivo descargado: %s" % archivo)        
        return 0

client = Client()
sys.exit(client.main(sys.argv))
