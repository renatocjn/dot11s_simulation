#!/bin/bash
# Script for running and organizing results of simulations
# Author: Renato Caminha J. Neto
# started: Tuesday, September 03, 2013
# usage: $main.sh <sim_code> <params_1>...<params_N>
# <sim_code> is the path (without the type extention) to the source code of the ns3 simulation and the
# <params_i> are the parameters for the simulation and are defined in the simulation source code

NumOfRuns=50 #number of runs for the simulation
minimumNumberOfNeighbors=3

ReturnDir=$(pwd) #directory to return to
if [ $(basename $ReturnDir) != 'dot11s_simulation' ]; then #just making sure we are on the right folder
	echo "Please run this from the 'dot11s_simulation' folder"
	echo "do something like '\$./scripts/$0' in the 'dot11s_simulation' folder"
	exit 1
fi
cd ..

name=''
for i in $@; do
	name=$name$i
done

#script variables
ResultDir=$ReturnDir/results/results_$name			#root folder path of results
SimScript=$1; shift									#simulation code path without the .cc extention

if [ -d $ResultDir ]; then
	read -p 'It seems this test has already been run, do you want to run it anyway? [y/N]' answer
	answer=${answer:-n}
	if [ y = $answer ]; then
		rm -Rf $ResultDir
	else
		echo 'okay, exiting...'
		exit
	fi
fi

mkdir -p $ResultDir

./waf build >/dev/null
i=1
while [ $i -le $NumOfRuns ]; do
	echo "Running test number $i of $NumOfRuns"
	echo "./build/dot11s_simulation/*$SimScript* $@" | ./waf shell

	notEnough=0 #false
	for report in mp-report-*; do
		numOfNeighbors=$(cat $report|grep 'peerMeshPointAddress'|sort|uniq|wc -l)
		if [ $numOfNeighbors -lt $minimumNumberOfNeighbors ]; then
			notEnough=1 #true
			break
		fi
	done

	if [ $notEnough -eq 0 ]; then
		mkdir -p $ResultDir/test_$i/MeshHelperXmls
		mv mp-report-*.xml $ResultDir/test_$i/MeshHelperXmls
		mv FlowMonitorResults.xml $ResultDir/test_$i

		i=$(($i+1))
	else
		echo 'Some node didnt have enought PeerLinks, trying again...'
	fi
done

cd $ReturnDir
./scripts/node_statistics.py $ResultDir
./scripts/flow_statistics.py $ResultDir
