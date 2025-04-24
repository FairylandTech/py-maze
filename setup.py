import cx_Freeze
import sys

is_windows = sys.platform == "win32"

executables = [
    cx_Freeze.Executable(
        "maze.py",
        base="Win32GUI" if is_windows else None
    ),
]

cx_Freeze.setup(
    name="Mazer",
    options={
        "build_exe": {
            "packages": [
                "pygame",
                "time",
                "threading",
                "random",
                "heapq",
                "queue",
                "sys",
                "os",
            ],
            "include_files": [
                "./assets/2.mp3",
                "./assets/fonts/msyh.ttf",
                "./assets/images/back button.png",
                "./assets/images/easy.png",
                "./assets/images/hard.png",
                "./assets/images/medium.png",
                "./assets/images/player_up.png",
                "./assets/images/player_down.png",
                "./assets/images/player_left.png",
                "./assets/images/player_right.png",
            ]
        }
    },
    executables=executables

)
