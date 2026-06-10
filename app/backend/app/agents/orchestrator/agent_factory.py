"""Agent factory — creates agent instances by type."""
from typing import Dict


class AgentFactory:
    """Factory that maps agent_type strings to agent callables/classes."""

    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, agent_type: str, agent_cls):
        """Register an agent class/callable for a given type."""
        cls._registry[agent_type] = agent_cls

    @classmethod
    def create(cls, agent_type: str, config: Dict | None = None):
        """Create an agent instance by type. Returns the callable directly.
        
        If config is provided, it's stored for the scheduler to pass as kwargs.
        """
        if agent_type not in cls._registry:
            raise ValueError(
                f"Unknown agent type: {agent_type}. "
                f"Available: {list(cls._registry.keys())}"
            )
        agent = cls._registry[agent_type]
        if config:
            # Return a lambda that injects config when called
            return lambda **kw: agent(**{**config, **kw})
        return agent
