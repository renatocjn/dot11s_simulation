#!/usr/bin/python

from os import curdir, pardir, chdir, walk, mkdir
from os.path import isdir, isfile
from sys import argv, exit
from subprocess import call
from glob import glob
import pylab as pl
from numpy import array
import pylab as pl
from mpl_toolkits.mplot3d import Axes3D
import argparse

parser = argparse.ArgumentParser(description='This script runs simulations and saves 3d graphs of the results.\
	The x-axis of the graph is the <Variating parameter 1> and it must be a parameter of the simulation.\
	The y-axis of the graph is the <Variating parameter 2> and it must be a parameter of the simulation.\
	The z-axis is a metric of what was run and must be in the file \'flow-statistics.txt\'.')


parser.add_argument('sim', metavar='Simulation', type=str,
                   help='simulation source code')

parser.add_argument('param1', metavar='Parameter1', type=str,
                   help='parameter for x axis of the graph')

parser.add_argument('vals1', metavar='ValuesForParameter1', type=str,
                   help='values for the variation of parameter 1, must be a list surrounded by quotes, i.e. \'v1 v2 v3 ...\'')

parser.add_argument('param2', metavar='Parameter2', type=str,
                   help='parameter for the y axis of the graph')

parser.add_argument('vals2', metavar='ValuesForParameter2', type=str,
                   help='values for the variation of parameter 2, must be a list surrounded by quotes, i.e. \'v1 v2 v3 ...\'')

parser.add_argument('--force-run', '-f', dest='force', action='store_true',
					help='makes this script overwrite previous runs, by default it will detect previous runs and skip running them')

parser.add_argument('others', metavar='Other Params', type=str, nargs=argparse.REMAINDER,
					help='Arguments to be put in every run of the simulation')

params = parser.parse_args()

simulation = params.sim

parameter1 = params.param1
parameter1Values = params.vals1.split()
if len(parameter1Values) < 2:
	print 'Weird number values for the parameter1 values'
	exit(1)

parameter2 = params.param2
parameter2Values = params.vals2.split()
if len(parameter2Values) < 2:
	print 'Weird number values for the parameter2 values'
	exit(1)

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
	print 'Simulation Script not found'
	exit(1)

combinations = [ (x, y) for x in parameter1Values for y in parameter2Values ]
directories = dict() #mapping of combination to the result directory of the run
for parameter1val, parameter2val in combinations:
		print 'Running simulation %s with parameter %s equal to %s and parameter %s equal to %s' % (simulation, parameter1, parameter1val, parameter2, parameter2val)
		curr_p1 = '--%s=%s' % (parameter1, parameter1val)
		curr_p2 = '--%s=%s' % (parameter2, parameter2val)
		exitCode = call( [ mainScriptPath ] + force + [ simulation, curr_p1, curr_p2 ] + others)
		if exitCode is not 0:
			print 'Something terribly wrong has happened, aborting...'
			exit(1)
		possibleDirs = [ directory for directory in glob('results/*') if all([ p in directory for p in [curr_p1, curr_p2]+others ]) ]
		directories[ (parameter1val, parameter2val) ] = min(possibleDirs, key=lambda x: len(x))

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
		metric = float([ line for line in flow_statistics if m in line and 'mean' in line ][0].split('=')[1]) #get line with the metric mean
		results[m].append( (p1Val, p2Val, metric) )
	for m in wantedNodeMetrics:
		metric = float([ line for line in node_statistics if m in line and 'mean' in line ][0].split('=')[1]) #get line with the metric mean
		results[m].append( (p1Val, p2Val, metric) )
	chdir(pardir)
	chdir(pardir)

'''
	draw graphics of the simulations
'''
plot_dir = '3d_%s_%s_vs_%s' % (simulation, parameter1, parameter2)
if not isdir(plot_dir):
	mkdir(plot_dir)
for m in results.keys():
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
	pl.savefig( plot_dir+'/3d_%s_vs_%s_vs_%s.png' % (m, parameter1, parameter2) )
	#pl.show()
