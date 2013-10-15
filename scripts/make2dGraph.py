#!/usr/bin/python

'''
	Usage:
		./make2dGraph.py <simulation> <Variating parameter> <list of values for variating parameter>

	This script runs simulations and show
	the horizontal axis of the graph is the <Variating parameter> and it must be a parameter of the simulations
	the vertical axis is a metric of what was run and must be in the file 'flow-statistics.txt'
'''
from os import curdir, pardir, chdir, walk
from os.path import isdir, join, isfile
from sys import argv, exit
from subprocess import call
from glob import glob
import pylab as pl
from numpy import array

if len(argv) < 4:
	print 'Usage:\n\t./make2dGraph.py <simulation> <Variating parameter> <list of at least 2 values for \'variating parameter\'>'

simulation = argv[1]
parameter = argv[2]
paramenterValues = argv[3:]

'''
	Running the simulations
'''
mainScriptPath = join(curdir, 'scripts', 'main.sh')
if not isfile(mainScriptPath):
	chdir(pardir)

directories = dict()
for val in paramenterValues:
	directoriesBeforeRun = set(glob(join('results','*')))
	print 'Running simulation %s with parameter %s equal to %s' % (simulation, parameter, val)
	call( [ mainScriptPath, simulation, '--%s=%s' % (parameter, val) ] )
	directoriesAfterRun = set(glob(join('results','*')))
	directories[val] = (directoriesAfterRun-directoriesBeforeRun).pop() #this should return the new result directorie created by the lattest run

'''
	Preparing data structure of the results
'''
wantedMetrics = ['deliveryRate', 'lostPackets', 'jitterSum', 'delay'] #these are the metrics that you want to make graphics of.
metrics = dict()
for m in wantedMetrics:
	metrics[m] = dict()

'''
Acquiring the results of the simulations
'''
for param_val in paramenterValues:
	chdir(directories[param_val]) # move to directory of the run with the param equal to current param val
	flow_statistics = open('flow-statistics.txt', 'r').read().split() # get list of lines in the statistics file
	for m in wantedMetrics:
		mean = float([ line for line in flow_statistics if m in line and 'mean' in line ][0].split('=')[1]) #get line with the metric mean
		std = float([ line for line in flow_statistics if m in line and 'std' in line ][0].split('=')[1]) #get line with the metric std
		metrics[m][param_val] = mean, std
	chdir(pardir)
	chdir(pardir)

'''
	draw graphics of the simulations
'''
for m in wantedMetrics:
	pl.clf()
	t = list(metrics[m].viewitems())
	comparer = lambda x, y: int(x[0])-int(y[0])
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
	pl.savefig('%s_vs_%s.png' % (m, parameter))
