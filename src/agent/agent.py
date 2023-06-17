"""
Defines the Agent class and its inheritors (SoloAgent, AskAgent)
"""

from copy import deepcopy
from query import Count, Product, Query
from util import only_given_keys, permutations, hellinger_dist
from causal_tools.enums import ASR
from math import inf
import pgmpy 


class Agent:
  def __init__(self, rng, name, environment, tau=None, asr=ASR.EG, epsilon=0, rand_trials=0, cooling_rate=0):
    self.rng = rng
    self.name = name
    self._environment = environment
    self.bn = environment.bn # this was cgm
    self.domains = environment.domains
    self.act_var = environment.act_var
    self.act_dom = self.domains[self.act_var]
    self.actions = permutations(only_given_keys(self.domains, [self.act_var]))
    self.rew_var = environment.rew_var
    self.rew_dom = self.domains[self.rew_var]
    self.rewards = permutations(only_given_keys(self.domains, [self.rew_var]))
    self.contexts = permutations(self.get_context())
    self.tau = tau
    self.asr_combo = asr
    self.asr = asr
    self.epsilon = ([1] * len(self.contexts)
                    if self.contexts else 1) if asr == ASR.ED else epsilon
    self.rand_trials = rand_trials
    self.rand_trials_rem = [rand_trials] * \
        len(self.contexts) if self.contexts else rand_trials
    self.cooling_rate = cooling_rate
    
    # self.my_cpts = environment.bn.model.get_cpds() # generate cpts here TODO generate them in BN?
    # nodes in the cgm that Y is dependent on that is either X or observed by X
    # in the OG example, this is Z, X
    # but if Z is not a counfounder on Y, but only connected to Y through X,
    # Z would not be included

    # parents = environment.bn.model.get_parents(self.act_var)
    # parents = {self.act_var} # Axel's original code
    # for var in self.bn.get_ancestors(self.act_var): # this was cgm
    #   if not self.bn.is_d_separated(var, self.rew_var, self.act_var): # this was cgm
    #     parents.add(var)
    # self.my_cpts["rew"] = CPT(self.rew_var, parents, self.domains)

  def update_divergence(self):
    return

  def get_context(self):
    return only_given_keys(self.domains, self.bn.get_parents(self.act_var)) # this was cgm

  def get_ind_var_value(self, ind_var):
    """
    Returns the assignment of the given
    "indepedent variable."
    """
    if ind_var == "tau":
      return self.tau
    elif ind_var == "otp":
      return self.get_otp()
    elif ind_var == "asr":
      return self.asr_combo
    elif ind_var == "epsilon":
      return self.epsilon
    elif ind_var == "rand_trials":
      return self.rand_trials
    elif ind_var == "cooling_rate":
      return self.cooling_rate
    else:
      return ""

  def epsilon_greedy(self, givens):
    if self.rng.random() < self.epsilon:
      return self.choose_random()
    return self.choose_optimal(givens)

  def epsilon_first(self, givens):
    if self.contexts:
      given_i = self.contexts.index(givens)
      if self.rand_trials_rem[given_i] > 0:
        self.rand_trials_rem[given_i] -= 1
        return self.choose_random()
    elif self.rand_trials_rem > 0:
      self.rand_trials_rem -= 1
      return self.choose_random()
    return self.choose_optimal(givens)

  def epsilon_decreasing(self, givens):
    if self.contexts:
      given_i = self.contexts.index(givens)
      if self.rng.random() < self.epsilon[given_i]:
        self.epsilon[given_i] *= self.cooling_rate
        return self.choose_random()
      self.epsilon[given_i] *= self.cooling_rate
      return self.choose_optimal(givens)
    elif self.rng.random() < self.epsilon:
      self.epsilon *= self.cooling_rate
      return self.choose_random()
    self.epsilon *= self.cooling_rate
    return self.choose_optimal(givens)

  def choose(self, givens):
    """
    Defines the logic of how the agent
    'chooses' according to their Action
    Selection Rule (ASR).
    """
    if self.asr == ASR.EG:
      return self.epsilon_greedy(givens)
    elif self.asr == ASR.EF:
      return self.epsilon_first(givens)
    elif self.asr == ASR.ED:
      return self.epsilon_decreasing(givens)
    elif self.asr == ASR.TS:
      return self.thompson_sample(givens)
    else:
      raise ValueError("%s ASR not found" % self.asr)

  def observe(self, sample):
    """
    The behavior of the agent returning
    """
    self.recent = sample
    for cpt in self.bn.model.get_cpds().values():
      cpt.add(sample)

  def get_recent(self):
    return self.recent

  def get_rew_query_unfactored(self):
    parents = {self.act_var}
    for var in self.bn.get_ancestors(self.act_var): # this was cgm
      if not self.bn.is_d_separated(var, self.rew_var, self.act_var): # this was cgm
        parents.add(var)
    return Query(self.rew_var, parents)

  def expected_rew(self, givens, cpts):
    summ = 0
    query = self.get_rew_query_unfactored()
    query.assign(givens)
    for rew in self.rewards:
      query.assign(rew)
      print(cpts)
      rew_prob = query.solve(cpts["rew"])
      summ += rew[self.rew_var] * rew_prob if rew_prob is not None else 0
    return summ

  def choose_optimal(self, context):
    cpts = self.bn.model.get_cpds()
    best_acts = []
    best_rew = -inf
    for act in self.actions:
      expected_rew = self.expected_rew({**context, **act}, cpts)
      if expected_rew is not None:
        if expected_rew > best_rew:
          best_acts = [act]
          best_rew = expected_rew
        elif expected_rew == best_rew:
          best_acts.append(act)
    # assert bool(best_acts)
    return self.rng.choice(best_acts)

  def choose_random(self):
    """
    Randomly chooses from the possible actions
    """
    return self.rng.choice(self.actions)

  def thompson_sample(self, context):
    best_acts = []
    best_sample = 0
    cpts = self.get_cpts()
    rew_query = self.get_rew_query_unfactored()
    rew_query = Count(rew_query)
    rew_query.assign(context)
    for act in self.actions:
      rew_query.assign(act)
      alpha = cpts["rew"][rew_query.assign({self.rew_var: 1})]
      beta = cpts["rew"][rew_query.assign({self.rew_var: 0})]
      sample = self.rng.beta(alpha + 1, beta + 1)
      if sample > best_sample:
        best_sample = sample
        best_acts = [act]
      if sample == best_sample:
        best_acts.append(act)
    return self.rng.choice(best_acts)

  def get_otp(self):
    return self.__class__.__name__[:-5]

  def __hash__(self):
    return hash(self.name)

  def __repr__(self):
    return "<" + self.get_otp() + self.name + ": " + self.asr.value + ">"

  def __eq__(self, other):
    return isinstance(other, self.__class__) \
        and self.name == other.name


class SoloAgent(Agent):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def get_cpts(self):
    return self.bn.model.get_cpts()


class AskAgent(Agent):
  def __init__(self, bn, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.name = "Unique Identifier" #TODO: make this a unique identifier
    self.bn = bn

  def ask():
    pass

  def __hash_askagent__(self):
    return hash(self.name)

  def __hash_dag__(self):
    return hash(self.dag)

  def __eq__(self, other):
    return self.__hash_askagent__() == other.__hash_askagent__() and self.__hash_dag__() == other.__hash_dag__()



