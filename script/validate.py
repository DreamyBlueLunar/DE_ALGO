from pathlib import Path
import sys

# ensure package root (de_python) is importable when running from script/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.params import GlobalState
from core.de_algo import DEAlgorithm


def run_once(kind: int, population: int, generations: int, factor: float, cross_prob: float):
    state = GlobalState()
    state.network_random_generated = False
    state.networkfilename = str(ROOT / "data" / "grid60.txt")
    state.de_population_size = population
    state.de_max_generations = generations
    state.de_factor = factor
    state.de_cross_prob = cross_prob
    algo = DEAlgorithm(state)
    if kind == 2:
        algo.run_jde()
        alg_name = "JDE"
    else:
        algo.run_simple_de()
        alg_name = "DE"
    runtime = getattr(algo, "tick3", 0.0) - getattr(algo, "tick1", 0.0)
    result = {
        "alg": alg_name,
        "initial_coverage": round(state.initialcoverage, 6),
        "final_coverage": round(state.finalcoverage, 6),
        "convergence_generation": algo.convergence.convergence_generation,
        "max_fitness": round(algo.convergence.max_fitness, 6),
        "convergence_time_sec": round(algo.convergence.spenttime, 3),
        "runtime_sec": round(runtime, 3),
        "avg_DE_move_dist": round(state.average_DE_dis, 3),
        "avg_move_dist_opt": round(state.average_move_dis, 3),
        "avg_move_dist_exchange": round(state.optimal_distance, 3),
        "need_move_num": state.needmovednum,
    }
    print(result)


def main():
    run_once(kind=1, population=30, generations=300, factor=0.9, cross_prob=0.95)
    run_once(kind=2, population=30, generations=300, factor=0.9, cross_prob=0.95)


if __name__ == "__main__":
    main()
