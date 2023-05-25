# https://networkx.org/documentation/stable/tutorial.html

import networkx as nx
import matplotlib.pyplot as plt
from pandas import ExcelFile

DIR_NAME = 'DIR_NAME'
G = nx.Graph()

if __name__ == '__main__':
    directory = '../output/%s' % DIR_NAME
    ex_file = '/%s.xlsx' % 'poa'
    results = ExcelFile(directory + ex_file).parse(sheet_name=None, index_col=0)
    # node_list = [{name, edges} for name, edges in results.items()}]

    for i, ind_var in enumerate(sorted(results)):
        print(ind_var)

    # Create an empty directed graph
    scm_graph = nx.DiGraph()

    # Add nodes to the graph
    scm_graph.add_nodes_from(['A', 'B', 'C', 'D'])

    # Add directed edges
    scm_graph.add_edges_from([('A', 'B'), ('C', 'B'), ('C', 'D')])

    # Draw the graph
    nx.draw(scm_graph, with_labels=True, node_color='lightblue', node_size=800, font_weight='bold')

    # Display the graph
    plt.show()






