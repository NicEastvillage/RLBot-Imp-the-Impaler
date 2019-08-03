import math

from rlbot.agents.base_agent import SimpleControllerState

from states.state import State
from util.rlmath import clip
from util.vec import Vec3


class GoToPointState(State):
    def __init__(self,
                 target: Vec3=Vec3(),
                 target_vel: float=1430,
                 allow_slide: bool=False,
                 boost_min: int=101,
                 can_keep_speed: bool=True,
                 can_dodge: bool=True,
                 wall_offset_allowed: float=110):
        super().__init__()
        self.target = target
        self.target_vel = target_vel
        self.allow_slide = allow_slide
        self.boost_min = boost_min
        self.can_keep_speed = can_keep_speed
        self.can_dodge = can_dodge
        self.wall_offset_allowed = wall_offset_allowed

    def exec(self, bot) -> SimpleControllerState:
        return bot.drive.go_towards_point(bot, self.target,
                                          target_vel=self.target_vel,
                                          slide=self.allow_slide,
                                          boost_min=self.boost_min,
                                          can_keep_speed=self.can_keep_speed,
                                          can_dodge=self.can_dodge,
                                          wall_offset_allowed=self.wall_offset_allowed)

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


class AtbaState(GoToPointState):
    def exec(self, bot) -> SimpleControllerState:
        self.target = bot.data.ball.pos
        return super().exec(bot)
