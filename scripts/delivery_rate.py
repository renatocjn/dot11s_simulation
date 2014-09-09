from os.path import isdir, join
from lxml import etree
from glob import glob
import os, sys, numpy, random, networkx as nx
from shutil import rmtree
import pylab as pl
from scipy.stats import norm
from math import sqrt
from utils import *
from numpy import array

if len(sys.argv) == 2 and isdir(sys.argv[1]): #minimum parameter checking
	os.chdir(sys.argv[1])
else:
	print 'please pass the directory with the results as the first parameter'
	sys.exit(1)

_, directories, _ = os.walk(os.curdir).next() #get diretories of the current folder
numerical_sort(directories)

txBytes = long(0)
rxBytes = long(0)

for run_dir in directories:
	os.chdir( join(run_dir, 'MeshHelperXmls') )
	report_files = glob('mp-report-*.xml')
	for report in report_files:
		MeshPointDevice = etree.XML(open(report, 'r').read())
		stats = MeshPointDevice.find('Statistics')
		txBytes += float(stats.get('txUnicastDataBytes'))
		rxBytes += float(stats.get('rxUnicastDataBytes'))
		#HwmpProtocolMacs = MeshPointDevice.find('Hwmp').findall('HwmpProtocolMac')
		#for mac in HwmpProtocolMacs:
			#txFrames += float(mac.find('Statistics').get('txDataBytes'))
			#rxFrames += float(mac.find('Statistics').get('rxDataBytes'))
	os.chdir(join(os.pardir, os.pardir))

print rxBytes/txBytes
