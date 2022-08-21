from abc import ABCMeta, abstractmethod

from pokeai.sim.model import Party


class PartyGenerator(metaclass=ABCMeta):
    @abstractmethod
    def generate(self) -> Party:
        raise NotImplementedError

    @abstractmethod
    def neighbor(self, party: Party) -> Party:
        raise NotImplementedError
