#!/usr/bin/python

from os.path import isdir, join
from lxml import etree
from glob import glob
import os, sys, numpy, random, networkx as nx
#from scikits.bootstrap import ci
from shutil import rmtree
import pylab as pl

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
	#try: tmp = list(ci( vals, numpy.average ))
	#except BaseException: tmp = None
	return vals.mean(), vals.std()#, tmp

clean_result = lambda x: float( filter( lambda x: x.isdigit() or x=='.', x ) )
numerical_sort = lambda l: l.sort(lambda x,y: cmp( int(filter(lambda z:z.isdigit(), x)), int(filter(lambda z:z.isdigit(), y)) )) # numerical sort of list
int_from_mac = lambda address: int(filter(lambda x: x!=':', address), 16) - 1

_, directories, _ = os.walk(os.curdir).next()
directories.remove('graphics')
numerical_sort(directories)


'''
	Writing the graph of links among the mesh points assuming that the links are constant among the runs
'''
os.chdir(join(random.choice(directories),'MeshHelperXmls'))
link_graph = nx.MultiGraph()
report_files = glob('mp-report-*.xml')
numerical_sort(report_files)
for report_file in report_files:
	r = etree.XML(open(report_file,'r').read())
	channels = {}
	interfaces = r.findall('Interface')
	aux = len(interfaces)
	for i in interfaces:
		channels[i.get('Address')] = i.get('Channel')
	emp = r.find('PeerManagementProtocol')
	curr_id = int_from_mac(emp.find('PeerManagementProtocolMac').get('address'))/aux
	link_graph.add_node(curr_id)
	for link in emp.findall('PeerLink'):
		peerId = int_from_mac(link.get('peerMeshPointAddress'))/aux
		m = channels[link.get('localAddress')]
		flag = False
		if link_graph.get_edge_data(curr_id, peerId) is not None:
			for d in link_graph.get_edge_data(curr_id, peerId).values():
				if d['label'] == m: flag = True
		if not flag:
			link_graph.add_edge(curr_id, peerId, label = m)

os.chdir(join(os.pardir, os.pardir))
nx.write_dot(link_graph, join('graphics','peer_link_graph.dot'))


'''
	recovering values from the nodes xml files
'''
node_number = len(glob(join(directories[0], 'MeshHelperXmls', '*')))
values = [ {} for i in range(node_number) ]
all_statistics_keys = {'txOpen', 'rxOpen', 'txConfirm', 'rxConfirm', 'rxClose', 'txClose', 'rxPerr', 'txPerr', 'rxPrep', 'txPrep', 'rxPreq', 'txPreq', 'dropped', 'taxaEntrega', 'droppedTtl', 'totalQueued', 'totalDropped', 'initiatedPreq', 'initiatedPrep', 'initiatedPerr'}

for i in values:
	for k in all_statistics_keys:
		i[k] = list()

for folder in directories:
	os.chdir( join(folder, 'MeshHelperXmls') )
	for nodeXml in glob('mp-report-*.xml'):
		xmlRoot = etree.XML( open(nodeXml,'r').read() )
		Id = int_from_mac( xmlRoot.get('address') )
		Id /= len(xmlRoot.findall('Interface'))

		n = xmlRoot.find('Hwmp').find('HwmpProtocolMac').find('Statistics')
		for key in ['rxPerr', 'rxPrep', 'rxPreq', 'txPerr', 'txPrep', 'txPreq']:
			values[Id][key].append( clean_result( n.get(key) ) )

		n = xmlRoot.find('PeerManagementProtocol').find('PeerManagementProtocolMac').find('Statistics')
		for key in ['txOpen', 'txConfirm', 'txClose', 'rxOpen', 'rxConfirm', 'rxClose', 'dropped']:
			values[Id][key].append( clean_result( n.get(key) ) )

		n = xmlRoot.find('Hwmp').find('Statistics')
		for key in ['droppedTtl', 'totalQueued', 'totalDropped', 'initiatedPreq', 'initiatedPrep', 'initiatedPerr']:
			values[Id][key].append( clean_result( n.get(key) ) )

		n = xmlRoot.find('Interface').find('Statistics')
		txBytes = clean_result( n.get('txBytes') )
		rxBytes = clean_result( n.get('rxBytes') )
		values[Id]['taxaEntrega'].append(rxBytes/txBytes)
	os.chdir(join(os.pardir, os.pardir))



'''
	Drawing graphs for the recovered values
'''
width = 0.5
x = numpy.arange(node_number)
labels = [ 'node_' + str(int(i)) for i in x ]
os.chdir('graphics')
for k in all_statistics_keys:
	pl.clf()
	y, std = zip(*[ statistics(values[i][k]) for i in range(node_number) ])
	pl.xlim(0, x[-1]+width*2)
	pl.ylim(ymin=0)
	pl.xticks(x + width, labels)
	pl.title(k)
	pl.bar(x + width/2.0, y, yerr=std, width=width)
	pl.savefig('%s_graph.png' % k)


print 'A folder containing the graphics of the results of the simulation was created in the %s folder' % sys.argv[1]

