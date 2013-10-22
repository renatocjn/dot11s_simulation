#!/usr/bin/python
'''
	Usage:
	./make2dGraph.py <simulation> <Variating parameter 1> <list of values for variating parameter 1> <Variating parameter 2> <list of values for variating parameter 2>

	This script runs simulations and shows a 3d graph os the results
	the x-axis of the graph is the <Variating parameter 1> and it must be a parameter of the simulations
	the y-axis of the graph is the <Variating parameter 2> and it must be a parameter of the simulations
	the z-axis is a metric of what was run and must be in the file 'flow-statistics.txt'

	the list of values of each parameter must be enclosed in quotations and each value must be separedted by a space like '1 2 3' to make it easier for this script
'''
from os import curdir, pardir, chdir, walk
from os.path import isdir, join, isfile
from sys import argv, exit
from subprocess import call
from glob import glob
import pylab as pl
from numpy import array
import pylab as pl
from mpl_toolkits.mplot3d import Axes3D
from copy import deepcopy

if len(argv) != 6:
	print 'Usage:./make2dGraph.py <simulation> <Variating parameter 1> <list of values for variating parameter 1> <Variating parameter 2> <list of values for variating parameter 2>\n\tThe list of values of each parameter must be enclosed in quotations and each value must be separedted by a space like \'1 2 3\' to make it easier for this script'
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
	print 'Simulation Script not found'
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
wantedMetrics = ['deliveryRate', 'lostPackets', 'jitterSum', 'delay'] #these are the metrics that you want to make graphics of.
results = dict()
for m in wantedMetrics:
	results[m] = list()

'''
Acquiring the results of the simulations
'''
for m in wantedMetrics:
	for p1Val, p2Val in combinations:
		resultDir = directories[ (p1Val, p2Val) ]
		chdir( resultDir)
		flow_statistics = open('flow-statistics.txt', 'r').read().split() # get list of lines in the statistics file
		for m in wantedMetrics:
			metric = float([ line for line in flow_statistics if m in line and 'mean' in line ][0].split('=')[1]) #get line with the metric mean
			results[m].append( (p1Val, p2Val, metric) )
		chdir(pardir)
		chdir(pardir)

'''
	draw graphics of the simulations
'''
for m in wantedMetrics:
	pl.clf()
	fig = pl.figure()
	ax = fig.add_subplot(111, projection='3d')
	x, y, z = zip(*results[m])
	x = map(float, x)
	y = map(float, y)
	pl.title('%s vs %s vs %s' % (m, parameter1, parameter2))
	ax.set_xlabel(parameter1)
	ax.set_ylabel(parameter2)
	ax.set_zlabel(m)
	ax.plot_trisurf(x, y, z)
	pl.savefig('3d_%s_vs_%s_vs_%s.png' % (m, parameter1, parameter2))
	#pl.show()
