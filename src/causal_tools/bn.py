from pgmpy.base import DAG
from pgmpy.models import BayesianNetwork
from pgmpy.estimators import MaximumLikelihoodEstimator
from pgmpy.factors.discrete.CPD import TabularCPD
import networkx as nx
import numpy as np
import pandas as pd
import math
import graphviz
import os
from itertools import combinations, chain
from copy import deepcopy
from re import findall


class BN:
    def __init__(self, nodes, edges, data=None, latent_edges=[], set_nodes=[]):
        self.model = BayesianNetwork()
        self.model.add_nodes_from(nodes)
        self.model.add_nodes_from(set_nodes)
        self.model.add_edges_from(edges)
        self.model.add_edges_from(latent_edges)
        if data is not None and not data.empty:
            estimator = MaximumLikelihoodEstimator(self.model, data)
            self.model.fit(data, estimator)
        else:
            for node in self.model.nodes():
                self.model.add_cpds(TabularCPD(node, 2, [[1], [0]]))
        self.draw()
    

    def node_entropy(self, node) -> float:
        cpd = self.model.get_cpds(node)

        if cpd is None:
            return f"No CPD found for node {node}"
        
        shannon_entropy = 0
        for prob in cpd.get_values()[-1]:
            shannon_entropy += prob * math.log((1 / prob), 2)
        return shannon_entropy

    def get_highest_entropy_pair(self) -> tuple:
        return max(list(combinations(self.model.nodes(), 2)), key=lambda pair: self.node_entropy(pair[0]) + self.node_entropy(pair[1]))

    def draw(self):
        dot = graphviz.Digraph()
        for node in self.model.nodes():
            dot.node(node, f"{node}\n{self.node_entropy(node)}")
        for edge in self.model.edges():
            dot.edge(edge[0], edge[1])
        dot.render(
            f'{os.path.dirname(__file__)}/../../output/causal-model.gv', view=True)

    def get_edges(self) -> list:
        nodes = list(combinations(self.model.nodes(), 2))
        edges = []
        for node_pair in nodes:
            if self.model.has_edge(node_pair[0], node_pair[1]):
                edges.append(node_pair)
        return edges

    def get_parents(self, nodes) -> set:
        """
        Returns the parents of a node or set of nodes.
        """
        if not isinstance(nodes, (list)):
            nodes = [nodes]
        
        all_nodes = [node for node in self.model.nodes]
        for node in nodes:
            if node not in all_nodes:
                raise ValueError(f"Node {node} not in graph")
        
        parents = set()
        for node_pair in self.model.edges:
            if node_pair[1] in nodes:
                parents.add(node_pair[0])

        return parents

    def get_ancestors(self, nodes) -> set:
        if not isinstance(nodes, (list)):
            nodes = [nodes]

        all_nodes = [node for node in self.model.nodes]
        for node in nodes:
            # print([node.to_tuple() for node in self.model.nodes])
            if node not in all_nodes:
                raise ValueError(f"Node {node} not in graph")

        ancestors_list = set()
        nodes_list = set(nodes)
        while nodes_list:
            node = nodes_list.pop()
            if node not in ancestors_list:
                nodes_list.update(self.model.predecessors(node))
            ancestors_list.add(node)

        return ancestors_list

    def get_feat_vars(self, act_var) -> set:
        return self.model.get_parents(act_var)

    def get_dist_as_dict(self, res) -> dict:
        if isinstance(res, str):
            parents = sorted(list(self.get_parents(res)))
            return {res: self.get_dist_as_dict(parents)}
        elif isinstance(res, list):
            if len(res) == 1:
                res == res[0]
            elif len(res) == 0:
                return None
            new_dict = {}
            for node in res:
                parents = sorted(list(self.get_parents(node)))
                new_dict[node] = self.get_dist_as_dict(parents)
            return new_dict
        return res if res else None

    def do(self, node) -> object:
        """
        Apply intervention on node to BN
        """
        return self.model.do(node)


def calculate_edit_distance(self, other_graph) -> int:
    """
    Calculates the edit distance between two graphs.
    currently from chat gpt, untested TODO see if it works
    """

    # Convert the pgmpy graphs to NetworkX graphs
    graph1 = self.model.to_networkx()
    graph2 = other_graph.to_networkx()

    # Define edit operations and their costs
    operation_costs = {
        'add_node': 1,
        'remove_node': 1,
        'add_edge': 1,
        'remove_edge': 1,
        'reverse_edge': 2
    }

    # Compute structural differences between the graphs
    node_diff = set(graph1.nodes()) ^ set(graph2.nodes())
    edge_diff = set(graph1.edges()) ^ set(graph2.edges())

    # Initialize the dynamic programming table
    dp_table = [[0] * (len(graph2.nodes()) + 1)
                for _ in range(len(graph1.nodes()) + 1)]

    # Fill in the dynamic programming table
    for i in range(len(graph1.nodes()) + 1):
        dp_table[i][0] = i * operation_costs['remove_node']

    for j in range(len(graph2.nodes()) + 1):
        dp_table[0][j] = j * operation_costs['add_node']

    for i in range(1, len(graph1.nodes()) + 1):
        for j in range(1, len(graph2.nodes()) + 1):
            if list(graph1.nodes())[i - 1] == list(graph2.nodes())[j - 1]:
                node_cost = 0
            else:
                node_cost = operation_costs['remove_node'] + \
                    operation_costs['add_node']

            dp_table[i][j] = min(
                dp_table[i - 1][j] + operation_costs['remove_node'],
                dp_table[i][j - 1] + operation_costs['add_node'],
                dp_table[i - 1][j - 1] + node_cost
            )

    # Add costs for edge modifications
    for edge in edge_diff:
        if edge in graph1.edges() and edge in graph2.edges():
            dp_table[len(graph1.nodes())][len(graph2.nodes())
                                          ] += operation_costs['reverse_edge']
        else:
            dp_table[len(graph1.nodes())][len(graph2.nodes())
                                          ] += operation_costs['remove_edge']

    # Return the edit distance
    return int(dp_table[len(graph1.nodes())][len(graph2.nodes())])
