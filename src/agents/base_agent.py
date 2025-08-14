from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def build_prompt(self, data):
        """
        Construct the prompt for this agent.
        :param data: Input data dict with at least a 'description' key.
        """
        raise NotImplementedError