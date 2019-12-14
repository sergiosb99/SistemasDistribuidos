#!/bin/sh
#

PYTHON=python3

DOWNLOADER_CONFIG=Downloader.config
ORCHESTRATOR_CONFIG=Orchestrator.config

PRX=$(tempfile)
$PYTHON Downloader.py --Ice.Config=$DOWNLOADER_CONFIG>$PRX &
PID=$!

# Dejamos arrancar al downloader
sleep 1
echo "Downloader's proxy: $(cat $PRX)"

# Lanzamos el orchestrator
$PYTHON Orchestrator.py --Ice.Config=$ORCHESTRATOR_CONFIG "$(cat $PRX)"

echo "Shoutting down..."
kill -KILL $PID
rm $PRX
