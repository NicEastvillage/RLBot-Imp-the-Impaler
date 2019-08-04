import time

from rlbot.agents.base_agent import SimpleControllerState

from maneuvers.dodge import DodgeManeuver
from util.rlmath import sign
from util.vec import Vec3, dot, normalize


class DodgeShotManeuver(DodgeManeuver):
    def __init__(self, bot):
        super().__init__(Vec3(y=-5440 * bot.data.team_sign), t_first_jump=0.25, t_first_wait=0.10)

        self._t_release_ball = self._t_second_jump + 0.06

    def exec(self, bot) -> SimpleControllerState:
        ctrl = super().exec(bot)

        ct = time.time() - self._start_time

        if ct >= self._t_release_ball:
            ctrl.use_item = True

        if self._t_second_jump >= ct >= 0:
            # Rotate away from target
            car = bot.data.my_car
            target = Vec3(y=-5440 * bot.data.team_sign)
            ball_to_target = target - bot.data.ball.pos

            target_local = dot(ball_to_target, car.rot)
            target_local.z = 0

            direction = normalize(-target_local)

            ctrl.roll = 0
            ctrl.pitch = -direction.x
            ctrl.yaw = sign(car.rot.get(2, 2)) * direction.y

        return ctrl
