from dataclasses import dataclass, field
import random
import math
import networkx as nx

@dataclass
class Consumer:
    name: str
    type: str # residential, commercial, industrial, etc
    base_demand: float # average demand for this consumer in kW
    temp_sens: float # float between 0 and 1, 0 temp doesn't affect much, 1 is a lot 
    time_sens: float # how much does the demand change depending on time of day, as maximum amount added at peak of day
    noise: float = 0.0 # how volatile this particular consumer is
    demand: float = field(init=False, default=0.0)


    def update_demand(self, temp, time, rn): 
        time_based_dem = self.time_sens * (math.sin(2*math.pi*(time-6)/24)+1)
        if temp > 30 or temp < 0:
            temp_dem = 20
        else:
            temp_dem = self.temp_sens * (max(0, 15 - temp) + max(0, temp - 22))
        dem =  temp_dem + time_based_dem + self.base_demand + self.noise*rn
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
    output: float = 0

@dataclass
class Gas(Generator):
    size: int = 3
    turbine_max: int = 400
    capacity: float = field(init=False)

    def __post_init__(self):
        self.capacity = self.size * self.turbine_max
        super().__post_init__()

### Energy Transportation

@dataclass
class Transformer():
    name: str
    power_in: float = 0 # set by the sum of the 
    efficiency: float = .97 # how much of the original wattage is preserved when converting

    @property
    def power_out(self):
        return self.power_in * self.efficiency

@dataclass
class PowerLine():
    name: str
    origin: Generator | Transformer
    destination: Consumer | Transformer
    length: float # in km
    type: str = "hvdc" # either high voltage dc (hvdc) or ac
    power_in: float = 0 # set by the output of the generator at origin
    loss: float = field(init=False)

    def __post_init__(self):
        if self.type == "hvdc":
            self.loss = .0035 * self.length ## this is mega simplifies, I just don't understand it well enough yet, but this is a decent sim benchmark
        else:
            self.loss = .05 * self.length

    def power_out(self):
        return max(0, self.power_in - self.loss)


##### Ornstein Uhlenbeck processes for updating weather conditions
## temperature update
def update_temp_z(z, dt, rn, light, theta=1/12, sigma=.25, mu=0.0): 
    mu = (light - .5) # temp behavior is different if it is night or day, mu is negative if less than 50% light, positive if more than 50% light
    z = z + theta * (mu - z) * dt + math.sqrt(dt) * sigma * rn
    return z

def get_temp(z,max=30): # default is max temperature of 30 celsius
    return max * (1 / (1+math.exp(-z)))

## windspeed update
def update_wind_z(z, dt, rn, theta=1/24, sigma = .5, mu = -1): # this sigma vs theta gives a roughly uniform distribution, 
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
        self.assets = list
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

def build_graph(state, nodes, positions): # nodes is a list of consumer or generator objects, coords is a list of tuples
    for obj in nodes:
        x, y = positions[obj.name]
        add_asset(state.graph, obj, x, y)
    for u,v in zip(state.graph.nodes, state.graph.nodes):
        state.graph.add_edge(u,v)


def step(state = SimState):
    # update time
    state.time = (state.time + state.dt)
    # update weather
    state.cloud_z = update_cloud_z(state.cloud_z, state.dt, state.rng.gauss(0,1))
    state.temp_z = update_temp_z(state.temp_z, state.dt, state.rng.gauss(0,1), state.light)
    state.wind_z = update_wind_z(state.wind_z, state.dt, state.rng.gauss(0,1))
    # update demand
    for ast in assets:
        if isinstance(ast, Consumer):
            print(ast.name)
            print(ast.demand)
            ast.update_demand(get_temp(state.temp_z), state.time, state.rng.gauss(0,1))
            print(ast.demand)


### Testing ground
# define the nodes and their coordinates
#consumers
town1 = Consumer("town1", "residential", 5000, .5, 1, 10)
town2 = Consumer("town2", "residential", 12000, .5, 1, 10)
factory1 = Consumer("factory1", "residential", 10000, .5, 1, 10)
#generators
mill1 = Windfarm("mill1")
array1 = Solar("array1")
nuke1 = Nuclear("nuke1")
gas1 = Gas("gas1")


# transmission
transformer1 = Transformer("transformer1")
hvdc1 = PowerLine("hvdc1", mill1, transformer1, 200)

assets = [mill1, array1, town1, factory1, town2, nuke1, gas1, transformer1, hvdc1]

state = SimState() #initialize state
state.assets = assets

positions = {
    "mill1": (1,1),
    "array1": (2,2),
    "town1": (3,3),
    "factory1": (4,4),
    "town2": (5,5)
}

#print(f"before: {state.graph}")

#build_graph(state, assets, positions) # build the graph

#print(f"after: {state.graph}")


for t in range(1000): # run some simulation steps
  
    # state update
    step(state)
    print(f"state {t}:")
    print(f"time (hours): {state.time}")
    #print(f"temp: {get_temp(state.temp_z)}")
    print(f"windspeed: {get_wind_speed(state.wind_z)}")
    #print(f"light: {state.light}")
    #print(f"cloud cover: {get_cloud_percentage(state.cloud_z)}")

    # renewables react to weather
    mill1.update_output(get_wind_speed(state.wind_z))
    print(f"mill1 output: {mill1.output}")
    hvdc1.power_in = mill1.output
    transformer1.power_in = hvdc1.power_out()
    print(f"hvdc1 input from mill1: {hvdc1.power_in}")
    print(f"hvdc1 power out to transformer1: {hvdc1.power_out()}")
    print(f"transformer1 power in from hvdc1: {transformer1.power_in}")
    print(f"tranformer1 power out: {transformer1.power_out}")

    #array1.update_output(get_cloud_percentage(state.cloud_z), state.light)
    #print(f"array1 output: {array1.output}")

    # consumer demand
    #town1.update_demand(get_temp(state.temp_z), state.time, state.rng.gauss(0,1))
    #print(f"town1 demand: {town1.demand}")

    

    print("")

