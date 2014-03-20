#!/usr/bin/python

from lxml import etree
from glob import glob
import os, sys, numpy
from scipy.stats import norm
from math import sqrt
from utils import *

if os.path.isdir(sys.argv[1]):
	os.chdir(sys.argv[1])
else:
	print 'please pass the directory with the results as the first parameter'
	sys.exit(1)

#_, directories, _ = os.walk(os.curdir).next()
directories = glob('test-*')
numerical_sort(directories)

txBytes = list()
rxBytes = list()
txPackets = list()
rxPackets = list()
timeFirstTxPacket = list()
timeFirstRxPacket = list()
timeLastTxPacket = list()
timeLastRxPacket = list()
deliveryRate = list()
delay = list()
delaySum = list()
jitterSum = list()
lastDelay = list()
lostPackets = list()
timesForwarded = list()
throughput = list()
node_stats = {}

for d in directories:
	os.chdir(d)
	xmlString = open('FlowMonitorResults.xml', 'r').read()
	xmlRoot = etree.XML(xmlString)
	#report_files = glob('MeshHelperXmls/mp-report-*.xml')
	#racc = long(0)
	#tacc = long(0)
	#for report in report_files:
		#MeshPointDevice = etree.XML(open(report).read())
		#stats = MeshPointDevice.find('Statistics')
		#tacc += clean_result(stats.get('txUnicastDataBytes'))
		#racc += clean_result(stats.get('rxUnicastDataBytes'))
	#rxBytes.append(racc)
	#txBytes.append(tacc)

	FlowStats = xmlRoot.find('FlowStats')
	all_flows = FlowStats.findall('Flow')
	for flow in all_flows: # get flow simulation values
		rxBytes.append(clean_result(flow.get('rxBytes')))
		txBytes.append(clean_result(flow.get('txBytes')))
		rxPackets.append(clean_result(flow.get('rxPackets')))
		txPackets.append(clean_result(flow.get('txPackets')))
		timeLastRxPacket.append(clean_result(flow.get('timeLastRxPacket')))
		timeLastTxPacket.append(clean_result(flow.get('timeLastTxPacket')))
		timeFirstRxPacket.append(clean_result(flow.get('timeFirstRxPacket')))
		timeFirstTxPacket.append(clean_result(flow.get('timeFirstTxPacket')))
		delaySum.append(clean_result(flow.get('delaySum')))
		jitterSum.append(clean_result(flow.get('jitterSum')))
		lastDelay.append(clean_result(flow.get('lastDelay')))
		lostPackets.append(clean_result(flow.get('lostPackets')))
		timesForwarded.append(clean_result(flow.get('timesForwarded')))
	os.chdir(os.pardir)

deliveryRate = map( lambda x: x[0]/x[1], zip(rxBytes, txBytes))
delay = map( lambda x: (x[0]-x[1])*10**(-9), zip(timeLastRxPacket, timeFirstTxPacket) )
throughput = map( lambda x: x[0]/x[1], zip(rxPackets, delay) )

stats = {}
stats['txBytes'] = statistics(txBytes)
stats['rxBytes'] = statistics(rxBytes)
stats['txPackets'] = statistics(txPackets)
stats['rxPackets'] = statistics(rxPackets)
stats['timeFirstTxPacket'] = statistics(timeFirstTxPacket)
stats['timeFirstRxPacket'] = statistics(timeFirstRxPacket)
stats['timeLastTxPacket'] = statistics(timeLastTxPacket)
stats['timeLastRxPacket'] = statistics(timeLastRxPacket)
stats['deliveryRate'] = statistics(deliveryRate)
stats['delay'] = statistics(delay)
stats['delaySum'] = statistics(delaySum)
stats['jitterSum'] = statistics(jitterSum)
stats['lastDelay'] = statistics(lastDelay)
stats['lostPackets'] = statistics(lostPackets)
stats['throughput'] = statistics(throughput)
#stats['timesForwarded'] = statistics(timesForwarded)

if len(sys.argv) == 2:
	output = open('flow-statistics.txt','w')
	lines = list()
	for metric in stats.keys():
		mean, std = stats[metric]
		lines.append( '%s-mean=%f\n' % (metric, mean) )
		lines.append( '%s-err=%f\n' % (metric, std) )
	output.writelines(lines)
	output.close()
	sys.exit()

for i in sys.argv[2:]:
	try:
		print i+':', '\n\tmedia:', stats[i][0], '\n\tdesvio padrao:', stats[i][1]
	except KeyError:
		print i, 'nao encontrado'

