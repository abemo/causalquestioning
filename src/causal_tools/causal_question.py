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
import dag


class Question:
    def __init__(self, dag):
        self.dag = dag
        self.possible_queries = []

    
    def choose_question(self):
        """
        choose a question to ask
        """
        return choice(self.possible_queries)

    def answer(self):
        """
        answer the question
        """
        return "question type not defined"

    
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

    class ReverseEdgeQ():
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


