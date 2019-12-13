#!/bin/sh
#

rm -rf IceStorm/
mkdir -p IceStorm/

echo "Running IceBox, press Ctrl + C to end"
icebox --Ice.Config=icebox.config
