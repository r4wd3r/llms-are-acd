"""Stand-in for a module the UCSC release imports but never published.

The original is only used for logging. This version records per-agent action counts so runs can
still be inspected, and accepts any other callback method as a no-op.
"""
from collections import Counter, defaultdict


class MetricsCallback:
    def __init__(self):
        self.steps = 0
        self.actions = defaultdict(Counter)

    def on_step(self, observations=None, actions=None, env=None, *args, **kwargs):
        self.steps += 1
        for agent, action in (actions or {}).items():
            self.actions[agent][type(action).__name__] += 1

    def summary(self):
        return {agent: dict(c) for agent, c in self.actions.items()}

    def __getattr__(self, name):
        if name.startswith('on_'):
            return lambda *a, **k: None
        raise AttributeError(name)
