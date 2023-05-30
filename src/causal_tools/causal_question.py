"""
1) formulate question --> do in constructor
    node 
    edge
    set_values
2) strategize how to answer
3) answer question (satisfying Q from collected data)
4) find the best answer
"""

import scm
from random import randint, choice


class CausalQuestion:
    def __init__(self, nodes: list):
        self.nodes = nodes
        self.possible_queries = []
        self.possible_queries.append(self.RemoveEdgeQ(node, edge))
        self.possible_queries.append(self.AddEdgeQ(node, edge))
        self.possible_queries.append(self.SetNodeQ(node, set_value))
        self.possible_queries.append(self.RemoveNodeQ(node))
        self.possible_queries.append(self.AddNodeQ(node))

    def best_query(self):
        return max(self.possible_queries, key=lambda q: q.entropy)
        

class Question:
    def __init__(self, type: str, node, edge):
        self.node = node
        self.edge = edge

    
    class RemoveEdgeQ:
        def __init__(self, node, edge):
            self.node = node
            self.edge = edge
            
    class AddEdgeQ:
        def __init__(self, node, edge):
            self.node = node
            self.edge = edge

    class SetNodeQ:
        def __init__(self, node, set_value=randint.choice([0, 1])):
            self.node = node
            self.set_values = set_value
    
    class RemoveNodeQ:
        def __init__(self, node):
            self.node = node

    class AddNodeQ:
        def __init__(self, node):
            self.node = node



