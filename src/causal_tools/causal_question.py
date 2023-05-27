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


class CausalQuestion:
    def __init__(self, node):
        self.node = node
        self.possible_queries = []

    def best_query(self):
        entropy = scm.node_entropy(self.node)
        pass

    def __repr__(self):
        pass



