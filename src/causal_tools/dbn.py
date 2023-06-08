from pgmpy.base import DAG
from pgmpy.models import DynamicBayesianNetwork as DBN
import numpy as np
import pandas as pd
import math
import graphviz
import os
from itertools import combinations


class DBN:
    def __init__(self):
        self.model = DAG.DBN()
        self.model.add_nodes_from(nodes)


    def node_entropy(self, node) -> float:
        cpd = self.model.get_cpds(node)
        shannon_entropy = 0
        for prob in cpd.get_values()[-1]:
            shannon_entropy += prob * math.log((1 / prob), 2)
        return shannon_entropy


    def draw(self):
        dot = graphviz.Digraph()
        for node in self.model.get_slice_nodes():
            dot.node(node, f"{node}\n{self.node_entropy(node)}")
        for edge in self.model.get_edges():
            dot.edge(edge[0], edge[1])
        dot.render(f'{os.path.dirname(__file__)}/../../output/causal-model.gv', view=True)
        

    def get_edges(self) -> list:
        nodes = list(combinations(self.model.get_slice_nodes(), 2))
        edges = []
        for node_pair in nodes:
            if self.model.has_edge(node_pair[0], node_pair[1]):
                edges.append(node_pair)
        return edges
    

if __name__ == "__main__":
    dbn = DBN()
    dbn.draw()

        

        
        
        