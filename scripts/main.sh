#!/bin/bash
# Script for running and organizing results of simulations
# Author: Renato Caminha J. Neto
# started: Tuesday, September 03, 2013
# usage: $main.sh <sim_code> <params_1>...<params_N>
# <sim_code> is the path (without the type extention) to the source code of the ns3 simulation and the
# <params_i> are the parameters for the simulation and are defined in the simulation source code

NumOfRuns=10 #number of runs for the simulation

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
	read -p 'It seams this test has already been run, do you want to run it anyway? [y/N]' answer
	answer=${answer:-n}
	if [ y = $answer ]; then
		rm -Rf $ResultDir
	else
		echo 'okay, exiting...'
		exit
	fi
fi

mkdir -p $ResultDir

for i in $(seq $NumOfRuns); do
	echo -e "\033[36;40mRunning test number $i of $NumOfRuns\033[0m" #these numbers are the color marking for cyan(36) letters and black(40) background
	mkdir -p $ResultDir/test_$i/pcaps
	mkdir $ResultDir/test_$i/MeshHelperXmls #folders for organization of results
	./waf --run "$SimScript --pcap=1 $@"
	mv *.pcap $ResultDir/test_$i/pcaps
	mv mp-report-*.xml $ResultDir/test_$i/MeshHelperXmls
	mv FlowMonitorResults.xml $ResultDir/test_$i
done

cd $ReturnDir
