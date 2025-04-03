from CybORG.Agents.SimpleAgents.FiniteStateRedAgent import FiniteStateRedAgent


class StealthyFSMAgent(FiniteStateRedAgent):
    def __init__(self, name=None, np_random=None, agent_subnets=None):
        super().__init__(name=name, np_random=np_random, agent_subnets=agent_subnets)

        # Changable variables:
        self.print_action_output = False
        self.print_obs_output = False
        self.prioritise_servers = False

    def state_transitions_probability(self):
        # Create new probability mapping to use
        map = {
            'K'  : [0.5,  0.0,  0.5, None, None, None, None, None, None],
            'KD' : [None, 0.0,  1.0,  None, None, None, None, None, None],
            'S'  : [0.25, None, None, 0.25, 0.5 , None, None, None, None],
            'SD' : [None, None, None, 0.25, 0.75, None, None, None, None],
            'U'  : [0.5 , None, None, None, None, 0.5 , None, None, 0.0 ],
            'UD' : [None, None, None, None, None, 1.0 , None, None, 0.0 ],
            'R'  : [0.5,  None, None, None, None, None, 0.25, 0.25, 0.0 ],
            'RD' : [None, None, None, None, None, None, 0.5,  0.5,  0.0 ],
        }
        return map
