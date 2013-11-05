#!/usr/bin/python

'''
	Usage:
		./make2dGraph.py <simulation> <Variating parameter> <list of values for variating parameter>

	This script runs simulations and shows a 2d graph of the results
	the horizontal axis of the graph is the <Variating parameter> and it must be a parameter of the simulations
	the vertical axis is a metric of what was run and must be in the file 'flow-statistics.txt'
'''
from os import curdir, pardir, chdir, walk, mkdir
from os.path import isdir, join, isfile
from sys import argv, exit
from subprocess import call
from glob import glob
import pylab as pl
from numpy import array
from copy import deepcopy

if len(argv) < 4:
	print 'Usage:\n\t./make2dGraph.py <simulation> <Variating parameter> <list of at least 2 values for \'variating parameter\'>'
	exit(1)

simulation = argv[1]
parameter = argv[2]
parameterValues = argv[3:]

'''
	Running the simulations
'''
mainScriptPath = join(curdir, 'scripts', 'main.sh')
if not isfile(mainScriptPath):
	chdir(pardir)
if not isfile(mainScriptPath):
	print 'Simulation Script not found'
	exit(1)

directories = dict()
for val in parameterValues:
	directoriesBeforeRun = set(glob(join('results','*')))
	print 'Running simulation %s with parameter %s equal to %s' % (simulation, parameter, val)
	call( [ mainScriptPath, simulation, '--%s=%s' % (parameter, val) ] )
	directoriesAfterRun = set(glob(join('results','*')))
	directories[val] = (directoriesAfterRun-directoriesBeforeRun).pop() #this should return the new result directorie created by the lattest run

'''
	Preparing data structure of the results
'''
metrics = dict()

wantedFlowMetrics = ['deliveryRate', 'lostPackets', 'jitterSum', 'delay', 'throughput'] #these are the metrics that you want to make graphics of.
for m in wantedFlowMetrics:
	metrics[m] = dict()

wantedNodeMetrics = ['totalDropped', 'totalPerr', 'totalPreq', 'totalPrep'] #these are the metrics that you want to make graphics of.
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
		std = float([ line for line in flow_statistics if m in line and 'std' in line ][0].split('=')[1]) #get line with the metric std
		metrics[m][param_val] = mean, std
	for m in wantedNodeMetrics:
		mean = float([ line for line in node_statistics if m in line and 'mean' in line ][0].split('=')[1]) #get line with the metric mean
		std = float([ line for line in node_statistics if m in line and 'std' in line ][0].split('=')[1]) #get line with the metric std
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
	pl.errorbar(x, y, yerr=std, marker='o')
	pl.savefig(join(plot_dir, '%s_vs_%s.png' % (m, parameter)))
