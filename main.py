from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple, Optional
import uvicorn
import time

# 导入Python版本的路径规划器
from route_planner_python import Coordinate, AlgorithmConfig, RoutePlanner
cpp_planner_available = True

# 为了代码兼容性，创建一个模拟的模块对象
class PythonRoutePlannerModule:
    Coordinate = Coordinate
    AlgorithmConfig = AlgorithmConfig
    RoutePlanner = RoutePlanner

cpp_planner = PythonRoutePlannerModule()

# 导入高德API客户端
from amap_api import AmapAPI

app = FastAPI(title="路径规划API")

# 请求模型
class RouteRequest(BaseModel):
    optimization_target: str  # driving_time, driving_distance, straight_distance
    amap_key: Optional[str] = None
    origin: Tuple[float, float]  # (longitude, latitude)
    destination: Tuple[float, float]
    waypoints: Optional[List[Tuple[float, float]]] = None
    # 算法配置参数
    cooling_rate: float = 0.995
    initial_temperature: float = 10000.0
    max_iterations: int = 100000
    use_cache: bool = True
    enable_local_search: bool = True

# 响应模型
class RouteResponse(BaseModel):
    optimization_target: str
    total_distance: float
    total_time: Optional[float] = None
    path: List[Tuple[float, float]]
    execution_time_ms: float
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    waypoints_order: Optional[List[int]] = None

def convert_to_cpp_coords(py_coords: List[Tuple[float, float]]) -> List:
    """转换Python坐标列表为C++ Coordinate对象列表"""
    return [cpp_planner.Coordinate(lon, lat) for lon, lat in py_coords]

def get_straight_route_result(request: RouteRequest) -> RouteResponse:
    """使用C++逻辑计算直线距离规划结果"""
    if not cpp_planner_available:
        raise HTTPException(status_code=501, detail="直线距离规划功能不可用: 无法加载route_planner模块")
    
    # 转换坐标格式
    starts = [cpp_planner.Coordinate(request.origin[0], request.origin[1])]
    ends = [cpp_planner.Coordinate(request.destination[0], request.destination[1])]
    waypoints = convert_to_cpp_coords(request.waypoints or [])

    # 配置算法参数
    config = cpp_planner.AlgorithmConfig(
        cooling_rate=request.cooling_rate,
        initial_temperature=request.initial_temperature,
        max_iterations=request.max_iterations
    )
    config.use_cache = request.use_cache
    config.enable_local_search = request.enable_local_search

    # 调用C++规划器
    planner = cpp_planner.RoutePlanner(config)
    result = planner.plan_route(starts, waypoints, ends)
    planner.clear_distance_cache()

    # 提取途经点顺序
    waypoints_order = []
    if request.waypoints:
        original_waypoints = { (p.longitude, p.latitude): i 
                             for i, p in enumerate(waypoints) }
        for p in result.path[1:-1]:  # 排除起点和终点
            coord = (p.longitude, p.latitude)
            if coord in original_waypoints:
                waypoints_order.append(original_waypoints[coord])

    # 构建响应
    return RouteResponse(
        optimization_target="straight_distance",
        total_distance=result.total_distance,
        path=[(p.longitude, p.latitude) for p in result.path],
        execution_time_ms=result.execution_time_ms,
        start_point=request.origin,
        end_point=request.destination,
        waypoints_order=waypoints_order if waypoints_order else None
    )

def convert_to_cpp_coords(py_coords: List[Tuple[float, float]]) -> List:
    """转换Python坐标列表为C++ Coordinate对象列表"""
    if not cpp_planner_available:
        return []
    return [cpp_planner.Coordinate(lon, lat) for lon, lat in py_coords]

def get_driving_route_result(request: RouteRequest) -> RouteResponse:
    """使用高德API获取驾车路线结果"""
    start_time = time.time()
    amap = AmapAPI(request.amap_key)
    
    # 调用高德API
    driving_info = amap.get_driving_info(
        origin=request.origin,
        destination=request.destination,
        waypoints=request.waypoints
    )
    
    if not driving_info:
        raise HTTPException(status_code=500, detail="高德API返回空结果")
    
    # 解析路线
    path_points = amap.parse_polyline(driving_info.get("polyline", ""))
    execution_time = (time.time() - start_time) * 1000

    return RouteResponse(
        optimization_target=request.optimization_target,
        total_distance=driving_info["distance"],
        total_time=driving_info["duration"],
        path=path_points,
        execution_time_ms=execution_time,
        start_point=request.origin,
        end_point=request.destination
    )

@app.post("/plan_route", response_model=RouteResponse)
async def plan_route(request: RouteRequest):
    try:
        # 参数验证
        if request.optimization_target in ["driving_time", "driving_distance"]:
            if not request.amap_key:
                raise HTTPException(status_code=400, detail="驾车模式需提供amap_key")
        
        # 处理不同优化目标
        if request.optimization_target == "straight_distance":
            return get_straight_route_result(request)
        elif request.optimization_target in ["driving_time", "driving_distance"]:
            return get_driving_route_result(request)
        else:
            raise HTTPException(status_code=400, detail="无效的优化目标")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)