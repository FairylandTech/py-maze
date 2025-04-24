# coding = utf-8
import sys
import os
import threading
import time

import pygame
from time import sleep

from maze_generator import generate_maze
from maze_solver import solve_maze
from maze_solver import calc_time
from maze_solver import Direction, CellType

from utils import stop_thread
import random

pygame.init()

WIDTH = 400
HEADER = 30
BOTTOM = 60
HEIGHT = WIDTH + HEADER + BOTTOM
WINDOW = (WIDTH, HEIGHT)

TITLE = "Python Project 5th sem"
SCREEN = pygame.display.set_mode(WINDOW)
pygame.display.set_caption(TITLE)
FPS = 60
CLOCK = pygame.time.Clock()

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_DARK_RED = (82, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_DARK_GREEN = (2, 100, 64)
COLOR_BLUE = (255, 160, 122)
COLOR_CYAN = (0, 255, 255)
COLOR_DARK_BLUE = pygame.Color("#3F46CB")
COLOR_YELLOW = pygame.Color("#F1CA3A")
COLOR_ORANGE = (255, 165, 0)
COLOR_DARK_ORANGE = (118, 76, 0)
COLOR_TRAP = (128, 0, 128)  # Purple for traps
COLOR_CONSIDERED = (173, 216, 230)  # Light Blue for considered cells
COLOR_CURRENT = (255, 215, 0)  # Gold for current cell

FONT_SIZE = 16
FONT = pygame.font.Font("assets/fonts/msyh.ttf", FONT_SIZE)
FONT_LARGE1 = pygame.font.Font("assets/fonts/msyh.ttf", FONT_SIZE * 3)
FONT_LARGE2 = pygame.font.Font("assets/fonts/msyh.ttf", int(FONT_SIZE * 1.5))

BUTTONS = []

SOLVE_THREAD = None
TIME_THREAD = None

r1 = r2 = 0
level_select = ""

# 创建data/images目录（如果不存在）
if not os.path.exists("assets/images"):
    try:
        os.makedirs("assets/images")
    except:
        pass


# 创建简单的玩家方向图标
def create_player_images():
    # 上方向
    up_img = pygame.Surface((20, 20), pygame.SRCALPHA)
    up_img.fill((0, 0, 0, 0))  # 透明背景
    pygame.draw.polygon(up_img, COLOR_BLUE, [(10, 2), (2, 18), (18, 18)])
    pygame.draw.polygon(up_img, COLOR_YELLOW, [(10, 5), (5, 15), (15, 15)])

    # 下方向
    down_img = pygame.Surface((20, 20), pygame.SRCALPHA)
    down_img.fill((0, 0, 0, 0))
    pygame.draw.polygon(down_img, COLOR_BLUE, [(2, 2), (18, 2), (10, 18)])
    pygame.draw.polygon(down_img, COLOR_YELLOW, [(5, 5), (15, 5), (10, 15)])

    # 左方向
    left_img = pygame.Surface((20, 20), pygame.SRCALPHA)
    left_img.fill((0, 0, 0, 0))
    pygame.draw.polygon(left_img, COLOR_BLUE, [(18, 2), (2, 10), (18, 18)])
    pygame.draw.polygon(left_img, COLOR_YELLOW, [(15, 5), (5, 10), (15, 15)])

    # 右方向
    right_img = pygame.Surface((20, 20), pygame.SRCALPHA)
    right_img.fill((0, 0, 0, 0))
    pygame.draw.polygon(right_img, COLOR_BLUE, [(2, 2), (18, 10), (2, 18)])
    pygame.draw.polygon(right_img, COLOR_YELLOW, [(5, 5), (15, 10), (5, 15)])

    # 保存图像
    try:
        pygame.image.save(up_img, "assets/images/player_up.png")
        pygame.image.save(down_img, "assets/images/player_down.png")
        pygame.image.save(left_img, "assets/images/player_left.png")
        pygame.image.save(right_img, "assets/images/player_right.png")
    except:
        print("无法保存玩家图像，将使用内存中的图像")

    return up_img, down_img, left_img, right_img


# 尝试加载玩家方向图像，如果不存在则创建
try:
    PLAYER_UP = pygame.image.load('assets/images/player_up.png')
    PLAYER_DOWN = pygame.image.load('assets/images/player_down.png')
    PLAYER_LEFT = pygame.image.load('assets/images/player_left.png')
    PLAYER_RIGHT = pygame.image.load('assets/images/player_right.png')
except:
    # 图像不存在，创建并加载
    PLAYER_UP, PLAYER_DOWN, PLAYER_LEFT, PLAYER_RIGHT = create_player_images()

CURRENT_DIRECTION = Direction.RIGHT  # 默认方向

# 当前选择的算法
ALGORITHM = "BFS"

# 尝试加载启动画面，如果失败，创建一个简单的画面
try:
    image = pygame.image.load('assets/images/splash.jpg')
    SCREEN.blit(image, (-79, 35))
    pygame.display.update()
    sleep(1)  # 减少显示时间
except:
    SCREEN.fill(COLOR_DARK_BLUE)
    font = pygame.font.Font(None, 48)
    text = font.render("Maze Game", True, COLOR_WHITE)
    SCREEN.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    pygame.display.update()
    sleep(1)  # 减少显示时间

# 尝试播放音乐，如果失败，忽略
try:
    pygame.mixer.init()
    pygame.mixer.music.load('assets\\2.mp3')
    pygame.mixer.music.play()
except:
    pass

AI = False
TRAP_CHANCES = 2  # 玩家有两次踩到陷阱的机会


def draw_rect(x, y, len, color):
    pygame.draw.rect(SCREEN, color, [x, y, len, len], 0)


def draw_back_button():
    try:
        image = pygame.image.load("assets\\images\\back button.png")
        image = pygame.transform.scale(image, (15, 15))
        SCREEN.blit(image, [5, 7])
    except:
        # 如果图片加载失败，绘制一个简单的按钮
        pygame.draw.rect(SCREEN, COLOR_DARK_BLUE, [5, 7, 15, 15], 2)
        pygame.draw.polygon(SCREEN, COLOR_DARK_BLUE, [(15, 7), (5, 15), (15, 22)])


def draw_button(x, y, len, height, tdata, color=COLOR_DARK_BLUE):
    # pygame.draw.rect(SCREEN, COLOR_BLACK, [x, y, len, height], 1)
    text_surface = FONT.render(tdata, True, color)
    text_len = tdata.__len__() * FONT_SIZE
    SCREEN.blit(text_surface, (x + (len - text_len) / 2, y + 2))


def draw_heading1(x, y, len, text, color=COLOR_BLACK, font_size=FONT_SIZE):
    # pygame.draw.rect(SCREEN, COLOR_BLACK, [x, y, len, height], 1)
    text_surface = FONT_LARGE1.render(text, True, color)
    text_len = text.__len__() * FONT_SIZE
    SCREEN.blit(text_surface, (x + (len - text_len - 60) / 2, y + 5))


def draw_heading2(x, y, len, text, color=COLOR_BLACK, font_size=FONT_SIZE):
    # pygame.draw.rect(SCREEN, COLOR_BLACK, [x, y, len, height], 1)
    text_surface = FONT_LARGE2.render(text, True, color)
    text_len = text.__len__() * font_size
    SCREEN.blit(text_surface, (x + (len - text_len - 30) / 2, y))


def draw_level_opener(x, y, len, height, text1, img, text2):
    # pygame.draw.rect(SCREEN, COLOR_YELLOW, [x, y, len, height], 1)
    text_surface = FONT.render(text1, True, COLOR_DARK_BLUE)
    text_len = text1.__len__() * FONT_SIZE
    SCREEN.blit(text_surface, (x, y + 2))
    try:
        image = pygame.image.load(img)
        image = pygame.transform.scale(image, (int(len - 3), int(len - 3)))
        SCREEN.blit(image, [x, y + 27])
    except:
        # 如果图片加载失败，绘制一个简单的框
        pygame.draw.rect(SCREEN, COLOR_DARK_BLUE, [x, y + 27, int(len - 3), int(len - 3)], 2)
        pygame.draw.rect(SCREEN, COLOR_YELLOW, [x + 10, y + 37, int(len - 23), int(len - 23)])

    text_surface = FONT.render(text2, True, COLOR_DARK_BLUE)
    text_len = text1.__len__() * FONT_SIZE
    SCREEN.blit(text_surface, (x, y + height - 30))


def draw_end_screen(status, score):
    global SOLVE_THREAD, TIME_THREAD, AI

    if TIME_THREAD is not None and TIME_THREAD.is_alive():
        stop_thread(TIME_THREAD)
        TIME_THREAD = None

    if status == 'complete':
        # 检查是否使用了AI
        if AI:
            # 先将AI置为False，避免后续重复判断
            SCREEN.fill(COLOR_ORANGE)
            draw_heading1(80, 150, 200, "You Used AI", COLOR_BLACK)
            draw_heading2(155, 225, 200, "To Complete the Level", COLOR_BLACK)
            draw_button(25, 3, 20, 50, "Menu", COLOR_BLACK)
            draw_button(380, 3, 20, 50, "Replay", COLOR_BLACK)

            # 清除按钮列表并添加菜单和重玩按钮
            BUTTONS.clear()
            BUTTONS.append({
                'x': 2,
                'y': 2,
                'length': 60,
                'height': 25,
                'click': menu
            })
            BUTTONS.append({
                'x': 340,
                'y': 3,
                'length': 60,
                'height': 25,
                'click': refresh
            })

            pygame.display.update()
            # 延迟一下，确保消息显示
            time.sleep(0.5)
            # 设置AI为False，以便下次重新开始
            AI = False
        else:
            SCREEN.fill(COLOR_GREEN)
            draw_heading1(85, 150, 200, "You Won", COLOR_DARK_GREEN)
            draw_heading2(150, 225, 200, "Congratulations", COLOR_DARK_GREEN)
            draw_heading2(150, 300, 200, "Your Score : " + str(score), COLOR_DARK_GREEN)
            draw_button(25, 3, 20, 50, "Menu", COLOR_DARK_GREEN)
            draw_button(380, 3, 20, 50, "Replay", COLOR_DARK_GREEN)

            # 清除按钮列表并添加菜单和重玩按钮
            BUTTONS.clear()
            BUTTONS.append({
                'x': 2,
                'y': 2,
                'length': 60,
                'height': 25,
                'click': menu
            })
            BUTTONS.append({
                'x': 340,
                'y': 3,
                'length': 60,
                'height': 25,
                'click': refresh
            })

            pygame.display.update()
            # High Score update
            try:
                f = open("assets/high_score.txt", "r")
                lines = f.read().splitlines()
                if r1 == 5 and score > int(lines[0]):
                    lines[0] = str(score)
                if r1 == 10 and score > int(lines[1]):
                    lines[1] = str(score)
                if r1 == 15 and score > int(lines[2]):
                    lines[2] = str(score)
                f.close()
                f = open("assets/high_score.txt", "w")
                f.write(lines[0] + '\n' + lines[1] + '\n' + lines[2])
                f.close()
            except:
                # 如果文件操作失败，尝试创建文件
                try:
                    f = open("assets/high_score.txt", "w")
                    f.write("0\n0\n0")
                    f.close()
                except:
                    pass

    elif status == 'score_0':
        SCREEN.fill(COLOR_RED)
        draw_heading1(85, 150, 200, "You Lost", COLOR_DARK_RED)
        draw_heading2(150, 225, 200, "Better Luck Next Time", COLOR_DARK_RED)
        draw_heading2(150, 300, 200, "Your Score : " + str(score), COLOR_DARK_RED)
        draw_button(25, 3, 20, 50, "Menu", COLOR_DARK_RED)
        draw_button(380, 3, 20, 50, "Replay", COLOR_DARK_RED)

        # 清除按钮列表并添加菜单和重玩按钮
        BUTTONS.clear()
        BUTTONS.append({
            'x': 2,
            'y': 2,
            'length': 60,
            'height': 25,
            'click': menu
        })
        BUTTONS.append({
            'x': 340,
            'y': 3,
            'length': 60,
            'height': 25,
            'click': refresh
        })

        pygame.display.update()


def refresh():
    global MAZE, SIZE, ENTRANCE, EXIT, SOLVE_THREAD, TIME_THREAD, AI, TRAP_CHANCES
    if SOLVE_THREAD is not None and SOLVE_THREAD.is_alive():
        stop_thread(SOLVE_THREAD)
        SOLVE_THREAD = None
    SIZE = random_maze_size()
    MAZE, ENTRANCE, EXIT = generate_maze(SIZE, SIZE)
    TRAP_CHANCES = 2  # 重置陷阱机会
    SOLVE_THREAD = threading.Thread(target=solve_maze,
                                    args=(MAZE, ENTRANCE, EXIT, draw_maze, draw_end_screen, display_time, AI, ALGORITHM))
    SOLVE_THREAD.start()

    if AI: AI = False

    if TIME_THREAD is not None and TIME_THREAD.is_alive():
        stop_thread(TIME_THREAD)
        TIME_THREAD = None
    TIME_THREAD = threading.Thread(target=calc_time, args=(display_time, AI))
    TIME_THREAD.start()


def draw_menu():
    # check for high score file
    try:
        f = open("assets/high_score.txt", "r+")
        lines = f.read().splitlines()
        if len(lines) == 0:
            f.write("0\n0\n0")
        f.close()
    except:
        # 如果文件不存在，创建一个新文件
        try:
            os.makedirs("assets", exist_ok=True)  # 确保目录存在
            f = open("assets/high_score.txt", "w")
            f.write("0\n0\n0")
            f.close()
        except:
            pass

    SCREEN.fill(COLOR_WHITE)
    draw_heading1(2, 2, WIDTH - 4, 'Maze', COLOR_DARK_BLUE, FONT_SIZE * 3)

    draw_level_opener(0 * WIDTH / 3 + 10, HEIGHT / 2 - 75, WIDTH / 3 - 10, WIDTH / 3 + 50, "LEVEL 1",
                      ".\\assets\\images\\easy.png", "Easy")
    draw_level_opener(1 * WIDTH / 3 + 10, HEIGHT / 2 - 75, WIDTH / 3 - 10, WIDTH / 3 + 50, "LEVEL 2",
                      ".\\assets\\images\\medium.png", "Medium")
    draw_level_opener(2 * WIDTH / 3 + 10, HEIGHT / 2 - 75, WIDTH / 3 - 10, WIDTH / 3 + 50, "LEVEL 3",
                      ".\\assets\\images\\hard.png", "Hard")

    # 清除之前的按钮
    BUTTONS.clear()
    BUTTONS.append({
        'x': 0 * WIDTH / 3 + 10,
        'y': HEIGHT / 2 - 75,
        'length': WIDTH / 3 - 10,
        'height': WIDTH / 3 + 50,
        'click': easy
    })

    BUTTONS.append({
        'x': 1 * WIDTH / 3 + 10,
        'y': HEIGHT / 2 - 75,
        'length': WIDTH / 3 - 10,
        'height': WIDTH / 3 + 50,
        'click': medium
    })

    BUTTONS.append({
        'x': 2 * WIDTH / 3 + 10,
        'y': HEIGHT / 2 - 75,
        'length': WIDTH / 3 - 10,
        'height': WIDTH / 3 + 50,
        'click': hard
    })

    pygame.display.flip()


def easy():
    global r1
    global r2
    global level_select
    r1 = 5
    r2 = 7
    level_select = "LEVEL 1 : Easy"
    refresh()


def medium():
    global r1
    global r2
    global level_select
    r1 = 10
    r2 = 12
    level_select = "LEVEL 2 : Medium"
    refresh()


def hard():
    global r1
    global r2
    global level_select
    r1 = 15
    r2 = 17
    level_select = "LEVEL 3 : Hard"
    refresh()


def display_high_score():
    global r1
    try:
        f = open("assets/high_score.txt", "r")
        lines = f.read().splitlines()
        if r1 == 5:  # Easy
            return lines[0]
        elif r1 == 10:  # Medium
            return lines[1]
        elif r1 == 15:  # Hard
            return lines[2]
        f.close()
    except:
        return "0"


def msec_to_time(msec):
    sec = msec // 100
    min, sec = divmod(sec, 60)
    min_str = ''
    sec_str = ''
    if min == 0:
        min_str = '00'
    elif min > 0 and min < 10:
        min_str = '0' + str(min)
    else:
        min_str = str(min)
    if sec == 0:
        sec_str = '00'
    elif sec > 0 and sec < 10:
        sec_str = '0' + str(sec)
    else:
        sec_str = str(sec)
    return min_str + ':' + sec_str


def display_time(curr_time, score):
    global SCREEN
    if AI: Score = 1000
    SCREEN.fill(COLOR_WHITE, (2, HEIGHT - BOTTOM, WIDTH // 3, BOTTOM - 4))
    draw_button(2, HEIGHT - BOTTOM, WIDTH // 3, BOTTOM - 4, 'Score')
    draw_heading2(1, HEIGHT - BOTTOM + 20, WIDTH // 3, str(score))
    SCREEN.fill(COLOR_WHITE, (2 + WIDTH // 3, HEIGHT - BOTTOM, WIDTH // 3, BOTTOM - 4))
    draw_button(2 + WIDTH // 3, HEIGHT - BOTTOM, WIDTH // 3, BOTTOM - 4, "Time")
    draw_heading2(13 + WIDTH // 3, HEIGHT - BOTTOM + 20, WIDTH // 3, msec_to_time(curr_time))
    pygame.display.flip()


def draw_maze(maze, cur_pos, score, time):
    global level_select, CURRENT_DIRECTION, TRAP_CHANCES, ALGORITHM
    SCREEN.fill(COLOR_WHITE)
    draw_back_button()
    draw_button(30, 3, WIDTH - 150, HEADER - 4, level_select)
    draw_button(200, 3, WIDTH - 150, HEADER - 4, "High Score : " + display_high_score())
    draw_button(380, 3, 20, HEADER - 4, "Replay")
    BUTTONS.clear()
    BUTTONS.append({
        'x': 2,
        'y': 2,
        'length': 40,
        'height': 25,
        'click': menu
    })
    BUTTONS.append({
        'x': 340,
        'y': 3,
        'length': 60,
        'height': HEADER - 4,
        'click': refresh
    })

    size = len(maze)
    cell_size = int(WIDTH / size)
    cell_padding = (WIDTH - (cell_size * size)) / 2
    for y in range(size):
        for x in range(size):
            cell = maze[y][x]
            # 常规单元格类型颜色映射
            if cell == CellType.WALL:  # 墙
                color = COLOR_BLACK
            elif cell == CellType.WALKED:  # 走过
                color = COLOR_CYAN
            elif cell == CellType.DEAD:  # 死路
                color = COLOR_RED
            elif cell == CellType.TRAP:  # 陷阱
                color = COLOR_TRAP
            elif cell == CellType.CONSIDERED:  # 考虑过的单元格 (BFS搜索)
                color = COLOR_CONSIDERED
            elif cell == CellType.CURRENT:  # 当前单元格 (BFS搜索)
                color = COLOR_CURRENT
            else:  # 道路
                color = COLOR_WHITE

            # 检查 cur_pos 的格式，确保它是正确的
            if isinstance(cur_pos, list) and len(cur_pos) >= 3:
                if x == cur_pos[1] and y == cur_pos[2]:
                    # 根据当前方向绘制玩家
                    if color == COLOR_BLACK:
                        draw_rect(cell_padding + x * cell_size, HEADER + cell_padding + y * cell_size, cell_size, color)
                    else:
                        draw_rect(cell_padding + x * cell_size, HEADER + cell_padding + y * cell_size, cell_size - 1, color)

                    player_img = None
                    # 根据 cur_pos[0] 确定方向，如果有的话
                    if hasattr(cur_pos, '__getitem__') and len(cur_pos) > 0:
                        dir_index = cur_pos[0]
                        if dir_index == Direction.UP[0]:
                            CURRENT_DIRECTION = Direction.UP
                        elif dir_index == Direction.RIGHT[0]:
                            CURRENT_DIRECTION = Direction.RIGHT
                        elif dir_index == Direction.DOWN[0]:
                            CURRENT_DIRECTION = Direction.DOWN
                        elif dir_index == Direction.LEFT[0]:
                            CURRENT_DIRECTION = Direction.LEFT

                    if CURRENT_DIRECTION == Direction.UP:
                        player_img = PLAYER_UP
                    elif CURRENT_DIRECTION == Direction.DOWN:
                        player_img = PLAYER_DOWN
                    elif CURRENT_DIRECTION == Direction.LEFT:
                        player_img = PLAYER_LEFT
                    else:
                        player_img = PLAYER_RIGHT

                    player_img = pygame.transform.scale(player_img, (cell_size - 2, cell_size - 2))
                    SCREEN.blit(player_img, (cell_padding + x * cell_size, HEADER + cell_padding + y * cell_size))
                else:
                    if color == COLOR_BLACK:
                        draw_rect(cell_padding + x * cell_size, HEADER + cell_padding + y * cell_size, cell_size, color)
                    else:
                        draw_rect(cell_padding + x * cell_size, HEADER + cell_padding + y * cell_size, cell_size - 1, color)
            else:
                # 如果 cur_pos 不是预期的格式，只绘制格子
                if color == COLOR_BLACK:
                    draw_rect(cell_padding + x * cell_size, HEADER + cell_padding + y * cell_size, cell_size, color)
                else:
                    draw_rect(cell_padding + x * cell_size, HEADER + cell_padding + y * cell_size, cell_size - 1, color)

    draw_button(2, HEIGHT - BOTTOM, WIDTH // 3, BOTTOM - 4, 'Score')
    draw_heading2(1, HEIGHT - BOTTOM + 20, WIDTH // 3, str(score))
    draw_button(2 + WIDTH // 3, HEIGHT - BOTTOM, WIDTH // 3, BOTTOM - 4, "Time")
    draw_heading2(13 + WIDTH // 3, HEIGHT - BOTTOM + 20, WIDTH // 3, msec_to_time(time))

    # 替换AI按钮为BFS按钮，并添加A*按钮
    draw_button(2 + 2 * (WIDTH // 3), HEIGHT - BOTTOM, WIDTH // 6, BOTTOM - 4, 'BFS')
    if (AI and ALGORITHM == "BFS"):
        draw_heading2(12 + 2 * (WIDTH // 3), HEIGHT - BOTTOM + 20, WIDTH // 6, 'ON')
    else:
        draw_heading2(12 + 2 * (WIDTH // 3), HEIGHT - BOTTOM + 20, WIDTH // 6, 'OFF')

    # 添加A*按钮
    draw_button(2 + 2 * (WIDTH // 3) + WIDTH // 6, HEIGHT - BOTTOM, WIDTH // 6, BOTTOM - 4, 'A*')
    if (AI and ALGORITHM == "ASTAR"):
        draw_heading2(12 + 2 * (WIDTH // 3) + WIDTH // 6, HEIGHT - BOTTOM + 20, WIDTH // 6, 'ON')
    else:
        draw_heading2(12 + 2 * (WIDTH // 3) + WIDTH // 6, HEIGHT - BOTTOM + 20, WIDTH // 6, 'OFF')

    # 显示剩余陷阱机会
    if not AI:
        draw_button(2 + 2 * (WIDTH // 3), HEIGHT - BOTTOM - 20, WIDTH // 3, 20, f'Trap Chances: {TRAP_CHANCES}')

    BUTTONS.append({
        'x': 2 + 2 * (WIDTH // 3),
        'y': HEIGHT - BOTTOM,
        'length': WIDTH // 6,
        'height': BOTTOM - 4,
        'click': bfs_toggle,
    })

    BUTTONS.append({
        'x': 2 + 2 * (WIDTH // 3) + WIDTH // 6,
        'y': HEIGHT - BOTTOM,
        'length': WIDTH // 6,
        'height': BOTTOM - 4,
        'click': astar_toggle,
    })

    pygame.display.flip()


def bfs_toggle():
    global AI, SOLVE_THREAD, ALGORITHM, MAZE, ENTRANCE, EXIT
    AI = not (AI and ALGORITHM == "BFS")  # 如果BFS已开启则关闭，否则开启
    ALGORITHM = "BFS"  # 设置算法为BFS

    if SOLVE_THREAD is not None and SOLVE_THREAD.is_alive():
        stop_thread(SOLVE_THREAD)
        SOLVE_THREAD = None

    # 重置迷宫路径
    for y in range(len(MAZE)):
        for x in range(len(MAZE[0])):
            if MAZE[y][x] != CellType.WALL and MAZE[y][x] != CellType.TRAP:  # 保留墙壁和陷阱
                MAZE[y][x] = CellType.ROAD

    # 确保起点是正确格式
    if isinstance(ENTRANCE, list):
        start_pos = ENTRANCE
    else:
        start_pos = [0, ENTRANCE[0], ENTRANCE[1]]

    SOLVE_THREAD = threading.Thread(target=solve_maze,
                                    args=(MAZE, start_pos, EXIT, draw_maze, draw_end_screen, display_time, AI, ALGORITHM))
    SOLVE_THREAD.start()


def astar_toggle():
    global AI, SOLVE_THREAD, ALGORITHM, MAZE, ENTRANCE, EXIT
    AI = not (AI and ALGORITHM == "ASTAR")  # 如果A*已开启则关闭，否则开启
    ALGORITHM = "ASTAR"  # 设置算法为A*

    if SOLVE_THREAD is not None and SOLVE_THREAD.is_alive():
        stop_thread(SOLVE_THREAD)
        SOLVE_THREAD = None

    # 重置迷宫路径
    for y in range(len(MAZE)):
        for x in range(len(MAZE[0])):
            if MAZE[y][x] != CellType.WALL and MAZE[y][x] != CellType.TRAP:  # 保留墙壁和陷阱
                MAZE[y][x] = CellType.ROAD

    # 确保起点是正确格式
    if isinstance(ENTRANCE, list):
        start_pos = ENTRANCE
    else:
        start_pos = [0, ENTRANCE[0], ENTRANCE[1]]

    SOLVE_THREAD = threading.Thread(target=solve_maze,
                                    args=(MAZE, start_pos, EXIT, draw_maze, draw_end_screen, display_time, AI, ALGORITHM))
    SOLVE_THREAD.start()


def dispatcher_click(pos):
    for button in BUTTONS:
        x, y, length, height = button['x'], button['y'], button['length'], button['height']
        pos_x, pos_y = pos
        if x <= pos_x <= x + length and y <= pos_y <= y + height:
            button['click']()


def random_maze_size():
    return random.randint(r1, r2) * 2 + 1


def menu():
    global SOLVE_THREAD, TIME_THREAD
    if SOLVE_THREAD is not None and SOLVE_THREAD.is_alive():
        stop_thread(SOLVE_THREAD)
        SOLVE_THREAD = None

    if TIME_THREAD is not None and TIME_THREAD.is_alive():
        stop_thread(TIME_THREAD)
        TIME_THREAD = None
    level = 0
    draw_menu()
    while not level:
        CLOCK.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if SOLVE_THREAD is not None and SOLVE_THREAD.is_alive():
                    stop_thread(SOLVE_THREAD)
                    SOLVE_THREAD = None

                if TIME_THREAD is not None and TIME_THREAD.is_alive():
                    stop_thread(TIME_THREAD)
                    TIME_THREAD = None
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                dispatcher_click(mouse_pos)


if __name__ == '__main__':
    menu()
