from maneuvers.aerialturn import AerialTurnManeuver
from util.rldata import Car
from util.vec import normalize, xy, Vec3, cross, Mat33


class RecoveryManeuver(AerialTurnManeuver):
    def __init__(self, bot):
        super().__init__(RecoveryManeuver.find_landing_orientation(bot.data.my_car, 200))

    def car_spiking_changed(self, bot):
        self.done = True

    @staticmethod
    def find_landing_orientation(car: Car, num_points: int) -> Mat33:
        """
        dummy = DummyObject(car)
        trajectory = [Vec3(dummy.pos)]

        for i in range(0, num_points):
            fall(dummy, 0.0333)  # Apply physics and let car fall through the air
            trajectory.append(Vec3(dummy.pos))
            up = dummy.pitch_surface_normal()
            if norm(up) > 0.0 and i > 10:
                up = normalize(up)
                forward = normalize(dummy.vel - dot(dummy.vel, up) * up)
                left = cross(up, forward)

                return Mat33.from_columns(forward, left, up)

        return Mat33(car.rot)
        """

        forward = normalize(xy(car.vel))
        up = Vec3(z=1)
        left = cross(up, forward)

        return Mat33.from_columns(forward, left, up)
