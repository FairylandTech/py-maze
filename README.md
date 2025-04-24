# Py-Maze 项目说明文档

> 一个用 Python 实现的可视化迷宫生成与求解游戏，支持多路径生成、动态陷阱和 AI 自动寻路。

---

## 目录

1. 技术栈
2. 项目设计
3. 算法实现与优化
4. 附录

---

## 1. 技术栈

### 1.1 开发语言与环境

- **Python 3.11**
    - 动态语言，语法简洁，丰富的开源库生态。
    - 脚本即运行，无需编译，方便二次开发与教学展示。

- **项目结构概览**
  ```
  ├── maze.py             # 主程序：游戏窗口、事件循环、线程管理
  ├── maze_generator.py   # 迷宫生成：Prim 算法变体 + 多路径 + 陷阱
  ├── maze_solver.py      # 迷宫求解：BFS / A* / 手动
  ├── utils.py            # 辅助工具：线程安全停止
  ├── assets/             # 资源：字体、图片、音乐
  ├── setup.py            # 打包配置：cx_Freeze
  └── README.md           # 文档
  ```

**优点与选型理由**

- `pygame` 上手快、社区活跃，专注于 2D 游戏渲染。
- `cx_Freeze` 原生支持 Windows GUI 打包，无需额外依赖。
- Python 标准库足够完成算法与并发需求，无需引入重量级框架。

- **项目架构**
    - **模块化设计**：
        - `maze_generator.py`：迷宫生成。
        - `maze_solver.py`：迷宫求解（BFS / A* / 手动 / AI 模式）。
        - `maze.py`：主程序，负责 UI 渲染、事件循环、多线程调度。
        - `utils.py`：工具函数（如安全终止线程等）。
    - **多线程**
        - 解迷线程与计时线程分离，保证渲染不卡顿与逻辑并发执行。

- **第三方组件**
    - **pygame**：游戏窗口与交互，提供渲染、键盘监听、音效支持。
    - **cx_Freeze**：打包为 Windows 可执行文件。
    - **标准库**：`threading`、`time`、`random`、`heapq`、`queue`、`sys`、`os`。

**优点及选型理由**

- Python 生态：快速迭代、易于演示算法原理；
- pygame：轻量、上手快，适合二维格子游戏；
- cx_Freeze：一键打包；
- 多线程：解算与渲染解耦，提升响应速度。

### 1.2 第三方组件

| 组件        | 版本建议 | 作用                     |
|-----------|------|------------------------|
| pygame    | ≥2.0 | 渲染窗口、图形绘制、键盘/鼠标事件、音效支持 |
| cx_Freeze | ≥6.0 | 将 Python 脚本打包为独立可执行文件  |
| heapq     | 标准库  | 实现 A* 优先队列管理           |
| queue     | 标准库  | 线程间安全队列（可选扩展）          |
| threading | 标准库  | 并发执行求解与计时线程            |

---

## 2. 项目设计

### 2.1 模块化解耦

- **生成 vs 求解 vs 渲染**：
    - `maze_generator.py` 只负责地图逻辑；
    - `maze_solver.py` 只关注路径搜索；
    - `maze.py` 专注 UI 和线程调度。
- **职责单一**：各模块关注单一功能，便于测试与替换新算法。

### 2.2 UI & 用户交互

- **主菜单**
    - 难度选择（Easy / Medium / Hard），对应不同尺寸与陷阱数量。
    - 算法选择（BFS / A* / 手动）。
- **游戏界面**
    - 顶部展示计时与剩余陷阱机会。
    - 右下角“刷新”与“菜单”按钮，支持热重载迷宫。
    - 实时绘制搜索过程：当前节点高亮、已探索标记、陷阱显色。

### 2.3 设计好处

- **易于扩展**：可在 `maze_generator.py` 中新增深度优先挖洞、分形地形等算法。
- **良好可视化**：用颜色区分状态，直观展示算法执行过程。
- **高内聚低耦合**：模块切分清晰，方便贡献者定位与修改。

1. **可视化界面**
    - 自绘按钮、方向指示图标和文字提示，用户体验友好。
    - 难度、算法模式（BFS/A*）、AI/手动切换等。

2. **动态生成 & 重刷机制**
    - 随机尺寸的迷宫：宽高由 `random_maze_size()` 决定，增加趣味性。
    - “刷新”按钮可生成新迷宫并重置线程、计时与陷阱机会。

3. **陷阱与多路径**
    - 在主路径基础上增设多条通路，提升探索自由度。
    - 随机分布陷阱，AI 模式下智能避开，手动模式下增添挑战。

4. **可扩展性**
    - 算法策略与 UI 解耦，未来可无缝接入新的生成或求解算法。

---

## 3. 算法实现与优化

### 3.1 迷宫生成

```python
def generate_maze(width=21, height=21):
    m = Maze(width, height)
    do_random_prime(m)  # 基于 Prim 算法变体
    generate_multiple_paths(m, num_paths)  # 增加支线，num_paths≈width//10
    entrance, exit = set_entrance_exit(m)  # 自动在左右边缘选取可行点
    add_traps(m, entrance, exit, num_traps)  # 随机布陷阱，BFS 确保至少一条安全路
    return m.maze, entrance, exit
```

- **Prim 算法变体**：在候选边集中随机选取，生成树形迷宫，无环且全连通。保证无环连通图，基础路径规则且随机性强。
- **多路径**：打通其他随机边，避免仅有单一主干，提升探索性。
- **陷阱布置**：
    1. 调用 `find_safe_path()` 用 BFS 标记一条无陷阱路径（`SAFE_PATH`）。
    2. 在非安全路径上随机放置 `TRAP`，保证游戏可通。
    3. 恢复未标记的安全路为普通路。

### 3.2 BFS 求解

- **基本流程**：从入口广度优先遍历，到达出口即停止。
- **陷阱跳过**：
    - 碰到陷阱在 AI 模式下视为不可通行，手动模式下可选择跳过。
- **优点**：
    - 简单易实现，找到最短步数（最少节点扩展层级），对等权图最优。

```python
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
```

- **跳过陷阱**：
  ```python
  # 跳过墙壁和陷阱
  if neighbor[0] == CellType.WALL or neighbor[0] == CellType.TRAP:
  ```
- **复杂度**：O(N) 节点级别，最优步数，适合小中型地图。

### 3.3 A* 求解

- **基本流程**：结合 `g(n)`（从起点到当前的真实代价）与 `h(n)`（启发式估价到终点）进行优先级队列调度。
- **陷阱跳过**：与 BFS 相同，碰到陷阱在 AI 模式下一律视为不可通行。
- **启发式**：曼哈顿距离
- **优点**：
    - 当启发式符合一致性（Manhattan on格子图），能显著减少搜索节点，速度快于 BFS。

```python
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
```

- **启发函数**：曼哈顿距离
  ```python
  def heuristic(a, b):
    """Manhattan距离启发式函数用于A*算法"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
  ```
- **跳过陷阱**：同 BFS。
- **优势**：在障碍、陷阱密集时，大幅减少搜索节点。

### 3.4 性能优化 & 多线程

- **并发执行**
    - `SOLVE_THREAD`：负责求解，避免阻塞主渲染。
    - `TIME_THREAD`：独立计时器，定时更新 UI。
- **停止旧线程**
  ```python
  from utils import stop_thread
  if thread.is_alive(): stop_thread(thread)
  ```
- **帧率控制**
    - `Clock.tick(FPS)` + `time.sleep(0.01)` 保持绘制平滑与 CPU 友好。

### 3.5 BFS vs A*

| 特性    | BFS       | A*               |
|-------|-----------|------------------|
| 路径最优性 | 最少步数（等权图） | 最少步数（启发式一致时）     |
| 时间复杂度 | O(b^d)    | O(b^d)（启发式好时常数小） |
| 空间复杂度 | 存储整层节点    | 存储开放与关闭列表        |
| 扩展节点数 | 较多（无引导）   | 较少（启发式引导）        |
| 实际性能  | 简单场景可用    | 大规模或复杂多障碍场景更优    |

---

# 附录

## 参考资料

- [迷宫生成与求解算法](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [BFS 算法详解 - GeeksforGeeks](https://www.geeksforgeeks.org/breadth-first-search-or-bfs-for-a-graph/)
- [BFS 在网格迷宫中的应用 - LeetCode](https://leetcode.com/problems/shortest-path-in-binary-matrix/solutions/313347/BFS-python/)
- [BFS 与障碍物优化 - Stack Overflow](https://stackoverflow.com/questions/52547474/moment-in-angular-not-displaying-correct-format/52547574#52547574)
- [Breadth First Search (BFS): A Comprehensive Guide for Algorithmic Problem Solving](https://algocademy.com/blog/breadth-first-search-bfs-a-comprehensive-guide-for-algorithmic-problem-solving/)
- [Mastering Breadth-First Search Techniques: A Comprehensive Guide](https://algocademy.com/blog/mastering-breadth-first-search-techniques-a-comprehensive-guide/)
- [Introduction to the A* Algorithm - Red Blob Games](https://www.redblobgames.com/pathfinding/a-star/introduction.html)
- [An Introduction to A* Pathfinding Algorithm - AlgoCademy Blog](https://algocademy.com/blog/an-introduction-to-a-pathfinding-algorithm/)
- [How to Do PATHFINDING: A* Algorithm (The Thing That Most AAA Games Use) – YouTube 视频](https://www.youtube.com/watch?v=FsParg61xGw)