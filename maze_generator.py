# coding=utf-8
from random import randint, choice
import queue


class CellType:
    ROAD = 0
    WALL = 1
    TRAP = 4  # 增加陷阱类型
    SAFE_PATH = 5  # 临时标记安全路径
    CONSIDERED = 5  # 算法考虑过的单元格
    CURRENT = 6  # 当前考虑的单元格


class Direction:
    LEFT = 0,
    UP = 1,
    RIGHT = 2,
    DOWN = 3,


class Maze:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.maze = [[0 for x in range(self.width)] for y in range(self.height)]

    def reset_maze(self, value):
        for y in range(self.height):
            for x in range(self.width):
                self.set_maze(x, y, value)

    def set_maze(self, x, y, value):
        self.maze[y][x] = CellType.ROAD if value == CellType.ROAD else CellType.WALL

    def visited(self, x, y):
        return self.maze[y][x] != 1


def check_neighbors(maze, x, y, width, height, checklist):
    """
    检查迷宫中给定单元格的邻近单元格，并确定是否有任何单元格可以访问 如果找到有效的相邻单元格，函数就会更新迷宫，并将路径移动到选定的相邻单元格。

    :param maze: 代表迷宫结构，其中的单元格会根据路径探索情况进行修改。的单元格。提供`visited`等方法检查单元格是否被访问，以及`set_maze`等方法更新单元格状态。和 `set_maze` 等方法来更新单元格状态。
    :type maze: Maze
    :param x: 被评估单元格的当前 x 坐标。
    :type x: int
    :param y: 正在评估的单元格的当前 y 坐标。
    :type y: int
    :param width: 迷宫网格中的列总数。
    :type width: int
    :param height: 迷宫网格的总行数。
    :type height: int
    :param checklist: 在迷宫生成过程中需要处理的跟踪单元格列表在迷宫生成过程中需要处理的
    :type checklist: list[tuple[int, int]]
    :return: 布尔值，表示是否成功访问并修改了相邻单元格作为迷宫路径的一部分。作为迷宫路径的一部分被访问和修改。
    :rtype: bool
    """
    directions = []
    if x > 0:
        if not maze.visited(2 * (x - 1) + 1, 2 * y + 1):
            directions.append(Direction.LEFT)
    if y > 0:
        if not maze.visited(2 * x + 1, 2 * (y - 1) + 1):
            directions.append(Direction.UP)
    if x < width - 1:
        if not maze.visited(2 * (x + 1) + 1, 2 * y + 1):
            directions.append(Direction.RIGHT)
    if y < height - 1:
        if not maze.visited(2 * x + 1, 2 * (y + 1) + 1):
            directions.append(Direction.DOWN)
    if len(directions):
        direction = choice(directions)
        if direction == Direction.LEFT:
            maze.set_maze(2 * (x - 1) + 1, 2 * y + 1, CellType.ROAD)
            maze.set_maze(2 * x, 2 * y + 1, CellType.ROAD)
            checklist.append((x - 1, y))
        elif direction == Direction.UP:
            maze.set_maze(2 * x + 1, 2 * (y - 1) + 1, CellType.ROAD)
            maze.set_maze(2 * x + 1, 2 * y, CellType.ROAD)
            checklist.append((x, y - 1))
        elif direction == Direction.RIGHT:
            maze.set_maze(2 * (x + 1) + 1, 2 * y + 1, CellType.ROAD)
            maze.set_maze(2 * x + 2, 2 * y + 1, CellType.ROAD)
            checklist.append((x + 1, y))
        elif direction == Direction.DOWN:
            maze.set_maze(2 * x + 1, 2 * (y + 1) + 1, CellType.ROAD)
            maze.set_maze(2 * x + 1, 2 * y + 2, CellType.ROAD)
            checklist.append((x, y + 1))
        return True
    return False


def random_prime(map, width, height):
    """
    使用随机普里姆算法生成随机迷宫。

    这个函数使用一个实现在给定的地图上创建一个随机迷宫 普里姆算法。
    它首先在中随机选择一个起点并通过将相应的单元格标记为路。从那一点开始，它通过随机选择和迭代地扩展迷宫
    处理清单中的单元格，直到清单为空。

    :param map: 生成迷宫的地图对象。它应该方法 "set_maze(x, y, cell_type)"，用于修改指定坐标处的单元格类型。
    :param width: 用于边界检查的地图宽度。
    :type width: int
    :param height: 用于边界检查的地图高度。
    :type height: int
    :return: None
    :rtype: None
    """
    start_x, start_y = (randint(0, width - 1), randint(0, height - 1))
    map.set_maze(2 * start_x + 1, 2 * start_y + 1, CellType.ROAD)
    checklist = [(start_x, start_y)]
    while len(checklist):
        entry = choice(checklist)
        if not check_neighbors(map, entry[0], entry[1], width, height, checklist):
            checklist.remove(entry)


def do_random_prime(map):
    map.reset_maze(CellType.WALL)
    random_prime(map, (map.width - 1) // 2, (map.height - 1) // 2)


def generate_multiple_paths(maze, num_paths=2):
    """添加额外路径以创建到达出口的多种方式"""
    width, height = maze.width, maze.height

    # 创建一些随机连接来增加路径
    for _ in range(num_paths):
        # 找一堵墙，它两侧都是路径
        for attempt in range(50):  # 限制尝试次数，避免无限循环
            x = randint(2, width - 3)
            y = randint(2, height - 3)

            # 检查是否是墙，且两侧相对的位置是路径
            if maze.maze[y][x] == CellType.WALL:
                # 检查水平连接
                if (maze.maze[y][x - 1] == CellType.ROAD and maze.maze[y][x + 1] == CellType.ROAD) or \
                        (maze.maze[y - 1][x] == CellType.ROAD and maze.maze[y + 1][x] == CellType.ROAD):
                    maze.maze[y][x] = CellType.ROAD  # 打通墙，创建新路径
                    break


def find_safe_path(maze, entrance, exit):
    """使用BFS查找从入口到出口的一条路径并标记为安全路径"""
    # 创建一个队列，用于BFS
    q = queue.Queue()
    q.put(entrance)

    # 创建一个字典，用于记录每个格子的前一个格子
    came_from = {}
    came_from[tuple(entrance)] = None

    found = False
    while not q.empty():
        current = q.get()
        current_tuple = tuple(current)

        # 如果到达出口，结束搜索
        if current[0] == exit[0] and current[1] == exit[1]:
            found = True
            break

        # 检查四个方向
        directions = [
            (0, -1),  # 上
            (1, 0),  # 右
            (0, 1),  # 下
            (-1, 0)  # 左
        ]

        for dx, dy in directions:
            nx, ny = current[0] + dx, current[1] + dy
            next_pos = (nx, ny)

            # 检查下一个格子是否在迷宫范围内并且是可通行的
            if 0 <= nx < maze.width and 0 <= ny < maze.height:
                # 检查是否是道路(0)，且尚未访问过
                if maze.maze[ny][nx] == CellType.ROAD and next_pos not in came_from:
                    q.put([nx, ny])
                    came_from[next_pos] = current_tuple

    # 如果找到路径，标记为安全路径
    if found:
        current = tuple(exit)
        while current != tuple(entrance):
            x, y = current
            # 临时标记为安全路径
            maze.maze[y][x] = CellType.SAFE_PATH
            current = came_from[current]

        # 标记入口为安全路径
        maze.maze[entrance[1]][entrance[0]] = CellType.SAFE_PATH
        return True

    return False


def add_traps(maze, entrance, exit, num_traps=5):
    """向迷宫添加陷阱，但确保有一条无陷阱的安全路径"""
    width, height = maze.width, maze.height

    # 先找出一条安全路径并标记
    find_safe_path(maze, entrance, exit)

    # 添加陷阱，避开安全路径
    traps_added = 0
    while traps_added < num_traps:
        x = randint(2, width - 3)
        y = randint(2, height - 3)

        # 只在非安全路径的路上放置陷阱
        if maze.maze[y][x] == CellType.ROAD:
            # 确保周围有路可走，避免死路
            has_path = False
            if (x > 0 and maze.maze[y][x - 1] in [CellType.ROAD, CellType.SAFE_PATH]) or \
                    (x < width - 1 and maze.maze[y][x + 1] in [CellType.ROAD, CellType.SAFE_PATH]) or \
                    (y > 0 and maze.maze[y - 1][x] in [CellType.ROAD, CellType.SAFE_PATH]) or \
                    (y < height - 1 and maze.maze[y + 1][x] in [CellType.ROAD, CellType.SAFE_PATH]):
                has_path = True

            if has_path:
                maze.maze[y][x] = CellType.TRAP  # 设置陷阱
                traps_added += 1

    # 将安全路径重新标记为普通路径
    for y in range(height):
        for x in range(width):
            if maze.maze[y][x] == CellType.SAFE_PATH:
                maze.maze[y][x] = CellType.ROAD


def set_entrance_exit(maze):
    entrance = []
    for i in range(maze.height):
        if maze.maze[i][1] == 0:
            maze.set_maze(0, i, 0)
            entrance = [0, i]
            break
    exit = []
    for i in range(maze.height - 1, 0, -1):
        if maze.maze[i][maze.width - 2] == 0:
            maze.set_maze(maze.width - 1, i, 0)
            exit = [maze.width - 1, i]
            break
    return entrance, exit


def generate_maze(width=21, height=21):
    maze = Maze(width, height)
    do_random_prime(maze)

    # 添加多条路径
    generate_multiple_paths(maze, num_paths=width // 10 + 1)

    # 设置入口和出口
    entrance, exit = set_entrance_exit(maze)

    # 添加陷阱，确保有一条安全路径
    add_traps(maze, entrance, exit, num_traps=width // 5)

    return maze.maze, entrance, exit