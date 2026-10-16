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

    def update():
        pass

@dataclass
class GasTurbine(Generator):
    fire_time: float # how long does it take to fire up this plant

@dataclass
class Windmill(Generator):
    capacity: float = 15000
    output: float = 0
    def update(self, wind_speed): #windspeed goes from 0 to 25, say, in m/s
        self.output = np.piecewise(wind_speed, 
                                   [wind_speed < 5.0, wind_speed >= 5.0 and wind_speed <= 25.0, wind_speed > 25.0],
                                   [0, lambda x:.9*x**3, .9*25**3]
                                   ) # models cut in speed of 5 m/s, maximum around 14,000 kW (14MW)

@dataclass
class Solar(Generator):
    pass

@dataclass
class Nuclear(Generator):
    pass


## temperature update
def update_temp(current_temp, alpha): #alpha is the coefficient to determine how fast temp can change
    rng = random.Random()
    u = rng.gauss(0,1)
    new_temp = current_temp + alpha * u # temp goes up or down uniformly randomly 
    return new_temp

