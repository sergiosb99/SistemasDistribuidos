#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet


class Client(Ice.Application):
    def run(self,argv):
        try:
            proxy = self.communicator().stringToProxy(argv[1])
        except IndexError:
            print("No has indicado el proxy de un orchestrator valido")
            return 1
        try:
            link = argv[2]
        except IndexError:
            print("No has indicado un link de descarga valido, por tanto se procede al getFileList")
            link = None # No se va a realizar el proceso de descarga

        orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy)        
        if not orchestrator:
            raise RuntimeError("Proxy invalido: %s" %argv[1])
        
        print("Link de descarga: %s" % link)
        if link:
            orchestrator.downloadTask(link)
            print("Archivo descargado correctamente")      
        else:
            lista = orchestrator.getFileList() # Por pulir 
            print("Archivos disponibles:")
            for i in range(len(lista)):
                print(lista[i])
                
        return 0

client = Client()
sys.exit(client.main(sys.argv))
