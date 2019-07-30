import math
from dataclasses import dataclass, field

from rlbot.agents.base_agent import SimpleControllerState

from states.state import State
from util.rlmath import clip
from util.vec import Vec3


@dataclass
class GoToPointState(State):

    target: Vec3 = Vec3()

    def exec(self, bot) -> SimpleControllerState:

        car_pos = Vec3(bot.data.my_car.pos)

        car_to_target = self.target - car_pos
        car_forward = bot.data.my_car.forward()
        ang = self.find_correction(car_forward, car_to_target)

        turn = -clip(ang + 3 * ang ** 3, -1, 1)

        return SimpleControllerState(
            throttle=1.0,
            steer=turn
        )

    def adjust(self, bot):
        pass

    @staticmethod
    def find_correction(current: Vec3, ideal: Vec3) -> float:
        # Finds the angle from current to ideal vector in the xy-plane. Angle will be between -pi and +pi.

        # The in-game axes are left handed, so use -x
        current_in_radians = math.atan2(current.y, -current.x)
        ideal_in_radians = math.atan2(ideal.y, -ideal.x)

        diff = ideal_in_radians - current_in_radians

        # Make sure that diff is between -pi and +pi.
        if abs(diff) > math.pi:
            if diff < 0:
                diff += 2 * math.pi
            else:
                diff -= 2 * math.pi

        return diff


@dataclass
class AtbaState(GoToPointState):
    def adjust(self, bot):
        self.target = bot.data.ball.pos
