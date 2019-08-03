from rlbot.agents.base_agent import SimpleControllerState

from states.atba import GoToPointState
from util.vec import Vec3, norm


class FallBackState(GoToPointState):
    def __init__(self, bot):
        super().__init__(Vec3(y=4700 * bot.data.team_sign))

    def exec(self, bot) -> SimpleControllerState:
        dist = norm(bot.data.my_car.pos - self.target)
        self.target_vel = dist
        self.done = dist < 200
        return super().exec(bot)
