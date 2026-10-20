from dataclasses import dataclass, field
import random
import math
import networkx as nx

@dataclass
class Consumer:
    name: str
    type: str # residential, commercial, industrial
    base_demand: float # average demand for this consumer in kW
    temp_sens: float # float between 0 and 1, 0 temp doesn't affect much, 1 is a lot 
    time_sens: float # how much does the demand change depending on time of day, as maximum amount added at peak of day
    noise: float = 0.0 # how volatile this particular consumer is


    def update_demand(self, temp, time, rn): 
        time_based_dem = self.time_sens * (math.sin(math.pi*(time-6))+1)
        if temp > 30 or temp < 30:
            temp_dem = 20
        else:
            temp_dem = self.temp_sens*((temp - 15)**2)
        dem =  temp_dem + time_based_dem + self.base_demand + self.noise*rn
        #print(f"temp_sens = {self.temp_sensitivity}")
        #print(f"temp = {temp}")
        #print(f"base demand = {self.base_demand}")
        self.demand = dem

@dataclass
class Generator:
    name: str
    capacity: float # the maximum power that this plant can produce

    def __post_init__(self):
        self._output = 0.0

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self,value):
        self._output = max(0,min(value,self.capacity))

    def update_output():
        pass

@dataclass
class GasTurbine(Generator):
    fire_time: float # how long does it take to fire up this plant

@dataclass
class Windfarm(Generator):
    size: int = 10 # num of mills in the farm
    mill_max = 15 # MW
    capacity: float = field(init=False)

    def __post_init__(self):
        self.capacity = self.size * self.mill_max
        super().__post_init__()

    def update_output(self, wind_speed): #windspeed goes from 0 to 25, say, in m/s, before cut out
        cut_in, rated, cut_out = 5.0, 15, 25
        if wind_speed < cut_in or wind_speed >= cut_out:
            frac = 0.0
        elif wind_speed>cut_in and wind_speed < cut_out:
            frac = (wind_speed / rated) ** 3
        else:
            frac = 1.0
        self.output = self.capacity * frac

@dataclass
class Solar(Generator): #say 
    size: int = 10 # number of panels
    panel_maximum: int = 400 # default of 400MW maximum, but can go up or down
    capacity: float = field(init=False)

    def __post_init__(self):
        self.capacity = self.size * self.panel_maximum
        super().__post_init__()
    
    def update_output(self, cloud_cover, light):
        self.output = light * (1-cloud_cover) * self.capacity

@dataclass
class Nuclear(Generator):
    capacity: float = 16600 #MW

### Energy Transportation

@dataclass
class PowerLine():
    name: str
    kind: str = "hvdc" # either high voltage dc (hvdc) or ac
    length: float # in km
    loss: float = field(init=False)

    def __post_init__(self):
        if self.kind == "hvdc":
            self.loss = .0035 * self.length
        else:
            self.loss = .05 * self.length

    

    


##### Ornstein Uhlenbeck processes for updating weather conditions
## temperature update
def update_temp_z(z, dt, rn, light, theta=1/12, sigma=.25, mu=0.0): 
    mu = (light - .5) # temp behavior is different if it is night or day, mu is negative if less than 50% light, positive if more than 50% light
    z = z + theta * (mu - z) * dt + math.sqrt(dt) * sigma * rn
    return z

def get_temp(z,max=30): # default is max temperature of 30 celsius
    return max * (1 / (1+math.exp(-z)))

## windspeed update
def update_wind_z(z, dt, rn, theta=1/24, sigma = .5, mu = 0.0): # this sigma vs theta gives a roughly uniform distribution, 
    z = z + theta * (mu - z) * dt + math.sqrt(dt) * sigma * rn
    return z

def get_wind_speed(z, max = 25): #default is max windspeed of 25 m/s
    return max * (1 / (1+math.exp(-z)))

## Cloud cover update
def update_cloud_z(z, dt, rn, theta=1/24, sigma=.9, mu=0.0): # sd above about 2.5 is the goal for correct distribution near 0 and 1
    z = z + theta * (mu - z) * dt + math.sqrt(dt) * sigma * rn
    return z

def get_cloud_percentage(z):
    return 1 / (1+math.exp(-z))

## get light
def get_light(time):
    if time < 18 and time > 6:
        light = .5 * math.sin((2*math.pi*(time-9))/12) + .5
    else:
        light = 0.0
    return light



### SIMULATION LOGIC
class SimState:
    def __init__(self, seed = 42):
        self.rng = random.Random(seed)
        self.time = 0 # in hours, total elapsed
        self.dt = .25 # in hours
        self.cloud_z = 0.0
        self.wind_z = 0.0 
        self.temp_z = 0.0 
        self.graph = nx.Graph()

    @property
    def hour(self):
        return self.time % 24

    @property
    def light(self):
        return get_light(self.hour)


def add_asset(graph, obj, x, y): #graph = state.graph, obj is a consumer or producer, x,y are coordinates
    graph.add_node(obj.name, obj=obj, x=x, y=y)
    return obj

def build_graph(state, nodes, coords): # nodes is a list of consumer or generator objects, coords is a list of tuples
    for obj, (x,y) in zip(nodes, coords):
        add_asset(state.graph, obj, x, y)
    for u,v in zip(state.graph.nodes, state.graph.nodes):
        state.graph.add_edge(u,v)


def step(state = SimState):
    state.time = (state.time + state.dt)
    state.cloud_z = update_cloud_z(state.cloud_z, state.dt, state.rng.gauss(0,1))
    state.temp_z = update_temp_z(state.temp_z, state.dt, state.rng.gauss(0,1), state.light)
    state.wind_z = update_wind_z(state.wind_z, state.dt, state.rng.gauss(0,1))


### Testing ground
# define the nodes and their coordinates
town1 = Consumer("town1", "residential", 50, .5, 1, 10)
factory1 = Consumer("factory1", "residential", 100, .5, 1, 10)

mill1 = Windfarm("mill1")
array1 = Solar("array1")

coordinates = [(1,1), (2,2), (3,3), (4,4)]
nodes = [mill1, array1, town1, factory1]

state = SimState() #initialize state

print(f"before: {state.graph}")

build_graph(state, nodes, coordinates) # build the graph

print(f"after: {state.graph}")

"""
for t in range(100): # run some simulation steps
  
    # state update
    step(state)
    print(f"state {t}:")
    print(f"time (hours): {state.time}")
    print(f"temp: {get_temp(state.temp_z)}")
    print(f"windspeed: {get_wind_speed(state.wind_z)}")
    print(f"light: {state.light}")
    print(f"cloud cover: {get_cloud_percentage(state.cloud_z)}")

    # renewables react to weather
    mill1.update_output(get_wind_speed(state.wind_z))
    print(f"mill1 output: {mill1.output}")

    array1.update_output(get_cloud_percentage(state.cloud_z), state.light)
    print(f"array1 output: {array1.output}")

    # consumer demand
    town1.update_demand(get_temp(state.temp_z), state.time, state.rng.gauss(0,1))
    print(f"town1 demand: {town1.demand}")

    

    print("")

"""