#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet


class Client(Ice.Application):
    def run(self,argv):
        proxy = self.communicator().stringToProxy(argv[1]) # Se obtiene un objeto proxy
        orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy)
        # OrchestratorPrx -> Para invocar los metodos de la interfaz Printer, proxy a un obj remoto Printer
        if not orchestrator:
            raise RuntimeError('Proxy invalido')

        orchestrator.downloadTask(argv[2]) #metodo del orquestador
        
        return 0


sys.exit(Client().main(sys.argv))
