# Élodie Millan
# June 2020
# Langevin equation 3D for a free particule close to a rigid wall without inertia and with weight.

import numpy as np
import matplotlib.pyplot as plt
#from OverdampedLangevin3D import Langevin3D
from InertialLangevin3D import InertialLangevin3D


class RigidWallOverdampedLangevin3D(InertialLangevin3D): #, Langevin3D
    def __init__(self, dt, Nt, R, rho, rhoF=1000., eta=0.001, T=300., x0=None):
        """

        :param dt: float - Time step [s].
        :param Nt: int - Number of time points.
        :param R: float - Radius of particule [m].
        :param rho: float - Volumic mass of the particule [kg/m³].
        :param rhoF: float - Volumic mass of the fluid [kg/m³] (DEFAULT = 1000 [kg/m³]).
        :param eta: float - Fluid viscosity (DEFAULT = 0.001 [Pa/s]).
        :param T: float - Temperature (DEFAULT = 300 [k]).
        :param x0: array float - Initial position of particule (DEFAULT = (0,0,R) [m]).
        """
        if x0 == None:
            x0 = (0., 0., R)
        super().__init__(dt, Nt, R, rho, eta=eta, T=T, x0=x0)
        self.rhoF = rhoF
        self.lD = 70e-9 # Debay length
        self.g = 9.81  # m/s²
        self.m = rho * (4 / 3) * np.pi * R ** 3
        self.delta_m = (4 / 3) * np.pi * self.R ** 3 * (self.rho - self.rhoF)
        self.lB = (self.kb * self.T) / (self.delta_m * self.g) # Boltzmann length

    def _gamma_xy(self, zi_1):
        """
        Intern methode of RigidWallInertialLangevin3D class - gamma on x and y at time t-dt.

        :param zi_1: float - Perpendicular position by the wall z at (t - dt).

        :return: gamma_x = gamma_y = 6πη(z)R : the gamma value for x and y trajectories dependant of z(t-dt).
        """
        self.gamma_xy = (
            6
            * np.pi
            * self.R
            * self.eta
            * (
                1
                - ((9 * self.R) / (16 * (zi_1 + self.R)))
                + (self.R / (8 * (zi_1 + self.R))) ** 3
                - (45 * self.R / (256 * (zi_1 + self.R))) ** 4
                - (self.R / (16 * (zi_1 + self.R))) ** 5
            )
            ** (-1)
        )
        # print("gamma_xy = ", self.gamma_xy)
        return self.gamma_xy

    def _gamma_z(self, zi_1):
        """
        Intern methode of RigidWallInertialLangevin3D class - gamma on z at time t-dt.

        :param zi_1: float - Perpendicular position by the wall z at (t - dt).

        :return: float - gamma_z = 6πη(z)R : the gamma value for z trajectory dependant of z(t-dt).
        """
        # Padé formula
        self.gamma_z = (
            6
            * np.pi
            * self.R
            * self.eta
            * ((
               (6 * zi_1 ** 2 + 2 * self.R * zi_1)
               / (6 * zi_1 ** 2 + 9 * self.R * zi_1 + 2 * self.R ** 2)
            )
            ** (-1))
        )

        # print("gamma_z = ", self.gamma_z)
        return self.gamma_z

    def _a(self, gamma):
        """
        Intern methode of RigidWallInertialLangevin3D class - white noise a = sqrt(k T gamma) at t-dt.

        :param zi_1: float - Perpendicular position by the wall z at (t - dt).
        :param gamma: the gamma value used (depends of the coordinate used).

        :return: The white noise a at the position z(t-dt) for a gamma value on x/y or z.
        """
        import warnings
        warnings.simplefilter("error")
        # print("gamma = ", gamma)
        try :
            a = np.sqrt(2 * self.kb * self.T / gamma)
        except RuntimeWarning:
            print("gamma =", gamma)


        return a

    def _PositionXi(self, xi_1, zi_1, rng, axis=None):
        """
        Intern methode of InertialLangevin3D class - Position of a Brownian particule inertial with rigid wall, at time t.

        :param xi_1: float - Position of the particule at (t - dt).
        :param xi_2: float - Position of the particule at (t - 2dt).
        :param zi_1: float - Perpendicular position by the wall z at (t - dt).
        :param rng: a random number for dBt/dt white noise.
        :param axis: The axis used : put "z"
        :return:
        :param xi1: Position of the particule at (t - dt).
        :param xi2: Position of the particule at (t - 2dt).


        :return: The position of the particule at time t.
        """

        if axis == "z":
            gamma = self._gamma_z
            weight = (self.delta_m / gamma(zi_1)) * self.g * self.dt
            elec = self.lD * (4*self.kb*self.T) * np.exp(- zi_1 / self.lD) / gamma(zi_1) * self.dt

            # print(self.delta_m)
        else:
            gamma = self._gamma_xy
            elec = 0
            weight = 0

        xi = (xi_1 - weight + elec + gamma(zi_1) * rng * self.dt)

        if axis == "z":
            if xi < 10e-9:
                xi =  10e-9

        return xi

    def trajectory(self, output=False):

        rngx = (1 / np.sqrt(self.dt)) * np.random.default_rng().normal(
            0.0, 1, size=self.Nt
        )
        rngy = (1 / np.sqrt(self.dt)) * np.random.default_rng().normal(
            0.0, 1, size=self.Nt
        )
        rngz = (1 / np.sqrt(self.dt)) * np.random.default_rng().normal(
            0.0, 1, size=self.Nt
        )

        x = np.zeros(self.Nt)
        y = np.zeros(self.Nt)
        z = np.zeros(self.Nt)

        # First values of trajectory compute with initial value.
        x[0] = self.x0[0]
        y[0] = self.x0[1]
        z[0] = self.x0[2]

        for i in range(1, self.Nt):
            x[i] = self._PositionXi(x[i - 1], z[i - 1], rngx[i])
            y[i] = self._PositionXi(y[i - 1], z[i - 1], rngy[i])
            z[i] = self._PositionXi(z[i - 1], z[i - 1], rngz[i], "z")

        self.x = x
        self.y = y
        self.z = z

        if output:
            return self.x, self.y, self.z


if __name__ == "__main__":
    langevin3D = RigidWallOverdampedLangevin3D(dt=1/60, Nt=100000, R=1.5e-6, rho=1050, x0=(0., 0., 1.e-6))

    langevin3D.trajectory()
    #langevin3D.plotTrajectory()

    MSDx = langevin3D.MSD1D("x", output=True)
    MSDy = langevin3D.MSD1D("y", output=True)
    MSDz = langevin3D.MSD1D("z", output=True)

    # ----- MSD 1D -----

    fig1 = plt.figure()
    plt.loglog(
        langevin3D.t[langevin3D.list_dt_MSD],
        MSDx,
        color="red",
        linewidth=0.8,
        label="MSDx inertial",
    )
    plt.loglog(
        langevin3D.t[langevin3D.list_dt_MSD] ,
        MSDy,
        color="green",
        linewidth=0.8,
        label="MSDy inertial",
    )
    plt.loglog(
        langevin3D.t[langevin3D.list_dt_MSD] ,
        MSDz,
        color="blue",
        linewidth=0.8,
        label="MSDz inertial",
    )
    plt.plot(
        langevin3D.t[langevin3D.list_dt_MSD] ,
        (2 * langevin3D.kb * langevin3D.T / langevin3D.gamma)
        * langevin3D.t[langevin3D.list_dt_MSD],
        color="black",
        linewidth=0.8,
        label="Non inertial theory : x = 2D t",
    )
    plt.xlabel("Times t/$ \tau $ [s]")
    plt.ylabel("MSD 1D [m²]")
    plt.title("Mean square displacement 1D")
    plt.legend()
    plt.show()

    plt.plot(langevin3D.t, langevin3D.z * 1e6)
    plt.show()