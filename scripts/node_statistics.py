#!/usr/bin/python

from os.path import isdir, join
from lxml import etree
from glob import glob
import os, sys, numpy, random, networkx as nx
from scikits.bootstrap import ci
from shutil import rmtree

if len(sys.argv) != 1 and isdir(sys.argv[1]):
	os.chdir(sys.argv[1])
else:
	print 'please pass the directory with the results as the first parameter'
	sys.exit(1)

if isdir('graphics'):
	answer = raw_input('This has already been run, want to run anyway? [y,N]:')
	if answer == 'y' or answer == 'Y' or answer == 'Yes' or answer == 'yes':
		rmtree ('graphics')
	else:
		print 'exiting...'
		sys.exit()
os.mkdir('graphics')

def statistics(vals):
	vals = numpy.array(vals)
	return {'mean':vals.mean(), 'std':vals.std(), 'ci':list(ci( vals, numpy.average ))}

clean_result = lambda x: float( filter( lambda x: x.isdigit() or x=='.', x ) )
numerical_sort = lambda l: l.sort(lambda x,y: cmp( int(filter(lambda z:z.isdigit(), x)), int(filter(lambda z:z.isdigit(), y)) )) # numerical sort of list
id_from_mac = lambda address: int(filter(lambda x: x!=':', address), 16) - 1

_, directories, _ = os.walk(os.curdir).next()
directories.remove('graphics')
numerical_sort(directories)


'''
	Writing the graph of links among the mesh points.
'''
os.chdir(join(random.choice(directories),'MeshHelperXmls'))
link_graph = nx.DiGraph()
report_files = glob('mp-report-*.xml')
numerical_sort(report_files)
for report_file in report_files:
	r = etree.XML(open(report_file,'r').read())
	emp = r.find('PeerManagementProtocol')
	curr_id = id_from_mac(emp.find('PeerManagementProtocolMac').get('address'))
	link_graph.add_node(curr_id)
	for link in emp.findall('PeerLink'):
		peerId = id_from_mac(link.get('peerMeshPointAddress'))
		m = link.get('metric')
		link_graph.add_edge(curr_id, peerId, label = m)

os.chdir(join(os.pardir, os.pardir))
nx.write_dot(link_graph, join('graphics','peer_link_graph.dot'))


'''
	Writing graph for various values in the xmls
'''
node_number = len(glob(join(directories[0], 'MeshHelperXmls', '*')))
values = [ {} for i in range(node_number) ]
for i in values:
	i['taxaEntrega'] = list()
	i['txOpen'] = list()
	i['txConfirm'] = list()
	i['txClose'] = list()
	i['rxOpen'] = list()
	i['rxConfirm'] = list()
	i['rxClose'] = list()
	i['dropped'] = list()
	i['txPreq'] = list()
	i['txPrep'] = list()
	i['txPerr'] = list()
	i['rxPreq'] = list()
	i['rxPrep'] = list()
	i['rxPerr'] = list()

for folder in directories:
	os.chdir( join(folder, 'MeshHelperXmls') )
	for nodeXml in glob('mp-report-*.xml'):
		xmlRoot = etree.XML( open(nodeXml,'r').read() )
		Id = id_from_mac( xmlRoot.get('address') )

		n = xmlRoot.find('Hwmp').find('HwmpProtocolMac').find('Statistics')
		for key in ['rxPerr', 'rxPrep', 'rxPreq', 'txPerr', 'txPrep', 'txPreq']:
			values[Id][key].append( clean_result( n.get(key) ) )

		n = xmlRoot.find('PeerManagementProtocol').find('PeerManagementProtocolMac').find('Statistics')
		for key in ['txOpen', 'txConfirm', 'txClose', 'rxOpen', 'rxConfirm', 'rxClose', 'dropped']:
			values[Id][key].append( clean_result( n.get(key) ) )

		n = xmlRoot.find('Interface').find('Statistics')
		txBytes = clean_result( n.get('txBytes') )
		rxBytes = clean_result( n.get('rxBytes') )
		values[Id]['taxaEntrega'].append(rxBytes/txBytes)
	os.chdir(join(os.pardir, os.pardir))



print 'A folder containing the graphics of the results of the simulation was created in the %s folder' % sys.argv[1]

