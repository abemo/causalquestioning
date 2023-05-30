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
        self.possible_queries.append(self.Remove_Edge_Q(node, edge))
        self.possible_queries.append(self.Add_Edge_Q(node, edge))
        self.possible_queries.append(self.Do_Q(node, set_value))
        self.possible_queries.append(self.Remove_Node_Q(node))
        self.possible_queries.append(self.Add_Node_Q(node))

    def best_query(self):
        return max(self.possible_queries, key=lambda q: q.entropy)
        

class Question:
    def __init__(self, type: str, node, edge):
        self.node = node
        self.edge = edge
                
    
    class Remove_Edge_Q:
        def __init__(self, node, edge):
            self.node = node
            self.edge = edge
            
    class Add_Edge_Q:
        def __init__(self, node, edge):
            self.node = node
            self.edge = edge

    class Do_Q:
        def __init__(self, node, set_value=randint.choice([0, 1])):
            self.node = node
            self.set_values = set_value
    
    class Remove_Node_Q:
        def __init__(self, node):
            self.node = node

    class Add_Node_Q:
        def __init__(self, node):
            self.node = node



