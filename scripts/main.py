#!/usr/bin/python

from os import mkdir, chdir, getcwd
from os.path import *
from multiprocessing import Pool, Value, Lock, Queue, Manager
from subprocess import call, Popen, PIPE
from sys import exit
import argparse
from shutil import rmtree, move
from glob import glob
from time import sleep, time
from random import randint, shuffle
from utils import check_run
import datetime
import dateutil.relativedelta

MAX_TOPOLOGIES = 10
DEFAULT_NUMBER_OF_RUNS = 30
MAX_SEED = 100000
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
topoCounter = Value('i', 0)
topologies_access_lock = Lock()
topologies_insertion_lock = Lock()
seedLock = Lock()

m = Manager()

seeds_set = set()
while len(seeds_set) < 10*params.num_runs + MAX_TOPOLOGIES:
	seeds_set.add( randint(0, MAX_SEED) )
seeds_list = list(seeds_set)
seeds_list = range(MAX_SEED)
shuffle(seeds_list)

topology_making_seeds = m.Queue()
for seed in seeds_list[-MAX_TOPOLOGIES:]:
	topology_making_seeds.put(seed)

seeds = m.Queue()
for seed in seeds_list[:-MAX_TOPOLOGIES]:
	seeds.put(seed)
topologies = m.Queue()

def gen_validTopology(not_used_param=None):
	global outDir, params, topology_making_seeds, MAX_TOPOLOGIES, topologies, topologies_insertion_lock, topoCounter
	seed = None
	with topologies_insertion_lock and topoCounter.get_lock():
		if topoCounter.value >= MAX_TOPOLOGIES:
			return False
		topoId = topoCounter.value + 1
		topoCounter.value += 1
		seed = topology_making_seeds.get()

	if not seed:
		return False

	topoDir = outDir+'/topoDir_%03d' % topoId
	mkdir(topoDir)

	topo_file = 'topology_%d.txt' % topoId
	ns3_simulation_simulation_and_params = [params.positioning, '--seed=%d'%seed, '--out-file=../'+topo_file ] + params.sim_params
	ns3_simulation_simulation_and_params = ' '.join(ns3_simulation_simulation_and_params)
	call_list = ['./waf', '--cwd=%s' % topoDir, '--run', ns3_simulation_simulation_and_params]
	outCode = call(call_list, stdout=PIPE, stderr=PIPE)

	if outCode is VALID_RUN:
		with topologies_insertion_lock:
			for i in range(6): topologies.put(topo_file)
		return True
	else:
		return gen_validTopology()

def runTest(i):
	print '[Thread %2d]'%i, 'Started'
	global outDir, params, doneCounter, topologies, seeds, seedLock, topologies_access_lock

	testDir = outDir+'/test-%d'%i
	mkdir(testDir)

	topo_file = None
	OK = False
	retries = 0
	t1 = None
	t2 = None
	while not OK:
		with seedLock: seed = seeds.get()
		print '[Thread %2d]'%i, 'Got seed', seed

		if topo_file is None or retries > 2:
			with topologies_access_lock:
				if topologies.empty():
					print '[Thread %2d]'%i, 'Making new topology'
					created = gen_validTopology()
					if not created:
						raise Exception("Limit exceeded for topology creation")
				topo_file = topologies.get()
			retries = 0
		print '[Thread %2d]'%i, 'Got topology', topo_file

		ns3_simulation_simulation_and_params = ['mesh_generic_runner', '--positions-file=../%s' % topo_file, '--seed=%d' % seed] + params.sim_params
		ns3_simulation_simulation_and_params = ' '.join(ns3_simulation_simulation_and_params)
		call_list = ['./waf', '--cwd=%s'%testDir, '--run', ns3_simulation_simulation_and_params]
		t1 = time()
		call(call_list, stderr=PIPE)
		t2 = time()

		OK = check_run(testDir)
		if not OK:
			print '[Thread %2d]'%i, 'Not ok, retry number', retries+1
			retries += 1

	mkdir(testDir+'/MeshHelperXmls')
	for report in glob(testDir+'/mp-report-*.xml'):
		move(report, testDir+'/MeshHelperXmls/'+report.split('/')[-1])

	fp = open(testDir + '/run_params.txt', 'w')
	fp.write(ns3_simulation_simulation_and_params)
	fp.close()

	dt1 = datetime.datetime.fromtimestamp(t1)
	dt2 = datetime.datetime.fromtimestamp(t2)
	rd = dateutil.relativedelta.relativedelta (dt2, dt1)
	with doneCounter.get_lock():
		print 'Finished run', doneCounter.value, 'out of', params.num_runs, 'runs / Duration: %d days, %d hours, %d minutes and %d seconds' % (rd.days, rd.hours, rd.minutes, rd.seconds)
		doneCounter.value += 1

runners = Pool(3)

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
	print 'Generating initial topologies'
	aux = runners.map(gen_validTopology, range(5))

	if not all(aux):
		raise Exception("Couldn't create initial topologies!")
	Ids = range(params.num_runs)

	print 'Running simulations with params:', params
	total_t1 = time()
	runners.map(runTest, Ids)
	total_t2 = time()

	print 'Running analisys'
	call(['./dot11s_simulation/scripts/node_statistics.py', outDir])
	call(['./dot11s_simulation/scripts/flow_statistics.py', outDir])

	total_dt1 = datetime.datetime.fromtimestamp(total_t1)
	total_dt2 = datetime.datetime.fromtimestamp(total_t2)
	total_rd = dateutil.relativedelta.relativedelta (total_dt2, total_dt1)
	print 'Experiment completed successfully / Total duration: %d days, %d hours, %d minutes and %d seconds' % (total_rd.days, total_rd.hours, total_rd.minutes, total_rd.seconds)
except BaseException as e:
	runners.terminate()
	print "Something went wrong with the experiment..."
	print "Message:", e.message
	#rmtree(outDir)
	exit(1)
