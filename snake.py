import os
import random
import time
import msvcrt
import json
from collections import deque

WIDTH = 30
HEIGHT = 15
SPEED = 0.08
MEMORY_FILE = "snake_memory.json"
ALPHA = 0.20
GAMMA = 0.90
EPSILON_START = 0.25
EPSILON_MIN = 0.03
EPSILON_DECAY = 0.995

snake = [(WIDTH // 2, HEIGHT // 2)]
direction = (1, 0)
score = 0
food = None
ai_mode = False
episode = 0
best_score = 0
best_length = 1
q_table = {}
epsilon = EPSILON_START

DIRECTIONS = [(1, 0), (-1, 0), (0, -1), (0, 1)]


def load_memory():
    global q_table, epsilon, episode, best_score, best_length
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        q_table = data.get("q_table", {})
        epsilon = data.get("epsilon", EPSILON_START)
        episode = data.get("episodes", 0)
        best_score = data.get("best_score", 0)
        best_length = data.get("best_length", 1)
    except (OSError, ValueError, json.JSONDecodeError):
        q_table = {}


def save_memory():
    data = {
        "q_table": q_table,
        "epsilon": epsilon,
        "episodes": episode,
        "best_score": best_score,
        "best_length": best_length,
    }
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except OSError:
        pass


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
    mode = "學習型 AI" if ai_mode else "玩家模式"
    print("🐍 貪食蛇 Snake - " + mode)
    print("分數:", score, "| 長度:", len(snake))
    print("AI 局數:", episode, "| 歷史最高:", best_score,
          "| 記憶狀態:", len(q_table), "個狀態")
    if ai_mode:
        print("探索率:", round(epsilon, 3))
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
        print("AI：BFS 路徑 + 安全評估 + Q-learning，A 切換、Q 離開")
    else:
        print("WASD 移動，A 開啟 AI，Q 離開")


def set_direction(new_direction):
    global direction
    if (new_direction[0] != -direction[0] or
            new_direction[1] != -direction[1]):
        direction = new_direction


def change_direction(key):
    directions = {b"w": (0, -1), b"s": (0, 1),
                  b"a": (-1, 0), b"d": (1, 0)}
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
    head = s[0]
    new_head = (head[0] + d[0], head[1] + d[1])
    if not inside(new_head):
        return None
    if new_head in set(s[:-1]):
        return None
    if new_head == food:
        return [new_head] + s
    return [new_head] + s[:-1]


def bfs_path(s, target):
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
            if nxt not in blocked and nxt not in previous:
                previous[nxt] = cur
                queue.append(nxt)
    return None


def reachable_area(s):
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


def relative_action(action):
    """0=直走、1=左轉、2=右轉。"""
    dx, dy = direction
    if action == 0:
        return direction
    if action == 1:
        return (dy, -dx)
    return (-dy, dx)


def danger_for(s, d):
    return int(simulate_move(s, d) is None)


def state_key():
    """把盤面壓縮成 Q-learning 可學習的狀態。"""
    head = snake[0]
    left = relative_action(1)
    right = relative_action(2)
    straight = direction
    danger = (danger_for(snake, straight),
              danger_for(snake, left),
              danger_for(snake, right))

    fx = 0 if food is None else (food[0] > head[0]) - (food[0] < head[0])
    fy = 0 if food is None else (food[1] > head[1]) - (food[1] < head[1])

    area = reachable_area(snake)
    area_level = 0 if area < 20 else 1 if area < 60 else 2 if area < 150 else 3
    length_level = 0 if len(snake) < 5 else 1 if len(snake) < 10 else 2 if len(snake) < 20 else 3

    return str((danger, fx, fy, area_level, length_level))


def q_values(state):
    if state not in q_table:
        q_table[state] = [0.0, 0.0, 0.0]
    return q_table[state]


def choose_action(state):
    values = q_values(state)
    if random.random() < epsilon:
        return random.randrange(3)
    best = max(values)
    choices = [i for i, v in enumerate(values) if v == best]
    return random.choice(choices)


def learn(state, action, reward, next_state, done=False):
    current = q_values(state)
    if done:
        target = reward
    else:
        target = reward + GAMMA * max(q_values(next_state))
    current[action] += ALPHA * (target - current[action])


def path_score(d, simulated):
    area = reachable_area(simulated)
    tail_safe = can_reach_tail(simulated)
    path = bfs_path(simulated, food) if food is not None else None
    value = area * 12 + (700 if tail_safe else -1400)
    if path:
        value += 500 - len(path) * 6
    if simulated[0] == food:
        value += 5000
    return value


def ai_move():
    global direction
    state = state_key()
    legal = []

    for action in range(3):
        d = relative_action(action)
        simulated = simulate_move(snake, d)
        if simulated is not None:
            learned = q_values(state)[action] * 80
            planning = path_score(d, simulated)
            legal.append((planning + learned, action, d))

    if not legal:
        return state, 0

    best_value = max(x[0] for x in legal)
    best_actions = [x for x in legal if x[0] == best_value]
    _, chosen, d = random.choice(best_actions)

    # 少量探索，讓 AI 能發現比目前策略更好的走法。
    if random.random() < epsilon:
        _, chosen, d = random.choice(legal)

    set_direction(d)
    return state, chosen


def end_episode(reward):
    global episode, best_score, best_length, epsilon
    episode += 1
    best_score = max(best_score, score)
    best_length = max(best_length, len(snake))
    epsilon = max(EPSILON_MIN, epsilon * EPSILON_DECAY)
    save_memory()


load_memory()
reset()

last_state = None
last_action = None

while True:
    draw()

    start_time = time.time()
    while time.time() - start_time < SPEED:
        if msvcrt.kbhit():
            key = msvcrt.getch().lower()
            if key == b"q":
                save_memory()
                raise SystemExit
            if key == b"a":
                ai_mode = not ai_mode
                if ai_mode:
                    reset()
                break
            if not ai_mode:
                change_direction(key)

    if ai_mode:
        last_state, last_action = ai_move()

    head = snake[0]
    new_head = (head[0] + direction[0], head[1] + direction[1])
    collision = not inside(new_head) or new_head in snake[:-1]

    if collision:
        if ai_mode and last_state is not None:
            learn(last_state, last_action, -100, last_state, True)
            end_episode(-100)
            time.sleep(0.25)
            reset()
            continue
        draw()
        print("\n遊戲結束！")
        print("最終分數:", score)
        print("按任意鍵結束...")
        msvcrt.getch()
        break

    old_distance = abs(head[0] - food[0]) + abs(head[1] - food[1]) if food else 0
    snake.insert(0, new_head)
    ate = new_head == food

    if ate:
        score += 1
        reward = 15
        food = new_food()
    else:
        snake.pop()
        new_distance = abs(new_head[0] - food[0]) + abs(new_head[1] - food[1]) if food else old_distance
        reward = 0.15 if new_distance < old_distance else -0.05

    if ai_mode and last_state is not None:
        next_state = state_key()
        learn(last_state, last_action, reward, next_state)

    if food is None:
        if ai_mode:
            end_episode(100)
            reset()
            continue
        draw()
        print("\n🎉 成功填滿整個地圖！")
        msvcrt.getch()
        break
