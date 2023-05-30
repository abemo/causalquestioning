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


"""
TODO:
How do we know which node(s) and edge(s) to query?
 --we can get this using entropy? but same problem as the entropy function, how do we access the nodes and edges?
Should each type of question be a class? 
 --this is what I did, but im not sure if it is the best way
Each question type class should have its own answer method
"""

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
        """
        return the query which results in the lowest entropy model
        """
        return min(self.possible_queries, key=lambda q: q.entropy)
        

class Question:
    def __init__(self, type: str, node, edge):
        self.node = node
        self.edge = edge
    
    def answer(self):
        """
        answer the question
        """
        return "answer type not defined"

    
    class RemoveEdgeQ():
        def __init__(self, edge):
            super.__init__(edge)
        
        def answer(self):
            #TODO
            pass
            
    class AddEdgeQ():
        def __init__(self, edge):
            super.__init__(edge)

        def answer(self):
            #TODO
            pass

    class SetNodeQ:
        def __init__(self, node, set_value=randint.choice([0, 1])):
            super.__init__(node)
            self.set_value = set_value
        
        def answer(self):
            #TODO
            pass

    class RemoveNodeQ:
        def __init__(self, node):
            super.__init__(node)

        def answer(self):
            #TODO
            pass

    class AddNodeQ:
        def __init__(self, node, location):
            super.__init__(node)
            self.location = location

        def answer(self):
            #TODO
            pass


