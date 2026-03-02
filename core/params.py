from dataclasses import dataclass
from pathlib import Path
import math
import random
from typing import List
from .data_utils import get_data_path, ensure_data_dir


POINT_RADIUS = 3
GRID = 28
FIELD_XA = 190
FIELD_XB = FIELD_XA + 280
FIELD_YA = 84
FIELD_YB = FIELD_YA + 280
ROW_GRID_NUM = (FIELD_YB - FIELD_YA) // GRID
COL_GRID_NUM = (FIELD_XB - FIELD_XA) // GRID
GRID_NUM = ROW_GRID_NUM * COL_GRID_NUM
PLACEMENT_UNIT = (FIELD_XB - FIELD_XA) / 10
DEF_TRANSMISSION_RANGE = 2.0 * PLACEMENT_UNIT
DEF_SENSE_RANGE = DEF_TRANSMISSION_RANGE / 2
DEF_MOBILE_PERCENT = 0.30
DEF_ALLSENSOR_NUM = 60
DEF_SENSORNETWORK = "grid60.txt"
MAX_MOVE_DIST = 5 * PLACEMENT_UNIT
SIGMA = 0.1
PI = 3.1415926
E = 2.7182818
REAL_MAX = 1.7e308
CMAX = 3.10e5
BORDERLENGTH = 0.8 * (FIELD_XB - FIELD_XA)


@dataclass
class Sensor:
    x: int
    y: int
    id: int


@dataclass
class Edge:
    u: int
    v: int
    dist: float


class GlobalState:
    def __init__(self):
        self.transmission_range = DEF_TRANSMISSION_RANGE
        self.sense_range = DEF_SENSE_RANGE
        self.mobile_percent = DEF_MOBILE_PERCENT
        self.random_placed = False
        self.network_random_generated = False
        self.alg_kind = 1
        self.operator_kind = 0
        self.de_population_size = 20
        self.de_cross_prob = DEF_PROBABILITY_CROSSOVER if 'DEF_PROBABILITY_CROSSOVER' in globals() else 0.95
        self.de_factor = DEF_F_FACTOR if 'DEF_F_FACTOR' in globals() else 0.9
        self.de_max_generations = DEF_MAX_GENERATIONS if 'DEF_MAX_GENERATIONS' in globals() else 1000
        self.average_DE_dis = 0.0
        self.average_move_dis = 0.0
        self.optimal_distance = 0.0
        self.nomoving_coverage = 0.0
        self.networkfilename = DEF_SENSORNETWORK
        self.gridcovered = [False] * (GRID_NUM + 1)
        self.initialcovered = [False] * (GRID_NUM + 1)
        self.staticcoveredGrid: List[int] = []
        self.staticcoverednum = 0
        self.coveragerate = 0.0
        self.initialcoverage = 0.0
        self.finalcoverage = 0.0
        self.allsensornum = DEF_ALLSENSOR_NUM
        self.static_num = 0
        self.mobile_num = 0
        self.needmovednum = 0
        self.sensors: List[Sensor] = [Sensor(0, 0, 0) for _ in range(self.allsensornum + 1)]
        self.newmobiles: List[Sensor] = []
        self.mobileneedmoved: List[bool] = []
        self.DEbestmobileposition: List[Sensor] = []
        self.bestmobileposition: List[Sensor] = []
        self.optimalmatch: List[Sensor] = []
        self.initialmobiles: List[Sensor] = []
        self.staticpos: List[int] = []
        self.mobilepos: List[int] = []
        self.ismobile: List[bool] = []
        self.edges: List[List[float]] = []


def _grid_center_x(col: int) -> float:
    return FIELD_XA + col * GRID + 0.5 * GRID


def _grid_center_y(row: int) -> float:
    return FIELD_YA + row * GRID + 0.5 * GRID


def _round_index_min(f: float) -> int:
    frac = f - int(f)
    return int(f) + 1 if frac > 0.5 else int(f)


def _round_index_max(f: float) -> int:
    frac = f - int(f)
    return int(f) + 1 if frac >= 0.5 else int(f)


def construct_real_WSN(state: GlobalState):
    p = Path(state.networkfilename)
    if not p.is_absolute():
        candidate = get_data_path(p.name)
        if candidate.exists():
            p = candidate
    if not p.exists():
        raise FileNotFoundError(str(p))
    lines = p.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
    if not lines:
        raise ValueError("empty network file")
    first = lines[0].strip().split()
    if len(first) == 1 and first[0].isdigit():
        count = int(first[0])
        data_lines = lines[1:]
    else:
        count = len(lines)
        data_lines = lines
    state.allsensornum = count
    state.mobile_num = int(round(state.allsensornum * state.mobile_percent))
    state.static_num = state.allsensornum - state.mobile_num
    state.sensors = [Sensor(0, 0, 0) for _ in range(state.allsensornum + 1)]
    for i in range(1, state.allsensornum + 1):
        parts = data_lines[i - 1].split()
        sid = int(parts[0])
        x = int(parts[1])
        y = int(parts[2])
        state.sensors[i] = Sensor(x, y, sid)
    state.ismobile = [False] * (state.allsensornum + 1)
    state.mobilepos = [0] * (state.mobile_num + 1)
    if state.random_placed:
        for i in range(1, state.mobile_num + 1):
            while True:
                k = random.randint((i - 1) * state.allsensornum // state.mobile_num + 1, i * state.allsensornum // state.mobile_num)
                if not state.ismobile[k]:
                    state.ismobile[k] = True
                    state.mobilepos[i] = k
                    break
    else:
        for i in range(1, state.mobile_num + 1):
            state.mobilepos[i] = state.static_num + i
            state.ismobile[state.static_num + i] = True
    state.staticpos = []
    for i in range(1, state.allsensornum + 1):
        if not state.ismobile[i]:
            state.staticpos.append(i)


def construct_random_distribution_wsn(xmin: int, xmax: int, ymin: int, ymax: int, nodenum: int, state: GlobalState):
    if xmax <= xmin or ymax <= ymin or xmin < 0 or ymin < 0 or nodenum <= 0:
        raise ValueError("invalid parameters")
    state.allsensornum = nodenum
    state.mobile_num = int(round(state.allsensornum * state.mobile_percent))
    state.static_num = state.allsensornum - state.mobile_num
    state.sensors = [Sensor(0, 0, 0) for _ in range(state.allsensornum + 1)]
    for i in range(1, nodenum + 1):
        x = int(xmin + (xmax - xmin) * random.random())
        y = int(ymin + (ymax - ymin) * random.random())
        state.sensors[i] = Sensor(x, y, i)
    state.ismobile = [False] * (state.allsensornum + 1)
    state.mobilepos = [0] * (state.mobile_num + 1)
    for i in range(1, state.mobile_num + 1):
        while True:
            k = random.randint((i - 1) * state.allsensornum // state.mobile_num + 1, i * state.allsensornum // state.mobile_num)
            if not state.ismobile[k]:
                state.ismobile[k] = True
                state.mobilepos[i] = k
                break
    state.staticpos = []
    for i in range(1, state.allsensornum + 1):
        if not state.ismobile[i]:
            state.staticpos.append(i)
    rf = get_data_path("Randomfile.txt")
    with rf.open("w", encoding="utf-8", errors="ignore") as f:
        k = 1
        for i in range(1, state.static_num + 1):
            s = state.sensors[state.staticpos[i - 1]]
            f.write(f"{k:<5d}  {s.x:<5d}  {s.y:<5d}\n")
            k += 1
        for i in range(1, state.mobile_num + 1):
            s = state.sensors[state.mobilepos[i]]
            f.write(f"{k:<5d}  {s.x:<5d}  {s.y:<5d}\n")
            k += 1


def outpput_network_to_file(state: GlobalState):
    p = Path("input.txt")
    with p.open("w", encoding="utf-8", errors="ignore") as f:
        f.write(f"{state.allsensornum}\n")
        for i in range(1, state.allsensornum + 1):
            s = state.sensors[i]
            f.write(f"{s.id:<5d}  {s.x:<5d}  {s.y:<5d}\n")


def SetSingleSensorCoverArea_initial(sen: Sensor, state: GlobalState):
    minx = max(sen.x - state.sense_range, FIELD_XA)
    maxx = min(sen.x + state.sense_range, FIELD_XB)
    miny = max(sen.y - state.sense_range, FIELD_YA)
    maxy = min(sen.y + state.sense_range, FIELD_YB)
    ixf = (minx - FIELD_XA) / GRID
    axf = (maxx - FIELD_XA) / GRID
    iyf = (miny - FIELD_YA) / GRID
    ayf = (maxy - FIELD_YA) / GRID
    ix = _round_index_min(ixf)
    ax = _round_index_max(axf)
    iy = _round_index_min(iyf)
    ay = _round_index_max(ayf)
    for i in range(iy, ay):
        for j in range(ix, ax):
            x = _grid_center_x(j)
            y = _grid_center_y(i)
            dx = x - sen.x
            dy = y - sen.y
            if dx * dx + dy * dy < state.sense_range * state.sense_range:
                k = i * COL_GRID_NUM + j + 1
                if 0 < k <= GRID_NUM:
                    state.initialcovered[k] = True


def SetSingleSensorCoverArea(sen: Sensor, state: GlobalState):
    minx = max(sen.x - state.sense_range, FIELD_XA)
    maxx = min(sen.x + state.sense_range, FIELD_XB)
    miny = max(sen.y - state.sense_range, FIELD_YA)
    maxy = min(sen.y + state.sense_range, FIELD_YB)
    ixf = (minx - FIELD_XA) / GRID
    axf = (maxx - FIELD_XA) / GRID
    iyf = (miny - FIELD_YA) / GRID
    ayf = (maxy - FIELD_YA) / GRID
    ix = _round_index_min(ixf)
    ax = _round_index_max(axf)
    iy = _round_index_min(iyf)
    ay = _round_index_max(ayf)
    for i in range(iy, ay):
        for j in range(ix, ax):
            x = _grid_center_x(j)
            y = _grid_center_y(i)
            dx = x - sen.x
            dy = y - sen.y
            if dx * dx + dy * dy < state.sense_range * state.sense_range:
                k = i * COL_GRID_NUM + j + 1
                if 0 < k <= GRID_NUM:
                    state.gridcovered[k] = True


def compute_coverage(state: GlobalState) -> float:
    c = sum(1 for i in range(1, GRID_NUM + 1) if state.gridcovered[i])
    return c / GRID_NUM


def compute_coverage_initial(state: GlobalState) -> float:
    c = sum(1 for i in range(1, GRID_NUM + 1) if state.initialcovered[i])
    return c / GRID_NUM


def initialize_grid_static_covered(state: GlobalState):
    for i in range(1, GRID_NUM + 1):
        state.gridcovered[i] = False
    for i in range(1, state.staticcoverednum + 1):
        k = state.staticcoveredGrid[i - 1]
        state.gridcovered[k] = True


def compute_static_covered_Grid(state: GlobalState):
    for i in range(1, GRID_NUM + 1):
        state.gridcovered[i] = False
    for i in range(1, state.static_num + 1):
        s = state.sensors[state.staticpos[i - 1]]
        SetSingleSensorCoverArea(s, state)
    state.staticcoverednum = 0
    for i in range(1, GRID_NUM + 1):
        if state.gridcovered[i]:
            state.staticcoverednum += 1
    state.staticcoveredGrid = []
    for i in range(1, GRID_NUM + 1):
        if state.gridcovered[i]:
            state.staticcoveredGrid.append(i)


def compute_coverage_new(mobilepos: List[Sensor], state: GlobalState) -> float:
    initialize_grid_static_covered(state)
    for j in range(1, state.mobile_num + 1):
        SetSingleSensorCoverArea(mobilepos[j], state)
    c = sum(1 for i in range(1, GRID_NUM + 1) if state.gridcovered[i])
    return c / GRID_NUM


def optimal_match(sens: List[Sensor], newpos: List[Sensor], length: int) -> List[Sensor]:
    originmatched = [False] * (length + 1)
    newmatched = [False] * (length + 1)
    edges = []
    for i in range(1, length + 1):
        for j in range(1, length + 1):
            dx = sens[i].x - newpos[j].x
            dy = sens[i].y - newpos[j].y
            edges.append(Edge(i, j, math.sqrt(dx * dx + dy * dy)))
    edges.sort(key=lambda e: e.dist)
    matches = [Sensor(0, 0, 0) for _ in range(length + 1)]
    i = 0
    selected = 0
    while selected < length and i < len(edges):
        e = edges[i]
        if not originmatched[e.u] and not newmatched[e.v]:
            matches[e.u] = Sensor(newpos[e.v].x, newpos[e.v].y, newpos[e.v].id)
            originmatched[e.u] = True
            newmatched[e.v] = True
            selected += 1
        i += 1
    return matches
