import time
import pygame
import threading
import heapq
import queue
from utils import stop_thread

SCORE = 1000
TIME = 0
TRAP_CHANCES = 2  # 玩家有两次踩到陷阱的机会
CURRENT_DIRECTION = None  # 存储当前方向，供maze.py使用


class CellType:
    ROAD = 0
    WALL = 1
    WALKED = 2
    DEAD = 3
    TRAP = 4  # 陷阱类型
    CONSIDERED = 5  # 算法考虑过的单元格
    CURRENT = 6  # 当前考虑的单元格


class Direction:
    LEFT = 0,
    UP = 1,
    RIGHT = 2,
    DOWN = 3,


def valid(maze, x, y):
    if x < 0 or y < 0:
        return False
    if x >= len(maze[0]) or y >= len(maze):
        return False
    val = maze[y][x]
    if val == CellType.WALL:
        return False
    return val, x, y


def neighbors(maze, pos):
    x, y = pos
    t, r, d, l = valid(maze, x, y - 1), valid(maze, x + 1, y), valid(maze, x, y + 1), valid(maze, x - 1, y)
    return t, r, d, l


def mark_walked(maze, pos):
    maze[pos[1]][pos[0]] = CellType.WALKED


def mark_dead(maze, pos):
    maze[pos[1]][pos[0]] = CellType.DEAD


def suggest_pos(cells, AI):
    if not AI:
        time.sleep(0.2)  # 减少等待时间

    arr = []
    for cell in cells:
        if cell:
            # AI会避开陷阱
            if cell[0] == CellType.TRAP and AI:
                arr.append(CellType.DEAD)  # 将陷阱标记为死路让AI避开
            else:
                arr.append(cell[0])
        else:
            arr.append(CellType.DEAD)
    if arr[1] == CellType.ROAD:
        return cells[1]
    if arr[2] == CellType.ROAD:
        return cells[2]
    return cells[arr.index(min(arr))]


def suggest_pos_man(cells):
    """修复的手动移动函数 - 处理键盘输入"""
    global CURRENT_DIRECTION

    # 获取当前按下的键
    keys = pygame.key.get_pressed()

    # 检查每个方向键并返回相应的移动
    if keys[pygame.K_UP]:
        if cells[0]:
            CURRENT_DIRECTION = Direction.UP
            return cells[0]
    if keys[pygame.K_RIGHT]:
        if cells[1]:
            CURRENT_DIRECTION = Direction.RIGHT
            return cells[1]
    if keys[pygame.K_DOWN]:
        if cells[2]:
            CURRENT_DIRECTION = Direction.DOWN
            return cells[2]
    if keys[pygame.K_LEFT]:
        if cells[3]:
            CURRENT_DIRECTION = Direction.LEFT
            return cells[3]

    # 处理pygame事件队列中的按键事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and cells[0]:
                CURRENT_DIRECTION = Direction.UP
                return cells[0]
            elif event.key == pygame.K_RIGHT and cells[1]:
                CURRENT_DIRECTION = Direction.RIGHT
                return cells[1]
            elif event.key == pygame.K_DOWN and cells[2]:
                CURRENT_DIRECTION = Direction.DOWN
                return cells[2]
            elif event.key == pygame.K_LEFT and cells[3]:
                CURRENT_DIRECTION = Direction.LEFT
                return cells[3]

    # 如果没有按键按下或方向不可行，返回None
    return None


def heuristic(a, b):
    """Manhattan距离启发式函数用于A*算法"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar_step(maze, pos, goal, neighbors_cells):
    """简单的A*算法单步实现"""
    best_neighbor = None
    best_score = float('infinity')

    for neighbor in neighbors_cells:
        if not neighbor:
            continue

        # 跳过墙壁和陷阱
        if neighbor[0] == CellType.WALL or neighbor[0] == CellType.TRAP:
            continue

        # 计算启发式距离
        h_score = heuristic((neighbor[1], neighbor[2]), (goal[0], goal[1]))

        # 优先未访问过的单元格
        if neighbor[0] == CellType.ROAD:
            h_score -= 5

        if h_score < best_score:
            best_score = h_score
            best_neighbor = neighbor

    return best_neighbor


def bfs_original_step(maze, visited, queue, came_from, callback, pos, score, time_elapsed):
    """原始BFS算法的单步实现，保留可视化过程"""
    import time  # 确保导入 time 模块

    if not queue:
        return False, None  # 队列为空，无法找到路径

    # 获取当前节点
    current = queue.pop(0)

    # 创建迷宫副本用于可视化
    maze_copy = [row[:] for row in maze]

    # 标记所有已访问节点为已考虑
    for node in visited:
        if node != pos:  # 不改变起点
            x, y = node
            if maze_copy[y][x] == CellType.ROAD:  # 只修改道路单元格
                maze_copy[y][x] = CellType.CONSIDERED

    # 标记当前节点为"正在考虑"
    if current != pos:  # 不要修改起点
        maze_copy[current[1]][current[0]] = CellType.CURRENT

    # 可视化当前状态
    callback(maze_copy, [0, pos[0], pos[1]], score, time_elapsed)
    time.sleep(0.08)  # 短暂延迟使可视化更清晰

    # 四个可能的移动方向
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # 上、右、下、左

    for dx, dy in directions:
        nx, ny = current[0] + dx, current[1] + dy
        next_pos = (nx, ny)

        # 检查边界
        if nx < 0 or ny < 0 or nx >= len(maze[0]) or ny >= len(maze):
            continue

        # 检查是否是墙或陷阱
        if maze[ny][nx] == CellType.WALL or maze[ny][nx] == CellType.TRAP:
            continue

        # 检查是否已访问
        if next_pos in visited:
            continue

        # 标记为已访问并记录来源
        visited.add(next_pos)
        came_from[next_pos] = current
        queue.append(next_pos)

        # 在副本上标记新发现的节点为"已考虑"
        if maze_copy[ny][nx] == CellType.ROAD:  # 只修改道路单元格
            maze_copy[ny][nx] = CellType.CONSIDERED

        # 可视化更新的状态
        callback(maze_copy, [0, pos[0], pos[1]], score, time_elapsed)
        time.sleep(0.01)  # 更短的延迟避免过于缓慢

    return True, came_from


def astar_search(maze, start, goal):
    """完整的A*搜索算法，但不可视化搜索过程"""
    # 初始化
    start_pos = (start[0], start[1])
    goal_pos = (goal[0], goal[1])

    open_set = []
    heapq.heappush(open_set, (0, start_pos))

    came_from = {start_pos: None}
    g_score = {start_pos: 0}
    f_score = {start_pos: heuristic(start_pos, goal_pos)}

    closed_set = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal_pos:
            path = []
            while current != start_pos:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        closed_set.add(current)

        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = current[0] + dx, current[1] + dy
            neighbor = (nx, ny)

            if nx < 0 or ny < 0 or nx >= len(maze[0]) or ny >= len(maze):
                continue

            if maze[ny][nx] == CellType.WALL or maze[ny][nx] == CellType.TRAP:
                continue

            if neighbor in closed_set:
                continue

            tentative_g_score = g_score[current] + 1

            if neighbor in g_score and tentative_g_score >= g_score[neighbor]:
                continue

            came_from[neighbor] = current
            g_score[neighbor] = tentative_g_score
            f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal_pos)

            if neighbor not in [item[1] for item in open_set if item]:
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return []


def bfs_visual_step_by_step(maze, start, goal, callback, end_screen, display_time):
    """步进式BFS算法实现，保留原始可视化过程"""
    global SCORE, TIME, CURRENT_DIRECTION, AI
    import time  # 确保导入 time 模块

    # 初始化搜索状态
    start_pos = (start[0], start[1])
    goal_pos = (goal[0], goal[1])

    queue = [start_pos]  # 使用列表替代Queue以便访问元素
    visited = {start_pos}  # 已访问节点集合
    came_from = {start_pos: None}  # 用于回溯路径

    found_path = False

    # BFS搜索阶段 - 可视化搜索过程
    while queue and not found_path:
        # 执行BFS的一步并更新可视化
        success, came_from_updated = bfs_original_step(maze, visited, queue, came_from, callback,
                                                       start, SCORE, TIME)  # 修改这里，确保传递参数名匹配

        if not success:
            break

        # 更新来源记录
        if came_from_updated:
            came_from = came_from_updated

        # 检查是否找到目标
        if goal_pos in came_from:
            found_path = True
            break

    # 重建路径
    path = []
    current = goal_pos
    while current != start_pos:
        path.append(current)
        current = came_from[current]
    path.reverse()

    # 创建迷宫副本用于路径可视化
    maze_final = [row[:] for row in maze]

    # 标记起点为已走过
    maze_final[start[1]][start[0]] = CellType.WALKED

    # 沿着路径移动
    prev_pos = start_pos
    for next_pos in path:
        time.sleep(0.1)

        # 计算方向
        dx = next_pos[0] - prev_pos[0]
        dy = next_pos[1] - prev_pos[1]

        direction = 0
        if dx > 0:
            direction = Direction.RIGHT[0]
            CURRENT_DIRECTION = Direction.RIGHT
        elif dx < 0:
            direction = Direction.LEFT[0]
            CURRENT_DIRECTION = Direction.LEFT
        elif dy > 0:
            direction = Direction.DOWN[0]
            CURRENT_DIRECTION = Direction.DOWN
        else:
            direction = Direction.UP[0]
            CURRENT_DIRECTION = Direction.UP

        # 标记为已走过
        maze_final[next_pos[1]][next_pos[0]] = CellType.WALKED

        # 更新显示
        callback(maze_final, [direction, next_pos[0], next_pos[1]], SCORE, TIME)

        prev_pos = next_pos

        # 如果到达终点
        if next_pos == goal_pos:
            time.sleep(0.5)
            # 确保AI标志设置为True
            AI = True  # 确保AI标志为True
            end_screen("complete", SCORE)
            return True

    return True


def astar_controller(maze, start, goal, callback, end_screen, display_time):
    """A* 算法控制器，不显示搜索过程"""
    global SCORE, TIME, CURRENT_DIRECTION, AI

    # 使用A*搜索获取路径
    path = astar_search(maze, start, goal)

    if not path:
        return False

    # 创建迷宫副本用于最终路径显示
    maze_final = [row[:] for row in maze]

    # 绘制初始位置
    current_pos = start
    callback(maze_final, [0, current_pos[0], current_pos[1]], SCORE, TIME)
    time.sleep(0.2)

    # 标记起点为已走过
    maze_final[start[1]][start[0]] = CellType.WALKED

    # 沿着路径移动
    prev_pos = (start[0], start[1])
    goal_pos = (goal[0], goal[1])
    for next_pos in path:
        time.sleep(0.1)

        # 计算方向
        dx = next_pos[0] - prev_pos[0]
        dy = next_pos[1] - prev_pos[1]

        direction = 0
        if dx > 0:
            direction = Direction.RIGHT[0]
            CURRENT_DIRECTION = Direction.RIGHT
        elif dx < 0:
            direction = Direction.LEFT[0]
            CURRENT_DIRECTION = Direction.LEFT
        elif dy > 0:
            direction = Direction.DOWN[0]
            CURRENT_DIRECTION = Direction.DOWN
        else:
            direction = Direction.UP[0]
            CURRENT_DIRECTION = Direction.UP

        # 标记为已走过
        maze_final[next_pos[1]][next_pos[0]] = CellType.WALKED

        # 更新显示
        callback(maze_final, [direction, next_pos[0], next_pos[1]], SCORE, TIME)

        prev_pos = next_pos

        if next_pos == goal_pos:
            time.sleep(0.5)
            # 确保AI标志设置为True
            AI = True  # 确保AI标志为True
            end_screen("complete", SCORE)
            return True

    return True


def calc_time(display_time, ai):
    global TIME_THREAD, TIME, SCORE
    while True:
        TIME += 100
        if not ai: SCORE -= 22
        display_time(TIME, SCORE)
        time.sleep(1)


def solve_maze(maze, pos, end, callback, end_screen, display_time, AI, algorithm="BFS"):
    global SCORE, TIME_THREAD, TIME, TRAP_CHANCES, CURRENT_DIRECTION
    time.sleep(0.1)

    if AI: SCORE = 1000

    if pos[0] == 0 and pos[1] == 1:
        SCORE = 1000
        TIME = 0
        TRAP_CHANCES = 2  # 重置陷阱机会

    if SCORE <= 0:
        end_screen('score_0', SCORE)
        SCORE = 1000
        return False

    # 如果选择A*算法且AI模式开启
    if AI and algorithm == "ASTAR":
        # 使用完整的A*算法
        return astar_controller(maze, pos, end, callback, end_screen, display_time)
    # 如果选择BFS算法且AI模式开启
    elif AI and algorithm == "BFS":
        # 使用修改后的BFS可视化算法
        return bfs_visual_step_by_step(maze, pos, end, callback, end_screen, display_time)

    # 以下是原来的代码逻辑，处理玩家手动移动
    if pos[0] == end[0] and pos[1] == end[1]:
        mark_walked(maze, pos)
        end_screen("complete", SCORE)
        TIME_THREAD = None
        return True

    # 检查玩家是否踩到陷阱
    x, y = pos[1], pos[0]
    if maze[y][x] == CellType.TRAP and not AI:
        TRAP_CHANCES -= 1
        SCORE -= 50  # 踩陷阱惩罚

        if TRAP_CHANCES <= 0:
            # 重置玩家到起点
            mark_walked(maze, pos)
            callback(maze, pos, SCORE, TIME)
            time.sleep(1)  # 短暂显示踩到陷阱
            TRAP_CHANCES = 2  # 重置陷阱机会
            return solve_maze(maze, (1, 0), end, callback, end_screen, display_time, AI, algorithm)

    t, r, d, l = neighbors(maze, pos)

    if not AI:
        if pos[0] == 0:
            next_pos = r
        else:
            # 处理键盘输入
            next_pos = suggest_pos_man((t, r, d, l))

            # 如果没有按键按下或无法移动，等待一段时间后再尝试
            if next_pos is None:
                pygame.event.pump()  # 确保pygame事件被处理
                # time.sleep(0.05)  # 短暂等待后再次尝试
                return solve_maze(maze, pos, end, callback, end_screen, display_time, AI, algorithm)
    else:
        if algorithm == "ASTAR":
            next_pos = astar_step(maze, pos, end, (t, r, d, l))
        else:
            next_pos = suggest_pos((t, r, d, l), AI)

    if next_pos:
        if next_pos[0] == CellType.WALKED:
            mark_dead(maze, pos)
            if not AI: SCORE -= 10
        else:
            if not AI: SCORE -= 1
            mark_walked(maze, pos)

        # 设置玩家图标方向
        direction = 0
        if next_pos[1] > pos[0]:  # 向右
            direction = Direction.RIGHT[0]
            CURRENT_DIRECTION = Direction.RIGHT
        elif next_pos[1] < pos[0]:  # 向左
            direction = Direction.LEFT[0]
            CURRENT_DIRECTION = Direction.LEFT
        elif next_pos[2] > pos[1]:  # 向下
            direction = Direction.DOWN[0]
            CURRENT_DIRECTION = Direction.DOWN
        else:  # 向上
            direction = Direction.UP[0]
            CURRENT_DIRECTION = Direction.UP

        # 更新next_pos以包含方向信息
        next_pos_with_dir = [direction, next_pos[1], next_pos[2]]

        callback(maze, next_pos_with_dir, SCORE, TIME)
        return solve_maze(maze, (next_pos[1], next_pos[2]), end, callback, end_screen, display_time, AI, algorithm)
    else:
        mark_dead(maze, pos)
        callback(maze, pos, SCORE, TIME)
        return False
