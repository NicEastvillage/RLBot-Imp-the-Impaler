from rlbot.agents.base_agent import SimpleControllerState

from maneuvers.dodgeshot import DodgeShotManeuver
from states.atba import GoToPointState
from states.state import State
from util.rlmath import proj_onto_size
from util.vec import Vec3, norm


class IHaveBallState(State):
    def __init__(self, bot):
        super().__init__()
        self.go_towards_goal = GoToPointState(target=Vec3(y=-5600 * bot.data.team_sign), can_dodge=False)

    def exec(self, bot) -> SimpleControllerState:

        car = bot.data.my_car
        target_goal = Vec3(y=-5600 * bot.data.team_sign)
        vel_prj_to_goal = proj_onto_size(car.vel, target_goal - car.pos)

        enemy, enemy_dist = bot.data.closest_enemy(bot.data.ball.pos)

        if car.on_ground and enemy_dist < 1100 and vel_prj_to_goal > 1230 and norm(target_goal - car.pos) > 1500:
            bot.maneuver = DodgeShotManeuver(bot)

        # Default to just going straight
        return self.go_towards_goal.exec(bot)
