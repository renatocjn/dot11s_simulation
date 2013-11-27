import numpy
from scipy.stats import norm
from math import sqrt
def statistics(lvals):
	vals = numpy.array(lvals)
	mean = vals.mean()
	if lvals.count(vals[0]) == len(vals): return mean, 0
	tmp = norm.interval(0.5,loc=mean,scale=vals.std()/sqrt(len(vals)))
	tmp = tmp[0] - tmp[1]
	tmp = abs(tmp/2.0)
	return mean, tmp

clean_result = lambda x: float( filter( lambda x: x.isdigit() or x=='.', x ) )
numerical_sort = lambda l: l.sort(lambda x,y: cmp( int(filter(lambda z:z.isdigit(), x)), int(filter(lambda z:z.isdigit(), y)) )) # numerical sort of list
