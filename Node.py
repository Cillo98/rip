import time
import Utils
import socket
import sys
from threading import Thread
from multiprocessing import Process

"""
    messages are in the format:
    NODE (from node) DATA (weight 1) (weight 2)...
    where the index of the data +1 is the node to which the distance is related. Example:
    NODE 23 DATA 2 999999 999999 34 21 999999 4

    vector is a list of tuples in the format:
    ((weight 1) (next hop 1)) ((weight 2) (next hop 2))...
    where the index of the data +1 is the node to which the weight is related. Example:
    999999 2 999999 5 34 8 21 9 999999 11 4 12
"""


def start(filename, me, src):
    """
    Begin the execution of this node. The node can be present in the file or not.
    In the first case, the node will gather its information, call the next node
    and start running; in the latter case, the node will immediately stop executing.
    :param filename: the name of file containing nodes info
    :param me: the number of this node
    :param src: the number of source node
    """
    global neighbours, myself, dataset_changed, last_update, vector, host, go_on, source

    # these variables will be used throughout the whole program
    neighbours = list(tuple())
    last_update = time.time()
    dataset_changed = True
    host = "localhost"
    myself = me
    vector = list(tuple())
    source = src

    # load this node's information from file
    init_neighbours = Utils.load_node(filename, myself)

    # proceed only if the file actually contains info about this node
    if init_neighbours is not -1:
        Process(target=start, args=(filename, me+1, src)).start()
        proceed(init_neighbours)


def proceed(init_neighbours):
    global dataset_changed, last_update, go_on

    # load the nodes' data from file into the vector
    initialize_vector(init_neighbours)

    # listen to incoming connections in a separate thread
    listening = Thread(target=listen)
    listening.start()

    # allow all nodes to start listening
    time.sleep(15)

    # say hi to all neighbours
    greet_neighbours(init_neighbours)

    # allow most nodes to greet each other
    time.sleep(5)

    last_update = time.time()

    # if after 5 seconds there is no update, exit the operations
    while time.time() - last_update < 10:
        # if this node has received any updates, it must transmit the update to all neighbouring nodes
        if dataset_changed:
            notify_neighbours()
            dataset_changed = False

    # once vectors have converged, save this node's info to file
    Utils.save_vector_to_file(myself, vector, source)
    listening.join()
    print("4. Node {} is closed".format(myself))


def listen():
    """
    This function must be put into a thread because it is made of a while True loop
    that stops only when the socket times out. This node will start listening on
    port 1000 + this nodes' number. If this is node 4, it will listen on port 1004.
    Messages are in the format:

    NODE (from node) DATA (weight 1) (weight 2)...
    where the index of the data +1 is the node to which the distance is related. Example:
    NODE 23 DATA 2 999999 999999 34 21 999999 4

    Hello I am node (node_number) (distance)
    For example:
    Hello I am node 4 8
    """
    global vector, last_update

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind((host, 1000 + myself))
    listener.listen(10000)  # allow up to 10000 connections to be queued

    print("1. Node {} started listening on port {}".format(myself, 1000+myself))
    wait_longer = True

    try:
        while True:
            # need to wait longer when nodes
            if wait_longer:
                listener.settimeout(30)
                wait_longer = False
            else:
                listener.settimeout(10)

            # accept incoming connection
            connection, address = listener.accept()
            last_update = time.time()

            # the first 8 bytes of the data always contain the length of the message
            data_length = int(connection.recv(8).decode())
            # then, get the rest of the message; no unuseful delays included
            data = connection.recv(data_length).decode()

            # this is when a node is sending his vector
            if data.startswith("NODE "):
                in_vector = data.split()  # see comment at the top for info on the format
                node_from = int(in_vector[1])  # the second element is the node receiving from
                in_vector = in_vector[3:]  # cut 'NODE' (node_no) and 'DATA'

                update_vector(in_vector, node_from)
                wait_longer = True

            # this is when a node is greeting this node
            elif data.startswith("Hello I am node"):
                # the last items in the message are the neighbour number and its distance
                new_neighbour = int(data.split()[-2])
                weight = int(data.split()[-1])

                # no need to check size, greetings are always from smaller nodes

                # update my distance to that neighbour, if a better path hasn't been found yet
                if vector[new_neighbour - 1][0] > weight:
                    vector[new_neighbour - 1] = weight, str(new_neighbour)

                neighbours.append((new_neighbour, weight))  # add neighbour to list

    except socket.timeout:
        # this node has stopped listening and will then be closed
        pass


def initialize_vector(file_neighbours):
    global neighbours, vector

    if file_neighbours is not None:
        for edge in file_neighbours:
            # edge[0] is the node to which the distance is calculated
            # edge[1] is its distance from that node

            # make sure the list contains the node (is long enough)
            check_vector_size(edge[0])

            # update vector's distance and next-hop
            vector[edge[0] - 1] = edge[1], str(edge[0])
            neighbours.append((edge[0], edge[1]))  # update the list of neighbouring nodes

    # assign my distance to myself to 0
    check_vector_size(myself)
    vector[myself-1] = 0, str(myself)


def update_vector(incoming_vector, from_node):
    global vector, dataset_changed

    updated = False

    # make sure the node is there
    check_vector_size(len(incoming_vector))

    # the incoming vector is a list in the format
    # (distance1) (distance2) (distance3) ...
    # where the index of a distance +1 is the node number to which the distance refers to
    for i in range(len(incoming_vector)):
        weight = int(incoming_vector[i])

        if weight != 0:
            # find the distance from myself to that node from my list of neighbours
            neighbour_dist = sys.maxsize
            for neighbour in neighbours:
                if neighbour[0] == from_node:
                    neighbour_dist = neighbour[1]
                    break

            # want to check if dist(node_no, this_node) > dist(node_no, from_node) + weight(from_node, this_node)
            if vector[i][0] > weight + neighbour_dist:
                # update the vector in position i, which means to node i+1, giving it the distance
                # received and setting as next hop the node that the information comes from
                vector[i] = weight + neighbour_dist, str(from_node)
                updated = True

    # since the dataset has changed, this node will then broadcast to all neighbours
    if updated:
        print("3. Node  {}  updated vector thanks to node  {}".format(myself, from_node))
        dataset_changed = True


def greet_neighbours(neighbours_to_greet):
    if neighbours_to_greet is not None:
        for neighbour in neighbours_to_greet:
            # neighbours are tuples is the format (node_number, distance)
            node, weight = neighbour

            # say HI! And also say who I am and what is my distance to the node I'm connecting to
            message = "Hello I am node " + str(myself) + " " + str(weight)
            # append the size of the message to it
            length = str(len(message))
            while len(length) < 8:
                length = "0" + length

            try:
                # establish the connection
                sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sender.connect((host, 1000 + node))

                # finally send and close the connection
                sender.sendall((length + message).encode())
                sender.close()
                print("2. Node {} greeted node {}".format(myself, node))
            except:
                print("ERROR: Node {} could not greet node {}".format(myself, node))


def notify_neighbours():
    if neighbours is not None:
        message = "NODE " + str(myself) + " DATA"

        # compose the vector to send
        for i in range(len(vector)):
            message += " " + str(vector[i][0])  # + " " + vector[i][1]

        # calculate the length of the string as a 8 bytes string
        length = str(len(message))
        while len(length) < 8:
            length = "0" + length
        message = length + message

        for neighbour in neighbours:
            node, _ = neighbour

            # establish the connection
            sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sender.connect((host, 1000 + node))
            sender.sendall(message.encode())
            sender.close()


def check_vector_size(size):
    # make sure this node's vector is long enough
    while len(vector) < size:
        vector.append((sys.maxsize, ""))
