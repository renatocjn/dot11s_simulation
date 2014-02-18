#!/usr/bin/python

from os import curdir, pardir, chdir, walk, mkdir
from os.path import isdir, isfile
from sys import argv, exit
from subprocess import call
from glob import glob
import pylab as pl
from numpy import array
import argparse
from utils import clean_params

parser = argparse.ArgumentParser(description='This script runs simulations and shows a 2d graph of the results.\
								 The horizontal axis of the graph is the <Variating parameter> and it must be a parameter of the simulation.\
								 The vertical axis is a metric of what was run and must be in the file \'flow-statistics.txt\'.')

parser.add_argument('sim', metavar='Positioning', type=str,
                   help='Which position generator to use')

parser.add_argument('param', metavar='VariatingParameter', type=str,
                   help='parameter for the simulation')

parser.add_argument('vals', metavar='val', type=float, nargs='+',
                   help='values for the variation of parameter')

parser.add_argument('--force-run', '-f', dest='force', action='store_true',
					help='makes this script overwrite previous runs, by default it will detect previous runs and skip running them')

parser.add_argument('others', metavar='Other Parameters', type=str, nargs=argparse.REMAINDER,
					help='Arguments to be put in every run of the simulation')

params = parser.parse_args()

simulation = params.sim
parameter = params.param
parameterValues = clean_params(params.vals)
others = params.others
force = []
if params.force:
	force = ['-f']

'''
	Running the simulations
'''
mainScriptPath = curdir+'/scripts/main.py'
if not isfile(mainScriptPath):
	chdir(pardir)
if not isfile(mainScriptPath):
	print 'Simulation Script not found, make sure you are in the dot11s_simulation folder'
	exit(1)

directories = dict()
failed_runs = list()
for val in parameterValues:
	curr_param = '--%s=%s' % (parameter, val)
	call_list = [ mainScriptPath ] + force + [ simulation, curr_param ] + others
	exitCode = call( call_list )
	if exitCode is not 0:
			failed_runs.append(call_list)
	possibleDirs = [ directory for directory in glob('results/*') if all([ p in directory for p in [curr_param]+others ]) ]
	directories[val] = min(possibleDirs, key=lambda x: len(x))

if failed_runs:
	print 'The following simulations failed:'
	for failed_run in failed_runs: print failed_run
	exit(1)
'''
	Preparing data structure of the results
'''
metrics = dict()

wantedFlowMetrics = ['deliveryRate', 'lostPackets', 'jitterSum', 'delay', 'throughput'] #these are the metrics that you want to make graphics of.
for m in wantedFlowMetrics:
	metrics[m] = dict()

wantedNodeMetrics = ['totalPreq',
							'totalPrep',
							'totalPerr',
							'totalControlPkgs',
							'totalDropped',
							'connectionsDensity',
							'mostConnected',
							'lessConnected',
							'forwardedPreq',
							'initiatedProactivePreq',
							'dropped',
							'droppedTtl',
							'totalQueued'] #these are the metrics that you want to make graphics of.
for m in wantedNodeMetrics:
	metrics[m] = dict()

'''
Acquiring the results of the simulations
'''
for param_val in parameterValues:
	chdir(directories[param_val]) # move to directory of the run with the param equal to current param val
	flow_statistics = open('flow-statistics.txt', 'r').read().split() # get list of lines in the statistics file
	node_statistics = open('node-statistics.txt', 'r').read().split() # get list of lines in the statistics file
	for m in wantedFlowMetrics:
		mean = float([ line for line in flow_statistics if m in line and 'mean' in line ][0].split('=')[1]) #get line with the metric mean
		std = float([ line for line in flow_statistics if m in line and 'err' in line ][0].split('=')[1]) #get line with the metric std
		metrics[m][param_val] = mean, std
	for m in wantedNodeMetrics:
		mean = float([ line for line in node_statistics if m in line and 'mean' in line ][0].split('=')[1]) #get line with the metric mean
		std = float([ line for line in node_statistics if m in line and 'err' in line ][0].split('=')[1]) #get line with the metric std
		metrics[m][param_val] = mean, std
	chdir(pardir)
	chdir(pardir)

'''
	draw graphics of the simulations
'''
plot_dir = '2d_%s_%s' % (simulation, parameter)
if not isdir(plot_dir):
	mkdir(plot_dir)
for m in metrics.keys():
	pl.clf()
	t = list(metrics[m].viewitems())
	comparer = lambda x, y: cmp(float(x[0]),float(y[0]))
	t.sort(comparer)
	x, z = zip(*t)
	y, std = zip(*z)
	x, y = array(x), array(y)
	ypadding = y.mean()/2.0
	x = x.astype(float)
	xpadding = x.mean()/2
	pl.xlim(x.min()-xpadding, x.max()+xpadding)
	pl.ylim(y.min()-ypadding, y.max()+ypadding)
	pl.title('%s vs %s' % (m, parameter))
	pl.xlabel(parameter)
	pl.ylabel(m)
	pl.margins(0.05, 0.05)
	pl.errorbar(x, y, yerr=std, marker='o', color='black')
	pl.savefig(plot_dir+'/%s_vs_%s.png' % (m, parameter))

param_file = open(plot_dir + '/params.txt', 'w')
param_file.write( ' '.join(argv) )
param_file.write( '\n' )
param_file.close()
