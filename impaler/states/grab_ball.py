from rlbot.agents.base_agent import SimpleControllerState

from predict import next_ball_landing
from states.atba import GoToPointState
from util.vec import norm


class GrabBallState(GoToPointState):
    def __init__(self):
        super().__init__(allow_slide=True, boost_min=20)

    def exec(self, bot) -> SimpleControllerState:

        car = bot.data.my_car
        ball = bot.data.ball

        land_event = next_ball_landing(bot)

        if land_event.happens:
            ball_at_landing = land_event.data["obj"]

            dist = norm(car.pos - ball_at_landing.pos)

            self.target = ball_at_landing.pos
            self.target_vel = dist / land_event.time

        else:
            self.target = ball.pos
            self.target_vel = 1400

        return super().exec(bot)
