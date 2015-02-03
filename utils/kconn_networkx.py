import sys
import networkx as nx
from collections import defaultdict

def kconn(g) :
    return nx.node_connectivity(g)

def exportToMathematica(g) :
    m = "{ "
    for n1 in g.nodes() :
        for n2 in g[n1] :
            if n2>n1 :
                m += "{%d, %d}, " % (n1+1,n2+1)
    m = m[:-2] + " }"
    return m

def importFromMathematica(s) :
    g = nx.Graph()
    a = s.split(" ")
    assert a[0]=="{"
    assert a[-1]=="}"
    a = a[1:-1]
    assert len(a)%2==0
    for i in range(len(a)/2) :
        x = a[2*i]
        y = a[2*i+1]
        assert x[0]=="{"
        assert x[-1]==","
        xn = int(x[1:-1])-1
        y = y.strip(",")
        y = y.strip("}")
        yn = int(y)-1
        if xn not in g.nodes() :
            g.add_node(xn)
        if yn not in g.nodes() :
            g.add_node(yn)
        g.add_edge(xn,yn)
    return g

def isomorphismClassification(gs) :
    classes = defaultdict(list)
    for g in gs :
	found = False
	for g2 in classes.keys() :
	    if nx.is_isomorphic(g,g2) :
		classes[g2].append(g)
		found = True
		break
	if not found :
	    classes[g].append(g)
    return classes

def dumpConn() :
    for l in sys.stdin :
	l = l.strip()
	g = importFromMathematica(l)
	print kconn(g),l

def main() :
    gs = []
    for l in sys.stdin :
	l = l.strip()
	g = importFromMathematica(l)
	gs.append(g)
    classes = isomorphismClassification(gs)
    for g,cl in classes.iteritems() :
	print len(cl),kconn(g),exportToMathematica(g)

if __name__ == '__main__':
    main()

