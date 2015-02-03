try:
    import matplotlib.pyplot as plt
except:
    raise
import sys
import networkx as nx
import numpy as np


from kconn_networkx import *

s = sys.stdin.readline().strip()

g = importFromMathematica(s)
n = len(g.nodes())

edge_color = [ 'Brown' if ( abs(a-b)==1 or set((a,b))==set((0,n-1)) ) else 'DodgerBlue' for (a,b) in g.edges() ]

nx.draw_graphviz(g, edge_color=edge_color)
# nx.draw_spectral(g, edge_color=edge_color)
# nx.draw_spring(g, edge_color=edge_color)

plt.savefig(sys.argv[1])

# plt.show()
