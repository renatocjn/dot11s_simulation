#!/bin/bash

if (( $# == 0 )); then
	echo "Error: Please input as parameter the result directories to run analises"
	exit 1
fi

echo "Starting analises"
while [[ ! -z $@ ]]; do
	~/ns-allinone-3.20/ns-3.20/dot11s_simulation/scripts/flow_statistics.py "$1"
	~/ns-allinone-3.20/ns-3.20/dot11s_simulation/scripts/node_statistics.py "$1"
	
	shift
	if (( $# == 0)); then
		echo 'Done! :D'
	else
		echo Finished one, $# to go
	fi
done

