import sys
import Node
from multiprocessing import Process


if __name__ == '__main__':
    if len(sys.argv) == 2:
        source = 1
    elif len(sys.argv) == 3:
        source = int(sys.argv[2])
    else:
        raise AttributeError('Given arguments are wrong.\nPlease enter "program.py <file_name.txt> [<node_from>]"')

    filename = sys.argv[1]

    # start the first node and quit immediately
    Process(target=Node.start, args=(filename, 1, source)).start()
