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
            print("Error, you have not indicated a proxy.")
            return 1
        except:
            print("Error, you have not indicated a valid proxy.")
            return 1
        
        try:
            link = argv[2]
        except IndexError:
            link = None # No se va a realizar el proceso de descarga

        try:
            orchestrator = TrawlNet.OrchestratorPrx.checkedCast(proxy)  
        except Ice.NoEndpointException:
            print("Error, the proxy is not valid.")
            return 1
        except Ice.ConnectionRefusedException:
            print("Error, you have entered a proxy not available.")
            return 1
               
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
