#!/usr/bin/python

from lxml import etree
from glob import glob
import os
import sys

if os.path.isdir(sys.argv[1]):
	os.chdir(sys.argv[1])
else:
	print 'please pass the directory with the results as the first parameter'
	sys.exit(1)

_, directories, _ = os.walk('.').next()

for d in directories:
	os.chdir(d)
	print 'para', d
	xmlString = open('FlowMonitorResults.xml', 'r').read()
	xmlRoot = etree.XML(xmlString)
	FlowStats = xmlRoot.find('FlowStats')

	flowcount=0

	for flow in FlowStats.iterfind('Flow'):
		rxBytes = float( filter( lambda x: x.isdigit() or x=='.', flow.get('rxBytes') ) )
		txBytes = float( filter( lambda x: x.isdigit() or x=='.', flow.get('txBytes') ) )
		deliveryRate = rxBytes/txBytes
		timeLastRxPacket = float( filter( lambda x: x.isdigit() or x=='.', flow.get('timeLastRxPacket') ) )
		timeFirstTxPacket = float( filter( lambda x: x.isdigit() or x=='.', flow.get('timeFirstTxPacket') ) )
		delay = (timeLastRxPacket - timeFirstTxPacket)/1000000000
		print '\tPara o flow', flow.get('flowId'), 'foi recuperado delay(s):',delay, 'e taxa de entrega(%):', deliveryRate, '\n'
	os.chdir('..')









