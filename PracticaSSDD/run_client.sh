#!/bin/sh
#

PYTHON=python3

CLIENT_CONFIG=Orchestrator.config

$PYTHON Client.py --Ice.Config=$CLIENT_CONFIG "$1" "$2"
