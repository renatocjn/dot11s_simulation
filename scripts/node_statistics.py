#!/usr/bin/python

from os.path import isdir, join
from lxml import etree
from glob import glob
import os, sys, numpy, random, networkx as nx
from scikits.bootstrap import ci
from shutil import rmtree
import pylab as pl
from scipy.stats import norm
from math import sqrt
from utils import *

if len(sys.argv) == 2 and isdir(sys.argv[1]): #minimum parameter checking
	os.chdir(sys.argv[1])
else:
	print 'please pass the directory with the results as the first parameter'
	sys.exit(1)

_, directories, _ = os.walk(os.curdir).next() #get direcories of the current folder
numerical_sort(directories)

'''
	Acquiring the graph of links among the mesh points for each run
'''
for run_dir in directories:

	for pfile in glob(run_dir+'/positions.txt'):
		pfile_contents = open(pfile, 'r').read()
		ids, x_positions, y_positions = list(), list(), list()
		for line in pfile_contents.strip().split():
			i, x, y = line.split('|')
			ids.append(i)
			x_positions.append(x)
			y_positions.append(y)
		pl.clf()
		pl.scatter(x_positions, y_positions)
		for i, x, y in zip(ids, x_positions, y_positions):
			pl.annotate(str(i), xy = (x, y), xytext = (0, 0), textcoords = 'offset points')
		pl.savefig(run_dir+'/positions.png')

	os.chdir( join(run_dir, 'MeshHelperXmls') )
	link_graph = nx.MultiGraph() #the mesh points can have multiple links among mesh points

	report_files = glob('mp-report-*.xml')
	addressToNodeId = dict()
	for report in report_files:
		MeshPointDevice = etree.XML(open(report, 'r').read())
		interfaces = MeshPointDevice.findall('Interface')
		for i in interfaces:
			addressToNodeId[i.get('Address')] = filter(str.isdigit, report)

	numerical_sort(report_files)
	for report_file in report_files:
		xmlAsString = open(report_file,'r').read()
		xmlRootElement = etree.XML(xmlAsString)

		#this section is meant to populate the mapping interface/assigned channel for this mesh point
		interfaces = xmlRootElement.findall('Interface')
		channels = dict() # this dict is meant to map a mesh points interface to its assigned channel
		for i in interfaces:
			channels[i.get('Address')] = i.get('Channel')

		PeerManagementProtocolElement = xmlRootElement.find('PeerManagementProtocol')
		currMeshPointAddress = PeerManagementProtocolElement.find('PeerManagementProtocolMac').get('address')
		curr_id = filter(str.isdigit, report_file)
		link_graph.add_node(curr_id)
		for link in PeerManagementProtocolElement.findall('PeerLink'):
			peerId = addressToNodeId[link.get('peerMeshPointAddress')]
			m = channels[link.get('localAddress')]
			flag = False
			if link_graph.get_edge_data(curr_id, peerId) is not None:
				for d in link_graph.get_edge_data(curr_id, peerId).values():
					if d['label'] == m: flag = True
			if not flag:
				link_graph.add_edge(curr_id, peerId, label = m)

	os.chdir(join(os.pardir, os.pardir))
	if not isdir( join(run_dir, 'graphics') ):
		os.mkdir(join(run_dir, 'graphics'))
	nx.write_dot(link_graph, join(run_dir, 'graphics', 'peer_link_graph.dot'))

'''
	recovering values from the nodes xml files
'''
node_number = len(glob(join(directories[0], 'MeshHelperXmls', '*')))
per_run_values = [ dict() for i in range(node_number) ]

per_run_statistics = {'rxOpen', 'txOpen',
					  'rxBytes', 'txBytes',
					  'rxConfirm', 'txConfirm',
					  'rxClose', 'txClose',
					  'rxPerr', 'txPerr',
					  'rxPrep', 'txPrep',
					  'rxPreq', 'txPreq',
					  'initiatedPreq', 'initiatedPrep', 'initiatedPerr',
					  'dropped',
					  'droppedTtl',
					  'totalQueued',
					  'totalDropped'
					  }

per_simulation_values = dict()
per_simulation_statistics = {'totalPreq', # Sum of initiatedPreq
							 'totalPrep', # Sum of initiatedPrep
							 'totalPerr', # Sum of initiatedPerr
							 'totalDropped' # Sum of dropped
							 }

for k in per_simulation_statistics:
	per_simulation_values[k] = list()

for folder in directories:
	for k in per_simulation_statistics:
		per_simulation_values[k].append(0.0)

	os.chdir( join(folder, 'MeshHelperXmls') )
	for nodeXml in glob('mp-report-*.xml'):
		xmlRootElement = etree.XML( open(nodeXml,'r').read() )
		Id = int(filter(str.isdigit, nodeXml))

		n = xmlRootElement.find('Hwmp').find('HwmpProtocolMac').find('Statistics')
		for key in ['rxPerr', 'rxPrep', 'rxPreq', 'txPerr', 'txPrep', 'txPreq']:
			per_run_values[Id][key] = clean_result( n.get(key) )

		n = xmlRootElement.find('PeerManagementProtocol').find('PeerManagementProtocolMac').find('Statistics')
		for key in ['txOpen', 'txConfirm', 'txClose', 'rxOpen', 'rxConfirm', 'rxClose', 'dropped']:
			per_run_values[Id][key] = clean_result( n.get(key) )

		n = xmlRootElement.find('Hwmp').find('Statistics')
		for key in ['droppedTtl', 'totalQueued', 'totalDropped', 'initiatedPreq', 'initiatedPrep', 'initiatedPerr']:
			per_run_values[Id][key] = clean_result( n.get(key) )

		per_simulation_values['totalPerr'	][-1] += clean_result( n.get('initiatedPerr') )
		per_simulation_values['totalPrep'	][-1] += clean_result( n.get('initiatedPrep') )
		per_simulation_values['totalDropped'][-1] += clean_result( n.get('totalDropped') )
		per_simulation_values['totalPreq'	][-1] += clean_result( n.get('initiatedPreq') )

		n = xmlRootElement.find('Interface').find('Statistics')
		for key in ['txBytes', 'rxBytes']:
			per_run_values[Id][key] = clean_result( n.get(key) )

	'''
		Graphics for each run
	'''
	os.chdir(os.pardir)
	width = 0.5
	x = numpy.arange(node_number)
	labels = [ 'node_' + str(int(i)) for i in x ]
	if not isdir('graphics'):
		os.mkdir('graphics')
	os.chdir('graphics')
	for k in per_run_statistics:
		pl.clf()
		y = [ per_run_values[i][k] for i in range(node_number) ]
		pl.xlim(0, x[-1]+width*2)
		pl.ylim(ymin=0, ymax=(max(y)+0.1))
		pl.xticks(x + width, labels)
		pl.title(k)
		pl.bar(x + width/2.0, y, width=width)
		pl.savefig('%s_graph.png' % k)
	os.chdir(join(os.pardir, os.pardir))

'''
	Savin per simulation values to statistics file
'''
fp = open('node-statistics.txt', 'w')
for metric in per_simulation_statistics:
	mean, std = statistics(per_simulation_values[metric])
	fp.write('%s-mean=%f\n' % (metric, mean))
	fp.write('%s-err=%f\n' % (metric, std))
fp.close()
