from CybORG.Agents.SimpleAgents.FiniteStateRedAgent import FiniteStateRedAgent


class ImpactFSMAgent(FiniteStateRedAgent):
    def __init__(self, name=None, np_random=None, agent_subnets=None):
        super().__init__(name=name, np_random=np_random, agent_subnets=agent_subnets)

        # Changable variables:
        self.print_action_output = False
        self.print_obs_output = False
        self.prioritise_servers = False

    def set_host_state_priority_list(self):
        """ Abstract function for child classes to overwrite with a host state priority list.
        
        Each dictionary value must be an integer or float from 0 to 100, with the total sum of values equaling 100.

        ??? example 
            ```
            host_state_priority_list = {
                'K':12.5, 'KD':12.5, 
                'S':12.5, 'SD':12.5, 
                'U':12.5, 'UD':12.5, 
                'R':12.5, 'RD':12.5}
            ```

        Returns
        -------
        host_state_priority_list : None
            when used in variant child classes, a dict would be returned.
        """

        host_state_priority_list = {
            'K':40 / 6, 'KD':40 / 6, 
            'S':40 / 6, 'SD':40 / 6, 
            'U':40 / 6, 'UD':40 / 6, 
            'R':30, 'RD':30
        }

        return host_state_priority_list

    def state_transitions_probability(self):
        # Create new probability mapping to use

        map = {
            'K'  : [0.5,  0.25, 0.25, None, None, None, None, None, None],
            'KD' : [None, 0.5,  0.5,  None, None, None, None, None, None],
            'S'  : [0.25, None, None, 0.25, 0.5 , None, None, None, None],
            'SD' : [None, None, None, 0.25, 0.75, None, None, None, None],
            'U'  : [0.5 , None, None, None, None, 0.5 , None, None, 0.0 ],
            'UD' : [None, None, None, None, None, 1.0 , None, None, 0.0 ],
            'R'  : [0.0,  None, None, None, None, None, 1.0, 0.0, 0.0 ],
            'RD' : [None, None, None, None, None, None, 1.0, 0.0, 0.0 ],
        }
        return map
