"""
Defines the behavior of the process which run simulations. Multiple processes
run in parallel to get averaged results.
"""

from agent.agent import SoloAgent
from agent.world import World
from util import printProgressBar
from agent.environment import Environment
import time
from itertools import cycle
from causal_tools.enums import OTP


class Process:
  def __init__(self, rng, environment, rew_var, is_community, nmc, ind_var, mc_sims, T, ass_perms, num_agents, rand_envs, domains, act_var):
    self.rng = rng
    self.environment = environment
    self.rew_var = rew_var
    self.is_community = is_community
    self.nmc = nmc
    self.ind_var = ind_var
    self.mc_sims = mc_sims
    self.T = T
    self.ass_perms = ass_perms
    self.num_agents = num_agents
    self.rand_envs = rand_envs
    self.domains = domains
    self.act_var = act_var

  def agent_maker(self, name, environment, assignments, agents):
    otp = assignments.pop("otp")
    if otp == OTP.SOLO:
      return SoloAgent(self.rng, name, environment, agents, **assignments)
    else:
      raise ValueError("OTP type %s is not supported." % otp)

  def environment_generator(self):
    nmc = self.nmc if isinstance(
        self.nmc, float) else self.rng.uniform(self.nmc[0], self.nmc[1])
    template = {node: model.randomize(
        self.rng) for node, model in self.environments[0]._assignment.items()}
    base = Environment(template, self.rew_var)
    yield base
    for _ in range(self.num_agents - 1):
      randomized = dict(template)
      for node in base.get_non_act_vars():
        if self.rng.random() < nmc:
          randomized[node] = randomized[node].randomize(self.rng)
      yield Environment(randomized, self.rew_var)

  def world_generator(self):
    # These two lines should NOT be necessary. Need to do testing to make sure.
    ap = list(self.ass_perms)
    self.rng.shuffle(ap)
    assignments = [dict(ass) for ass in ap for _ in range(self.num_agents)]
    # uncomment this line and set is_community to True to get a blend of input ASR
    # assignments = [dict(ass) for _ in range(self.num_agents) for ass in ap]
    if not self.is_community:
      self.rng.shuffle(assignments)
    agent = SoloAgent(self.rng, "SoloAgent", self.environment, *assignments)
    return World(agent, self.T)

  def simulate(self):
    res = [{}, {}]
    sim_time = []
    for i in range(self.mc_sims):
      sim_start = time.time()
      world = self.world_generator()
      time_rem = None if not sim_time else \
          (sum(sim_time) / len(sim_time)) * \
          (self.mc_sims - (i + (1 / len(self.ass_perms))))
      time_rem_str = '?' if time_rem is None else \
          '%dh %dm   ' % (time_rem // (60 * 60), time_rem // 60 % 60)
      for k in range(self.T): # these are time steps
        world.run_episode(k)
        # printProgressBar(
        #     iteration=i*len(self.ass_perms)+1+(k+1)/self.T,
        #     total=self.mc_sims * len(self.ass_perms),
        #     suffix=time_rem_str,
        # )
        self.update_process_result(res, world)
      sim_time.append(time.time() - sim_start)
    return res

  def update_process_result(self, res, world):
    raw = (world.cpr, world.poa)
    for i in (0, 1):
      for data in raw[i]:
        ind_var = world.agent.get_ind_var_value(self.ind_var)
        if ind_var not in res[i]:
          res[i][ind_var] = [data]
          continue
        res[i][ind_var].append(data)
    return

  def __eq__(self, other):
      # custom equality logic so daemons can be hashed
      return self.value == other.value

  def __hash__(self):
      return hash(self.value)