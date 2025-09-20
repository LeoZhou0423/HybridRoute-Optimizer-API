# 路径规划器 Python 版本

## 项目简介

这是一个完全使用Python实现的路径规划器，基于模拟退火算法和2-opt局部搜索优化。该项目是对原始C++路径规划代码的完整重写，解决了C++编译为Python模块时可能遇到的DLL加载问题。

## 功能特点

- **纯Python实现**：无需编译，直接运行
- **多种算法支持**：
  - 模拟退火算法（适用于大规模问题）
  - 精确解计算（适用于小规模问题，n ≤ 12）
  - 2-opt局部搜索优化
- **灵活的配置参数**：可自定义冷却率、初始温度、最大迭代次数等
- **多起点多终点选择**：自动选择最优的起点和终点组合
- **距离缓存**：可选的距离计算缓存功能，提高性能

## 快速开始

### 直接使用

1. 确保您的系统已安装Python 3.6或更高版本

2. 运行测试脚本查看效果：
   ```bash
   python test_route_planner_python.py
   ```

### 在您的代码中使用

```python
from route_planner_python import Coordinate, AlgorithmConfig, RoutePlanner, print_result

# 创建配置
config = AlgorithmConfig()
config.cooling_rate = 0.995
config.initial_temperature = 10000.0
config.max_iterations = 100000

# 创建路径规划器
planner = RoutePlanner(config)

# 定义起点、途经点和终点
starts = [Coordinate(116.397428, 39.90923)]  # 北京天安门
waypoints = [
    Coordinate(116.466263, 39.921466),  # 颐和园
    Coordinate(116.432919, 39.999659)   # 奥林匹克公园
]
ends = [Coordinate(116.473168, 39.993015)]  # 北京南站

# 执行路径规划
result = planner.plan_route(starts, waypoints, ends)

# 打印结果
print_result(result)

# 释放缓存（大规模计算后）
planner.clear_distance_cache()
```

## 类和方法说明

### Coordinate 类
表示地理坐标点
- `__init__(longitude=0.0, latitude=0.0)`: 初始化坐标
- 属性: `longitude`（经度）, `latitude`（纬度）

### AlgorithmConfig 类
算法配置参数
- `__init__(cooling_rate=0.995, initial_temperature=10000.0, max_iterations=100000)`: 初始化配置
- 属性: 
  - `cooling_rate`: 模拟退火冷却率
  - `initial_temperature`: 初始温度
  - `max_iterations`: 最大迭代次数
  - `use_cache`: 是否启用距离缓存（默认为True）
  - `enable_local_search`: 是否启用2-opt局部搜索（默认为True）

### RoutePlanner 类
路径规划的主要类
- `__init__(config=None)`: 初始化路径规划器
- `plan_route(starts, waypoints, ends)`: 规划路径
  - 参数: `starts`（起点列表）, `waypoints`（途经点列表）, `ends`（终点列表）
  - 返回: `RouteResult`对象
- `clear_distance_cache()`: 清理距离缓存

### RouteResult 类
路径规划结果
- 属性: 
  - `path`: 规划的路径（坐标点列表）
  - `total_distance`: 总距离（米）
  - `execution_time_ms`: 计算耗时（毫秒）
  - `start_index`: 最佳起点索引
  - `end_index`: 最佳终点索引

## 辅助函数

- `generate_random_coordinates(count, lon_min, lon_max, lat_min, lat_max)`: 生成随机坐标
- `print_coordinates(coords, title)`: 打印坐标列表
- `print_result(result)`: 打印路径规划结果

## 性能说明

- 对于小规模问题（途经点数量 ≤ 12），使用精确算法求解
- 对于大规模问题（途经点数量 > 12），使用模拟退火算法和2-opt优化
- 使用距离缓存可显著提高重复计算的性能
- 计算时间与问题规模、算法参数设置有关

## 问题解决方案

原始C++代码在编译为Python模块时可能遇到DLL加载失败问题。本项目通过以下方式解决：

1. **完全Python重写**：将C++代码的所有功能直接用Python实现
2. **保留原有算法逻辑**：确保计算结果与原始实现一致
3. **移除编译依赖**：无需安装MinGW、MSVC等编译器
4. **简化使用流程**：无需复杂的环境配置

## API服务使用说明

本项目提供了基于FastAPI的RESTful API服务，可以作为路径规划接口使用。

### 启动API服务

```bash
python main.py
```

服务将在 http://0.0.0.0:8000 启动

### API端点

#### POST /plan_route

用于规划路径的主要端点。

### 请求参数

```json
{
  "optimization_target": "string",  // 优化目标：driving_time, driving_distance, straight_distance
  "amap_key": "string",             // 可选，使用高德地图API时需要
  "origin": [float, float],          // 起点坐标 [经度, 纬度]
  "destination": [float, float],     // 终点坐标 [经度, 纬度]
  "waypoints": [                     // 可选，途经点列表
    [float, float],
    ...
  ],
  "cooling_rate": float,             // 可选，模拟退火冷却率，默认为0.995
  "initial_temperature": float,      // 可选，初始温度，默认为10000.0
  "max_iterations": int,             // 可选，最大迭代次数，默认为100000
  "use_cache": boolean,              // 可选，是否使用缓存，默认为True
  "enable_local_search": boolean     // 可选，是否启用局部搜索，默认为True
}
```

### 响应格式

```json
{
  "optimization_target": "string",  // 优化目标
  "total_distance": float,           // 总距离（米）
  "total_time": float,               // 驾车模式下的总时间（秒）
  "path": [                          // 规划的路径点列表
    [float, float],
    ...
  ],
  "execution_time_ms": float,        // 计算耗时（毫秒）
  "start_point": [float, float],     // 起点坐标
  "end_point": [float, float],       // 终点坐标
  "waypoints_order": [int, ...]      // 途经点的访问顺序（索引）
}
```

### 请求示例

#### 使用直线距离规划

```bash
curl -X POST "http://localhost:8000/plan_route" \
  -H "Content-Type: application/json" \
  -d '{
    "optimization_target": "straight_distance",
    "origin": [116.397428, 39.90923],
    "destination": [116.473168, 39.993015],
    "waypoints": [
      [116.466263, 39.921466],
      [116.432919, 39.999659]
    ]
  }'
```

#### 使用驾车路线规划（需要高德地图API密钥）

```bash
curl -X POST "http://localhost:8000/plan_route" \
  -H "Content-Type: application/json" \
  -d '{
    "optimization_target": "driving_distance",
    "amap_key": "your_amap_api_key",
    "origin": [116.397428, 39.90923],
    "destination": [116.473168, 39.993015]
  }'
```

## 测试用例

项目包含两个测试脚本：
- `route_planner_python.py`: 包含完整的路径规划器实现和简单的测试功能
- `test_route_planner_python.py`: 提供更详细的测试用例，包括简单和复杂路径规划

## 注意事项

- 路径规划基于地球表面距离计算（Haversine公式）
- 对于大规模问题，可调整算法参数以平衡计算速度和结果质量
- 大规模计算后，建议调用`clear_distance_cache()`释放内存
- Python版本的性能可能略低于C++版本，但使用更加便捷

## 版本历史

- v1.0: 初始版本，完成基本功能实现

## 作者信息

此项目由AI助手根据原始C++代码重写为Python版本。