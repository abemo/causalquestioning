from world import World
from assignment_models import ActionModel, DiscreteModel, RandomModel
from agent import Agent
from environment import Environment
from enums import Policy, Result
import gutil
import matplotlib.pyplot as plt
import numpy as np
import multiprocessing as mp
import time
from copy import copy

class Sim:
  def __init__(self, world, num_episodes, num_trials):
    self.world = world
    self.num_episodes = num_episodes
    self.num_trials = num_trials
    self.trials = []
  
  def run(self):
    for i in range(self.num_trials):
      world = self.world.__copy__()
      for j in range(self.num_episodes):
        world.run_once()
        gutil.printProgressBar(i+((j+1)/self.num_episodes), self.num_trials)
      self.trials.append(world.episodes)
    return

  def get_policy_data(self, dep_var):
    policies = {}
    for trial in self.trials:
      for a in self.world.agents:
        if a.policy not in policies:
          policies[a.policy] = []
        policies[a.policy].append(gutil.list_from_dicts(trial, dep_var, a.name))
    return policies
  
  def plot_policy(self, dep_var):
    policies = {}
    for trial_episode in self.trials:
      for a in self.world.agents:
        if a.policy not in policies:
            policies[a.policy] = []
        policies[a.policy].append(gutil.list_from_dicts(trial_episode, dep_var, a.name))
    for p in policies:
      plt.plot(
        np.arange(self.num_episodes),
        np.array(gutil.avg_list(policies[p])),
        label=p
      )
    plt.xlabel("Iterations")
    plt.ylabel(dep_var.value)
    plt.legend()
    plt.show()
    return
  
  def simulate(self, results, index, dep_var):
    sim = copy(self)
    sim.run()
    results[index] = sim.get_policy_data(dep_var)

  def multithreaded_sim(self, dep_var, lbl=None, show=False):
    print(lbl)
    if lbl == 0.04:
      color = "#{0}{1}{2}".format("ff","00","00")
    elif lbl == 0.02:
      color = "#{0}{1}{2}".format("ff","6a","00")
    elif lbl == 0.05:
      color = "#{0}{1}{2}".format("ff","ff","00")
    elif lbl == 0.04:
      color = "#{0}{1}{2}".format("51","ff","00")
    elif lbl == 0.06:
      color = "#{0}{1}{2}".format("00","ff","8c")
    elif lbl == 0.06:
      color = "#{0}{1}{2}".format("00","e1","ff")
    elif lbl == 0.07:
      color = "#{0}{1}{2}".format("00","55","ff")
    elif lbl == 0.08:
      color = "#{0}{1}{2}".format("1e","00","ff")
    elif lbl == 0.08:
      color = "#{0}{1}{2}".format("88","00","ff")
    elif lbl == 0.1:
      color = "#{0}{1}{2}".format("ff","00","dd")
    num_threads = mp.cpu_count()
    jobs = []
    results = mp.Manager().list([None] * num_threads)
    for i in range(num_threads):
      job = mp.Process(target=self.simulate,args=(results, i, dep_var))
      jobs.append(job)
      job.start()
    [job.join() for job in jobs]
    policies = {}
    for res in results:
      for p in res:
        if p not in policies:
          policies[p] = []
        policies[p].extend(res[p])
    for p in policies:
      plt.plot(
          np.arange(len(policies[p][0])),
          np.array(gutil.avg_list(policies[p])),
          label=lbl,
          c=color
      )
    plt.xlabel("Iterations")
    plt.ylabel(dep_var.value)
    plt.legend()
    if show:
      plt.show()

  def __copy__(self):
    return Sim(copy(self.world), self.num_episodes, self.num_trials)

if __name__ == "__main__":  
  baseline = {
    "W": RandomModel((0.4, 0.6)),
    "X": ActionModel(("W"), (0, 1)),
    "Z": DiscreteModel(("X"), {(0,): (0.75, 0.25), (1,): (0.25, 0.75)}),
    "Y": DiscreteModel(("W", "Z"), {(0, 0): (1, 0), (0, 1): (1, 0), (1, 0): (1, 0), (1, 1): (0, 1)})
  }
  w1 = dict(baseline)
  w1["W"] = RandomModel((0.1, 0.9))
  w9 = dict(baseline)
  w9["W"] = RandomModel((0.9, 0.1))
  z5 = dict(baseline)
  z5["Z"] = DiscreteModel(("X"), {(0,): (0.9, 0.1), (1,): (0.5, 0.5)})
  reversed_z = dict(baseline)
  reversed_z["Z"] = DiscreteModel(("X"), {(0,): (0.25, 0.75), (1,): (0.75, 0.25)})
  reversed_y = dict(baseline)
  reversed_y["Y"] = DiscreteModel(("W", "Z"), {(0, 0): (0, 1), (0, 1): (1, 0), (1, 0): (1, 0), (1, 1): (1, 0)})

  # Policy.DEAF, Policy.NAIVE,
  # Policy.DEAF, Policy.SENSITIVE,
  pol = Policy.ADJUST
  eps = 0.03
  # dnc = 0.03
  sn = 10
  start = time.time()
  for dnc in [0.04, 0.05, 0.06, 0.07, 0.08]:
    agents = [
        Agent("00", Environment(baseline), pol, eps, dnc, sn),
        Agent("01", Environment(baseline), pol, eps, dnc, sn),
        Agent("02", Environment(reversed_z), pol, eps, dnc, sn),
        Agent("03", Environment(reversed_z), pol, eps, dnc, sn)
    ]
    sim = Sim(World(agents), 240, 20)
    sim.multithreaded_sim(Result.CUM_REGRET, lbl=dnc)
  time = time.time() - start
  mins = time // 60
  sec = time % 60
  print("Time elapsed = {0}:{1}".format(int(mins), sec))
  plt.show()
  # plt.savefig("../output/0705-{}agent-{}ep-{}n".format(len(agents), sim.num_episodes, sim.num_trials * mp.cpu_count()))