from dataclasses import dataclass
import random
import math

@dataclass
class Consumer:
    name: str
    type: str # residential, commercial, industrial
    base_demand: float # average demand for this consumer in kWh
    temp_sensitivity: float # float between 0 and 1, 0 being doesn't care about temperature, 1 cares a lot
    noise: float = 0.0 # how volatile this particular consumer is

    def demand(self, temp, time_of_day): 
        mwh_dem = 10*math.cos((math.pi * temp)/50) + self.base_demand
        #print(f"temp_sens = {self.temp_sensitivity}")
        #print(f"temp = {temp}")
        #print(f"base demand = {self.base_demand}")
        return mwh_dem


## temperature update
def update_temp(current_temp, alpha): #alpha is the coefficient to determine how fast temp can change
    rng = random.Random()
    u = rng.gauss(0,1)
    new_temp = current_temp + alpha * u # temp goes up or down uniformly randomly 
    return new_temp


