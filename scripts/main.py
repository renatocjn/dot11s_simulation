#!/usr/bin/python

from os import *
from os.path import *
from multiprocessing import Pool, Value, Array
from subprocess import call, Popen, PIPE
from sys import exit
import argparse
from shutil import rmtree, move
from glob import glob
from time import sleep
from random import randint

DEFAULT_NUMBER_OF_RUNS = 30
MAX_SEED = 10000
MAX_RETRIES = 1
VALID_RUN = 0
INVALID_RUN = 1

parser = argparse.ArgumentParser(description='This script runs the simulations a number of times for statistical porpoises and organizes the outputs. It will use multiple processors if available')

parser.add_argument('positioning', metavar='Positioning', type=str,
                   help='Indicates which positioning generator to use')

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

outDir = [params.positioning] + params.sim_params
outDir = 'dot11s_simulation/results/'+''.join(outDir)

doneCounter = Value('i', 1)

seeds = set()
while len(seeds) < params.num_runs+1:
	seeds.add( randint(0, MAX_SEED) )
seeds = list(seeds)

def runTest(conf):
	i, seed = conf
	global outDir, params, doneCounter

	testDir = outDir+'/test-%d'%i
	mkdir(testDir)

	ns3_simulation_simulation_and_params = ['mesh_generic_runner', '--positions-file=../topology_%d.txt' % (i%5), '--seed=%d' % seed] + params.sim_params
	ns3_simulation_simulation_and_params = ' '.join(ns3_simulation_simulation_and_params)
	call_list = ['./waf', '--cwd=%s'%testDir, '--run', ns3_simulation_simulation_and_params]
	call(call_list)

	if len(glob(testDir+'/mp-report-*.xml'))==0:
		raise Exception('mesh point reports were not found!')

	mkdir(testDir+'/MeshHelperXmls')
	for report in glob(testDir+'/mp-report-*.xml'):
		move(report, testDir+'/MeshHelperXmls/'+report.split('/')[-1])

	with doneCounter.get_lock():
		print 'Finished run', doneCounter.value, 'out of', params.num_runs, 'runs'
		doneCounter.value += 1

runners = Pool()

if isdir(outDir) and params.force:
		rmtree(outDir)
elif isdir(outDir):
	print "Already run this, skipping"
	exit(0)
mkdir(outDir)

print 'Compiling the experiment'
builder = Popen(['./waf', 'build'], stderr=PIPE, stdout=PIPE)
ret = builder.wait()
if ret == 1:
	print 'Errors during compilation:'
	print builder.stderr.read()
	exit(1)
try:
	print 'Generating topologies'

	topology_making_seed = seeds.pop()
	ns3_simulation_simulation_and_params = [params.positioning, '--seed=%d' % topology_making_seed] + params.sim_params
	ns3_simulation_simulation_and_params = ' '.join(ns3_simulation_simulation_and_params)
	call_list = ['./waf', '--cwd=%s' % outDir, '--run', ns3_simulation_simulation_and_params]
	topology_maker = Popen(call_list)
	ret = topology_maker.wait()
	if ret != 0:
		raise Exception("Couldn't create topologies!")

	print 'Running simulation with params:', params
	runners.map(runTest, enumerate(seeds, 1))

	print 'Running analisys'
	call(['./dot11s_simulation/scripts/node_statistics.py', outDir])
	call(['./dot11s_simulation/scripts/flow_statistics.py', outDir])
	print 'Experiment completed successfully'
except BaseException as e:
	rmtree(outDir)
	runners.terminate()
	print "Something went wrong with the experiment..."
	print "Message:", e.message
	exit(1)
