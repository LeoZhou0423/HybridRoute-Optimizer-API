# 路径规划API 请求和返回示例参数

本文档提供了路径规划API的详细请求和返回示例参数，帮助开发者理解如何使用该API进行路径规划。

## 1. API概述

这是一个使用FastAPI构建的路径规划API，支持三种路径规划模式：
- **straight_distance**: 使用直线距离进行路径规划
- **driving_time**: 使用高德地图API进行驾车时间最短规划
- **driving_distance**: 使用高德地图API进行驾车距离最短规划

## 2. 基础API信息

- **API端点**: `/plan_route`
- **请求方法**: POST
- **内容类型**: application/json

## 3. 请求参数示例

### 3.1 直线距离规划示例

```json
{
  "optimization_target": "straight_distance",
  "origin": [116.404, 39.915],
  "destination": [116.508, 39.928],
  "waypoints": [
    [116.455, 39.923],
    [116.478, 39.918]
  ],
  "cooling_rate": 0.995,
  "initial_temperature": 10000.0,
  "max_iterations": 100000,
  "use_cache": true,
  "enable_local_search": true
}
```

### 3.2 驾车时间规划示例

```json
{
  "optimization_target": "driving_time",
  "amap_key": "your_amap_api_key_here",
  "origin": [116.404, 39.915],
  "destination": [116.508, 39.928],
  "waypoints": [
    [116.455, 39.923],
    [116.478, 39.918]
  ]
}
```

### 3.3 驾车距离规划示例

```json
{
  "optimization_target": "driving_distance",
  "amap_key": "your_amap_api_key_here",
  "origin": [116.404, 39.915],
  "destination": [116.508, 39.928],
  "cooling_rate": 0.99,
  "initial_temperature": 5000.0,
  "max_iterations": 50000
}
```

## 4. 请求参数详解

| 参数名 | 类型 | 必需/可选 | 默认值 | 描述 |
|--------|------|-----------|--------|------|
| optimization_target | string | 必需 | - | 优化目标，可选值：`driving_time`, `driving_distance`, `straight_distance` |
| amap_key | string | 条件必需 | null | 高德地图API密钥(使用`driving_time`或`driving_distance`时必需) |
| origin | array | 必需 | - | 起点坐标，格式：`[longitude, latitude]` |
| destination | array | 必需 | - | 终点坐标，格式：`[longitude, latitude]` |
| waypoints | array | 可选 | null | 途经点列表，格式：`[[longitude, latitude], ...]` |
| cooling_rate | float | 可选 | 0.995 | 冷却率(用于模拟退火算法) |
| initial_temperature | float | 可选 | 10000.0 | 初始温度(用于模拟退火算法) |
| max_iterations | integer | 可选 | 100000 | 最大迭代次数(用于模拟退火算法) |
| use_cache | boolean | 可选 | true | 是否使用缓存 |
| enable_local_search | boolean | 可选 | true | 是否启用局部搜索 |

## 5. 返回参数示例

### 5.1 直线距离规划返回示例

```json
{
  "optimization_target": "straight_distance",
  "total_distance": 17520.5,
  "path": [
    [116.404, 39.915],
    [116.455, 39.923],
    [116.478, 39.918],
    [116.508, 39.928]
  ],
  "execution_time_ms": 35.8,
  "start_point": [116.404, 39.915],
  "end_point": [116.508, 39.928],
  "waypoints_order": [0, 1]
}
```

### 5.2 驾车时间规划返回示例

```json
{
  "optimization_target": "driving_time",
  "total_distance": 18950.0,
  "total_time": 1860.0,
  "path": [
    [116.404, 39.915],
    [116.405, 39.916],
    // ... 更多路径点 ...
    [116.507, 39.927],
    [116.508, 39.928]
  ],
  "execution_time_ms": 1250.3,
  "start_point": [116.404, 39.915],
  "end_point": [116.508, 39.928]
}
```

### 5.3 驾车距离规划返回示例

```json
{
  "optimization_target": "driving_distance",
  "total_distance": 17250.0,
  "total_time": 2100.0,
  "path": [
    [116.404, 39.915],
    [116.406, 39.914],
    // ... 更多路径点 ...
    [116.506, 39.929],
    [116.508, 39.928]
  ],
  "execution_time_ms": 1320.7,
  "start_point": [116.404, 39.915],
  "end_point": [116.508, 39.928]
}
```

## 6. 返回参数详解

| 参数名 | 类型 | 描述 |
|--------|------|------|
| optimization_target | string | 优化目标 |
| total_distance | float | 总距离(米) |
| total_time | float | 总时间(秒)，仅在使用高德地图API时返回 |
| path | array | 路径点列表，格式：`[[longitude, latitude], ...]` |
| execution_time_ms | float | API执行时间(毫秒) |
| start_point | array | 起点坐标 |
| end_point | array | 终点坐标 |
| waypoints_order | array | 途经点顺序，仅在使用直线距离规划且有途经点时可能返回 |

## 7. 错误处理示例

### 7.1 缺少高德地图API密钥

```json
{
  "detail": "驾车模式需提供amap_key"
}
```

### 7.2 无效的优化目标

```json
{
  "detail": "无效的优化目标"
}
```

### 7.3 高德API错误

```json
{
  "detail": "高德API返回空结果"
}
```

## 8. 实际使用建议

1. **API密钥管理**：不要将高德地图API密钥直接硬编码在前端或客户端代码中
2. **缓存使用**：启用`use_cache`参数可以提高API响应速度
3. **参数调优**：对于直线距离规划，可以根据实际需求调整模拟退火算法的参数(冷却率、初始温度等)
4. **错误处理**：实现良好的错误处理逻辑，处理可能的网络问题或API限制

## 9. 完整请求示例(使用curl)

```bash
# 直线距离规划请求示例
curl -X POST "http://localhost:8001/plan_route" \
  -H "Content-Type: application/json" \
  -d '{
    "optimization_target": "straight_distance",
    "origin": [116.404, 39.915],
    "destination": [116.508, 39.928],
    "waypoints": [[116.455, 39.923], [116.478, 39.918]]
  }'

# 驾车时间规划请求示例
curl -X POST "http://localhost:8001/plan_route" \
  -H "Content-Type: application/json" \
  -d '{
    "optimization_target": "driving_time",
    "amap_key": "your_amap_api_key_here",
    "origin": [116.404, 39.915],
    "destination": [116.508, 39.928]
  }'
```