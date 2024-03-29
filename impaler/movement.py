import time

from rlbot.agents.base_agent import SimpleControllerState

from maneuvers.dodge import DodgeManeuver
from maneuvers.recovery import RecoveryManeuver
from util import rendering
from util.rldata import Field, Ball, is_near_wall
from predict import ball_predict, next_ball_landing
from util.rlmath import *


class DriveController:
    def __init__(self):
        self.controls = SimpleControllerState()
        self.dodge = None
        self.last_point = None
        self.last_dodge_end_time = 0
        self.dodge_cooldown = 0.26
        self.recovery = None

    def start_dodge(self):
        if self.dodge is None:
            self.dodge = DodgeManeuver(self.last_point)

    def go_towards_point(self, bot, point: Vec3, target_vel=1430, slide=False, boost_min=101, can_keep_speed=True, can_dodge=True, wall_offset_allowed=110) -> SimpleControllerState:
        REQUIRED_ANG_FOR_SLIDE = 1.65
        REQUIRED_VELF_FOR_DODGE = 1100

        car = bot.data.my_car

        # Dodge is finished
        if self.dodge is not None and self.dodge.done:
            self.dodge = None
            self.last_dodge_end_time = bot.data.time

        # Continue dodge
        if self.dodge is not None:
            self.dodge.target = point
            return self.dodge.exec(bot)

        # Begin recovery
        if not car.on_ground:
            bot.maneuver = RecoveryManeuver(bot)
            return self.controls

        # Get down from wall by choosing a point close to ground
        if not is_near_wall(point, wall_offset_allowed) and angle_between(car.up(), Vec3(0, 0, 1)) > math.pi * 0.31:
            point = lerp(xy(car.pos), xy(point), 0.5)

        # If the car is in a goal, avoid goal posts
        self.avoid_goal_post(bot, point)

        car_to_point = point - car.pos

        # The vector from the car to the point in local coordinates:
        # point_local.x: how far in front of my car
        # point_local.y: how far to the left of my car
        # point_local.z: how far above my car
        point_local = dot(point - car.pos, car.rot)

        # Angle to point in local xy plane and other stuff
        angle = math.atan2(point_local.y, point_local.x)
        dist = norm(point_local)
        vel_f = proj_onto_size(car.vel, car.forward())
        vel_towards_point = proj_onto_size(car.vel, car_to_point)

        # Start dodge
        if can_dodge and abs(angle) <= 0.02 and vel_towards_point > REQUIRED_VELF_FOR_DODGE\
                and dist > vel_towards_point + 500 + 700 and bot.data.time > self.last_dodge_end_time + self.dodge_cooldown:
            self.dodge = DodgeManeuver(point)

        # Is in turn radius deadzone?
        tr = turn_radius(abs(vel_f + 50))  # small bias
        tr_side = sign(angle)
        tr_center_local = Vec3(0, tr * tr_side, 0)
        point_is_in_turn_radius_deadzone = norm(point_local - tr_center_local) < tr
        # Draw turn radius deadzone
        if car.on_ground:
            tr_center_world = car.pos + dot(car.rot, tr_center_local)
            tr_center_world_2 = car.pos + dot(car.rot, -1 * tr_center_local)
            rendering.draw_circle(bot, tr_center_world, car.up(), tr, 22)
            rendering.draw_circle(bot, tr_center_world_2, car.up(), tr, 22)

        if point_is_in_turn_radius_deadzone:
            # Hard turn
            self.controls.steer = sign(angle)
            self.controls.boost = False
            self.controls.throttle = 0 if vel_f > 150 else 0.1
            if point_local.x < 25:
                # Brake or go backwards when the point is really close but not in front of us
                self.controls.throttle = clip((25 - point_local.x) * -.5, 0, -0.6)
                self.controls.steer = 0
                if vel_f > 300:
                    self.controls.handbrake = True

        else:
            # Should drop speed or just keep up the speed?
            if can_keep_speed and target_vel < vel_towards_point:
                target_vel = vel_towards_point
            else:
                # Small lerp adjustment
                target_vel = lerp(vel_towards_point, target_vel, 1.2)

            # Turn and maybe slide
            self.controls.steer = clip(angle + (2.5*angle) ** 3, -1.0, 1.0)
            if slide and abs(angle) > REQUIRED_ANG_FOR_SLIDE:
                self.controls.handbrake = True
                self.controls.steer = sign(angle)
            else:
                self.controls.handbrake = False

            # Overshoot target vel for quick adjustment
            target_vel = lerp(vel_towards_point, target_vel, 1.2)

            # Find appropriate throttle/boost
            if vel_towards_point < target_vel:
                self.controls.throttle = 1
                if boost_min < car.boost and vel_towards_point + 25 < target_vel and target_vel > 1400 \
                        and not self.controls.handbrake and is_heading_towards(angle, dist):
                    self.controls.boost = True
                else:
                    self.controls.boost = False

            else:
                vel_delta = target_vel - vel_towards_point
                self.controls.throttle = clip(0.2 + vel_delta / 500, 0, -1)
                self.controls.boost = False
                if self.controls.handbrake:
                    self.controls.throttle = min(0.4, self.controls.throttle)

        # Saved if something outside calls start_dodge() in the meantime
        self.last_point = point

        return self.controls

    def avoid_goal_post(self, bot, point):
        car = bot.data.my_car
        car_to_point = point - car.pos

        # Car is not in goal, not adjustment needed
        if abs(car.pos.y) < Field.LENGTH / 2:
            return

        # Car can go straight, not adjustment needed
        if car_to_point.x == 0:
            return

        # Do we need to cross a goal post to get to the point?
        goalx = Field.GOAL_WIDTH / 2 - 100
        goaly = Field.LENGTH / 2 - 100
        t = max((goalx - car.pos.x) / car_to_point.x,
                (-goalx - car.pos.x) / car_to_point.x)
        # This is the y coordinate when car would hit a goal wall. Is that inside the goal?
        crossing_goalx_at_y = abs(car.pos.y + t * car_to_point.y)
        if crossing_goalx_at_y > goaly:
            # Adjustment is needed
            point.x = clip(point.x, -goalx, goalx)
            point.y = clip(point.y, -goaly, goaly)

            bot.renderer.draw_line_3d(car.pos, point, bot.renderer.green())


class AimCone:
    def __init__(self, right_most, left_most):
        # Right angle and direction
        if isinstance(right_most, float):
            self.right_ang = fix_ang(right_most)
            self.right_dir = Vec3(math.cos(right_most), math.sin(right_most), 0)
        elif isinstance(right_most, Vec3):
            self.right_ang = math.atan2(right_most.y, right_most.x)
            self.right_dir = normalize(right_most)
        # Left angle and direction
        if isinstance(left_most, float):
            self.left_ang = fix_ang(left_most)
            self.left_dir = Vec3(math.cos(left_most), math.sin(left_most), 0)
        elif isinstance(left_most, Vec3):
            self.left_ang = math.atan2(left_most.y, left_most.x)
            self.left_dir = normalize(left_most)

    def contains_direction(self, direction, span_offset: float=0):
        ang_delta = angle_between(direction, self.get_center_dir())
        return abs(ang_delta) < self.span_size() / 2.0 + span_offset

    def span_size(self):
        if self.right_ang < self.left_ang:
            return math.tau + self.right_ang - self.left_ang
        else:
            return self.right_ang - self.left_ang

    def get_center_ang(self):
        return fix_ang(self.right_ang - self.span_size() / 2)

    def get_center_dir(self):
        ang = self.get_center_ang()
        return Vec3(math.cos(ang), math.sin(ang), 0)

    def get_closest_dir_in_cone(self, direction, span_offset: float=0):
        if self.contains_direction(direction, span_offset):
            return normalize(direction)
        else:
            ang_to_right = abs(angle_between(direction, self.right_dir))
            ang_to_left = abs(angle_between(direction, self.left_dir))
            return self.right_dir if ang_to_right < ang_to_left else self.left_dir

    def get_goto_point(self, bot, src, point):
        point = xy(point)
        desired_dir = self.get_center_dir()

        desired_dir_inv = -1 * desired_dir
        car_pos = xy(src)
        point_to_car = car_pos - point

        ang_to_desired_dir = angle_between(desired_dir_inv, point_to_car)

        ANG_ROUTE_ACCEPTED = math.pi / 4.3
        can_go_straight = abs(ang_to_desired_dir) < self.span_size() / 2.0
        can_with_route = abs(ang_to_desired_dir) < self.span_size() / 2.0 + ANG_ROUTE_ACCEPTED
        point = point + desired_dir_inv * 50
        if can_go_straight:
            return point, 1.0
        elif can_with_route:
            ang_to_right = abs(angle_between(point_to_car, -1 * self.right_dir))
            ang_to_left = abs(angle_between(point_to_car, -1 * self.left_dir))
            closest_dir = self.right_dir if ang_to_right < ang_to_left else self.left_dir

            goto = curve_from_arrival_dir(car_pos, point, closest_dir)

            goto.x = clip(goto.x, -Field.WIDTH / 2, Field.WIDTH / 2)
            goto.y = clip(goto.y, -Field.LENGTH / 2, Field.LENGTH / 2)

            bot.renderer.draw_line_3d(car_pos, goto, bot.renderer.create_color(255, 150, 150, 150))
            bot.renderer.draw_line_3d(point, goto, bot.renderer.create_color(255, 150, 150, 150))

            # Bezier
            rendering.draw_bezier(bot, [car_pos, goto, point])

            return goto, 0.5
        else:
            return None, 1

    def draw(self, bot, center, arm_len=500, arm_count=5, r=255, g=255, b=255):
        renderer = bot.renderer
        ang_step = self.span_size() / (arm_count - 1)

        for i in range(arm_count):
            ang = self.right_ang - ang_step * i
            arm_dir = Vec3(math.cos(ang), math.sin(ang), 0)
            end = center + arm_dir * arm_len
            alpha = 255 if i == 0 or i == arm_count - 1 else 110
            renderer.draw_line_3d(center, end, renderer.create_color(alpha, r, g, b))


def celebrate(bot):
    controls = SimpleControllerState()
    controls.steer = math.sin(time.time() * 13)
    return controls


# ----------------------------------------- Helper functions --------------------------------


def is_heading_towards(ang, dist):
    # The further away the car is the less accurate the angle is required
    required_ang = 0.05 + 0.0001 * dist
    return abs(ang) <= required_ang


def turn_radius(vf):
    if vf == 0:
        return 0
    return 1.0 / turn_curvature(vf)


def turn_curvature(vf):
    if 0.0 <= vf < 500.0:
        return 0.006900 - 5.84e-6 * vf
    elif 500.0 <= vf < 1000.0:
        return 0.005610 - 3.26e-6 * vf
    elif 1000.0 <= vf < 1500.0:
        return 0.004300 - 1.95e-6 * vf
    elif 1500.0 <= vf < 1750.0:
        return 0.003025 - 1.10e-6 * vf
    elif 1750.0 <= vf < 2500.0:
        return 0.001800 - 0.40e-6 * vf
    else:
        return 0.0
