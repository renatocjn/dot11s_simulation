#!/bin/sh
# Script for running and organizing results of simulations
# Author: Renato Caminha J. Neto
# started: Tuesday, September 03, 2013
# usage: $main.sh <sim_code> <params_1>...<params_N>
# <sim_code> is the path (without the type extention) to the source code of the ns3 simulation and the
# <params_i> are the parameters for the simulation and are defined in the simulation code

NumOfRuns=10 #number of runs for the simulation

ReturnDir=$(pwd) #directory to return to
if [ $(basename $ReturnDir) != 'dot11s_simulation' ]; then #just making sure we are on the right folder
	echo "Please run this from the 'dot11s_simulation' folder"
	echo "do something like '\$./scripts/$0' in the 'dot11s_simulation' folder"
	exit 1
fi
cd ..

#script variables
ResultDir=$ReturnDir/results/$(date +results_%s)	#root folder path of results
# WafScript=$ReturnDir/waf							#main waf script path to run simulation
SimScript=$1; shift									#simulation code path without the .cc extention

mkdir -p $ResultDir
echo "script: $SimScript, params: $@" > $ResultDir/command.txt #backup of the simulation params for later consulting
for i in $(seq $NumOfRuns); do
	echo "running test number $i of $NumOfRuns"
	mkdir -p $ResultDir/test_$i/pcaps
	mkdir $ResultDir/test_$i/MeshHelperXmls #folders for organization of results
	./waf --run "$SimScript --pcap=1 $@" 2> /dev/null
	mv *.pcap $ResultDir/test_$i/pcaps
	mv mp-report-*.xml $ResultDir/test_$i/MeshHelperXmls
	mv FlowMonitorResults.xml $ResultDir/test_$i
done

cd $ReturnDir
