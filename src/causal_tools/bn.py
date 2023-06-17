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
import random
from causal_tools.assignment_models import ActionModel
from collections.abc import Iterable

class BN:
    def __init__(self, nodes=None, edges=None, assignment=None, data=None, latent_edges=[], set_nodes=[]):
        self.model = BayesianNetwork()

        if assignment is not None:
            print(assignment)
            self.assignment = assignment
            return # TODO learn from assignment and pre_nodes

        if nodes is not None:
            self.model.add_nodes_from(nodes)
        self.model.add_nodes_from(set_nodes)

        if edges is not None:
            self.model.add_edges_from(edges)
        self.model.add_edges_from(latent_edges)

        if data is not None and not data.empty:
            estimator = MaximumLikelihoodEstimator(self.model, data)
            self.model.fit(data, estimator)
        else:
            for node in self.model.nodes():
                self.model.add_cpds(TabularCPD(node, 2, [[1], [0]]))
        self.observed_vars = sorted(nodes + set_nodes)
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

    def is_d_separated(self, x, y, zs=None):
        """
        Is x d-separated from y, conditioned on zs?
        """
        zs = self._variable_or_iterable_to_set(zs)
        assert x in self.observed_vars
        assert y in self.observed_vars
        assert all([z in self.observed_vars for z in zs])

        graph = nx.Graph()
        graph.add_nodes_from(self.model.nodes)
        graph.add_edges_from(self.model.edges)
        paths = nx.all_simple_paths(graph, x, y)
        return all(self._check_d_separation(path, zs) for path in paths)

    def _variable_or_iterable_to_set(self, x) -> frozenset:
        if x is None:
            return frozenset([])

        if isinstance(x, str):
            return frozenset([x])

        if not isinstance(x, Iterable) or not all(isinstance(xx, str) for xx in x):
            raise ValueError(
                "{} is expected to be either a string or an iterable of strings"
                .format(x))

        return frozenset(x)
    
    def _check_d_separation(self, path, zs=None):
        """
        Check if a path is d-separated by set of variables zs.
        """
        zs = self._variable_or_iterable_to_set(zs)

        if len(path) < 3:
            return False

        for a, b, c in zip(path[:-2], path[1:-1], path[2:]):
            structure = self._classify_three_structure(a, b, c)

        if structure in ("chain", "fork") and b in zs:
            return True

        if structure == "collider":
            descendants = (nx.descendants(self.dag, b) | {b})
            if not descendants & set(zs):
                return True

        return False
    
    def _classify_three_structure(self, a, b, c):
        """
        Classify three structure as a chain, fork or collider.
        """
        dag = nx.Graph()
        dag.add_nodes_from(self.model.nodes)
        dag.add_edges_from(self.model.edges)

        if dag.has_edge(a, b) and dag.has_edge(b, c):
            return "chain"

        if dag.has_edge(c, b) and dag.has_edge(b, a):
            return "chain"

        if dag.has_edge(a, b) and dag.has_edge(c, b):
            return "collider"

        if dag.has_edge(b, a) and dag.has_edge(b, c):
            return "fork"

        raise ValueError("Unsure how to classify ({},{},{})".format(a, b, c))

    def sample(self, rng, set_values={}):
        """
        Arguments
        ---------
        n_samples: int
            the number of samples to return

        set_values: dict[variable:str, set_value:np.array]
            the values of the interventional variable

        Returns
        -------
        samples: pd.DataFrame
        """
        samples = {}
        for node in self.model.nodes: # this was cgm
            c_model = self.assignment[node]

            if isinstance(c_model, ActionModel):
                samples[node] = set_values[node]
            else:
                parent_samples = {
                    parent: samples[parent]
                    for parent in c_model.parents
                }
                samples[node] = c_model(rng, **parent_samples)
        return samples

    def do(self, node):
        """
        Returns a StructualCausalModel after an intervention on node
        """
        new_assignment = self.assignment.copy()
        new_assignment[node] = None
        return BN(new_assignment)
