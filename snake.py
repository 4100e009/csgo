import os
import random
import time
import msvcrt

WIDTH = 30
HEIGHT = 15
SPEED = 0.12

snake = [(WIDTH // 2, HEIGHT // 2)]
direction = (1, 0)
score = 0


def new_food():
    while True:
        food = (random.randrange(WIDTH), random.randrange(HEIGHT))
        if food not in snake:
            return food


food = new_food()


def draw():
    os.system("cls")
    print("🐍 貪食蛇 Snake")
    print("分數:", score)
    print("+" + "-" * WIDTH + "+")

    for y in range(HEIGHT):
        row = ""
        for x in range(WIDTH):
            if (x, y) == snake[0]:
                row += "O"
            elif (x, y) in snake:
                row += "o"
            elif (x, y) == food:
                row += "*"
            else:
                row += " "
        print("|" + row + "|")

    print("+" + "-" * WIDTH + "+")
    print("WASD 移動，Q 離開")


def change_direction(key):
    global direction

    directions = {
        b"w": (0, -1),
        b"s": (0, 1),
        b"a": (-1, 0),
        b"d": (1, 0),
    }

    if key in directions:
        new_direction = directions[key]
        # 不允許直接往自己的身體方向走
        if (new_direction[0] != -direction[0] or
                new_direction[1] != -direction[1]):
            direction = new_direction


def game_over():
    draw()
    print("\n遊戲結束！")
    print("最終分數:", score)
    print("按任意鍵結束...")
    msvcrt.getch()


while True:
    draw()

    start_time = time.time()
    while time.time() - start_time < SPEED:
        if msvcrt.kbhit():
            key = msvcrt.getch().lower()
            if key == b"q":
                print("\n遊戲結束！")
                raise SystemExit
            change_direction(key)

    head = snake[0]
    new_head = (head[0] + direction[0], head[1] + direction[1])

    # 撞牆
    if (new_head[0] < 0 or new_head[0] >= WIDTH or
            new_head[1] < 0 or new_head[1] >= HEIGHT):
        game_over()
        break

    # 撞到自己
    if new_head in snake:
        game_over()
        break

    snake.insert(0, new_head)

    # 吃到食物
    if new_head == food:
        score += 1
        food = new_food()
    else:
        snake.pop()
