#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径规划器 Python 版本
直接将 C++ 代码逻辑转换为纯 Python 实现，避免 DLL 加载问题
"""

import math
import random
import time
import itertools
from typing import List, Tuple, Dict, Optional

# --- 地理坐标类 ---
class Coordinate:
    def __init__(self, longitude: float = 0.0, latitude: float = 0.0):
        self.longitude = longitude
        self.latitude = latitude
    
    def __repr__(self):
        return f"Coordinate({self.longitude:.6f}, {self.latitude:.6f})"

# --- 距离计算器（支持缓存可选）---
class DistanceCalculator:
    def __init__(self, enable_cache: bool = True):
        self.distance_cache: Dict[Tuple[int, int], float] = {}
        self.use_cache = enable_cache
    
    # 清理缓存：在大规模计算后调用，释放内存
    def clear_distance_cache(self):
        self.distance_cache.clear()
    
    # 使用 Haversine 公式计算地球表面两点间距离
    def calculate(self, a: Coordinate, b: Coordinate) -> float:
        R = 6371000  # 地球半径（米）
        lat1 = a.latitude * math.pi / 180.0
        lat2 = b.latitude * math.pi / 180.0
        delta_lat = (b.latitude - a.latitude) * math.pi / 180.0
        delta_lon = (b.longitude - a.longitude) * math.pi / 180.0
        
        aa = math.sin(delta_lat / 2) * math.sin(delta_lat / 2) + \
             math.cos(lat1) * math.cos(lat2) * \
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2)
        c = 2 * math.atan2(math.sqrt(aa), math.sqrt(1 - aa))
        return R * c
    
    # 带缓存的距离查询（仅用于精确算法）
    def get_distance(self, points: List[Coordinate], i: int, j: int) -> float:
        if not self.use_cache:
            return self.calculate(points[i], points[j])
        
        # 缓存键，确保 (i,j) 和 (j,i) 对应同一个值
        key = (min(i, j), max(i, j))
        if key in self.distance_cache:
            return self.distance_cache[key]
        
        dist = self.calculate(points[i], points[j])
        self.distance_cache[key] = dist
        return dist

# --- 算法参数配置类 --- 
class AlgorithmConfig:
    def __init__(self, cooling_rate: float = 0.995, initial_temperature: float = 10000.0, max_iterations: int = 100000):
        self.population_size = 100          # 遗传算法种群大小（预留）
        self.cooling_rate = cooling_rate    # 模拟退火冷却率
        self.initial_temperature = initial_temperature  # 初始温度
        self.max_iterations = max_iterations  # 最大迭代次数
        self.use_cache = True               # 是否启用距离缓存
        self.enable_local_search = True     # 是否启用 2-opt 后优化

# --- 路径规划结果 --- 
class RouteResult:
    def __init__(self):
        self.path: List[Coordinate] = []
        self.total_distance: float = 0.0
        self.execution_time_ms: float = 0.0
        self.start_index: int = 0
        self.end_index: int = 0

# --- 路径规划器 --- 
class RoutePlanner:
    def __init__(self, config: Optional[AlgorithmConfig] = None):
        self.config = config if config else AlgorithmConfig()
        self.dist_calc = DistanceCalculator(self.config.use_cache)
        random.seed()  # 初始化随机数生成器
    
    # 计算路径总距离
    def calculate_path_distance(self, path: List[Coordinate]) -> float:
        if len(path) < 2:
            return 0.0
        total = 0.0
        for i in range(len(path) - 1):
            total += self.dist_calc.calculate(path[i], path[i+1])
        return total
    
    # 构造最近邻路径（贪心初始化）
    def construct_greedy_path(self, waypoints: List[Coordinate]) -> List[int]:
        n = len(waypoints)
        path = list(range(n))
        visited = [False] * n
        
        current = random.randint(0, n-1)
        path[0] = current
        visited[current] = True
        
        for i in range(1, n):
            best_dist = float('inf')
            next_point = current
            for j in range(n):
                if visited[j]:
                    continue
                d = self.dist_calc.calculate(waypoints[current], waypoints[j])
                if d < best_dist:
                    best_dist = d
                    next_point = j
            if next_point != current:
                path[i] = next_point
                visited[next_point] = True
                current = next_point
        
        return path
    
    # 2-opt 反转
    def two_opt_swap(self, path: List[int], i: int, j: int):
        while i < j:
            path[i], path[j] = path[j], path[i]
            i += 1
            j -= 1
    
    # 2-opt 局部搜索
    def two_opt_optimize(self, waypoints: List[Coordinate], path: List[int]) -> List[int]:
        if not self.config.enable_local_search:
            return path
        
        improved = True
        best_distance = self.calculate_path_distance(self.extract_path(waypoints, path))
        n = len(path)
        
        while improved:
            improved = False
            for i in range(1, n - 1):
                for j in range(i + 1, n):
                    # 创建一个临时路径副本进行修改
                    temp_path = path.copy()
                    self.two_opt_swap(temp_path, i, j)
                    new_distance = self.calculate_path_distance(self.extract_path(waypoints, temp_path))
                    
                    if new_distance < best_distance:
                        path = temp_path
                        best_distance = new_distance
                        improved = True
        
        return path
    
    # 根据索引提取路径
    def extract_path(self, waypoints: List[Coordinate], indices: List[int]) -> List[Coordinate]:
        return [waypoints[idx] for idx in indices]
    
    # 模拟退火算法（使用 2-opt 邻域）
    def simulated_annealing(self, waypoints: List[Coordinate]) -> List[int]:
        n = len(waypoints)
        current_path = self.construct_greedy_path(waypoints)
        best_path = current_path.copy()
        current_dist = self.calculate_path_distance(self.extract_path(waypoints, current_path))
        best_dist = current_dist
        
        temp = self.config.initial_temperature
        cooling_rate = self.config.cooling_rate
        max_iter = min(self.config.max_iterations, n * n * 50)
        
        for _ in range(max_iter):
            # 随机选择两个点进行交换
            i = random.randint(1, n-1)
            j = random.randint(1, n-1)
            if i == j:
                continue
            if i > j:
                i, j = j, i
            
            # 保存当前路径用于可能的回滚
            old_path = current_path.copy()
            self.two_opt_swap(current_path, i, j)
            new_dist = self.calculate_path_distance(self.extract_path(waypoints, current_path))
            
            # 计算能量差
            delta = new_dist - current_dist
            # 接受更优解或根据概率接受较差解
            if delta < 0 or (temp > 1e-9 and random.random() < math.exp(-delta / temp)):
                current_dist = new_dist
                if new_dist < best_dist:
                    best_dist = new_dist
                    best_path = current_path.copy()
            else:
                # 回滚到之前的路径
                current_path = old_path
            
            # 降温
            temp *= cooling_rate
            if temp < 1.0:
                break
        
        return best_path
    
    # 精确解：枚举所有排列（n <= 12）
    def solve_exact_internal(self, waypoints: List[Coordinate]) -> List[int]:
        n = len(waypoints)
        if n > 12:
            # 对于 n > 12，退化为模拟退火
            return self.simulated_annealing(waypoints)
        
        best_perm = list(range(n))
        best_dist = self.calculate_path_distance(self.extract_path(waypoints, best_perm))
        
        # 枚举所有排列
        for perm in itertools.permutations(range(n)):
            perm_list = list(perm)
            dist = self.calculate_path_distance(self.extract_path(waypoints, perm_list))
            if dist < best_dist:
                best_dist = dist
                best_perm = perm_list
        
        return best_perm
    
    # 规划路径的主函数
    def plan_route(self, starts: List[Coordinate], waypoints: List[Coordinate], ends: List[Coordinate]) -> RouteResult:
        start_time = time.time()
        
        best_full_path = []
        best_total_distance = float('inf')
        best_start_idx = 0
        best_end_idx = 0
        
        # 遍历所有可能的起点和终点组合
        for si in range(len(starts)):
            for ei in range(len(ends)):
                # 根据途经点数量选择算法
                if len(waypoints) <= 12:
                    internal_order = self.solve_exact_internal(waypoints)
                else:
                    internal_order = self.simulated_annealing(waypoints)
                    if self.config.enable_local_search:
                        internal_order = self.two_opt_optimize(waypoints, internal_order)
                
                # 构建完整路径
                full_path = [starts[si]]
                for idx in internal_order:
                    full_path.append(waypoints[idx])
                full_path.append(ends[ei])
                
                # 计算总距离
                total_dist = self.calculate_path_distance(full_path)
                if total_dist < best_total_distance:
                    best_total_distance = total_dist
                    best_full_path = full_path
                    best_start_idx = si
                    best_end_idx = ei
        
        # 计算执行时间
        end_time = time.time()
        exec_time = (end_time - start_time) * 1000.0  # 转换为毫秒
        
        # 构建结果对象
        result = RouteResult()
        result.path = best_full_path
        result.total_distance = best_total_distance
        result.execution_time_ms = exec_time
        result.start_index = best_start_idx
        result.end_index = best_end_idx
        
        return result
    
    # 清理距离缓存
    def clear_distance_cache(self):
        self.dist_calc.clear_distance_cache()

# ===== 辅助函数 =====

# 随机生成坐标
def generate_random_coordinates(count: int, lon_min: float, lon_max: float, lat_min: float, lat_max: float) -> List[Coordinate]:
    coords = []
    for _ in range(count):
        lon = random.uniform(lon_min, lon_max)
        lat = random.uniform(lat_min, lat_max)
        coords.append(Coordinate(lon, lat))
    return coords

# 打印坐标列表
def print_coordinates(coords: List[Coordinate], title: str):
    print(f"===== {title} =====")
    for i, coord in enumerate(coords):
        print(f"  点{i+1}: 经度={coord.longitude:.6f}, 纬度={coord.latitude:.6f}")

# 打印路径规划结果
def print_result(result: RouteResult):
    print("\n===== 路线规划结果 =====")
    print(f"总距离: {result.total_distance:.2f} 米")
    print(f"计算耗时: {result.execution_time_ms:.0f} 毫秒")
    print(f"路线顺序 ({len(result.path)}个点):")
    
    for i, coord in enumerate(result.path):
        print(f"  {i+1}. 经度={coord.longitude:.6f}, 纬度={coord.latitude:.6f}")
    
    # 验证距离计算
    dist_calc = DistanceCalculator()
    verify_dist = 0.0
    print("\n===== 路线验证 =====")
    for i in range(len(result.path) - 1):
        d = dist_calc.calculate(result.path[i], result.path[i+1])
        print(f"  路段 {i+1}: {d:.2f} 米")
        verify_dist += d
    
    print(f"  算法计算总距离: {result.total_distance:.2f} 米")
    print(f"  验证计算总距离: {verify_dist:.2f} 米")
    print(f"  误差: {abs(result.total_distance - verify_dist):.2f} 米")
    print("所有途经点均已访问（算法保证）")

# ===== 测试函数 =====

def test_route_planner():
    # 创建配置
    config = AlgorithmConfig(0.995, 10000.0, 100000)
    config.use_cache = True
    config.enable_local_search = True
    
    # 生成测试数据
    print("请选择数据规模:")
    print("  1. 小规模 (2起点, 3途经点, 2终点)")
    print("  2. 中规模 (5起点, 15途经点, 5终点)")
    print("  3. 大规模 (10起点, 30途经点, 10终点)")
    
    try:
        choice = int(input("输入选项 (1-3): "))
    except ValueError:
        print("无效选择，默认使用小规模")
        choice = 1
    
    if choice == 1:
        num_starts, num_waypoints, num_ends = 2, 3, 2
    elif choice == 2:
        num_starts, num_waypoints, num_ends = 5, 15, 5
    elif choice == 3:
        num_starts, num_waypoints, num_ends = 10, 30, 10
    else:
        print("无效选择，使用小规模")
        num_starts, num_waypoints, num_ends = 2, 3, 2
    
    # 生成随机坐标（以上海区域为例）
    starts = generate_random_coordinates(num_starts, 120.05, 120.25, 30.18, 30.38)
    waypoints = generate_random_coordinates(num_waypoints, 120.05, 120.25, 30.18, 30.38)
    ends = generate_random_coordinates(num_ends, 120.05, 120.25, 30.18, 30.38)
    
    # 打印输入数据
    print_coordinates(starts, "待选起点")
    print_coordinates(waypoints, "途经点")
    print_coordinates(ends, "待选终点")
    
    # 执行路径规划
    planner = RoutePlanner(config)
    result = planner.plan_route(starts, waypoints, ends)
    
    # 打印结果
    print_result(result)
    
    # 大规模计算后，释放缓存
    planner.clear_distance_cache()
    print("\n距离缓存已清理")

# ===== 主函数 =====

if __name__ == "__main__":
    test_route_planner()