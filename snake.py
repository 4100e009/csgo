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
food = None
ai_mode = False


def new_food():
    while True:
        food = (random.randrange(WIDTH), random.randrange(HEIGHT))
        if food not in snake:
            return food


def reset():
    global snake, direction, score, food
    snake = [(WIDTH // 2, HEIGHT // 2)]
    direction = (1, 0)
    score = 0
    food = new_food()


def draw():
    os.system("cls")
    mode = "AI 自動模式" if ai_mode else "玩家模式"
    print("🐍 貪食蛇 Snake - " + mode)
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
    if ai_mode:
        print("AI 正在自動遊玩，按 Q 離開")
    else:
        print("WASD 移動，A 開啟 AI，Q 離開")


def set_direction(new_direction):
    global direction
    if (new_direction[0] != -direction[0] or
            new_direction[1] != -direction[1]):
        direction = new_direction


def change_direction(key):
    directions = {
        b"w": (0, -1),
        b"s": (0, 1),
        b"a": (-1, 0),
        b"d": (1, 0),
    }
    if key in directions:
        set_direction(directions[key])


def safe(pos):
    x, y = pos
    return (0 <= x < WIDTH and 0 <= y < HEIGHT and pos not in snake)


def ai_move():
    """簡單的安全 AI：優先接近食物，同時避免撞牆和身體。"""
    head = snake[0]
    candidates = [
        (1, 0), (-1, 0), (0, -1), (0, 1)
    ]

    # 優先選擇距離食物較近的方向
    candidates.sort(key=lambda d: abs(head[0] + d[0] - food[0]) +
                    abs(head[1] + d[1] - food[1]))

    for d in candidates:
        if d == (-direction[0], -direction[1]):
            continue
        next_pos = (head[0] + d[0], head[1] + d[1])
        if safe(next_pos):
            set_direction(d)
            return

    # 如果所有方向都不安全，嘗試任何不會立即撞牆的方向
    for d in candidates:
        next_pos = (head[0] + d[0], head[1] + d[1])
        if safe(next_pos):
            set_direction(d)
            return


def game_over():
    draw()
    print("\n遊戲結束！")
    print("最終分數:", score)
    print("按任意鍵結束...")
    msvcrt.getch()


reset()

while True:
    draw()

    start_time = time.time()
    while time.time() - start_time < SPEED:
        if msvcrt.kbhit():
            key = msvcrt.getch().lower()
            if key == b"q":
                raise SystemExit
            if key == b"a":
                ai_mode = not ai_mode
                break
            if not ai_mode:
                change_direction(key)

    if ai_mode:
        ai_move()

    head = snake[0]
    new_head = (head[0] + direction[0], head[1] + direction[1])

    if (new_head[0] < 0 or new_head[0] >= WIDTH or
            new_head[1] < 0 or new_head[1] >= HEIGHT or
            new_head in snake):
        game_over()
        break

    snake.insert(0, new_head)

    if new_head == food:
        score += 1
        food = new_food()
    else:
        snake.pop()
