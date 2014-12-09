#!/usr/bin/python

from glob import glob
from os import chdir, pardir, getcwd
from os.path import isfile
from pprint import pprint
from lxml import etree
from utils import *
from pylab import *
from sys import getsizeof
from scipy.ndimage.filters import maximum_filter, median_filter

def getCurrentDirTopologies():
	topologies = dict()
	topologies_files = glob('topology_*.txt')
	for f in topologies_files:
		topologies[f] = dict()
		fp = open(f)
		for line in fp:
			Id, x, y = line.strip().split("|")
			topologies[f][int(Id)] = float(x), float(y)
	return topologies
	
	
def getTopologyOfThisTestFolder():
	param_file = open('run_params.txt')
	params = param_file.next().strip().split(' ')
	topo_param = params[1]
	topo = topo_param.split('/')[1]
	return topo


def getThisTestNodesDeliveryRates():
	fp = open('FlowMonitorResults.xml')
	xmlString = fp.read()
	xmlRootElement = etree.XML(xmlString)
	
	deliveryRates = dict()
	
	flowIdToNode = dict()
	classifiedFlows = xmlRootElement.find('Ipv4FlowClassifier').findall('Flow')
	for flow in classifiedFlows:
		flowId = flow.get('flowId')
		source = flow.get('sourceAddress')
		sourceId = int(source.split('.')[-1]) - 1 # last int of the IP minus 1
		if sourceId == 50: sourceId=49
		flowIdToNode[flowId] = sourceId

	all_flows = xmlRootElement.find('FlowStats').findall('Flow')	
	for flow in all_flows: # get flow simulation values
		flowId = flow.get('flowId')
		rxBytes = clean_result(flow.get('rxBytes'))
		txBytes = clean_result(flow.get('txBytes'))
		deliveryRates[ flowIdToNode[flowId] ] = rxBytes / txBytes
	return deliveryRates

radius = 400
x = range(-radius, radius)
y = range(-radius, radius)

def makeDimension(pos, deliveryRates):
	global x, y, radius
	Z = np.zeros((2*radius, 2*radius))
	for i in deliveryRates.keys():
		if i == 50: i=49
		xi, yi = floor(pos[i])
		#text(xi, yi, i, horizontalalignment='center', verticalalignment='center')
		Z[x.index(xi),y.index(yi)] = deliveryRates[i]
	return Z

				#### MAIN ####
results_dir = "results/"
chdir(results_dir)
centered_disc_folders = glob('centered_disc*')
c1 = 0
t1 = len(centered_disc_folders)
finalcube = list()

if not isfile('finalcube.npy'):
	for folder in centered_disc_folders:
		c1 += 1
		print "scenarios:", c1, '/', t1
		chdir(folder)
	
		topologies = getCurrentDirTopologies()
		runFolders = glob('test-*')
		cube = list()
		for f in runFolders:
			chdir(f)
			
			t = getTopologyOfThisTestFolder()
			pos = topologies[t]
			deliveryRates = getThisTestNodesDeliveryRates()
			
			newDimension = makeDimension(pos, deliveryRates)
			cube.append(newDimension)
		
			chdir(pardir)
		scenario = array(cube)
		cube = zeros((2*radius, 2*radius))
		for i in xrange(2*radius):
			for j in xrange(2*radius):
				values = scenario[:,i,j]
				if sum(values > 0) > 1:
					cube[i,j] = values.mean()
				else:
					cube[i,j] = values.max()
		finalcube.append(cube)
		chdir(pardir)
	np.save('finalcube.npy', finalcube)
else:
	print 'loading full matrix'
	finalcube = np.load('finalcube.npy')

mean_cube = zeros((2*radius, 2*radius))
for i in xrange(2*radius):
	for j in xrange(2*radius):
		values = finalcube[:,i,j]
		if sum(values > 0) > 1:
			mean_cube[i,j] = values.mean()
		else:
			mean_cube[i,j] = values.max()

X, Y = np.meshgrid(x, y, indexing='ij')
cmap = 'jet'
s = 15

subplot(211)
Z = maximum_filter(mean_cube, size=s, mode='constant')
title('Raw')
contourf(X, Y, Z, cmap=cmap)
colorbar()

subplot(212)
Z1 = median_filter(Z, size=s, mode='constant')
title('smoothed')
contourf(X, Y, Z1, cmap=cmap)
colorbar()

show()
