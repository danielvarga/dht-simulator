import random
import sys
import heapq

n = 30

def logg(s) :
    sys.stderr.write(s+"\n")

class Node :
    def __init__(self,depth,value) :
	self.m = [None,None]
	self.nodes = []
	self.depth = depth
	self.prefix = "unimpl"
	self.value = value # Only leaf nodes have values.

def consistency(node) :
    pass

def kth(nodeId,k) :
    return ( nodeId >> k ) % 2


def bitvec(nodeId) :
    v = []
    i = nodeId
    for j in range(n) :
	v.append(i%2)
	i /= 2
    v.reverse()
    return v

def pretty(nodeId) :
    return "".join(map(str,bitvec(nodeId)))

def prefix(nodeId,k) :
    return nodeId >> k

def isLeaf(node) :
    assert node is not None
    il = (node.m[0] is None) and (node.m[1] is None)
    if il :
	assert node.value is not None
    return il

def direction(node,nodeId) :
    return kth(nodeId,n-node.depth-1)

def splitNode(node,nodeId) :
    assert isLeaf(node)
    v = node.value
    assert v is not None
    dOld = direction(node,v)
    dNew = direction(node,nodeId)
    if dOld==dNew :
	node.value = None
	newNode = Node(node.depth+1, v)
	node.m[dOld] = newNode
	splitNode(newNode,nodeId)
    else :
	newNodeOld = Node(node.depth+1, v)
	newNodeNew = Node(node.depth+1, nodeId)
	node.m[dOld] = newNodeOld
	node.m[dNew] = newNodeNew

def add(node,nodeId) :
    if isLeaf(node) :
	splitNode(node,nodeId)
    else :
        b = direction(node,nodeId)
        if node.m[b] is None :
    	    node.m[b] = Node(node.depth+1,nodeId)
    	else :
	    add(node.m[b],nodeId)

def build(nodeIds) :
    root = None
    for nodeId in nodeIds :
	if root is None :
	    root = Node(0,nodeId)
	else :
	    add(root,nodeId)
    return root

def aggregate(node) :
    s = set()
    if isLeaf(node) :
	node.nodes = set((node.value,))
	return node.nodes
    for d in (0,1) :
	if node.m[d] is not None :
	    s |= aggregate(node.m[d])
    node.nodes = s
    return node.nodes

def aggregateToList(node) :
    s = set()
    if isLeaf(node) :
	node.nodes = [node.value]
	return set((node.value,))
    for d in (0,1) :
	if node.m[d] is not None :
	    s |= aggregateToList(node.m[d])
    node.nodes = sorted(list(s))
    return s

def collect(node,dic) :
    if isLeaf(node) :
	dic[node.value] = node
    else :
	for d in (0,1) :
	    if node.m[d] is not None :
		collect(node.m[d],dic)

def dump(root,indent=0) :
    print " "*indent, "pre=", root.prefix, "depth=", root.depth, "nodes=", str(sorted(list(root.nodes)))
    if root.m[0] is not None :
	print " "*indent,"0"
	dump(root.m[0], indent+1)
    if root.m[1] is not None :
	print " "*indent,"1"
	dump(root.m[1], indent+1)

def fastSample(l,k) :
    m = len(l)
    if k<=m :
	return l[:]
    if k*5<=m :
	return random.sample(l,k)
    s = set()
    while len(s)<k :
	s.add(random.choice(l))
    return list(s)

def buildRoutingTable(root,nodeId,bucketSize) :
    bv = bitvec(nodeId)
    cursor = root
    rt = []
    doRealSampling = True
    for i,b in enumerate(bv) :
	# altSet is (a reference to) the set of all nodes that share their first i bits with nodeId,
	# but their i+1-th bit is different. It is asserted that aggregate was already run.
	alt = cursor.m[1-b]
	if alt is not None :
	    altSet = alt.nodes
	else :
	    altSet = []
	try :
	    # bucket = random.sample(altSet,bucketSize)
	    if doRealSampling :
		bucket = random.sample(altSet,bucketSize)
	    else :
		bucket = altSet[:bucketSize]
	except ValueError :
	    bucket = list(altSet)
	rt.append(bucket)
	last = cursor
	cursor = cursor.m[b]
	if cursor is None :
	    assert last.value==nodeId
	    break
    return rt

def distance(nodeId1,nodeId2) :
    return nodeId1 ^ nodeId2

def prefixLength(dist) :
    d = dist
    m = 2**(n-1)
    i = 0
    while d<m :
	d << 1
	i += 1
    return i

# Returns a list of (dist,nodeId) pairs.
def closest(rt,target,peerLimit) :
    nodesCloseness = []
    for bucket in rt :
	for nodeId in bucket :
	    nodesCloseness.append((distance(target,nodeId),nodeId))
    nodesCloseness.sort()
    nodesCloseness = nodesCloseness[:peerLimit]
    return nodesCloseness


# Non-forwarding
def queriedDHT(rts,selfId,targetId,peerLimit) :
    rt = rts[selfId]
    nodesCloseness = closest(rt,targetId,peerLimit)
    dist = distance(selfId,targetId)

    # How do others solve this issue? We don't want to suggest nodes
    # farther than us, to avoid infinite recursion.
    nodesCloseness = [ (d,n) for (d,n) in nodesCloseness if d<dist ]

    if len(nodesCloseness)==0 :
	return "closest",[(dist,selfId)]
    else :
	return "closer",nodesCloseness

def queryDHT(rts,sourceId,targetId) :
    peerLimit = 8 # Mainline DHT uses 8 both for bucket size and peerLimit.
    rt = rts[sourceId]
    print sourceId,targetId
    print "initial_querying",distance(sourceId,targetId),pretty(sourceId)
    nodesCloseness = closest(rt,targetId,peerLimit)
    heapq.heapify(nodesCloseness)
    results = []
    while True :
	try :
	    dist,nodeId = heapq.heappop(nodesCloseness)
	except IndexError :
	    break
	print "querying",dist,pretty(nodeId)
	response = queriedDHT(rts,nodeId,targetId,peerLimit)
	if response[0]=="closest" :
	    item = response[1][0]
	    dist2,nodeIdNew = item
	    results.append(nodeIdNew)
	    print "settled_at",dist2,pretty(nodeIdNew)
	else :
	    nodesClosenessNew = response[1]
	    for item in nodesClosenessNew :
		heapq.heappush(nodesCloseness,item)
		dist2,nodeIdNew = item
		print "added_to_heap",dist2,pretty(nodeIdNew)
    print "#_of_nodes",len(results)
    print "#_of_unique_nodes",len(set(results))
    # Of course that's stupid. These are local optima. What we really care about:
    # Do they have the key-value pair? But that's unimplemented so far.
    return results

def dumpBucket(bucket) :
    for nodeId in bucket :
	print "".join(map(str,bitvec(nodeId)))

def dumpRoutingTable(rt) :
    for i,bucket in enumerate(rt) :
	print i
	dumpBucket(bucket)

def dumpRoutingTablesPyplot(nodeIds,rts) :
    import matplotlib.pyplot as plt
    import networkx as nx
    # nx.draw_spring(g, edge_color=edge_color)
    g = nx.Graph()
    for nodeId in nodeIds :
	g.add_node(pretty(nodeId))
    for nodeId,rt in rts.iteritems() :
	for bucket in rt :
	    for nodeId2 in bucket :
		g.add_edge(pretty(nodeId),pretty(nodeId2))
    nx.draw_spring(g)
    plt.savefig("plot.png")

def test() :
    cnt = 30
    nodeIds = set( random.randrange(2**n) for i in range(cnt) )
    root = build(nodeIds)
    logg("Tree built.")
    aggregateToList(root)
    logg("Aggregation done.")
    dic = {}
    collect(root,dic)
    # dump(root)
    # nodeId = random.choice(dic.keys())
    # rt = buildRoutingTable(root,nodeId,bucketSize=10)
    # dumpRoutingTable(rt)
    rts = {}
    for nodeId in nodeIds :
	rt = buildRoutingTable(root,nodeId,bucketSize=5)
	rts[nodeId] = rt
    logg("All routing tables built.")

    # dumpRoutingTablesPyplot(nodeIds,rts)

    sourceId = random.choice(list(nodeIds))
    targetId = random.randrange(2**n)
    queryDHT(rts,sourceId,targetId)

test()
