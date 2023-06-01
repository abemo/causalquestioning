import networkx as nx
import matplotlib.pyplot as plt
import math 
import graphviz
import os
import pydot
import numpy as np


class DAG:
    def __init__(self, nodes, edges, cpts):
        """
        nodes: list of nodes in the graph
        edges: list of edges in the graph
        cpts: a numpy ndarray of the conditional probability tables, with a column for each variable,
            where the last column is the probabilities
        """
        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)
        self.cpts = {} #TODO: way to generate the cpts from the data
        for node, cpt in zip(nodes, cpts):
            self.cpts[node] = cpt

    def draw_model(self, v=True):
        dot = graphviz.Digraph()
        dot.graph_attr['label'] = f"Total Entropy: {self.total_entropy()}"
        for node in self.graph.nodes():
            dot.node(node, f"{node}\n{self.node_entropy(node)}")
        for edge in self.graph.edges():
            dot.edge(edge[0], edge[1])
        dot.render(f'{os.path.dirname(__file__)}/../../output/causal-model.gv', view=v)

    def node_entropy(self, node, base: int = 2) -> float:
        """
        Returns the Shannon Entropy of a given node
        Base is defaulted to 2 for binary decision problems, but can be set to other values
        """
        shannon_entropy = 0
        for prob in self.cpts[node][-1]: 
            shannon_entropy += prob * math.log((1 / prob), base)
        return shannon_entropy
  
    def total_entropy(self) -> float:
        """
        Returns the total entropy of the model
        """
        total_entropy = 0
        for node in self.graph.nodes():
            total_entropy += self.node_entropy(node)
        return total_entropy
    
    def highest_entropy(self) -> str:
        """
        Returns the node with the highest entropy
        """
        highest_entropy = 0
        highest_entropy_node = None
        for node in self.graph.nodes():
            if self.node_entropy(node) > highest_entropy:
                highest_entropy = self.node_entropy(node)
                highest_entropy_node = node
        return highest_entropy_node
    
    def remove_node():
        pass

    def add_node():
        pass
    
    def set_node():
        pass

    def remove_edge():
        pass

    def add_edge(edge):
        self.graph.add_edge(edge)

    def update_cpts():
        pass
    
    def __hash_graph__(self) -> int:
        return hash(self.graph)
    
    def __hash_cpts__(self) -> int:
        return hash(tuple(self.cpts))
    
    def __eq__(self, __value: object) -> bool:
        return self.__hash_graph__() == __value.__hash_graph__() and self.__hash_cpts__() == __value.__hash_cpts__()
    

if __name__ == "__main__":
    """
    Example usage of the DAG class,
    as well as example of cpt format
    """
    cpts = np.array([[[False, False, True, True], [False, True, False, True], [0.7, 0.3, 0.2, 0.8]],
            [[False, False, True, True], [False, True, False, True], [0.7, 0.3, 0.2, 0.8]],
            [[False, False, True, True], [False, True, False, True], [0.7, 0.3, 0.2, 0.8]],
            [[False, False, True, True], [False, True, False, True], [0.7, 0.3, 0.2, 0.8]],
            [[False, False, True, True], [False, True, False, True], [0.7, 0.3, 0.2, 0.8]],
    ])
    dag = DAG(["A", "B", "C", "D", "E"], [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E")], cpts)
    dag.draw_model()
    print(dag.cpts["A"])
    print(dag.node_entropy("A"))
    print(dag.total_entropy())