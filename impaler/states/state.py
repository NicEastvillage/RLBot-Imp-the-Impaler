from rlbot.agents.base_agent import SimpleControllerState


class State:
    def __init__(self):
        self.done = False

    def exec(self, bot) -> SimpleControllerState:
        raise NotImplementedError

    def adjust(self, bot):
        pass

    def car_spiking_changed(self, bot):
        self.done = True
