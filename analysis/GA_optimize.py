import random
import multiprocessing
import numpy as np
from deap import base, creator, tools, algorithms

# 假设的 get_effectiveness 函数
def get_effectiveness(combination):
    # 实际逻辑替换为你的函数
    return sum(combination)  # 示例: 组合中数字的总和

# 参数设置
NUM_OBJECTIVES = 32
NUM_SELECTED = 8

# 定义问题
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()

# 定义如何随机选择目标
toolbox.register("attribute", random.randint, 0, NUM_OBJECTIVES - 1)
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attribute, n=NUM_SELECTED)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

# 评估函数
def evalEffectiveness(individual):
    return get_effectiveness(individual),

toolbox.register("evaluate", evalEffectiveness)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutUniformInt, low=0, up=NUM_OBJECTIVES-1, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)

# 并行设置
def setup_pool(pool_size):
    pool = multiprocessing.Pool(processes=pool_size)
    toolbox.register("map", pool.map)

def main(pool_size=4):
    setup_pool(pool_size)

    random.seed(64)
    pop = toolbox.population(n=300)

    # 指定一些初始组合
    initial_combinations = [[random.randint(0, NUM_OBJECTIVES-1) for _ in range(NUM_SELECTED)] for _ in range(10)]
    for comb in initial_combinations:
        pop.append(creator.Individual(comb))

    # 遗传算法参数
    CXPB, MUTPB, NGEN = 0.5, 0.2, 40

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    pop, log = algorithms.eaSimple(pop, toolbox, CXPB, MUTPB, NGEN, stats=stats, verbose=True)

    best_ind = tools.selBest(pop, 1)[0]
    print("Best Individual = ", best_ind, "\nBest Fitness = ", best_ind.fitness.values)

if __name__ == "__main__":
    main(8)
