"""
Defines the World class, which constitutes the environment agents interact in for a single
simulation. All agents and their environments exist in a World, and this class is used to
store results to be returned to the process and simulation at the end of execution.
"""

from agent.agent import AdjustAgent
from util import only_given_keys


class World:
  def __init__(self, agents, T):
    self.agents = agents #this is the main model
    self.cpr = {a: [0] * T for a in self.agents}
    self.poa = {a: [0] * T for a in self.agents}
    self.has_sensitive = any(
        [isinstance(a, (AdjustAgent)) for a in self.agents])
    self.daemons = []

  def run_episode(self, ep):# this is one trial 
    for a in self.agents:
      if self.has_sensitive:
        a.update_divergence()
      context = a._environment.pre.sample(a.rng)
      action = a.choose(context)
      sample = a._environment.post.sample(a.rng, {**context, **action})
      a.observe(sample)
    self.update(ep)
    self.check_for_questions()
    self.run_daemons()
    return

  def update(self, ep):
    for a in self.agents:
      recent = a.get_recent()
      rew_received = recent[a.rew_var]
      feature_assignments = only_given_keys(recent, a._environment.feat_vars)
      rew_optimal = a._environment.get_optimal_reward(feature_assignments)
      curr_regret = self.cpr[a][ep-1]
      new_regret = curr_regret + (rew_optimal - rew_received)
      self.cpr[a][ep] = new_regret
      optimal_actions = a._environment.get_optimal_actions(feature_assignments)
      self.poa[a][ep] = 1 if only_given_keys(
          recent, a.act_var) in optimal_actions else 0
    return

  def check_for_questions(self):
    # if there is a question to be asked, check if it's been asked and
      # should we keep a list of asked questions?
    # if it hasn't add the question to self.daemons
    # this will be done via checking the environments
    pass

  def run_daemons(self):
    for daemon in self.daemons:
        daemon.simulate()
        # if daemon.age > environment.daemon_death_age:
            # self.possible_questions.remove(daemon)
        # if calculate_entropy(daemon.pointed_to_node) > environment.entropy_threshhold

  def __reduce__(self):
    return (self.__class__, (self.agents, self.T))
