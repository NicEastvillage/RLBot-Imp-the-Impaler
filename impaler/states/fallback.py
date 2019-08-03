from rlbot.agents.base_agent import SimpleControllerState

from states.atba import GoToPointState
from util.vec import Vec3, norm


class FallBackState(GoToPointState):
    def __init__(self, bot):
        super().__init__(Vec3(y=4500 * bot.data.team_sign))

    def exec(self, bot) -> SimpleControllerState:
        dist = norm(bot.data.my_car.pos - self.target)
        self.target_vel = dist
        self.done = dist < 200
        self.target.x = bot.data.ball.pos.x / 2
        return super().exec(bot)
