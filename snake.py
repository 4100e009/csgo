import os
import random
import time
import msvcrt
from collections import deque

WIDTH = 30
HEIGHT = 15
SPEED = 0.08

snake = [(WIDTH // 2, HEIGHT // 2)]
direction = (1, 0)
score = 0
food = None
ai_mode = False

DIRECTIONS = [(1, 0), (-1, 0), (0, -1), (0, 1)]


def new_food():
    empty = [(x, y) for y in range(HEIGHT) for x in range(WIDTH)
             if (x, y) not in snake]
    return random.choice(empty) if empty else None


def reset():
    global snake, direction, score, food
    snake = [(WIDTH // 2, HEIGHT // 2)]
    direction = (1, 0)
    score = 0
    food = new_food()


def draw():
    os.system("cls")
    mode = "進階 AI 自動模式" if ai_mode else "玩家模式"
    print("🐍 貪食蛇 Snake - " + mode)
    print("分數:", score)
    print("+" + "-" * WIDTH + "+")

    body = set(snake[1:])
    for y in range(HEIGHT):
        row = ""
        for x in range(WIDTH):
            pos = (x, y)
            if pos == snake[0]:
                row += "O"
            elif pos in body:
                row += "o"
            elif pos == food:
                row += "*"
            else:
                row += " "
        print("|" + row + "|")

    print("+" + "-" * WIDTH + "+")
    if ai_mode:
        print("AI：路徑搜尋 + 安全性評估，按 A 切換、Q 離開")
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


def inside(pos):
    x, y = pos
    return 0 <= x < WIDTH and 0 <= y < HEIGHT


def neighbors(pos):
    x, y = pos
    for dx, dy in DIRECTIONS:
        nxt = (x + dx, y + dy)
        if inside(nxt):
            yield nxt


def simulate_move(s, d):
    """模擬一步移動，回傳新蛇身；若撞牆/身體則回傳 None。"""
    head = s[0]
    new_head = (head[0] + d[0], head[1] + d[1])
    if not inside(new_head):
        return None

    # 沒吃到食物時，尾巴會移走，因此允許進入原本的尾巴位置。
    occupied = set(s[:-1])
    if new_head in occupied:
        return None

    if new_head == food:
        return [new_head] + s
    return [new_head] + s[:-1]


def bfs_path(s, target):
    """BFS 找到目前蛇身狀態下到 target 的最短安全路徑。"""
    start = s[0]
    blocked = set(s[:-1])
    queue = deque([start])
    previous = {start: None}

    while queue:
        cur = queue.popleft()
        if cur == target:
            path = []
            while cur != start:
                path.append(cur)
                cur = previous[cur]
            path.reverse()
            return path

        for nxt in neighbors(cur):
            if nxt in blocked or nxt in previous:
                continue
            previous[nxt] = cur
            queue.append(nxt)

    return None


def reachable_area(s):
    """計算蛇頭目前能活動的空間，越大越不容易把自己困死。"""
    start = s[0]
    blocked = set(s[:-1])
    queue = deque([start])
    seen = {start}

    while queue:
        cur = queue.popleft()
        for nxt in neighbors(cur):
            if nxt not in blocked and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return len(seen)


def can_reach_tail(s):
    """檢查走這一步後，蛇頭是否仍有機會追到尾巴。"""
    if len(s) <= 2:
        return True
    target = s[-1]
    blocked = set(s[:-1])
    queue = deque([s[0]])
    seen = {s[0]}

    while queue:
        cur = queue.popleft()
        if cur == target:
            return True
        for nxt in neighbors(cur):
            if nxt in blocked and nxt != target:
                continue
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return False


def direction_from(head, next_pos):
    return (next_pos[0] - head[0], next_pos[1] - head[1])


def ai_move():
    """進階 AI：BFS 尋路 + 吃食物後的安全檢查 + 空間評估。"""
    global direction

    head = snake[0]
    legal = []

    for d in DIRECTIONS:
        if d == (-direction[0], -direction[1]):
            continue
        simulated = simulate_move(snake, d)
        if simulated is not None:
            legal.append((d, simulated))

    if not legal:
        return

    best = None

    for d, simulated in legal:
        # 先評估這一步之後能不能活著追到尾巴。
        tail_safe = can_reach_tail(simulated)
        area = reachable_area(simulated)

        # 尋找通往食物的路徑。
        path = bfs_path(simulated, food) if food is not None else None

        # 若能吃到食物，模擬整條路徑，確認最後不會立刻把自己困死。
        food_safe = False
        path_len = 9999
        if path:
            path_len = len(path)
            test = simulated
            valid = True
            for next_pos in path:
                d2 = direction_from(test[0], next_pos)
                test = simulate_move(test, d2)
                if test is None:
                    valid = False
                    break
            if valid:
                food_safe = can_reach_tail(test) and reachable_area(test) >= max(3, len(test) // 3)

        # 評分：安全性優先，其次追食物，最後偏好較大的活動空間。
        score_value = 0
        score_value += area * 12
        score_value += 500 if tail_safe else -1000
        if food_safe:
            score_value += 3000
            score_value -= path_len * 15
        elif path:
            score_value += 300
            score_value -= path_len * 5
        if simulated[0] == food:
            score_value += 5000

        # 避免太靠近死角；可達空間越大越優先。
        candidate = (score_value, d, simulated)
        if best is None or candidate[0] > best[0]:
            best = candidate

    set_direction(best[1])


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

    if not inside(new_head) or new_head in snake[:-1]:
        game_over()
        break

    snake.insert(0, new_head)

    if new_head == food:
        score += 1
        food = new_food()
        if food is None:
            draw()
            print("\n🎉 AI 成功填滿整個地圖！")
            print("最終分數:", score)
            msvcrt.getch()
            break
    else:
        snake.pop()
