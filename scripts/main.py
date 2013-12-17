#!/usr/bin/python

from os import *
from os.path import *
from multiprocessing import Pool, Value
from subprocess import call, Popen, PIPE
from sys import exit
import argparse
from shutil import rmtree, move
from glob import glob
from time import sleep
from random import randint

DEFAULT_NUMBER_OF_RUNS = 10
MAX_SEED = 10000
MAX_RETRIES = 3
VALID_RUN = 0
INVALID_RUN = 1

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

retryCounter = Value('i', 0)

def runTest(conf):
	i, seed = conf
	global outDir, params, retryCounter, MAX_RETRIES

	testDir = outDir+'/test-%d'%i
	mkdir(testDir)

	ns3_simulation_simulation_and_params = [params.sim] + ['--seed=%d' % seed] + params.sim_params
	ns3_simulation_simulation_and_params = ' '.join(ns3_simulation_simulation_and_params)

	call_list = ['./waf', '--cwd=%s'%testDir, '--run', ns3_simulation_simulation_and_params]
	ret = call(call_list)

	while( ret != VALID_RUN and retryCounter.value < MAX_RETRIES ):
		with retryCounter.get_lock(): retryCounter.value += 1
		ret = call(call_list)
	if retryCounter.value >= MAX_RETRIES:
		return False

	if len(glob(testDir+'/mp-report-*.xml'))==0:
		raise Exception('mesh point reports were not found!')

	mkdir(testDir+'/MeshHelperXmls')
	for report in glob(testDir+'/mp-report-*.xml'):
		move(report, testDir+'/MeshHelperXmls/'+report.split('/')[-1])

	return True

runners = Pool()

print 'Compiling the experiment'
builder = Popen(['./waf', 'build'], stderr=PIPE, stdout=PIPE)
ret = builder.wait()
if ret == 1:
	print 'Erros na compilacao:'
	print builder.stderr.read()
	exit(1)

try:
	seeds = set()
	while len(seeds) < params.num_runs:
		seeds.add( randint(0, MAX_SEED) )
	if isdir(outDir) and params.force:
		rmtree(outDir)
	elif isdir(outDir):
		print "Already run this, skipping"
		exit(0)
	mkdir(outDir)

	print 'Starting the experiment'
	results = runners.map(runTest, enumerate(seeds, 1))
	if not all(results) is True:
		raise Exception('Limit of retries exceeded!')
	call(['./dot11s_simulation/scripts/node_statistics.py', outDir])
	call(['./dot11s_simulation/scripts/flow_statistics.py', outDir])
except BaseException as e:
	runners.terminate()
	print "Something went wrong with the experiment..."
	print "Message:", e.message
	exit(1)
