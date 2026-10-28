import asyncio
from pyscript import document
from grid import build_grid, step

canvas = document.getElementById("grid")
ctx = canvas.getContext("2d")

state = build_grid()

def draw_edges(state, w, h):
    for edge in state.graph.edges(data = True):
        u = edge[0]
        v = edge[1]
        G = state.graph
        ctx.beginPath()
        ctx.moveTo(G.nodes[u]['x'])

def draw_nodes(state, w, h):
    pass

def draw_labels(state, w, h):
    pass

def draw(state):
    rect = canvas.getBoundingClientRect()
    canvas.width = int(rect.width)
    canvas.height = int(rect.height)
    w, h = canvas.width, canvas.height
    draw_edges(state, w, h)
    draw_nodes(state, w, h)
    draw_labels(state, w, h)

async def run():
    while True:
        step(state)
        draw(state)
        await asyncio.sleep(0.1)

run()