#!/bin/bash

./Downloader.py --Ice.Config=Downloader.config > downloader-proxy.out &
PID=$!

sleep 1

./Orchestrator.py --Ice.Config=Orchestrator.config "$(head -1 downloader-proxy.out)"
kill -9 $PID
