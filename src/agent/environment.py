"""
Defines the Environment Class, which Agents interact with to get take actions, make observations, etc.

CREDIT:
Much of this class was written by Iain Barr (ijmbarr on GitHub)
from his public repository, causalgraphicalmodels, which is registered with the MIT License.
The code has been imported and modified into this project for ease/consistency
"""


import pandas as pd
from util import hash_from_dict, only_given_keys, permutations
from math import inf
from causal_tools.scm import StructuralCausalModel
from causal_tools.assignment_models import ActionModel
from causal_tools.bn import BN


class Environment:
    def __init__(self, assignment, rew_var="Y"):
        """
        Creates StructuralCausalModel from assignment of the form
        { variable: Function(parents) }
        """
        self.domains = {}
        self._assignment = assignment.copy()
        nodes = list(assignment.keys())
        self.act_var = None
        self.rew_var = rew_var
        set_nodes = []
        edges = []
        print(f"Assignment: {assignment}")

        for node, model in assignment.items():
            self.domains[node] = model.domain
            if isinstance(model, ActionModel):
                assert self.act_var == None
                self.act_var = node
            edges.extend([
                (parent, node)
                for parent in model.parents
            ])

        # TODO: data is empty right now?
        data = pd.DataFrame()
        self.bn = BN(nodes=nodes, edges=edges,
                       data=data, set_nodes=set_nodes)

        pre_nodes = list(self.bn.get_ancestors(self.act_var))
        self.pre = StructuralCausalModel(
            only_given_keys(self._assignment, pre_nodes))
        post_ass = self._assignment.copy()
        print("===========================")
        print(pre_nodes)
        print("Domains: " + str(self.domains))
        print("===========================")
        [post_ass.update({n: ActionModel(self.bn.get_parents(n), self.domains[n])})
         for n in pre_nodes]
        self.post = StructuralCausalModel(post_ass)

        self.feat_vars = self.get_feat_vars()
        self.assigned_optimal_actions()
        

    def get_domains(self):
        return self.domains

    def get_domain(self, node):
        return self.domains[node]

    def get_vars(self):
        return set(self.domains.keys())

    def get_non_act_vars(self):
        return self.get_vars() - {self.act_var}

    def get_act_var(self):
        return self.act_var

    def get_act_dom(self):
        return {self.act_var: self.domains[self.act_var]}

    def get_feat_vars(self):
        return set(self.bn.get_parents(self.act_var))

    def get_feat_doms(self):
        return only_given_keys(self.domains, self.get_feat_vars())

    def has_context(self):
        return bool(self.get_feat_vars())

    def get_act_feat_vars(self):
        return self.feat_vars.union(set(self.act_var))

    def get_act_feat_doms(self):
        return only_given_keys(self.domains, self.get_act_feat_vars())

    def get_rew_var(self):
        return self.rew_var

    def get_rew_dom(self):
        return only_given_keys(self.domains, [self.rew_var])

    def assigned_optimal_actions(self):
        if self.has_context():
            self.optimal_reward = {}
            self.optimal_actions = {}
            for feat_combo in permutations(self.get_feat_doms()):
                best = self.get_optimal(feat_combo)
                feat_hash = hash_from_dict(feat_combo)
                self.optimal_reward[feat_hash] = best[0]
                self.optimal_actions[feat_hash] = best[1]
            return
        best = self.get_optimal()
        self.optimal_reward = best[0]
        self.optimal_actions = best[1]

    def get_optimal(self, givens={}):
        best_actions = list()
        best_rew = -inf
        for action in permutations(self.get_act_dom()):
            expected_rew = self.expected_reward({**action, **givens})
            if expected_rew > best_rew:
                best_actions = [action]
                best_rew = expected_rew
            elif expected_rew == best_rew:
                best_actions.append(action)
        return (best_rew, best_actions)

    def assign_dist_with_givens(self, dist, givens):
        for var, parents in dist.items():
            if var in givens:
                dist[var] = givens[var]
            elif isinstance(parents, dict):
                self.assign_dist_with_givens(parents, givens)
        return dist

    def parse_dist_as_probs(self, assigned_dist):
        for var, assignment in assigned_dist.items():
            if isinstance(assignment, dict):
                assigned_dist[var] = self.parse_dist_as_probs(assignment)
            assigned_dist[var] = self._assignment[var].prob(assignment)
        return assigned_dist

    def expected_reward(self, givens={}):
        assigned_dist = self.assign_dist_with_givens(
            self.bn.get_dist_as_dict(self.rew_var), givens)
        reward_value_probs = self._assignment[self.rew_var].prob(
            self.parse_dist_as_probs(assigned_dist[self.rew_var]))
        return self.expected_value(reward_value_probs)

    def expected_value(self, value_probs):
        expected_value = 0
        for value, prob in value_probs.items():
            expected_value += value * prob
        return expected_value

    def get_optimal_reward(self, context):
        if context:
            return self.optimal_reward[hash_from_dict(context)]
        return self.optimal_reward

    def get_optimal_actions(self, context):
        if context:
            return self.optimal_actions[hash_from_dict(context)]
        return self.optimal_actions

    def __reduce__(self):
        return (self.__class__, (self._assignment, self.rew_var))

    def __repr__(self):
        variables = ", ".join(map(str, sorted(self.bn.dag.nodes())))
        return ("{classname}({vars})"
                .format(classname=self.__class__.__name__,
                        vars=variables))

    def __copy__(self):
        return Environment(self._assignment, self.rew_var)

    def __getitem__(self, key):
        return self._assignment[key]
