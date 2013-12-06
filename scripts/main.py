#!/usr/bin/python

from os import *
from os.path import *
from multiprocessing import Pool
from subprocess import call
from sys import exit
import argparse
from shutil import rmtree, move
from glob import glob
from time import sleep
from random import random

DEFAULT_NUMBER_OF_RUNS = 1

parser = argparse.ArgumentParser(description='This script runs the simulations a number of times for statistical porpoises and organizes the outputs. It will use multiple processors if available')

parser.add_argument('sim', metavar='Simulation', type=str,
                   help='simulation source code name without extension')

parser.add_argument('--force-run', '-f', dest='force', action='store_true',
					help='Makes this script overwrite previous runs, by default it will detect previous runs and skip running them')

parser.add_argument('num_runs', metavar='Number of runs', nargs='?', type=int, default=DEFAULT_NUMBER_OF_RUNS,
                   help='Number of times the simulation must be run, DEFAULT=%d' % DEFAULT_NUMBER_OF_RUNS)

parser.add_argument('sim_params', metavar='Others', type=str, nargs=argparse.REMAINDER,
					help='Arguments to be put in every run of the simulation')

if getcwd().endswith("scripts"): chdir('..')
if getcwd().endswith("dot11s_simulation"): chdir('..')

params = parser.parse_args()
params.sim_params.sort()

outDir = [params.sim] + params.sim_params
outDir = 'dot11s_simulation/results/'+''.join(outDir)

if isdir(outDir) and params.force:
	rmtree(outDir)
elif isdir(outDir):
	print "Already run this, skipping"
	exit(0)
mkdir(outDir)

subEnv = environ.copy()
subEnv['PATH'] = subEnv['PATH'] + ':' + getcwd()+'/dot11s_simulation/scripts'

def runTest(i):
	t = random()*10 + i%5
	sleep(t)
	global outDir
	global params
	global subEnv

	testDir = outDir+'/test-%d'%i

	mkdir(testDir)

	ns3_simulation_simulation_and_params = [params.sim] + params.sim_params
	ns3_simulation_simulation_and_params = ' '.join(ns3_simulation_simulation_and_params)

	call_list = ['./waf', '--cwd=%s'%testDir, '--run', ns3_simulation_simulation_and_params]
	call(call_list, env=subEnv)

	if len(glob(testDir+'/mp-report-*.xml'))==0:
		raise Exception('mesh point reports were not found!')

	mkdir(testDir+'/MeshHelperXmls')
	for report in glob(testDir+'/mp-report-*.xml'):
		move(report, testDir+'/MeshHelperXmls/'+report.split('/')[-1])

runners = Pool()
runs = range(1, params.num_runs+1)

print 'Starting the experiment'
call(['./waf', 'build'])
try:
	results = runners.map(runTest, runs)
	call(['./dot11s_simulation/scripts/node_statistics.py', outDir])
	call(['./dot11s_simulation/scripts/flow_statistics.py', outDir])
except Exception as e:
	print "Something went wrong with the experiment..."
	print e.message
