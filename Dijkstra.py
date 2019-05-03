import sys
import Utils
from time import time


def dijkstra(dist, source):
    # the number of nodes in the graph
    nodes = len(dist)

    min_dist = [(sys.maxsize, "")] * nodes     # initialize all nodes' distances to infinity
    min_dist[source] = (0, "")     # make the source's distance 0
    included = [False] * nodes   # list of included nodes in the MST

    # outer loop
    for _ in range(nodes):
        # pick the node whose edge is minimum and not yet included in the MST
        u = min_index(min_dist, included)
        included[u] = True

        # update the distance to all newly reachable nodes and to all nodes for which a shorter path is discovered
        for node in range(nodes):
            if (not included[node]) and (dist[u][node] != 0) and (min_dist[u][0] + dist[u][node] < min_dist[node][0]):
                # min_dist keeps track of both the distance and the path to go through
                min_dist[node] = (min_dist[u][0] + dist[u][node], min_dist[u][1]+str(u+1)+" ")

    # if a node is not part of the graph, mark it as unreachable
    for i in range(nodes):
        if min_dist[i][0] == sys.maxsize:
            min_dist[i] = ("N/A", "N/A")

    return min_dist


def min_index(path_lengths, included):
    """
    :param path_lengths: list of composite distances
    :param included: list of included nodes in the MST
    :return: the index of the node with shortest path that is not included in the MST
    """
    min_dist = sys.maxsize
    index = 0

    for node in range(len(path_lengths)):
        if (not included[node]) and (path_lengths[node][0] < min_dist):
            min_dist = path_lengths[node][0]
            index = node

    return index


# Program starts here

# make sure parameters are ok
if len(sys.argv) == 2:
    filename = sys.argv[1]
else:
    raise AttributeError('Given arguments are wrong.\nPlease enter "program.py <file_name.txt>"')

# start counting the time
ti = time()
# load the grapth from file and feed it to the algorithm
graph = Utils.load_from_file(filename)

# find the set of minimum distances from the source (0+1 = 1)
min_distances = dijkstra(graph, 0)

# save the result to file
Utils.save_dijkstra_to_file(min_distances, 0)

tf = time()

# count how many nodes and edges were in the graph
nodes = len(graph)
edges = 0
for k in range(nodes):
    for j in range(nodes):
        if graph[k][j] != 0 and graph[k][j] != sys.maxsize:
            edges += 1
edges = int(edges/2)  # because of the matrix's symmetry

# print out a success message
print("Finished. It took {} seconds to process a {}-nodes graph with {} edges".format(float(tf-ti), nodes, edges))
