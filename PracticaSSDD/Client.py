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
            print("The proxy is not valid.")
            return 1
        
        try:
            link = argv[2]
        except IndexError:
            link = None # No se va a realizar el proceso de descarga

        orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy) # Try Catch  
        if not orchestrator:
            raise RuntimeError("Invalid proxy: %s" %argv[1])
               
        if link:
            print("Download link: %s" % link)
            orchestrator.downloadTask(link)
            print("File downloaded successfully.")      
        else:
            lista = orchestrator.getFileList()
            if len(lista) == 0:
                print("No files available.")
            else:
                print("Available files:")
                for i in range(len(lista)):
                    print(lista[i])
                
        return 0

client = Client()
sys.exit(client.main(sys.argv))
