#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import os
import Ice
Ice.loadSlice('trawlnet.ice')
Ice.IPv6 = 0
Ice.IPv4 = 1
import TrawlNet

APP_DIRECTORY = './'
DOWNLOADS_DIRECTORY = os.path.join(APP_DIRECTORY, 'downloads')

"""
Clase cliente
"""
class Client(Ice.Application):

    """
    Metodo encargado del transfer request
    """
    def transfer_request(self, file_name):
        block_size = 1024
        transfer = None
        binascii = None

        try:
            transfer = self.orchestrator.getFile(file_name)
        except TrawlNet.TransferError as e:
            print(e.reason)
            return 1

        with open(os.path.join(DOWNLOADS_DIRECTORY, file_name), 'wb') as file_:
            remote_eof = False
            while not remote_eof:
                data = transfer.recv(block_size)
                if len(data) > 1:
                    data = data[1:]
                data = binascii.a2b_base64(data)
                remote_eof = len(data) < block_size
                if data:
                    file_.write(data)
            transfer.close()

        transfer.destroy()
        print('Transfer finished!')

    """
    Metodo que gestiona la linea de ordenes del cliente
    """
    def run(self, argv):
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
            if lista:
                print("Available files:")
                for i in enumerate(lista):
                    print(i)
            else:
                print("No files available.")               
        return 0

client = Client()
sys.exit(client.main(sys.argv))
