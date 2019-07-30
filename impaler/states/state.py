from dataclasses import dataclass

from rlbot.agents.base_agent import SimpleControllerState


@dataclass
class State:
    done: bool = False

    def exec(self, bot) -> SimpleControllerState:
        raise NotImplementedError

    def adjust(self, bot):
        pass
