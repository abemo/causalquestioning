import networkx as nx
import matplotlib.pyplot as plt
import math 
import graphviz
import os

class DAG:
    def __init__(self, nodes, edges, cpts):
        """
        TODO: figure out how best to store CPTs, and update entropy calculations accordingly
        """
        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(nodes)
        self.graph.add_edges_from(edges)
        self.cpts = {}
        for node, cpt in zip(nodes, cpts):
            self.cpts[node] = cpt

    def draw_model(self, v=True):
        self.graph.render(f'{os.path.dirname(__file__)}/../../output/causal-model.gv', view=v)

    def node_entropy(self, node, base: int = 2) -> float:
        """
        Returns the Shannon Entropy of a given node
        Base is defaulted to 2 for binary decision problems, but can be set to other values
        """
        shannon_entropy = 0
        for prob in self.cpts[node].probabilities(): 
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
    
    def __hash_graph__(self) -> int:
        return hash(self.graph)
    
    def __hash_cpts__(self) -> int:
        return hash(tuple(self.cpts))
    
    def __eq__(self, __value: object) -> bool:
        return self.__hash_graph__() == __value.__hash_graph__() and self.__hash_cpts__() == __value.__hash_cpts__()