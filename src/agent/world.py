"""
Defines the World class, which constitutes the environment agents interact in for a single
simulation. All agents and their environments exist in a World, and this class is used to
store results to be returned to the process and simulation at the end of execution.
"""

from util import only_given_keys


class World:
  def __init__(self, agent, T):
    self.agent = agent #this is the main model
    self.cpr = [0] * T
    self.poa = [0] * T
    self.daemons = set()

  def run_episode(self, ep): # this is one trial 
    context = self.agent._environment.pre.sample(self.agent.rng)
    action = self.agent.choose(context)
    sample = self.agent._environment.post.sample(self.agent.rng, {**context, **action})
    self.agent.observe(sample)
    self.update(ep)
    # self.check_for_questions()
    # self.run_daemons()
    return

  def update(self, ep):
    recent = self.agent.get_recent()
    rew_received = recent[self.agent.rew_var]
    feature_assignments = only_given_keys(recent, self.agent._environment.feat_vars)
    rew_optimal = self.agent._environment.get_optimal_reward(feature_assignments)
    curr_regret = self.cpr[ep-1]
    new_regret = curr_regret + (rew_optimal - rew_received)
    self.cpr[ep] = new_regret
    optimal_actions = self.agent._environment.get_optimal_actions(feature_assignments)
    self.poa[ep] = 1 if only_given_keys(
        recent, self.agent.act_var) in optimal_actions else 0
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

