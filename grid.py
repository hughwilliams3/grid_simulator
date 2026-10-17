from dataclasses import dataclass
import random
import math
import numpy as np

@dataclass
class Consumer:
    name: str
    type: str # residential, commercial, industrial
    base_demand: float # average demand for this consumer in kW
    temp_sensitivity: float # float between 0 and 1, 0 being doesn't care about temperature, 1 cares a lot
    noise: float = 0.0 # how volatile this particular consumer is

    def demand(self, temp, time_of_day): 
        mwh_dem = 10*math.cos((math.pi * temp)/50) + self.base_demand
        #print(f"temp_sens = {self.temp_sensitivity}")
        #print(f"temp = {temp}")
        #print(f"base demand = {self.base_demand}")
        return mwh_dem

@dataclass
class Generator:
    name: str
    capacity: float # the maximum power that this plant can produce
    output : float # the amount of power being produced at the current timestep

    def update_output():
        pass

@dataclass
class GasTurbine(Generator):
    fire_time: float # how long does it take to fire up this plant

@dataclass
class Windmill(Generator):
    capacity: float = 15000
    output: float = 0
    def update_output(self, wind_speed): #windspeed goes from 0 to 25, say, in m/s
        self.output = np.piecewise(wind_speed, 
                                   [wind_speed < 5.0, wind_speed >= 5.0 and wind_speed <= 25.0, wind_speed > 25.0],
                                   [0, lambda x:.9*x**3, .9*25**3]
                                   ) # models cut in speed of 5 m/s, maximum around 14,000 kW (14MW)

@dataclass
class Solar(Generator): #say 
    size: int # number of panels
    panel_maximum: int = 400 # default of 400W maximum, but can go up or down
    capacity: float = size * panel_maximum # max output of the array is number of panels * max output of each panel
    output: float = 0

    def update_output(self, cloud_cover, light):
        self.output = light * (cloud_cover * self.panel_maximum)

@dataclass
class Nuclear(Generator):
    pass

rng = random.Random()
## temperature update
def update_temp(current_temp=float, alpha=float, rn = rng.gauss(0,1)): #alpha is the coefficient to determine how fast temp can change
    new_temp = current_temp + alpha * rn # temp goes up or down uniformly randomly 
    return new_temp

## windspeed update
def update_wind(current_wind=float, alpha=float, rn=rng.gauss(0,1)): #alpha is the coefficient to determine how fast temp can change
    new_wind = current_wind + alpha * rn # temp goes up or down uniformly randomly 
    return new_wind

def update_cloud_latent(z, dt, rn=rng.gauss(0,1), theta=1/24, sigma=.9, mu=0.0): # sd above about 2.5 is the goal for correct distribution near 0 and 1
    z += z + theta * (mu - z) * dt + math.sqrt(dt) * sigma * rn
    return z

def cloud_percentage(z):
    return 1 / (1+math.exp(-z))

def update_light(time):
    light = np.piecewise(time,[time< 18 and time > 6], [lambda x: .5 * math.sin((2*math.pi*(x-9))/12) + .5])
    return light



