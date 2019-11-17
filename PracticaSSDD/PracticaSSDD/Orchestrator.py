#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet

class OrchestratorI (TrawlNet.Orchestrator):
    downloader = None
    def downloadTask(self, link, current = None):
        print("Solicitud de descarga: %s" %link)
        if self.downloader is not None:
            return self.downloader.addDownloadTask(url)

class Orchestrator (Ice.Application):
    def print(self, message):
        