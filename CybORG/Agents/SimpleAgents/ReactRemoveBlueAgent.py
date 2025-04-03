from typing import Dict, Iterable

from CybORG.Agents.SimpleAgents.LinearAgent import LinearAgent
from CybORG.Shared.Enums import TernaryEnum
from CybORG.Simulator.Actions import Action, Sleep, Monitor, Remove, Restore, InvalidAction, DeployDecoy
from CybORG.Simulator.Actions.ConcreteActions.ControlTraffic import ControlTraffic, BlockTrafficZone, AllowTrafficZone

class ReactRemoveBlueAgent(LinearAgent):

    def __init__(
        self, name: str, print_action_output: bool = True, print_obs_output: bool = False):
        super().__init__(name, print_action_output, print_obs_output)
        self._setup_subnets()
        self.end_episode()

    def end_episode(self):
        """Allows an agent to update its internal state"""
        self.suspected_infected = set()
        self.suspected_under_attack = set()
        self.deceptive_hosts = set()
        self.is_blocked = False

    def set_initial_values(self, action_space, observation):
        self.reverse_ip_map = {v["Interface"][0]["ip_address"]: k for k, v in observation.items() if k not in ("success", "action", "phase")}
        # self.session_map = {v["Interface"][0]["ip_address"]: next(filter(lambda x: x["agent"] == self.name, v["Sessions"]))["session_id"] for v in observation.values() if isinstance(v, dict)}

    def get_action(self, observation, action_space):
        """Returns the next action from the action list, or Sleep."""

        if self.step == 0:
            # self.initial_obs = observation
            self.reverse_ip_map = {v["Interface"][0]["ip_address"]: k for k, v in observation.items() if k not in ("success", "action", "phase")}
            # self.session_map = {v["Interface"][0]["ip_address"]: next(filter(lambda x: x["agent"] == self.name, v["Sessions"]))["session_id"] for v in observation.values() if isinstance(v, dict)}
        elif len(observation.keys()) > 2:
            # Monitor caught something
            # Suspect the sending server to be infected and the receiving server to be under attack
            attackers, compromised = self._get_proc_info(observation)
            self.suspected_infected |= attackers
            self.suspected_under_attack |= compromised
            self.suspected_under_attack -= self.suspected_infected

        self.step += 1
        if observation['success'] == TernaryEnum.IN_PROGRESS:
            return Sleep()

        if self.print_action_output:
            self.last_turn_summary(observation)

        phase = -1

        # Prime directive
        # 1. Block subnets if allowed by spec
        # 2. Restore infected
        # ~~3. Remove attacked, if we can get to them before escalation~~
        # 3. Unblock subnets if forced by spec
        # 4. Setup decoys
        # 5. Zzzzzz...

        action_class = None
        sel = None
        if phase == self.phase_to_block and not self.is_blocked and self.subnet_to_block:
            self.is_blocked = True
            action_class = BlockTrafficZone
            sel = self.subnet_to_block
        elif self.suspected_under_attack:
            sel = self.suspected_under_attack.pop()
            action_class = Remove
        elif self.suspected_infected:
            sel = self.suspected_infected.pop()
            if sel in self.deceptive_hosts:
                self.deceptive_hosts.remove(sel)
            action_class = Restore
        elif phase != self.phase_to_block and self.is_blocked:
            self.is_blocked = False
            action_class = AllowTrafficZone
            sel = self.subnet_to_block
        elif len(self.deceptive_hosts) < len(self.reverse_ip_map):
            sel = (set(self.reverse_ip_map.values()) - self.deceptive_hosts).pop()
            action_class = DeployDecoy
            self.deceptive_hosts.add(sel)

        if sel is not None:
            if isinstance(action_class, ControlTraffic):
                action = action_class(agent=self.name, session=0, from_subnet=self.subnet, to_subnet=sel)
            else:
                action = action_class(agent=self.name, hostname=sel, session=0)
        else:
            action = Sleep()

        return action

    def _get_proc_info(self, obs: dict):
        attackers = set()
        compromised = set()
        for k, v in obs.items():
            if not isinstance(v, dict) or "Processes" not in v:
                continue
            pids = filter(lambda x: "PID" in x and "username" not in x, v["Processes"])
            if next(pids, None) is not None:
                compromised.add(k)
            conns = (x["Connections"][0] for x in v["Processes"] if "Connections" in x)
            # Technically this handles the SSH anomaly, but a better solution would be preferred
            malicious_conns = filter(lambda x: "PID" not in x and len(x) == 4, conns)
            attackers |= {self.reverse_ip_map[x["remote_address"]] for x in malicious_conns}
        return attackers, compromised

    def _setup_subnets(self):
        subnet_ind = int(self.name[-1])
        self.subnet = (
            "restricted_zone_a_subnet",
            "operational_zone_a_subnet",
            "restricted_zone_b_subnet",
            "operational_zone_b_subnet",
            "public_access_zone_subnet"
        )[subnet_ind]
        self.subnet_to_block = (
            "operational_zone_a_subnet", None, "restricted_zone_b_subnet", None, None
        )[subnet_ind]
        self.phase_to_block = (1, 3, 2, 3, 3)[subnet_ind]