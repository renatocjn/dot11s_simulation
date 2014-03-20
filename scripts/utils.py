import numpy
from scipy.stats import norm
from math import sqrt
from lxml import etree
from glob import glob

def statistics(lvals):
	vals = numpy.array(lvals)
	vals = vals
	mean = vals.mean()
	#if lvals.count(vals[0]) == len(vals): return mean, 0
	tmp = norm.interval(0.5,loc=mean,scale=vals.std()/sqrt(len(vals)))
	tmp = tmp[0] - tmp[1]
	tmp = abs(tmp/2.0)
	return mean, tmp

clean_result = lambda x: float( filter( lambda x: x.isdigit() or x=='.', x ) )
numerical_sort = lambda l: l.sort(lambda x,y: cmp( int(filter(lambda z:z.isdigit(), x)), int(filter(lambda z:z.isdigit(), y)) )) # numerical sort of list

def clean_params(param_list):
	new_params = list()
	for param in param_list:
		if float(param)%1 == 0:
			new_params.append(int(param))
		else:
			new_params.append(float(param))
	return new_params

def check_run(test_dir):
	if not glob(test_dir+'/mp-report*.xml'):
		print 'None mesh Point report found'
		return False

	rxBytes = list()
	txBytes = list()

	flowmonitor_file = test_dir + "/FlowMonitorResults.xml"
	xmlFile = open(flowmonitor_file)
	xmlString = xmlFile.read()
	xmlRoot = etree.XML(xmlString)
	FlowStats = xmlRoot.find('FlowStats')
	all_flows = FlowStats.findall('Flow')
	for flow in all_flows: # get flow simulation values
		rxBytes.append(clean_result(flow.get('rxBytes')))
		txBytes.append(clean_result(flow.get('txBytes')))

	deliveryRate = map( lambda x: x[0]/x[1], zip(rxBytes, txBytes))
	tmp = map(lambda x: x>0.001, deliveryRate)
	if not all(tmp):
		print numpy.array(deliveryRate)
	return all(tmp)
