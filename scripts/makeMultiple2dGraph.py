#!/usr/bin/python
'''
	Usage:
	./make2dGraph.py <simulation> <Variating parameter1 for x axis> <list of values for variating parameter1> <Variating parameter2 for each plot> <list of values for variating parameter2>

	This script runs simulations and shows a graph with muiltiple2D plot of the results.
	The x-axis of the graphs is the <Variating parameter1> and it must be a parameter of the simulations.
	Each plot is run with variating parameter2.
	The z-axis is a metric of what was run and must be in the file 'flow-statistics.txt'.

	the list of values of each parameter must be enclosed in quotations and each value must be separedted by a space like '1 2 3' to make it easier for this script
'''
from os import curdir, pardir, chdir, walk, mkdir
from os.path import isdir, join, isfile
from sys import argv, exit
from subprocess import call
from glob import glob
import pylab as pl
from numpy import array
import pylab as pl
from mpl_toolkits.mplot3d import Axes3D
from copy import deepcopy
from random import shuffle

if len(argv) != 6:
	print 'Usage:./make2dGraph.py <simulation> <Variating parameter for x axis> <list of values for variating parameter> <Variating parameter for each plot> <list of values for variating parameter>\n\tThe list of values of each parameter must be enclosed in quotations and each value must be separedted by a space like \'v1 v2 v3\' to make it easier for this script\n\t'
	exit(1)

simulation = argv[1]

parameter1 = argv[2]
parameter1Values = argv[3].split()
if len(parameter1Values) < 2:
	print 'Error on the values of parameter1'
	exit(1)

parameter2 = argv[4]
parameter2Values = argv[5].split()
if len(parameter2Values) < 2:
	print 'Error on the values of parameter2'
	exit(1)

'''
	Running the simulations
'''
mainScriptPath = join(curdir, 'scripts', 'main.sh')
if not isfile(mainScriptPath):
	chdir(pardir)
if not isfile(mainScriptPath):
	print 'Main Script not found'
	exit(1)

combinations = [ (x, y) for x in parameter1Values for y in parameter2Values ]
directories = dict() #mapping of combination to the result directory of the run
for parameter1val, parameter2val in combinations:
		directoriesBeforeRun = set(glob(join('results','*')))
		print 'Running simulation %s with parameter %s equal to %s and parameter %s equal to %s' % (simulation, parameter1, parameter1val, parameter2, parameter2val)
		call( [ mainScriptPath, simulation, '--%s=%s' % (parameter1, parameter1val), '--%s=%s' % (parameter2, parameter2val) ] )
		directoriesAfterRun = set(glob(join('results','*')))
		directories[ (parameter1val,parameter2val) ] = (directoriesAfterRun-directoriesBeforeRun).pop() #this should return the new result directory created by the latest run

'''
	Preparing data structure of the results
'''
results = dict()

wantedFlowMetrics = ['deliveryRate', 'lostPackets', 'jitterSum', 'delay', 'throughput'] #these are the metrics that you want to make graphics of.
for m in wantedFlowMetrics:
	results[m] = list()

wantedNodeMetrics = ['totalDropped', 'totalPerr', 'totalPreq', 'totalPrep'] #these are the metrics that you want to make graphics of.
for m in wantedNodeMetrics:
	results[m] = list()

'''
Acquiring the results of the simulations
'''
for p1Val, p2Val in combinations:
	resultDir = directories[ (p1Val, p2Val) ]
	chdir( resultDir )
	flow_statistics = open('flow-statistics.txt', 'r').read().split() # get list of lines in the statistics file
	node_statistics = open('node-statistics.txt', 'r').read().split() # get list of lines in the statistics file
	for m in wantedFlowMetrics:
		metric_mean = float([ line for line in flow_statistics if m in line and 'mean' in line ][0].split('=')[1]) #get line with the metric mean
		metric_std = float([ line for line in flow_statistics if m in line and 'std' in line ][0].split('=')[1]) #get line with the metric mean
		results[m].append( (p1Val, p2Val, metric_mean, metric_std) )
	for m in wantedNodeMetrics:
		metric_mean = float([ line for line in node_statistics if m in line and 'mean' in line ][0].split('=')[1]) #get line with the metric mean
		metric_std = float([ line for line in node_statistics if m in line and 'std' in line ][0].split('=')[1]) #get line with the metric mean
		results[m].append( (p1Val, p2Val, metric_mean, metric_std) )
	chdir(pardir)
	chdir(pardir)

'''
	draw graphics of the simulations
'''
plot_dir = 'multiple2D_%s_%s_vs_%s' % (simulation, parameter1, parameter2)

lineFormats = '--', '-.', '-'
lineMarkers = '', 'o', 'd', 'v', 's'
formatStrings = [ y+x for y in lineMarkers for x in lineFormats ]
shuffle(formatStrings)

if not isdir(plot_dir):
	mkdir(plot_dir)
for m in results.keys():
	pl.clf()
	pl.xlabel(parameter1)
	pl.xticks(map(float,parameter1Values))
	pl.ylabel(m)

	maxy = -1
	i=0
	for plotv in parameter2Values:
		values = filter(lambda x: x[1]==plotv, results[m])
		x, _, y, std = zip(*values)

		if maxy < max(y):
			maxy = max(y)
		x = map(float, x)

		plot_label = '%s=%s'%(parameter2, plotv)
		curr_format = formatStrings[i]
		pl.errorbar(x, y, yerr=std, fmt=curr_format, label=plot_label)
		i = (i+1)%len(formatStrings)

	pl.margins(0.05, 0.05)
	pl.legend(loc='best')
	pl.savefig( join( plot_dir, 'm2d_%s_vs_%s_vs_%s.png' % (m, parameter1, parameter2) ) )
	#pl.show()
