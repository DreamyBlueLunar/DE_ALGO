import math
import random
import time
from pathlib import Path
from typing import List
from .params import (
    GlobalState,
    Sensor,
    FIELD_XA,
    FIELD_XB,
    FIELD_YA,
    FIELD_YB,
    PLACEMENT_UNIT,
    DEF_TRANSMISSION_RANGE,
    DEF_SENSE_RANGE,
    DEF_ALLSENSOR_NUM,
    DEF_MOBILE_PERCENT,
    GRID_NUM,
    MAX_MOVE_DIST,
    compute_coverage,
    compute_coverage_initial,
    compute_static_covered_Grid,
    initialize_grid_static_covered,
    SetSingleSensorCoverArea,
    SetSingleSensorCoverArea_initial,
)


DEF_CHROMOSOME_NUM = 10
DEF_F_FACTOR = 0.9
DEF_PROBABILITY_CROSSOVER = 0.95
DEF_PROBABILITY_MUTATE = 0.85
DEF_MAX_GENERATIONS = 1000
DEF_TAO1 = 0.1
DEF_TAO2 = 0.1
COV_DIST_CONSTANT = 100
cov_times = 1000
BEST_MUTATE_NUM = 10


class ConvergenceStatus:
    def __init__(self):
        self.spenttime = 0.0
        self.convergence_generation = 0
        self.convergence_index = 1
        self.max_fitness = 0.0
        self.best_gene: List[int] = []


class DEAlgorithm:
    def __init__(self, state: GlobalState):
        self.state = state
        self.CHROMOSOME_NUM = DEF_CHROMOSOME_NUM
        self.CHROMOSOME_LEN = 0
        self.F_FACTOR = DEF_F_FACTOR
        self.Probability_Crossover = DEF_PROBABILITY_CROSSOVER
        self.Probability_Mutate = DEF_PROBABILITY_MUTATE
        self.Max_Generations = DEF_MAX_GENERATIONS
        self.convergence = ConvergenceStatus()
        self.generation = 1
        self.chromosomes: List[List[int]] = []
        self.offspring: List[List[int]] = []
        self.eval_results: List[float] = []
        self.offspring_results: List[float] = []
        self.ideal_length = 0.0
        self.F_Factor_JDE: List[float] = []
        self.Probability_Crossover_JDE: List[float] = []
        self.tao1 = DEF_TAO1
        self.tao2 = DEF_TAO2
        self.operator_kind = 0
        self.alg_kind = 1
        self.output_file = None
        self.coords_file = None

    def _randrange(self, a: int, b: int) -> int:
        return random.randrange(a, b)

    def _random_real(self) -> float:
        return random.random()

    def _allocate_arrays(self):
        self.state.sensors = [Sensor(0, 0, 0) for _ in range(self.state.allsensornum + 1)]
        self.state.newmobiles = [Sensor(0, 0, 0) for _ in range(self.state.mobile_num + 1)]
        self.state.staticpos = [0 for _ in range(self.state.static_num + 1)]
        self.state.mobilepos = [0 for _ in range(self.state.mobile_num + 1)]
        self.state.mobileneedmoved = [True for _ in range(self.state.mobile_num + 1)]
        self.state.bestmobileposition = [Sensor(0, 0, 0) for _ in range(self.state.mobile_num + 1)]
        self.state.DEbestmobileposition = [Sensor(0, 0, 0) for _ in range(self.state.mobile_num + 1)]
        self.state.ismobile = [False for _ in range(self.state.allsensornum + 1)]
        self.eval_results = [0.0 for _ in range(self.CHROMOSOME_NUM + 1)]
        self.state.gridcovered = [False for _ in range(GRID_NUM + 1)]

    def initialize(self):
        self.state.transmission_range = DEF_TRANSMISSION_RANGE
        self.state.sense_range = DEF_SENSE_RANGE
        self.state.mobile_percent = DEF_MOBILE_PERCENT if self.state.mobile_percent is None else self.state.mobile_percent
        self.state.random_placed = False
        self.state.network_random_generated = False
        self.state.allsensornum = DEF_ALLSENSOR_NUM if self.state.allsensornum is None else self.state.allsensornum
        self.CHROMOSOME_NUM = self.state.de_population_size or DEF_CHROMOSOME_NUM
        self.F_FACTOR = self.state.de_factor or DEF_F_FACTOR
        self.Probability_Crossover = self.state.de_cross_prob or DEF_PROBABILITY_CROSSOVER
        self.Probability_Mutate = DEF_PROBABILITY_MUTATE
        self.Max_Generations = self.state.de_max_generations or DEF_MAX_GENERATIONS
        self.tao1 = DEF_TAO1
        self.tao2 = DEF_TAO2
        self.operator_kind = self.state.operator_kind
        self.state.mobile_num = int(round(self.state.allsensornum * self.state.mobile_percent))
        self.state.static_num = self.state.allsensornum - self.state.mobile_num
        self.CHROMOSOME_LEN = 2 * self.state.mobile_num
        self.state.transmission_range = 2.0 * PLACEMENT_UNIT * math.sqrt(60 / self.state.allsensornum)
        self.state.sense_range = self.state.transmission_range / 2.0
        self._allocate_arrays()
        base_dir = Path(__file__).resolve().parent.parent
        (base_dir / "result").mkdir(parents=True, exist_ok=True)
        self.output_file = (base_dir / "result" / "output.txt").open("w", encoding="utf-8", errors="ignore")
        self.coords_file = (base_dir / "result" / "coordinates.txt").open("w", encoding="utf-8", errors="ignore")
        if not self.state.network_random_generated:
            from .params import construct_real_WSN

            construct_real_WSN(self.state)
        else:
            from .params import construct_random_distribution_wsn

            construct_random_distribution_wsn(FIELD_XA, FIELD_XB, FIELD_YA, FIELD_YB, self.state.allsensornum, self.state)
        random.seed()
        self.chromosomes = [[0 for _ in range(2 * self.state.mobile_num + 1)] for _ in range(self.CHROMOSOME_NUM + 1)]
        self.offspring = [[0 for _ in range(2 * self.state.mobile_num + 1)] for _ in range(self.CHROMOSOME_NUM + 1)]
        for i in range(1, self.CHROMOSOME_NUM + 1):
            for j in range(1, 2 * self.state.mobile_num + 1):
                if j % 2 == 1:
                    self.chromosomes[i][j] = self._randrange(FIELD_XA, FIELD_XB + 1)
                else:
                    self.chromosomes[i][j] = self._randrange(FIELD_YA, FIELD_YB + 1)
        self.convergence.best_gene = [0 for _ in range(2 * self.state.mobile_num + 1)]
        self.convergence.max_fitness = 0.0
        self.convergence.convergence_index = 1
        self.generation = 1
        self.ideal_length = math.sqrt((FIELD_XB - FIELD_XA) * (FIELD_YB - FIELD_YA) / (self.state.mobile_num + self.state.static_num))
        if self.alg_kind == 2:
            self.F_Factor_JDE = [DEF_F_FACTOR for _ in range(self.CHROMOSOME_NUM + 1)]
            self.Probability_Crossover_JDE = [DEF_PROBABILITY_CROSSOVER for _ in range(self.CHROMOSOME_NUM + 1)]
        self.state.initialcovered = [False for _ in range(GRID_NUM + 1)]
        for i in range(1, self.state.allsensornum + 1):
            SetSingleSensorCoverArea_initial(self.state.sensors[i], self.state)
        self.state.initialcoverage = compute_coverage_initial(self.state)
        compute_static_covered_Grid(self.state)
        initialize_grid_static_covered(self.state)

    def _update_convergence(self, idx: int, fitness: float, gene: List[int]):
        if fitness > self.convergence.max_fitness:
            self.convergence.convergence_generation = self.generation
            self.convergence.convergence_index = idx
            self.convergence.max_fitness = fitness
            for k in range(1, 2 * self.state.mobile_num + 1):
                self.convergence.best_gene[k] = gene[k]
            self.tick2 = time.perf_counter()

    def evaluate(self, chromosomes: List[List[int]]) -> List[float]:
        results = [0.0 for _ in range(self.CHROMOSOME_NUM + 1)]
        for i in range(1, self.CHROMOSOME_NUM + 1):
            for j in range(1, self.state.mobile_num + 1):
                self.state.newmobiles[j].x = chromosomes[i][2 * j - 1]
                self.state.newmobiles[j].y = chromosomes[i][2 * j]
                self.state.newmobiles[j].id = j
            initialize_grid_static_covered(self.state)
            for j in range(1, self.state.mobile_num + 1):
                SetSingleSensorCoverArea(self.state.newmobiles[j], self.state)
            results[i] = compute_coverage(self.state)
            self._update_convergence(i, results[i], chromosomes[i])
        return results

    def evaluate_coverage_move_distance(self, chromosomes: List[List[int]]) -> List[float]:
        results = [0.0 for _ in range(self.CHROMOSOME_NUM + 1)]
        for i in range(1, self.CHROMOSOME_NUM + 1):
            for j in range(1, self.state.mobile_num + 1):
                self.state.newmobiles[j].x = chromosomes[i][2 * j - 1]
                self.state.newmobiles[j].y = chromosomes[i][2 * j]
                self.state.newmobiles[j].id = j
            initialize_grid_static_covered(self.state)
            for j in range(1, self.state.mobile_num + 1):
                SetSingleSensorCoverArea(self.state.newmobiles[j], self.state)
            temp_coverage = compute_coverage(self.state)
            aver_dist = 0.0
            for k in range(1, self.state.mobile_num + 1):
                dx = self.state.sensors[self.state.mobilepos[k]].x - self.state.newmobiles[k].x
                dy = self.state.sensors[self.state.mobilepos[k]].y - self.state.newmobiles[k].y
                aver_dist += math.sqrt(dx * dx + dy * dy)
            aver_dist /= max(1, self.state.mobile_num)
            results[i] = temp_coverage * cov_times / (aver_dist + COV_DIST_CONSTANT)
            self._update_convergence(i, results[i], chromosomes[i])
        return results

    def evaluate_coverage_neighbor_distance(self, chromosomes: List[List[int]]) -> List[float]:
        results = [0.0 for _ in range(self.CHROMOSOME_NUM + 1)]
        for i in range(1, self.CHROMOSOME_NUM + 1):
            for j in range(1, self.state.mobile_num + 1):
                self.state.newmobiles[j].x = chromosomes[i][2 * j - 1]
                self.state.newmobiles[j].y = chromosomes[i][2 * j]
                self.state.newmobiles[j].id = j
            initialize_grid_static_covered(self.state)
            for j in range(1, self.state.mobile_num + 1):
                SetSingleSensorCoverArea(self.state.newmobiles[j], self.state)
            temp_coverage = compute_coverage(self.state)
            sense_dist = 0.0
            for k in range(1, self.state.mobile_num + 1):
                for j in range(1, self.state.allsensornum + 1):
                    if j == k:
                        continue
                    dx = self.state.sensors[self.state.mobilepos[k]].x - self.state.sensors[j].x
                    dy = self.state.sensors[self.state.mobilepos[k]].y - self.state.sensors[j].y
                    d = math.sqrt(dx * dx + dy * dy)
                    if d < self.state.sense_range:
                        sense_dist += abs(d - self.state.sense_range)
            results[i] = temp_coverage * cov_times / (sense_dist + COV_DIST_CONSTANT)
            self._update_convergence(i, results[i], chromosomes[i])
        return results

    def _mutate_rand_1(self, chromosomes: List[List[int]], offspring: List[List[int]]):
        for i in range(1, self.CHROMOSOME_NUM + 1):
            r1 = self._rand_distinct(i, [])
            r2 = self._rand_distinct(i, [r1])
            r3 = self._rand_distinct(i, [r1, r2])
            jrand = self._randrange(1, 2 * self.state.mobile_num + 1)
            for j in range(1, 2 * self.state.mobile_num + 1):
                randreal = self._random_real()
                if randreal < self.Probability_Crossover or j == jrand:
                    offspring[i][j] = chromosomes[r1][j] + int(round(self.F_FACTOR * (chromosomes[r2][j] - chromosomes[r3][j])))
                else:
                    offspring[i][j] = chromosomes[i][j]

    def _mutate_best_1(self, chromosomes: List[List[int]], offspring: List[List[int]]):
        for i in range(1, self.CHROMOSOME_NUM + 1):
            r2 = self._rand_distinct(i, [])
            r3 = self._rand_distinct(i, [r2])
            jrand = self._randrange(1, 2 * self.state.mobile_num + 1)
            for j in range(1, 2 * self.state.mobile_num + 1):
                randreal = self._random_real()
                if randreal < self.Probability_Crossover or j == jrand:
                    offspring[i][j] = self.convergence.best_gene[j] + int(round(self.F_FACTOR * (chromosomes[r2][j] - chromosomes[r3][j])))
                else:
                    offspring[i][j] = chromosomes[i][j]

    def _mutate_rand_2(self, chromosomes: List[List[int]], offspring: List[List[int]]):
        for i in range(1, self.CHROMOSOME_NUM + 1):
            r1 = self._rand_distinct(i, [])
            r2 = self._rand_distinct(i, [r1])
            r3 = self._rand_distinct(i, [r1, r2])
            r4 = self._rand_distinct(i, [r1, r2, r3])
            r5 = self._rand_distinct(i, [r1, r2, r3, r4])
            jrand = self._randrange(1, 2 * self.state.mobile_num + 1)
            for j in range(1, 2 * self.state.mobile_num + 1):
                randreal = self._random_real()
                if randreal < self.Probability_Crossover or j == jrand:
                    offspring[i][j] = chromosomes[r1][j] + int(round(self.F_FACTOR * (chromosomes[r2][j] - chromosomes[r3][j]))) + int(round(self.F_FACTOR * (chromosomes[r4][j] - chromosomes[r5][j])))
                else:
                    offspring[i][j] = chromosomes[i][j]

    def _mutate_current_to_best_1(self, chromosomes: List[List[int]], offspring: List[List[int]]):
        for i in range(1, self.CHROMOSOME_NUM + 1):
            r2 = self._rand_distinct(i, [])
            r3 = self._rand_distinct(i, [r2])
            jrand = self._randrange(1, 2 * self.state.mobile_num + 1)
            for j in range(1, 2 * self.state.mobile_num + 1):
                randreal = self._random_real()
                if randreal < self.Probability_Crossover or j == jrand:
                    offspring[i][j] = chromosomes[i][j] + int(round(self.F_FACTOR * (self.convergence.best_gene[j] - chromosomes[i][j]))) + int(round(self.F_FACTOR * (chromosomes[r2][j] - chromosomes[r3][j])))
                else:
                    offspring[i][j] = chromosomes[i][j]

    def _mutate_rand_to_best_1(self, chromosomes: List[List[int]], offspring: List[List[int]]):
        for i in range(1, self.CHROMOSOME_NUM + 1):
            r1 = self._rand_distinct(i, [])
            r2 = self._rand_distinct(i, [r1])
            r3 = self._rand_distinct(i, [r1, r2])
            jrand = self._randrange(1, 2 * self.state.mobile_num + 1)
            for j in range(1, 2 * self.state.mobile_num + 1):
                randreal = self._random_real()
                if randreal < self.Probability_Crossover or j == jrand:
                    offspring[i][j] = chromosomes[r1][j] + int(round(self.F_FACTOR * (self.convergence.best_gene[j] - chromosomes[r1][j]))) + int(round(self.F_FACTOR * (chromosomes[r2][j] - chromosomes[r3][j])))
                else:
                    offspring[i][j] = chromosomes[i][j]

    def _rand_distinct(self, i: int, taken: List[int]) -> int:
        while True:
            r = self._randrange(1, self.CHROMOSOME_NUM + 1)
            if r != i and r not in taken:
                return r

    def _out_of_bound_random(self, chromosomes: List[List[int]]):
        for i in range(1, self.CHROMOSOME_NUM + 1):
            for j in range(1, self.state.mobile_num + 1):
                x = chromosomes[i][2 * j - 1]
                y = chromosomes[i][2 * j]
                if x > FIELD_XB or x < FIELD_XA:
                    chromosomes[i][2 * j - 1] = self._randrange(FIELD_XA, FIELD_XB + 1)
                if y > FIELD_YB or y < FIELD_YA:
                    chromosomes[i][2 * j] = self._randrange(FIELD_YA, FIELD_YB + 1)

    def run_simple_de(self):
        self.tick1 = time.perf_counter()
        self.initialize()
        while self.generation <= self.Max_Generations:
            self.F_FACTOR = (1 - self.generation / self.Max_Generations) * DEF_F_FACTOR
            if self.operator_kind == 0:
                self._mutate_best_1(self.chromosomes, self.offspring)
            elif self.operator_kind == 1:
                self._mutate_rand_2(self.chromosomes, self.offspring)
            elif self.operator_kind == 2:
                self._mutate_rand_1(self.chromosomes, self.offspring)
            elif self.operator_kind == 3:
                self._mutate_rand_2(self.chromosomes, self.offspring)
            elif self.operator_kind == 4:
                self._mutate_current_to_best_1(self.chromosomes, self.offspring)
            elif self.operator_kind == 5:
                self._mutate_rand_to_best_1(self.chromosomes, self.offspring)
            self._out_of_bound_random(self.offspring)
            self.eval_results = self.evaluate_coverage_move_distance(self.chromosomes)
            self.offspring_results = self.evaluate_coverage_move_distance(self.offspring)
            for i in range(1, self.CHROMOSOME_NUM + 1):
                if self.offspring_results[i] > self.eval_results[i]:
                    for j in range(1, 2 * self.state.mobile_num + 1):
                        self.chromosomes[i][j] = self.offspring[i][j]
            self.generation += 1
        self._finalize_results()

    def run_jde(self):
        self.tick1 = time.perf_counter()
        self.alg_kind = 2
        self.initialize()
        while self.generation <= self.Max_Generations:
            self.F_FACTOR = (1 - self.generation / self.Max_Generations) * DEF_F_FACTOR
            if self.operator_kind == 0:
                self._mutate_best_1(self.chromosomes, self.offspring)
            elif self.operator_kind == 1:
                self._mutate_rand_2(self.chromosomes, self.offspring)
            elif self.operator_kind == 2:
                self._mutate_rand_1(self.chromosomes, self.offspring)
            elif self.operator_kind == 3:
                self._mutate_rand_2(self.chromosomes, self.offspring)
            elif self.operator_kind == 4:
                self._mutate_current_to_best_1(self.chromosomes, self.offspring)
            elif self.operator_kind == 5:
                self._mutate_rand_to_best_1(self.chromosomes, self.offspring)
            self._out_of_bound_random(self.offspring)
            self.eval_results = self.evaluate(self.chromosomes)
            self.offspring_results = self.evaluate(self.offspring)
            for i in range(1, self.CHROMOSOME_NUM + 1):
                if self.offspring_results[i] > self.eval_results[i]:
                    for j in range(1, 2 * self.state.mobile_num + 1):
                        self.chromosomes[i][j] = self.offspring[i][j]
            self.generation += 1
        self._finalize_results()

    def _finalize_results(self):
        self.convergence.spenttime = self.tick2 - self.tick1 if hasattr(self, "tick2") else 0.0
        for j in range(1, self.state.mobile_num + 1):
            self.state.bestmobileposition[j].x = self.convergence.best_gene[2 * j - 1]
            self.state.bestmobileposition[j].y = self.convergence.best_gene[2 * j]
            self.state.bestmobileposition[j].id = self.state.sensors[self.state.mobilepos[j]].id
            self.state.DEbestmobileposition[j].x = self.convergence.best_gene[2 * j - 1]
            self.state.DEbestmobileposition[j].y = self.convergence.best_gene[2 * j]
            self.state.DEbestmobileposition[j].id = self.state.sensors[self.state.mobilepos[j]].id
        initialize_grid_static_covered(self.state)
        for j in range(1, self.state.mobile_num + 1):
            SetSingleSensorCoverArea(self.state.DEbestmobileposition[j], self.state)
        self.state.finalcoverage = compute_coverage(self.state)
        self.state.average_DE_dis = 0.0
        for k in range(1, self.state.mobile_num + 1):
            dx = self.state.sensors[self.state.mobilepos[k]].x - self.state.DEbestmobileposition[k].x
            dy = self.state.sensors[self.state.mobilepos[k]].y - self.state.DEbestmobileposition[k].y
            self.state.average_DE_dis += math.sqrt(dx * dx + dy * dy)
        self.state.average_DE_dis /= max(1, self.state.mobile_num)
        self._post_optimize_discard()
        self.tick3 = time.perf_counter()
        self._post_optimize_exchange()
        # write summaries to files
        try:
            if self.output_file:
                self.output_file.write(f"InitialCoverage: {self.state.initialcoverage:.6f}\n")
                self.output_file.write(f"FinalCoverage: {self.state.finalcoverage:.6f}\n")
                self.output_file.write(f"ConvergenceGeneration: {self.convergence.convergence_generation}\n")
                self.output_file.write(f"MaxFitness: {self.convergence.max_fitness:.6f}\n")
                self.output_file.write(f"ConvergenceTimeSec: {self.convergence.spenttime:.3f}\n")
                runtime = self.tick3 - self.tick1 if hasattr(self, "tick3") and hasattr(self, "tick1") else 0.0
                self.output_file.write(f"RuntimeSec: {runtime:.3f}\n")
                self.output_file.write(f"AverageDEMoveDistance: {self.state.average_DE_dis:.3f}\n")
                self.output_file.write(f"AverageMoveDistanceOpt: {self.state.average_move_dis:.3f}\n")
                self.output_file.write(f"AverageMoveDistanceExchange: {self.state.optimal_distance:.3f}\n")
                self.output_file.write(f"NeedMovedNum: {self.state.needmovednum}\n")
                self.output_file.write("BestPositions:\n")
                for i in range(1, self.state.mobile_num + 1):
                    s = self.state.DEbestmobileposition[i]
                    self.output_file.write(f"{s.id:3d} {s.x:5d} {s.y:5d}\n")
                self.output_file.write("OptimalMatch:\n")
                for i in range(1, self.state.mobile_num + 1):
                    s = self.state.optimalmatch[i] if i < len(self.state.optimalmatch) else self.state.bestmobileposition[i]
                    self.output_file.write(f"{s.id:3d} {s.x:5d} {s.y:5d}\n")
                self.output_file.flush()
            if self.coords_file:
                for i in range(1, self.state.mobile_num + 1):
                    s = self.state.optimalmatch[i] if i < len(self.state.optimalmatch) else self.state.bestmobileposition[i]
                    self.coords_file.write(f"{s.id:3d} {s.x:5d} {s.y:5d}\n")
                self.coords_file.flush()
        except Exception:
            pass
        if self.output_file:
            self.output_file.close()
        if self.coords_file:
            self.coords_file.close()

    def _post_optimize_discard(self):
        edges = []
        for k in range(1, self.state.mobile_num + 1):
            dx = self.state.sensors[self.state.mobilepos[k]].x - self.state.DEbestmobileposition[k].x
            dy = self.state.sensors[self.state.mobilepos[k]].y - self.state.DEbestmobileposition[k].y
            edges.append((k, math.sqrt(dx * dx + dy * dy)))
        edges.sort(key=lambda x: x[1], reverse=True)
        needmovednum1 = self.state.mobile_num
        finalcoverage1 = self.state.finalcoverage
        mobileneedmoved1 = [True for _ in range(self.state.mobile_num + 1)]
        for _, m in edges:
            idx = _
            temp_sensor = self.state.bestmobileposition[idx]
            self.state.bestmobileposition[idx] = self.state.sensors[self.state.mobilepos[idx]]
            initialize_grid_static_covered(self.state)
            for k in range(1, self.state.mobile_num + 1):
                SetSingleSensorCoverArea(self.state.bestmobileposition[k], self.state)
            tempcoverage = compute_coverage(self.state)
            if tempcoverage == finalcoverage1:
                needmovednum1 -= 1
                mobileneedmoved1[idx] = False
            if tempcoverage < finalcoverage1:
                self.state.bestmobileposition[idx] = temp_sensor
            if tempcoverage > finalcoverage1:
                needmovednum1 -= 1
                mobileneedmoved1[idx] = False
                finalcoverage1 = tempcoverage
        initialize_grid_static_covered(self.state)
        for k in range(1, self.state.mobile_num + 1):
            SetSingleSensorCoverArea(self.state.DEbestmobileposition[k], self.state)
        self.state.average_move_dis = 0.0
        for k in range(1, self.state.mobile_num + 1):
            dx = self.state.sensors[self.state.mobilepos[k]].x - self.state.bestmobileposition[k].x
            dy = self.state.sensors[self.state.mobilepos[k]].y - self.state.bestmobileposition[k].y
            self.state.average_move_dis += math.sqrt(dx * dx + dy * dy)
        self.state.average_move_dis /= max(1, self.state.mobile_num)
        self.state.finalcoverage = finalcoverage1
        self.state.needmovednum = needmovednum1
        self.state.mobileneedmoved = mobileneedmoved1

    def _post_optimize_exchange(self):
        origin = [Sensor(0, 0, 0) for _ in range(self.state.mobile_num + 1)]
        pos = [Sensor(0, 0, 0) for _ in range(self.state.mobile_num + 1)]
        for i in range(1, self.state.mobile_num + 1):
            s = self.state.sensors[self.state.mobilepos[i]]
            origin[i] = Sensor(s.x, s.y, i)
            p = self.state.bestmobileposition[i]
            pos[i] = Sensor(p.x, p.y, i)
        for i in range(1, self.state.mobile_num + 1):
            if not self.state.mobileneedmoved[i]:
                continue
            for j in range(1, self.state.mobile_num + 1):
                if not self.state.mobileneedmoved[j]:
                    continue
                dx = origin[i].x - pos[i].x
                dy = origin[i].y - pos[i].y
                dist1 = dx * dx + dy * dy
                dx = origin[j].x - pos[j].x
                dy = origin[j].y - pos[j].y
                dist2 = dx * dx + dy * dy
                dx = origin[i].x - pos[j].x
                dy = origin[i].y - pos[j].y
                dist3 = dx * dx + dy * dy
                dx = origin[j].x - pos[i].x
                dy = origin[j].y - pos[i].y
                dist4 = dx * dx + dy * dy
                if dist1 + dist2 > dist3 + dist4:
                    temp = pos[i]
                    pos[i] = pos[j]
                    pos[j] = temp
                    pos[i].id = i
                    pos[j].id = j
        self.state.optimalmatch = [Sensor(0, 0, 0) for _ in range(self.state.mobile_num + 1)]
        for i in range(1, self.state.mobile_num + 1):
            s = pos[i]
            self.state.optimalmatch[i] = Sensor(s.x, s.y, self.state.sensors[self.state.mobilepos[i]].id)
        initialize_grid_static_covered(self.state)
        for k in range(1, self.state.mobile_num + 1):
            SetSingleSensorCoverArea(self.state.optimalmatch[k], self.state)
        tempcoverage = compute_coverage(self.state)
        if tempcoverage >= self.state.finalcoverage:
            self.state.finalcoverage = tempcoverage
        self.state.optimal_distance = 0.0
        for k in range(1, self.state.mobile_num + 1):
            dx = self.state.sensors[self.state.mobilepos[k]].x - self.state.optimalmatch[k].x
            dy = self.state.sensors[self.state.mobilepos[k]].y - self.state.optimalmatch[k].y
            self.state.optimal_distance += math.sqrt(dx * dx + dy * dy)
        self.state.optimal_distance /= max(1, self.state.mobile_num)
