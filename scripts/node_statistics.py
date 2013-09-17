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
		return 0

def statistics(vals):
	vals = numpy.array(vals)
	return {'mean':vals.mean(), 'std':vals.std(), 'ci':list(ci( vals, numpy.average ))}

clean_result = lambda x: float( filter( lambda x: x.isdigit() or x=='.', x ) )
numerical_sort = lambda l: l.sort(lambda x,y: cmp( int(filter(lambda z:z.isdigit(), x)), int(filter(lambda z:z.isdigit(), y)) )) # numerical sort of list
id_from_mac = lambda address: int(filter(lambda x: x!=':', address), 16)

_, directories, _ = os.walk(os.curdir).next()
numerical_sort(directories)

os.chdir(os.join(random.choice(directories),'MeshHelperXmls'))
