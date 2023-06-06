from pgmpy.base import DAG
from pgmpy.models import DynamicBayesianNetwork as DBN
import numpy as np
import pandas as pd
import math
import graphviz
import os


class PGM:
    def __init__(self, nodes, given_cpts):
        self.model = DAG.DBN()
        self.model.add_nodes_from(nodes)

        self.cpts = {}
        for cpt in given_cpts:
            self.cpts[f'cpt_{cpt.variable}'] = cpt
            self.model.add_cpds(cpt)


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
        for edge in self.model.get_edges(): #TODO: not right way to get edges
            dot.edge(edge[0], edge[1])
        dot.render(f'{os.path.dirname(__file__)}/../../output/causal-model.gv', view=True)
        

    def get_edges(self) -> list: #TODO: just do the edge thing a:BCD B:CD C:D
        nodes = self.model.get_slice_nodes()
        for node in nodes:

            pass

        

        
        
        