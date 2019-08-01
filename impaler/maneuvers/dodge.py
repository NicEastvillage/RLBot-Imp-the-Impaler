import time

from rlbot.agents.base_agent import SimpleControllerState

from maneuvers.maneuver import Maneuver
from maneuvers.recovery import RecoveryManeuver
from util.rlmath import *


class DodgeManeuver(Maneuver):
    def __init__(self, target=None, boost=False):
        super().__init__()
        
        self.target = target
        self.boost = boost
        self._start_time = time.time()
        self._almost_finished = False

        self._t_first_unjump = 0.10
        self._t_aim = 0.13
        self._t_second_jump = 0.18
        self._t_second_unjump = 0.46
        self._t_finishing = 1.0  # After this, fix orientation until lands on ground

        self._t_steady_again = 0.25  # Time on ground before steady and ready again
        self._max_speed = 2000  # Don't boost if above this speed
        self._boost_ang_req = 0.25

    def execute(self, bot):
        ct = time.time() - self._start_time
        controls = SimpleControllerState()
        controls.throttle = 1

        car = bot.info.my_car

        # Target is allowed to be a function that takes bot as a parameter. Check what it is
        if callable(self.target):
            target = self.target(bot)
        else:
            target = self.target

        # To boost or not to boost, that is the question
        car_to_target = target - car.pos
        vel_p = proj_onto_size(car.vel, car_to_target)
        angle = angle_between(car_to_target, car.forward())
        controls.boost = self.boost and angle < self._boost_ang_req and vel_p < self._max_speed

        # States of dodge (note reversed order)
        # Land on ground
        if ct >= self._t_finishing:
            self._almost_finished = True
            if car.on_ground:
                self.done = True
            else:
                bot.maneuver = RecoveryManeuver(bot)
                self.done = True
            return controls
        elif ct >= self._t_second_unjump:
            # Stop pressing jump and rotate and wait for flip is done
            pass
        elif ct >= self._t_aim:
            if ct >= self._t_second_jump:
                controls.jump = 1

            # Direction, yaw, pitch, roll
            if self.target is None:
                controls.roll = 0
                controls.pitch = -1
                controls.yaw = 0
            else:
                target_local = dot(car_to_target, car.rot)
                target_local.z = 0

                direction = normalize(target_local)

                controls.roll = 0
                controls.pitch = -direction.x
                controls.yaw = sign(car.rot.get(2, 2)) * direction.y

        # Stop pressing jump
        elif ct >= self._t_first_unjump:
            pass

        # First jump
        else:
            controls.jump = 1

        return controls
