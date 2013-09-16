#!/usr/bin/python

from lxml import etree
from glob import glob
import os, sys, numpy
from scikits.bootstrap import ci

def statistics(vals):
	vals = numpy.array(vals)
	return {'mean':vals.mean(), 'std':vals.std(), 'ci':list(ci( vals, numpy.average ))}

clean_result = lambda x: float( filter( lambda x: x.isdigit() or x=='.', x ) )

if os.path.isdir(sys.argv[1]):
	os.chdir(sys.argv[1])
else:
	print 'please pass the directory with the results as the first parameter'
	sys.exit(1)

_, directories, _ = os.walk(os.curdir).next()

txBytes = list()
rxBytes = list()
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

for d in directories:
	os.chdir(d)
	xmlString = open('FlowMonitorResults.xml', 'r').read()
	xmlRoot = etree.XML(xmlString)
	FlowStats = xmlRoot.find('FlowStats')
	flowcount=0
	for flow in FlowStats.iterfind('Flow'):
		flowcount+=1
		rxBytes.append(clean_result(flow.get('rxBytes')))
		txBytes.append(clean_result(flow.get('txBytes')))
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
delay = map ( lambda x: (x[0]-x[1])*10**(-9), zip(timeLastRxPacket, timeFirstTxPacket))

#print timesForwarded

stats = {}
stats['txBytes'] = statistics(txBytes)
stats['rxBytes'] = statistics(rxBytes)
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
#stats['timesForwarded'] = statistics(timesForwarded)

if len(sys.argv) < 2:
	print 'print usage'
	sys.exit(1)

for i in sys.argv[2:]:
	try:
		print i+':', stats[i]
	except KeyError:
		print i, 'nao encontrado'
