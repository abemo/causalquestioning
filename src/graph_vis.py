import networkx as nx
import matplotlib.pyplot as plt

DIR_NAME = 'DIR_NAME'
G = nx.Graph()

if __name__ == '__main__':
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






