"""
Defines the absolute top-level behavior of the project. This is the python file to be run from the command line.
Simulation parameters can be set where a Sim object is created and called.
"""
import os
from enum import Enum
import shutil
from causal_tools.assignment_models import ActionModel, DiscreteModel, RandomModel
from agent.environment import Environment
import plotly.graph_objs as go
import time
from numpy.random import randint, default_rng
import multiprocessing as mp
from pandas import DataFrame, ExcelWriter
from json import dump
from causal_tools.enums import OTP, ASR
from process import Process
from itertools import combinations_with_replacement
from pgmpy.factors.discrete import TabularCPD

class Sim:
    def __init__(self, environment_dict, otp, tau, asr, T, mc_sims, EG_epsilon=0, EF_rand_trials=0, ED_cooling_rate=0, is_community=False, rand_envs=False, node_mutation_chance=0, show=True, save=False, seed=None, cpds=[]):
        asr = tuple(tuple(e) for e in asr) if isinstance(
            asr, combinations_with_replacement) else asr
        self.start_time = time.time()
        self.rand_envs = rand_envs
        self.nmc = node_mutation_chance
        self.environment = Environment(environment_dict, cpds=cpds)
        self.num_agents = 1
        self.assignments = self.get_assignments(
            otp, tau, asr, EG_epsilon, EF_rand_trials, ED_cooling_rate)
        self.ind_var = self.get_ind_var()
        self.T = T
        self.mc_sims = mc_sims
        self.num_processes = mp.cpu_count()
        self.seed = randint(0, 2**31 - (1 + self.num_processes)
                            ) if seed is None else seed
        self.ass_perms = self.get_assignment_permutations()
        self.is_community = is_community
        self.show = show
        self.save = save
        self.data_cpr = {}
        self.data_poa = {}
        self.last_episode_cpr = DataFrame()
        self.last_episode_poa = DataFrame()
        self.values = self.get_values(locals())
        self.domains = self.environment.get_domains()
        self.act_var = self.environment.get_act_var()
        self.rew_var = self.environment.get_rew_var()

    def get_assignments(self, otp, tau, asr, EG_epsilon, EF_rand_trials, ED_cooling_rate):
        assignments = {
            "otp": otp,
            "tau": tau,
            "asr": asr,
            "epsilon": EG_epsilon,
            "rand_trials": EF_rand_trials,
            "cooling_rate": ED_cooling_rate,
        }
        if isinstance(asr, (tuple, list)):
            if isinstance(asr[0], (tuple, list)):
                if any(ASR.EG in combo for combo in asr):
                    del assignments['epsilon']
                if any(ASR.EF in combo for combo in asr):
                    del assignments['rand_trials']
                if any(ASR.ED in combo for combo in asr):
                    del assignments['cooling_rate']
                return assignments
            if ASR.EG not in asr:
                del assignments["epsilon"]
            if ASR.EF not in asr:
                del assignments["rand_trials"]
            if ASR.ED not in asr:
                del assignments["cooling_rate"]
            return assignments
        if asr != ASR.EG:
            del assignments["epsilon"]
        if asr != ASR.EF:
            del assignments["rand_trials"]
        if asr != ASR.ED:
            del assignments["cooling_rate"]
        return assignments

    def multithreaded_sim(self):
        jobs = []
        results = mp.Manager().list([None] * self.num_processes)
        proc = Process(**self.process_args(0))
        results[0] = proc.simulate()
        # for i in range(self.num_processes):
        #     job = mp.Process(target=self.sim_process, args=(results, i))
        #     jobs.append(job)
        #     job.start()
        # [job.join() for job in jobs]
        return results

    def process_args(self, index):
        return {
            'rng': default_rng(self.seed + index),
            'environment': self.environment,
            'rew_var': self.rew_var,
            'is_community': self.is_community,
            'nmc': self.nmc,
            'ind_var': self.ind_var,
            'mc_sims': self.mc_sims,
            'T': self.T,
            'ass_perms': self.ass_perms,
            'num_agents': self.num_agents,
            'rand_envs': self.rand_envs,
            'domains': self.domains,
            'act_var': self.act_var,
        }

    def sim_process(self, results, index):
        proc = Process(**self.process_args(index))
        results[index] = proc.simulate()

    def combine_results(self, process_results):
        results = [{}, {}]
        for pr in process_results:
            for i in range(len(results)):
                for ind_var, res in pr[i].items():
                    if ind_var not in results[i]:
                        results[i][ind_var] = res
                        continue
                    results[i][ind_var].extend(res)
        return results

    def get_ind_var(self):
        ind_var = None
        for var, assignment in self.assignments.items():
            if isinstance(assignment, (list, tuple, set)):
                assert ind_var is None
                ind_var = var
        return ind_var

    def get_assignment_permutations(self):
        if self.ind_var is None:
            return [self.assignments]
        permutations = []
        for ind_var_assignment in self.assignments[self.ind_var]:
            permutation = dict(self.assignments)
            permutation[self.ind_var] = ind_var_assignment
            permutations.append(permutation)
        return permutations

    def get_plot(self, results, plot_title, yaxis_title):
        figure = []
        x = list(range(self.T))
        line_dashes = ['solid', 'dot', 'dash', 'dashdot']
        if yaxis_title == "Cumulative Pseudo Regret":
            line_width = 4.5
            legend = dict(yanchor='top', y=0.99, xanchor='left', x=0.01)
        else:
            line_width = 2.5
            legend = dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99)
        for i, ind_var in enumerate(sorted(results)):
            line_name = str(ind_var)
            line_hue = str(int(360 * (i / len(results))))
            line_dash = line_dashes[i] if len(results) <= 4 else 'solid'
            df = DataFrame(results[ind_var])
            if yaxis_title == "Cumulative Pseudo Regret":
                self.last_episode_cpr.insert(0, line_name, df.iloc[:, -1])
                self.data_cpr[ind_var] = df
            else:
                self.last_episode_poa.insert(0, line_name, df.iloc[:, -1])
                self.data_poa[ind_var] = df
            y = df.mean(axis=0, numeric_only=True)
            sem = df.sem(axis=0, numeric_only=True)
            y_upper = y + sem
            y_lower = y - sem
            line_color = "hsla(" + line_hue + ",100%,40%,1)"
            error_band_color = "hsla(" + line_hue + ",100%,40%,0.125)"
            figure.extend([
                go.Scatter(
                    name=line_name,
                    x=x,
                    y=y,
                    line=dict(color=line_color,
                              width=line_width, dash=line_dash),
                    mode='lines',
                ),
                go.Scatter(
                    name=line_name+"-upper",
                    x=x,
                    y=y_upper,
                    mode='lines',
                    marker=dict(color=error_band_color),
                    line=dict(width=0),
                    showlegend=False,
                ),
                go.Scatter(
                    name=line_name+"-lower",
                    x=x,
                    y=y_lower,
                    marker=dict(color=error_band_color),
                    line=dict(width=0),
                    mode='lines',
                    fillcolor=error_band_color,
                    fill='tonexty',
                    showlegend=False,
                )
            ])
        plotly_fig = go.Figure(figure)
        plotly_fig.update_layout(
            font=dict(size=18),
            margin=dict(l=20, r=20, t=20, b=20),
            legend=legend,
            yaxis_title=yaxis_title,
            xaxis_title="Trial",
            # title=plot_title,
        )
        return plotly_fig

    def get_cpr_plot(self, results, desc):
        plot_title = "Community CPR of " + \
            desc if self.is_community else "Mean Agent CPR of " + desc
        return self.get_plot(results, plot_title, "Cumulative Pseudo Regret")

    def get_poa_plot(self, results, desc):
        plot_title = "POA of " + desc
        return self.get_plot(results, plot_title, "Probability of Optimal Action")

    def display_and_save(self, results, desc):
        """
        Taking in a 'results' pandas Dataframe and a description of the results,
        outputs a
        """
        cpr_plot = self.get_cpr_plot(results[0], desc)
        poa_plot = self.get_poa_plot(results[1], desc)
        elapsed_time = time.time() - self.start_time
        print_info = "Time Elapsed: {}h {}m {}s".format(
            int(elapsed_time // (60 * 60)),
            int(elapsed_time // 60 % 60),
            int(elapsed_time % 60)
        )
        print(f'{print_info}{" " * (70 - len(print_info))}')

        if self.show:
            cpr_plot.show()
            poa_plot.show()
        if self.save:
            file_name = "{}_N{}".format(desc, self.get_N())
            dir_path = f"{os.path.dirname(__file__)}/../output/{file_name}"
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
            os.mkdir(dir_path)
            cpr_plot.write_html(dir_path + "/cpr.html")
            poa_plot.write_html(dir_path + "/poa.html")
            self.last_episode_cpr.to_csv(dir_path + "/last_episode_cpr.csv")
            with ExcelWriter(dir_path + '/cpr.xlsx') as writer:  # doctest: +SKIP
                for ind_var, df in self.data_cpr.items():
                    sheet_name = str(ind_var) if ind_var else 'Sheet1'
                    df.to_excel(writer, sheet_name=sheet_name)
            with ExcelWriter(dir_path + '/poa.xlsx') as writer:  # doctest: +SKIP
                for ind_var, df in self.data_poa.items():
                    sheet_name = str(ind_var) if ind_var else 'Sheet1'
                    df.to_excel(writer, sheet_name=sheet_name)
            with open(dir_path + '/values.json', 'w') as outfile:
                dump(self.values, outfile)
            self.environment.bn.draw() # this was cgm

    def run(self, desc=None):
        if desc:
            print(desc)
        print("seed=%d | N=%d" % (self.seed, self.get_N()))
        results = self.combine_results(self.multithreaded_sim())
        self.display_and_save(results, desc)

    def get_N(self):
        return self.num_processes * self.mc_sims * self.num_agents

    def get_values(self, locals):
        values = {key: val for key, val in locals.items() if key != 'self'}
        values["otp"] = values["otp"].value if isinstance(values["otp"], Enum) else [
            e.value for e in values["otp"]]
        values["asr"] = values["asr"].value if isinstance(values["asr"], Enum) else [
            e.value for e in values["asr"]] if isinstance(values["asr"][0], Enum) else [
            [e.value for e in a] for a in values['asr']]
        parsed_env_dicts = []
        env = values["environment_dict"]
        parsed_env = {}
        for node, model in env.items():
            parsed_env[node] = str(model)
        parsed_env_dicts.append(parsed_env)
        values["environment_dict"] = tuple(parsed_env_dicts)
        values["seed"] = self.seed
        return values


if __name__ == "__main__":
    baseline = {
        "Z": RandomModel((0.5, 0.5)),
        "X": ActionModel(("Z"), (0, 1)),
        "W": DiscreteModel(("X"), {(0,): (0.75, 0.25), (1,): (0.25, 0.75)}),
        "Y": DiscreteModel(("Z", "W"), {(0, 0): (0.8, 0.2), (0, 1): (0.5, 0.5), (1, 0): (0.5, 0.5), (1, 1): (0.2, 0.8)})
    }
    cpd_Z = TabularCPD("Z", 2, [[0.5], [0.5]])
    cpd_X = TabularCPD("X", 2, [[0], [1]])
    cpd_W = TabularCPD("W", 2,[[0.75,0.25],[0.25, 0.75]], ["X"], [2])
    cpd_Y = TabularCPD("Y", 2,[[0.8, 0.5, 0.5, 0.2], [0.2, 0.5, 0.5, 0.8]],["Z", "W"],[2,2])
    
    
    cpd_list = [cpd_Z, cpd_X, cpd_W, cpd_Y]
    
    reversed_w = dict(baseline)
    reversed_w["W"] = DiscreteModel(
        ("X"), {(0,): (0.25, 0.75), (1,): (0.75, 0.25)})

    # This is a 'big chain' causal structure'
    # X -> S -> R -> Y
    # baseline = {
    #     "X": ActionModel(None, (0, 1)),
    #     "S": DiscreteModel("X", {(0,): (0.75, 0.25), (1,): (0.25, 0.75)}),
    #     "R": DiscreteModel("S", {(0,): (0.75, 0.25), (1,): (0.25, 0.75)}),
    #     "Y": DiscreteModel("R", {(0,): (0.75, 0.25), (1,): (0.25, 0.75)})
    # }
    # reversed_w = dict(baseline)
    # reversed_w["S"] = DiscreteModel("X", {(0,): (0.25, 0.75), (1,): (0.75, 0.25)})

    experiment = Sim(
        environment_dict=baseline,
        # (baseline, reversed_w, baseline, reversed_w),
        otp=OTP.SOLO,
        asr=ASR.EG,
        T=4,
        mc_sims=8,
        tau=0.05,
        EG_epsilon=100/3000,
        EF_rand_trials=50,
        ED_cooling_rate=0.98,
        is_community=True,
        rand_envs=True,
        node_mutation_chance=(0.2, 0.8),
        show=True,
        save=True,
        seed=420,
        cpds=cpd_list
    )
    experiment.run(desc="0208ASR_community_LETSGO_1")
