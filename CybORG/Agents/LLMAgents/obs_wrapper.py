import itertools
from typing import Any
from collections import defaultdict

import networkx as nx
import numpy as np
from gymnasium import Space, spaces

from CybORG import CybORG
from CybORG.Agents.Wrappers.BlueFixedActionWrapper import (
    EMPTY_MESSAGE, MESSAGE_LENGTH, NUM_MESSAGES, BlueFixedActionWrapper)
from CybORG.Agents.Wrappers.BlueFlatWrapper import (MAX_HOSTS,
                                                    MAX_SERVER_HOSTS,
                                                    MAX_USER_HOSTS,
                                                    NUM_HQ_SUBNETS,
                                                    NUM_SUBNETS,
                                                    BlueFlatWrapper)
from CybORG.Shared.Enums import TernaryEnum
from CybORG.Simulator.Actions import Action, InvalidAction, Monitor, Sleep, Analyse, Restore, DeployDecoy, Remove
from CybORG.Simulator.Scenarios.EnterpriseScenarioGenerator import SUBNET

from ray.rllib.env.multi_agent_env import MultiAgentEnv

DECOY_POTENTIAL_PORTS = (80, 443, 25)

class StickyStateEntry:
    def __init__(self):
        self.reset()

    def reset(self):
        self.is_attacker = False
        self.mal_connections = 0
        self.mal_processes = 0
        self.analyze_data = 0

    def update_connections(self, mal_connections):
        self.mal_connections = max(self.mal_connections, mal_connections)
        return self.mal_connections

    def update_processes(self, mal_processes):
        self.mal_processes = max(self.mal_processes, mal_processes)
        return self.mal_processes

    def update_analyze(self, analyze_data):
        self.analyze_data = max(self.analyze_data, analyze_data)
        return self.analyze_data

    def update_is_attacker(self, is_attacker):
        if is_attacker:
            self.is_attacker = True
        return self.is_attacker

class BlueObsSpaceWrapper(BlueFlatWrapper):
    def __init__(self, env: CybORG, msg_agents: dict[str, Any], analyze = False, sticky = True, decoys = True, penalize_mask = False, *args, **kwargs):
        self.analyze = analyze
        self.decoys = decoys
        self.sticky = sticky
        self.penalize_mask = penalize_mask
        if sticky:
            self.sticky_state = defaultdict(StickyStateEntry)
        super().__init__(env, *args, **kwargs)
        self.waiting = {a: False for a in self.agents}
        self.crossnet_attackers = set()
        self.msg_agents = msg_agents
        if decoys:
            self.decoy_state = {}

    def reset(self, *args, **kwargs):
        agents = self.agents if self.agents else self.possible_agents
        if self.sticky:
            self.sticky_state = defaultdict(StickyStateEntry)
        observations, info = super().reset(*args, **kwargs)
        self.waiting = {a: False for a in agents}

        if self.decoys:
            self.initial_decoy_state = {}
            state = self.env.environment_controller.state
            for a in agents:
                hosts = filter(lambda y: "router" not in y and y in state.hosts, self.hosts(a))
                for h in hosts:
                    self.initial_decoy_state[h] = len(tuple(filter(state.hosts[h].is_using_port, DECOY_POTENTIAL_PORTS))) + 1
            self.decoy_state = self.initial_decoy_state.copy()
        return observations, info

    def _get_init_obs_spaces(self):
        """Calculates the size of the largest observation space for each agent."""
        # phase, waiting, messages
        observation_space_components = [3, 2] + (NUM_MESSAGES * MESSAGE_LENGTH) * [2]

        subnet_subvector_components = (
            NUM_SUBNETS * [2] # subnet id
            + NUM_SUBNETS * [2] # blocked subnets
            + NUM_SUBNETS * [2] # comms policy
            + MAX_HOSTS * [4] # malicious events
            + MAX_HOSTS * [2] # malicious processes
            + MAX_HOSTS * [2] # launched attack
            + (MAX_HOSTS * [5] if self.analyze else []) # analyze results
            + (MAX_HOSTS * [5] if self.decoys else []) # decoys count, max 3, + -1 for invalid host
        )

        short_observation_components = (
            observation_space_components + subnet_subvector_components
        )

        long_observation_components = (
            observation_space_components + (NUM_HQ_SUBNETS * subnet_subvector_components)
        )

        short_observation_space = spaces.MultiDiscrete(short_observation_components)
        long_observation_space = spaces.MultiDiscrete(long_observation_components)

        self._observation_space = {
            agent: long_observation_space
            if self.is_padded or agent == "blue_agent_4"
            else short_observation_space
            for agent in self.agents
        }

        return short_observation_space, long_observation_space

    def observation_change(self, agent_name: str, observation: dict) -> np.ndarray:
        """Converts an observation dictionary to a vector of fixed size and ordering.

        Parameters
        ----------
        agent_name : str
            Agent corresponding to the observation.
        observation : dict 
            Observation to convert to a fixed vector.

        Returns
        -------
        output : np.ndarray
        """
        state = self.env.environment_controller.state

        # Mission Phase
        mission_phase = state.mission_phase
        # Invert mission phase if we are managing operation/restricted zone B
        # This theoretically allows for agents 0 and 2 and agents 1 and 3 to share the same model
        # Agent 4 (3 subnet) still needs to know the correct mission phase
        if mission_phase > 0 and 2 <= int(agent_name[-1]) <= 3:
            mission_phase = mission_phase ^ 0x3

        # Useful (sorted) information
        sorted_subnet_name_to_cidr = sorted(state.subnet_name_to_cidr.items())
        subnet_names, subnet_cidrs = zip(*sorted_subnet_name_to_cidr)
        subnet_names = [name.lower() for name in subnet_names]
        hosts = lambda x: filter(lambda y: y.startswith(x) and "router" not in y, self.hosts(agent_name))
        conn_info, proc_info, attackers = self._get_proc_info(observation)
        file_info = self._get_file_info(observation) if self.analyze else None

        subnet_info = []
        for subnet in self.subnets(agent_name):
            # One-hot encoded subnet vector
            subnet_subvector = [subnet == name for name in subnet_names]

            # Get blocklist
            cidr = state.subnet_name_to_cidr[subnet]
            blocked_subnets = state.blocks.get(cidr, [])
            blocked_subvector = [s in blocked_subnets for s in subnet_cidrs]

            # Comms
            comms_policy = self.comms_policies[state.mission_phase]
            comms_matrix = nx.to_numpy_array(comms_policy, nodelist=subnet_names)
            comms_policy_subvector = list(comms_matrix[subnet_names.index(subnet)])
            self.policy[agent_name] = comms_policy

            # Process malware events for users, then servers
            subnet_hosts = tuple(hosts(subnet))

            # XOR with 3 so that connections with two (or more) ports and connections with 1 port get swapped
            # so that the numbers increase with severity/likelyhood of actual attack
            mal_event_subvector = (conn_info.get(h, 3) ^ 3 for h in subnet_hosts)
            proc_event_subvector = (int(h in proc_info) for h in subnet_hosts)

            local_attackers = set(map(state.ip_addresses.get, filter(lambda x: x in cidr, attackers)))
            is_attacker_subvector = ((h in local_attackers) for h in subnet_hosts)
            analyze_subvector = (file_info.get(h, 0) for h in subnet_hosts) if self.analyze else tuple()
            # Decoys can be on ports 80, 443, or 25, but only if we aren't already using them
            # At the start, keep count of which of these 3 ports is used, incr on deploy, reset on restore
            # Set 0 if server not valid this episode because apparently spaces.MultiDiscrete can't handle negative numbers
            decoys_subvector = (self.decoy_state.get(h, 0) for h in subnet_hosts) if self.decoys else tuple()

            if self.sticky:
                mal_event_subvector = map(lambda x: self.sticky_state[x[0]].update_connections(x[1]), zip(subnet_hosts, mal_event_subvector))
                proc_event_subvector = map(lambda x: self.sticky_state[x[0]].update_processes(x[1]), zip(subnet_hosts, proc_event_subvector))
                is_attacker_subvector = map(lambda x: self.sticky_state[x[0]].update_is_attacker(x[1]), zip(subnet_hosts, is_attacker_subvector))
                if self.analyze:
                    analyze_subvector = map(lambda x: self.sticky_state[x[0]].update_analyze(x[1]), zip(subnet_hosts, analyze_subvector))

            # subnet_info.append((subnet, blocked_subnets, {x[0]: x[1:] for x in zip(subnet_hosts, mal_event_subvector, proc_event_subvector, is_attacker_subvector, decoys_subvector) if x[-1] >= 0}))

            subnet_info.extend(
                itertools.chain(
                    subnet_subvector,
                    blocked_subvector,
                    comms_policy_subvector,
                    mal_event_subvector,
                    proc_event_subvector,
                    is_attacker_subvector,
                    analyze_subvector,
                    decoys_subvector
                )
            )

        # Messages from other agents
        # This assumes CybORG provides a consistent ordering.
        messages = observation.get("message", [EMPTY_MESSAGE] * NUM_MESSAGES)
        assert len(messages) == NUM_MESSAGES
        # If we manage zone B, change message order
        # For both zones, we want the order to be:
        # XO/R, YR, YO, HQ, where our zone is X and the other is Y
        # For 2 and 3, the default order is YR, YO, XO/R, HQ
        # So we right rotate 0-2
        # TODO wait this doesn't reorder the bits
        if 2 <= int(agent_name[-1]) <= 3:
            temp = messages[2]
            messages[2] = messages[1]
            messages[1] = messages[0]
            messages[0] = temp

        message_subvector = np.concatenate(messages, dtype=np.int32)
        assert len(message_subvector) == NUM_MESSAGES * MESSAGE_LENGTH

        output = np.array(subnet_info, dtype=np.int32)
        self.waiting[agent_name] = observation["success"] == TernaryEnum.IN_PROGRESS
        output = np.concatenate(((mission_phase, self.waiting[agent_name]), message_subvector, output), dtype=np.int32)

        # Apply padding as required
        if self.is_padded:
            output = np.pad(
                output, (0, self._long_obs_space.shape[0] - output.shape[0])
            )

        return output

    def _get_proc_info(self, obs: dict):
        data = {}
        procs = set()
        attackers = set()
        for k, v in obs.items():
            if not isinstance(v, dict) or "Processes" not in v:
                continue
            pids = filter(lambda x: "PID" in x and "username" not in x, v["Processes"])
            if next(pids, None) is not None:
                procs.add(k)
            conns = (x["Connections"][0] for x in v["Processes"] if "Connections" in x and "PID" not in x)
            # Technically this handles the SSH anomaly, but a better solution would be preferred
            malicious_conns = tuple(filter(lambda x: len(x) == 4, conns))
            if malicious_conns:
                attackers |= set(map(lambda x: x["remote_address"], malicious_conns))
                malicious_conns = len(set(map(lambda x: x["local_port"], malicious_conns)))
                data[k] = min(malicious_conns, 2)
        return data, procs, attackers

    def _get_file_info(self, obs: dict):
        data = {}
        for k, v in obs.items():
            if not isinstance(v, dict) or "Files" not in v:
                continue
            files = filter(lambda x: "Density" in x, v["Files"])
            densities = list(sorted(map(lambda x: x["Density"], files), reverse=True))
            if densities and densities[0] > 0.5:
                data[k] = int((densities[0] - 0.5) * 10)
        return data

    def step(self,
        actions: dict[str, int | Action] = None,
        messages: dict[str, Any] = None,
        **kwargs,
    ) -> tuple[
        dict[str, np.ndarray],
        dict[str, float],
        dict[str, bool],
        dict[str, bool],
        dict[str, dict],
    ]:
        if actions is not None:
            for k, v in actions.items():
                if self.waiting[k]:
                    continue
                if not isinstance(v, Action):
                    v = self._action_space[k]["actions"][v]
                if self.decoys and isinstance(v, DeployDecoy) and 0 < self.decoy_state[v.hostname] < 4:
                    self.decoy_state[v.hostname] += 1
                elif isinstance(v, Restore):
                    if self.decoys:
                        self.decoy_state[v.hostname] = self.initial_decoy_state[v.hostname]
                    if self.sticky:
                        self.sticky_state[v.hostname].reset()
                # TODO: we probably shouldn't reset on analyse... right?
                elif self.sticky and isinstance(v, Remove): # or isinstance(v, Analyze)):
                    self.sticky_state[v.hostname].reset()
        if messages is None and self.msg_agents:
            state = self.env.environment_controller.state
            messages = {
                a: v.create_comm_message(a, self.unwrapped.get_observation(a),
                    lambda x: state.hostname_subnet_map.get(
                        state.ip_addresses.get(x, "")
                        , SUBNET.INTERNET))
                for a, v in self.msg_agents.items()
            }
        return super().step(actions, messages, **kwargs)

    def _populate_action_space(self, agent_name: str):
        super()._populate_action_space(agent_name)
        if not self.analyze:
            space = self._action_space[agent_name]
            for i, x in enumerate(space["actions"]):
                if isinstance(x, Analyse):
                    space["mask"][i] = False
                    space["actions"][i] = Sleep()
        if self.penalize_mask:
            for i, x in enumerate(space["mask"]):
                if not x:
                    space["actions"][i] = InvalidAction(error = space["labels"])

class EnterpriseObsWrapper(BlueObsSpaceWrapper, MultiAgentEnv):
    def step(self, actions = {}, messages = None):
        # Use EnterpriseMAE parameter handling
        if "actions" in actions:
            # Messages keyword is ignored if action_dict specifies messages.
            messages = actions.get("messages", messages)
            actions = actions["actions"]

        # Use CybORG parameters
        obs, rew, terminated, truncated, info = super().step(
            actions=actions, messages=messages
        )
        terminated["__all__"] = False
        truncated["__all__"] = self.env.environment_controller.determine_done()
        return obs, rew, terminated, truncated, info

    def reset(self, agent=None, seed=None, *args, **kwargs):
        return super().reset(agent=agent, seed=seed)
