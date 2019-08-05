from rlbot.agents.base_agent import SimpleControllerState

from predict import next_ball_landing
from states.atba import GoToPointState
from util.rlmath import lerp
from util.vec import norm, Vec3


class GrabBallState(GoToPointState):
    def __init__(self):
        super().__init__(allow_slide=True, boost_min=20)

    def exec(self, bot) -> SimpleControllerState:

        car = bot.data.my_car
        ball = bot.data.ball
        teammate = None
        if len(bot.data.teammates) > 0:
            teammate = bot.data.teammates[0]

        if teammate is not None:
            my_dist = norm(car.pos - ball.pos)
            teammate_dist = norm(teammate.pos - ball.pos)

            if my_dist < teammate_dist:
                return self.go_for_ball(bot)
            else:
                return self.approach_defensively(bot)

        else:
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

    def approach_defensively(self, bot) -> SimpleControllerState:
        car = bot.data.my_car
        ball = bot.data.ball
        goal = Vec3(y=5400 * bot.data.team_sign)

        self.target = lerp(ball.pos, goal, 0.8)
        self.target_vel = norm(self.target - car.pos)

        return super().exec(bot)

    def go_for_ball(self, bot) -> SimpleControllerState:
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
