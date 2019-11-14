#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('trawlnet.ice')
import TrawlNet

class OrchestratorI (TrawlNet.Orchestrator):
    
    n = 0

    def downloadTask(self, message, current = None):
        print("{0}: {1}".format(self.n,message))
        sys.stdout.flush()
        self.n += 1

class Orchestrator (Ice.Application):
    def print(self, message):
        