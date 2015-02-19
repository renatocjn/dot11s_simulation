#!/usr/bin/python

from glob import glob
from os import chdir, pardir, getcwd
from os.path import isfile
from lxml import etree
from pylab import *
from scipy.ndimage.filters import maximum_filter, median_filter
from utils import *
from pprint import pprint

def getCurrentDirTopologies():
	topologies = dict()
	topologies_files = glob('topology_*.txt')
	for f in topologies_files:
		topologies[f] = dict()
		fp = open(f)
		for line in fp:
			Id, x, y = line.strip().split("|")
			topologies[f][int(Id)] = float(x), float(y)
		fp.close()
	return topologies
	
	
def getTopologyOfThisTestFolder():
	param_file = open('run_params.txt')
	params = param_file.next().strip().split(' ')
	topo_param = params[1]
	topo = topo_param.split('/')[1]
	param_file.close()
	return topo


def getThisTestNodesDeliveryRates():
	fp = open('FlowMonitorResults.xml')
	xmlString = fp.read()
	xmlRootElement = etree.XML(xmlString)
	
	deliveryRates = dict()
	
	flowIdToNode = dict()
	classifiedFlows = xmlRootElement.find('Ipv4FlowClassifier').findall('Flow')
	for flow in classifiedFlows:
		flowId = int(flow.get('flowId'))
		source = flow.get('sourceAddress')
		sourceId = int(source.split('.')[-1]) - 1 # last int of the IP minus 1
		#if sourceId == 50: sourceId=49
		flowIdToNode[flowId] = sourceId

	all_flows = xmlRootElement.find('FlowStats').findall('Flow')	
	for flow in all_flows: # get flow simulation values
		flowId = int(flow.get('flowId'))
		rxBytes = clean_result(flow.get('rxBytes'))
		txBytes = clean_result(flow.get('txBytes'))
		deliveryRates[ flowIdToNode[flowId] ] = rxBytes / txBytes
	
	del(all_flows)
	del(classifiedFlows)
	del(xmlRootElement)
	del(xmlString)
	fp.close()
	return deliveryRates

radius = 400
x = range(-radius, radius)
y = range(-radius, radius)

def makeDimension(pos, deliveryRates):
	global x, y, radius
	Z = np.zeros((len(x), len(x)))
	for i in deliveryRates.keys():
		xi, yi = floor(pos[i])
		Z[x.index(xi),y.index(yi)] = deliveryRates[i]
	return Z

				#### MAIN ####
results_dir = "results/"
chdir(results_dir)
#centered_disc_folders = glob('centered_grid*flows=40*')
centered_disc_folders = glob('centered_disc--flows=6*')
c1 = 0
t1 = len(centered_disc_folders)
finalcube = list()
problems = 0.0
total = 0.0

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
			#pprint(deliveryRates)
			#raw_input('press <enter>')
			total+=1		
			try:
				newDimension = makeDimension(pos, deliveryRates)
				cube.append(newDimension)
			except:
				problems+=1
				pass
		
			chdir(pardir)
		if not cube: 
			chdir(pardir)
			continue
		scenario = array(cube)
		cube = zeros(scenario[0].shape)
		for i in xrange(-radius, radius):
			for j in xrange(-radius, radius):
				values = scenario[:,i,j]
				if np.count_nonzero(values) > 1:
					cube[i,j] = values.mean()
				else:
					cube[i,j] = values.max()
		del(scenario)
		finalcube.append(cube)
		chdir(pardir)
	finalcube = array(finalcube)
	save('finalcube.npy', finalcube)
	print "errors: %.2f%%" % (100*problems/total)
else:
	finalcube = load('finalcube.npy')
	
mean_cube = zeros(finalcube[0].shape)
for i in x:
	for j in y:
		values = finalcube[:,i,j]
		if np.count_nonzero(values) > 1:
			mean_cube[i,j] = values.mean() * 100.0
		else:
			mean_cube[i,j] = values.max() * 100.0

X, Y = np.meshgrid(x, y, indexing='ij')
cmap = 'jet'
s = 100
l = np.linspace(0,100,100)
ticks = range(0, 101, 10)

xlim(-radius, radius)
ylim(-radius, radius)
Z = maximum_filter(mean_cube, size=s, mode='constant')
Z = median_filter(Z, size=50, mode='constant')
title('Taxa de entrega (%) em topologias em grade')
contourf(X, Y, Z, cmap=cmap, vmin=0.0, vmax=100.0, levels=l)
colorbar(ticks=ticks)

show()
