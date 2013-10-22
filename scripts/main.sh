#!/bin/bash
# Script for running and organizing results of simulations
# Author: Renato Caminha J. Neto
# started: Tuesday, September 03, 2013
# usage: $main.sh <sim_code> <params_1>...<params_N>
# <sim_code> is the path (without the type extention) to the source code of the ns3 simulation and the
# <params_i> are the parameters for the simulation and are defined in the simulation source code

NumOfRuns=1 #number of runs for the simulation

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
for i in $(seq $NumOfRuns); do
	echo "Running test number $i of $NumOfRuns"
	mkdir -p $ResultDir/test_$i/pcaps		#folders for organization of results
	mkdir $ResultDir/test_$i/MeshHelperXmls
	echo "./build/dot11s_simulation/*$SimScript* --pcap=1 $@" | ./waf shell
	mv *.pcap $ResultDir/test_$i/pcaps
	mv mp-report-*.xml $ResultDir/test_$i/MeshHelperXmls
	mv FlowMonitorResults.xml $ResultDir/test_$i
done

cd $ReturnDir
./scripts/node_statistics.py $ResultDir
./scripts/flow_statistics.py $ResultDir
