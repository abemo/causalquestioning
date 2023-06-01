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
import agent


class Question:
    def __init__(self, dag, number_of_questions=3):
        self.dag = dag
        self.possible_questions = []
        self.questions = [self.choose_question() for _ in range(number_of_questions)]


    def add_questions(self, agent, edge=None, node=None):
        """
        For now just brute force, add all possible questions to possible_questions
        """
        if edge:
            self.remove_edge_q(agent,edge)
            self.add_edge_q(agent,edge)
            self.reverse_edge(agent,edge)
        elif node:
            self.remove_node_q(agent, node)
            self.add_node_q(agent, node)
            self.set_node_q(agent, node)
        else:
            raise Exception("Not given an Edge or Node")
    
    def choose_question(self):
        """
        choose a question to ask and spin off daemon
        """
        question = choice(self.possible_questions)
        #run daemon on question
        # daemon(current agent, question)
        self.possible_questions.remove(question)
        return question


    #TODO: start with only add adge, 
    # start with every node as an island, than the daemons try to connect them in the right direction
    # we should observe the entropy of the node being pointed to (does adding this effect help us understand the effect we're observing)

    
    # def remove_edge_q(self, agent, edge):
    #    #TODO: check if a legal question
    #    cloned_agent = agent.clone() #TODO: implement agent.clone that truly clones
    #    cloned_agent.dag.remove_edge(edge)
    #    self.possible_questions.append(cloned_agent)


    # def add_edge_q(self, agent, edge):
    #     #TODO: check if a legal question
    #     cloned_agent = agent.clone()
    #     cloned_agent.dag.add_edge(edge)
    #     self.possible_questions.append(cloned_agent)


    # def reverse_edge_q(self,agent, edge):
    #     #TODO: check if a legal question
    #     reversed_edge = (edge[1], edge[0])
    #     cloned_agent = agent.clone()
    #     cloned_agent.dag.remove_edge(edge)
    #     cloned_agent.dag.add_edge(reversed_edge)
    #     self.possible_questions.append(cloned_agent)
    

    # def set_node_q(self,agent, node): #intervene on that node
    #     #TODO: check if a legal question
    #     pass


    # def remove_node_q(self,agent, node):
    #     #TODO: check if a legal question
    #     cloned_agent = agent.clone()
    #     cloned_agent.dag.remove_node(node) #TODO: add a method to dag.py that removes a node, its cpt and all edges connected to it
    #     self.possible_questions.append(cloned_agent)


    # def add_node_q(self,agent, node, cpt, edges):
    #     #TODO: check if a legal question
    #     cloned_agent = agent.clone()
    #     cloned_agent.dag.add_node(node, cpt, edges) #TODO add a method to dag.py that adds a node, its cpt and all edges connected to it
    #     self.possible_questions.append(cloned_agent)


