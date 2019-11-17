#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet


class Client(Ice.Application):
    def run(self,args):
        ## FALTA CONTROL DE ERRORES
        proxy = self.communicator().stringToProxy(argv[1]) # se obtiene un objeto proxy
        ## FALTA CONTROL DE ERRORES
        link = args[2]

        orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy)
        # OrchestratorPrx -> para invocar los metodos de la interfaz printer, proxy a un obj remoto printer
        if not orchestrator:
            raise RuntimeError('Proxy invalido')
        
        print("Link de descarga: %s" % link)
        archivo = orchestrator.downloadTask(url) #metodo del orquestador
        printf("Archivo descargado: %s" % archivo)
        return 0

sys.exit(Client().main(sys.argv))
