#!/bin/bash
# Script for running and organizing results of simulations
# Author: Renato Caminha J. Neto
# started: Tuesday, September 03, 2013
# usage: $main.sh <sim_code> <params_1>...<params_N>
# <sim_code> is the name (without the type extention) of the source code of the ns3 simulation
# <params_i> are the parameters for the simulation and are defined in the simulation source code

SimScript=$1; shift
params=`echo $@|fmt -s -w 1|sort`

NumOfRuns=5 #number of runs for the simulation

ReturnDir=$(pwd) #directory to return to
if [ $(basename $ReturnDir) != 'dot11s_simulation' ]; then #just making sure we are on the right folder
	echo "Please run this from the 'dot11s_simulation' folder"
	echo "do something like '\$./scripts/$0' in the 'dot11s_simulation' folder"
	exit 1
fi
cd ..

name=$SimScript
for i in $params; do
	name=$name$i
done
ResultDir=$ReturnDir/results/$name

if [ -d $ResultDir ]; then
	echo "Already ran this..."
	ForceRun=${ForceRun:-n}
	if [ y = $ForceRun ]; then
		echo "Running again!"
		rm -Rf $ResultDir
	else
		echo "Skipping the run!"
		exit 0
	fi
fi

mkdir -p $ResultDir

rm -f *.mp-report*
rm -f FlowMonitorResults*

./waf build >/dev/null 2> /dev/null
for i in `seq 1 $NumOfRuns`; do
	echo "Running test number $i of $NumOfRuns"
	echo "./build/dot11s_simulation/*$SimScript* $@" | ./waf shell

	if [ ! -f FlowMonitorResults.xml ]; then
		echo "XMLs not generated, aborting.."
		rm -Rf $ResultDir
		exit 1
	fi

	mkdir -p $ResultDir/test_$i/MeshHelperXmls
	mv mp-report-*.xml $ResultDir/test_$i/MeshHelperXmls
	mv FlowMonitorResults.xml $ResultDir/test_$i
done

cd $ReturnDir
./scripts/node_statistics.py $ResultDir
./scripts/flow_statistics.py $ResultDir
