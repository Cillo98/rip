import os
import re


def load_from_file(filename):
    """
    Load the graph from file into a distance matrix

    :param filename: the name of the file to read. File extension must be included
    :return: the distance matrix of the graph read from file
    """
    # must know in advance the highest node in the graph
    num_nodes = max_node(filename)
    graph = [[0 for _ in range(num_nodes)] for _ in range(num_nodes)]

    with open(filename, "r") as file:
        data = file.readlines()
        num_lines = len(data)

        # when a 'Node ...' is encountered, start reading the following lines until another 'Node ...' is
        # found or the file finishes
        for i in range(num_lines):
            if data[i].startswith("Node "):

                cut_from = 5    # len("Node ") = 5
                node = int(data[i][cut_from:])
                i += 1
                while not data[i].startswith("Node "):
                    # node number and distance are separated by a tabulation
                    connection = data[i].split("\t")
                    to_node = int(connection[0])
                    weight = int(connection[1])

                    # the distance matrix is symmetric
                    graph[node-1][to_node-1] = weight
                    graph[to_node-1][node-1] = weight

                    # if this is the end of the file, quit
                    if i == num_lines-1:
                        break

                    # read next line
                    i += 1
    return graph


def load_node(filename, node):
    """
    Load the information regarding a node from file. This will return ONLY information for
    that node alone that can be found from 'Node x' to the end of the list of neighbours. If
    another node connects to this node, that information will not be given.

    :param filename: the name of the file to read. File extension must be included
    :param node: the node whose data must be loaded
    :return: a list of tuples for neighbouring nodes and distances
    """
    with open(filename, "r") as file:
        data = file.read()

        # if the node can be found this way, return its data (if any)
        if data.find("Node "+str(node)) != -1:
            cut_from = data.find("Node "+str(node)) + len("Node "+str(node)) + 1  # +1 to include '\n'
            cut_to = data[cut_from:].find("Node") - 1  # -1 to exclude '\n'

            # particular case for node at the end of the file
            if cut_to == -2:
                cut_to = len(data[cut_from:])-1
            data = data[cut_from:cut_to + cut_from]

            if data == "":
                return None

            return [(int(edge.split()[0]), int(edge.split()[1])) for edge in data.split("\n")]

        # it is possible that the node is only mentioned as a connection in some other node
        elif data.find("\n"+str(node)+"\t") != -1:
            return None

        return -1


def save_vector_to_file(node_no, vector, source):
    """
    Save a node's vector to file.

    :param node_no: what is the node that is saving to file
    :param vector: whole node's vector
    :param source: the source in the algorithm
    """
    filename = "vectors/"+str(node_no)+".txt"

    # make sure the file is there
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    # this tells the distance to the source
    head = "I am node  \t\t{}\n" \
           "The source is \t\t{}\n" \
           "My distance to it is \t{}\n" \
           "The next hop is \t{}\n\n" \
           "Here is my vector:\n\n" \
        .format(node_no, source, vector[source - 1][0], vector[source - 1][1])

    # and this is the full vector of the node
    table = "To node\tDist\tNext hop\n"
    for i in range(len(vector)):
        table += "{}\t{}\t{}\n".format(i+1, vector[i][0], vector[i][1])

    # finally, write the file
    with open(filename, "w") as file:
        file.write(head+table)


def save_dijkstra_to_file(minimum_distances, source):
    # header
    text = "Result of Dijkstra's algorithm on the given graph with source {}\n\n" \
           "Node\tCost\tPath\n".format(source+1)

    # body
    for i in range(len(minimum_distances)):
        text += str(i + 1) + "\t" + str(minimum_distances[i][0]) + "\t" + minimum_distances[i][1] + "\n"

    # write it
    with open("RESULT_dijkstra.txt", "w") as file:
        file.write(text)


def max_node(filename):
    """
    Find what is the highest node in a graph saved on file

    :param filename: the name of the file to read. File extension must be included
    :return: the highest node found in the file
    """
    with open(filename, "r") as file:
        data = file.read()
        # find the highest node other nodes are connected to. It cannot be otherwise
        nodes = set(re.findall("(\d+)\t\d", data))

    max = 0
    for node in nodes:
        if int(node) > max:
            max = int(node)

    return max
