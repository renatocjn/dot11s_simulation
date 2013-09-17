#!/usr/bin/python

from lxml import etree
from glob import glob
import os, sys, numpy, random, networkx as nx
from scikits.bootstrap import ci
from shutil import rmtree

if os.path.isdir(sys.argv[1]):
	os.chdir(sys.argv[1])
else:
	print 'please pass the directory with the results as the first parameter'
	sys.exit(1)

if os.path.isdir('graphics'):
	answer = raw_input('This has already been run, want to run anyway? [y,N]\n:')
	if answer == 'y' or answer == 'Y' or answer == 'Yes' or answer == 'yes':
		rmtree ('graphics')
		os.mkdir('graphics')
	else:
		print 'exiting...'
		sys.exit()

def statistics(vals):
	vals = numpy.array(vals)
	return {'mean':vals.mean(), 'std':vals.std(), 'ci':list(ci( vals, numpy.average ))}

clean_result = lambda x: float( filter( lambda x: x.isdigit() or x=='.', x ) )
numerical_sort = lambda l: l.sort(lambda x,y: cmp( int(filter(lambda z:z.isdigit(), x)), int(filter(lambda z:z.isdigit(), y)) )) # numerical sort of list
id_from_mac = lambda address: int(filter(lambda x: x!=':', address), 16)

_, directories, _ = os.walk(os.curdir).next()
numerical_sort(directories)
os.chdir(os.path.join(random.choice(directories),'MeshHelperXmls'))

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
		link_graph.add_edge(curr_id, peerId, metric = m)

os.chdir(os.path.join(os.pardir, os.pardir))
nx.write_dot(link_graph, 'peer_link_graph.dot')

