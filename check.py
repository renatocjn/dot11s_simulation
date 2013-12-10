#!/usr/bin/python

from glob import glob
import networkx as nx
from lxml import etree
from sys import exit

reports = glob('mp-report-*.xml')
G = nx.Graph()
for report in reports:
	aux = open(report).read()
	meshPointDevice = etree.XML(aux)
	curr_address = meshPointDevice.get('address')
	G.add_node(curr_address)

	peerManagementProtocol = meshPointDevice.find('PeerManagementProtocol')
	links = peerManagementProtocol.findall('PeerLink')
	for link in links:
		peerAddress = link.get('peerMeshPointAddress')
		G.add_edge(curr_address, peerAddress)
if not nx.is_connected(G):
	raise Exception("[check.py] invalid topology!")
