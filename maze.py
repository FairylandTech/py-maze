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

TITLE = "迷宫游戏"
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
    """
    根据游戏状态显示结束画面，并管理活动线程的清理和用户界面交互。
    和用户界面交互。该功能会根据用户是否成功完成游戏、是否使用了人工智能和是否按了按钮，用适当的图形更新屏幕、标题和按钮。辅助，还是得分为零。

    该函数通过在向前移动前终止活动线程（`TIME_THREAD`）、重置 AI
    重置人工智能状态，并在需要时更新高分。它还会设置
    重放游戏或返回菜单的 UI 按钮。

    :param status: 代表游戏状态，它决定了结束屏幕的内容。它支持的值包括 "complete"（成功完成）、"score_0"（失败且得分为零）。
    :param score: 玩家的最终得分，显示在终点屏幕上，用于更新高分。
    :type status: str
    :type score: int
    """
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
    """
    刷新并重新初始化全局迷宫环境。这包括生成新的随机迷宫大小、重置迷宫布局、入口和出口点、陷阱机会以及任何相关的解迷宫线程，并为解迷宫过程计时。
    以及为迷宫解谜过程计时的相关线程。在初始化新线程之前，会安全停止用于解迷宫和计时的现有活动线程。
    初始化新线程。如果之前已启用人工智能，则也会重置人工智能状态。

    :global MAZE: 当前的迷宫网格。更新为新生成的随机迷宫布局。
    :global SIZE: 当前迷宫的大小。随机决定。
    :global ENTRANCE: 迷宫入口坐标。随新迷宫的生成而更新。
    :global EXIT: 迷宫的出口坐标。随新迷宫的生成而更新。
    :global SOLVE_THREAD: 负责解迷宫的线程。重置并开始使用新的迷宫设置。
    :global TIME_THREAD: 负责跟踪和计算所耗时间的线程。如果激活，则在停止前一个线程后重置并重新初始化。
    :global AI: 是否启用人工智能辅助。如果当前已启用，则自动重置。
    :global TRAP_CHANCES: 在迷宫中放置陷阱的剩余机会。在刷新过程中重置。

    :return: None
    :rtype: None
    """
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
    """
    绘制带有可选难度选项的游戏主菜单。

    该函数初始化并验证用于存储最高分的高分文件
    如果该文件不存在，则会以默认值创建一个文件。然后准备并渲染游戏的主菜单屏幕，其中包含可选择的难度级别。为用户交互配置按钮状态和位置交互。

    :raises OSError: 如果高分文件或目录因权限或其他操作系统级问题而无法创建或访问权限或其他操作系统层面的问题而无法创建或访问。
    :return: None
    :rtype: None
    """
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
    """
    初始化全局变量，以设置 "简易 "级别。此函数设置全局变量 `r1`、`r2` 和 `level_select` 的值。level_select "的值，以配置 "简易 "关卡模式的设置。
    初始化完成后，它将调用 `refresh` 函数来最终完成设置过程。

    :return: None
    :rtype: None
    """
    global r1
    global r2
    global level_select
    r1 = 5
    r2 = 7
    level_select = "LEVEL 1 : Easy"
    refresh()


def medium():
    """
    将全局变量调整为中等难度。

    此函数将全局变量 `r1`、`r2` 和 `level_select` 设置为与中等难度级别相对应的特定值。设置为与中等难度级别相对应的特定值。然后调用刷新 "函数来应用这些设置。

    :raises NameError: 如果 "刷新 "函数未定义或不可访问。
    :raises TypeError: 如果 `level_select` 被错误访问或更改。

    :return: None
    :rtype: None
    """
    global r1
    global r2
    global level_select
    r1 = 10
    r2 = 12
    level_select = "LEVEL 2 : Medium"
    refresh()


def hard():
    """
    设置全局变量，将游戏配置为 "困难 "难度。

    此函数通过更新变量 `r1`、`r2` 和`level_select` 变量来定义 "Hard "难度级别的参数。全局 然后调用全局 `refresh` 函数来应用这些更改。

    :raises NameError: 如果未定义所需的全局变量或 `refresh` 函数未定义。

    :return: None
    :rtype: None
    """
    global r1
    global r2
    global level_select
    r1 = 15
    r2 = 17
    level_select = "LEVEL 3 : Hard"
    refresh()


def display_high_score():
    """
    从与当前游戏难度相对应的文件中读取并返回高分。难度。高分是根据全局变量 `r1` 的值检索的。
    变量的值来获取高分，该变量决定了游戏的难度级别：5 分代表简单，10 分代表中等，15 分代表困难、
    15 为困难。如果在文件读取过程中出现任何错误，默认情况下会返回字符串 "0"。
    返回字符串 "0"。

    :return: 当前难度下记录的最高分，如果出现错误则为 "0"。
    :rtype: str
    """
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
    """
    将毫秒转换为格式为 MM:SS 的时间字符串。

    该函数接收以毫秒为单位的输入，并将其转换为以标准 MM:SS 格式表示时间长度的字符串。它确保分钟和秒钟都正确归零到两位数。

    :param msec: 输入持续时间（毫秒）。
    :type msec: int
    :return: 以 MM:SS 格式表示持续时间的字符串。
    :rtype: str
    """
    sec = msec // 100
    min, sec = divmod(sec, 60)
    min_str = ''
    sec_str = ''
    if min == 0:
        min_str = '00'
    elif 0 < min < 10:
        min_str = '0' + str(min)
    else:
        min_str = str(min)
    if sec == 0:
        sec_str = '00'
    elif 0 < sec < 10:
        sec_str = '0' + str(sec)
    else:
        sec_str = str(sec)
    return min_str + ':' + sec_str


def display_time(curr_time, score):
    """
    在屏幕上渲染并显示当前分数和时间。该功能在保持视觉结构（如按钮屏幕上的特定区域更新分数和转换后的时间值，同时保持视觉结构，如按钮和标题，以提高清晰度。
    和标题等视觉结构，以确保清晰度。它还会刷新显示屏，以确保更新可见。

    :param curr_time: 以毫秒为单位转换并显示在屏幕上的时间量。
    :type curr_time: int
    :param score: 屏幕上显示的当前分数。
    :type score: int
    :return: None
    :rtype: None
    """
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
    """
    在屏幕上绘制迷宫以及当前玩家的位置、得分、时间和用户界面元素。

    该函数负责渲染迷宫网格、玩家头像、用户界面按钮、标题、分数和游戏状态
    指示器。它还会根据游戏状态调整按钮和显示行为，如人工智能算法模式
    (如 BFS、A*）或手动模式下留下的陷阱机会。

    :param maze: 以 2D 单元列表或网格的形式表示，其中每个单元都有一个定义其状态的特定类型（如墙壁、可穿越、陷阱等）。(如墙、可穿越、陷阱等）。
    :param cur_pos: 玩家在迷宫中的当前位置。通常是一个列表，其中第一个元素表示方向，后面的元素则定义了 X 和 Y 坐标。
    :param score:代表玩家当前得分的整数。
    :param time: 游戏耗时（毫秒）。

    :return: None
    :rtype: None
    """
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
    if AI and ALGORITHM == "BFS":
        draw_heading2(12 + 2 * (WIDTH // 3), HEIGHT - BOTTOM + 20, WIDTH // 6, 'ON')
    else:
        draw_heading2(12 + 2 * (WIDTH // 3), HEIGHT - BOTTOM + 20, WIDTH // 6, 'OFF')

    # 添加A*按钮
    draw_button(2 + 2 * (WIDTH // 3) + WIDTH // 6, HEIGHT - BOTTOM, WIDTH // 6, BOTTOM - 4, 'A*')
    if AI and ALGORITHM == "ASTAR":
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
    """
    切换迷宫解法应用程序的广度优先搜索（BFS）算法。
    全局状态决定是否启用或禁用 BFS，该函数将重置必要的变量、清理当前迷宫并在适当情况下启动解迷宫线程。
    必要的变量，清理当前迷宫，并在适当时启动解迷宫线程。

    :raises RuntimeError: 如果求解线程无法正常停止，则发生该事件。
    """
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
    """
    切换解迷宫的 A* 算法并管理其线程执行。使用 A* 算法交替人工智能的状态，重置特定迷宫状态，并启动解迷宫线程，同时确保正确处理现有线程。
    同时确保现有线程得到妥善处理。

    :return: None
    :rtype: None

    :raises AttributeError: 如果某些全局变量（如 AI、ALGORITHM 或 MAZE）定义错误或丢失，则会引发定义不正确或丢失时会引发。
    :raises TypeError: 当更新迷宫起始位置时，如果 ENTRANCE 或 EXIT 参数的格式与预期不符，则会发生该事件。
    """
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
