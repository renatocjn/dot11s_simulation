#!/usr/bin/python

from glob import glob
import networkx as nx
from lxml import etree
from sys import exit
from time import time
import os
reports = glob('mp-report-*.xml')

ids = dict()
for report in reports:
	aux = open(report).read()
	meshPointDevice = etree.XML(aux)
	curr_address = meshPointDevice.get('address')
	curr_id = int(filter(str.isdigit, report))
	ids[curr_address] = curr_id

G = nx.Graph()
for report in reports:
	aux = open(report).read()
	meshPointDevice = etree.XML(aux)
	currAddress = meshPointDevice.get('address')
	currId = ids[currAddress]
	G.add_node(currId)

	peerManagementProtocol = meshPointDevice.find('PeerManagementProtocol')
	links = peerManagementProtocol.findall('PeerLink')
	for link in links:
		peerAddress = link.get('peerMeshPointAddress')
		peerId = ids[peerAddress]
		G.add_edge(currId, peerId)
if not nx.is_connected(G):
	n = 'failed_%d' % int(time())
	os.mkdir(n)
	for rep in reports:
		os.rename(rep, n+'/'+rep);
	nx.write_dot(G, n+'/failed.dot')
	raise Exception("[check.py] invalid topology!")
