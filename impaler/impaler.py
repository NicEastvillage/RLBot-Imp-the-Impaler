import random
from typing import Optional

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket

from maneuvers.maneuver import Maneuver
from movement import celebrate, DriveController
from states.atba import AtbaState, GoToPointState
from states.state import State
from util.rendering import draw_ball_path, Vec3
from util.rldata import GameInfo


class ImpalerBot(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.data: GameInfo = None
        self.state: Optional[State] = None
        self.maneuver: Optional[Maneuver] = None
        self.doing_kickoff = False

        self.drive = DriveController()

    def initialize_agent(self):
        self.data = GameInfo(self.index, self.team)

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:

        # Read packet
        if not self.data.field_info_loaded:
            self.data.read_field_info(self.get_field_info())
            if not self.data.field_info_loaded:
                return SimpleControllerState()
        self.data.read_packet(packet)

        # Check if match is over
        if packet.game_info.is_match_ended:
            return celebrate(self)

        self.renderer.begin_rendering()

        # This is where the logic happens
        ctrl = self.use_brain()

        # Additional rendering
        draw_ball_path(self, 4, 5)
        car_pos = self.data.my_car.pos
        self.renderer.draw_string_3d(car_pos, 1, 1, self.state.__class__.__name__, self.renderer.team_color(alt_color=True))
        if self.data.car_spiking_ball is not None:
            self.renderer.draw_rect_3d(self.data.car_spiking_ball.pos + Vec3(z=20), 30, 30, True, self.renderer.purple())
        self.renderer.end_rendering()

        # Save some stuff for next frame
        self.feedback(ctrl)

        return ctrl

    def use_brain(self) -> SimpleControllerState:
        # Check kickoff
        if self.data.is_kickoff and not self.doing_kickoff:
            self.state = AtbaState(boost_min=True)  # TODO choose_kickoff_plan(self)
            self.doing_kickoff = True
            self.greet()

        # Car who is spiking the ball has changed. Let current state and maneuver know
        if self.data.car_spiking_changed:
            if self.state is not None:
                self.state.car_spiking_changed(self)
            if self.maneuver is not None:
                self.maneuver.car_spiking_changed(self)

        # Maneuvers have first priority. If we are not in the middle of a maneuver, execute current state instead
        if self.maneuver is not None:
            if self.maneuver.done:
                self.maneuver = None
            else:
                return self.maneuver.exec(self)

        # Choose state if we have none
        if self.state is None or self.state.done:
            self.doing_kickoff = False

            # Pick state based on who is currently spiking the ball
            if self.data.car_spiking_ball is None:
                self.state = AtbaState(target_vel=1900, boost_min=25)

            elif self.data.car_spiking_ball == self.data.my_car:
                self.state = GoToPointState(target=Vec3(y=-5500 * self.data.team_sign), can_dodge=False)

            elif self.data.car_spiking_ball in self.data.teammates:
                self.state = AtbaState()

            else:
                self.state = AtbaState(target_vel=2300, boost_min=0)

        return self.state.exec(self)

    def print(self, s):
        team_name = "[BLUE]" if self.team == 0 else "[ORANGE]"
        print("Imp", self.index, team_name, ":", s)

    def greet(self):
        self.print(random.choice([
            "I'll be your doom!",
            "PAAAIN, GAH.",
            "ARHG, OKAY THEN.",
            "Hehehe, this will be fun.",
            "For the master!",
            "Do you know how I got this name?",
            "As you wish, master.",
            "Huh, GAAAAHRH.",
            "What? It's just spikes.",
            "It's not a phase, mom!"
        ]))

    def feedback(self, ctrl):
        self.data.my_car.last_input.roll = ctrl.roll
        self.data.my_car.last_input.pitch = ctrl.pitch
        self.data.my_car.last_input.yaw = ctrl.yaw
        self.data.my_car.last_input.boost = ctrl.boost
