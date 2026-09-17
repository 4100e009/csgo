from collections import deque

DIRECTIONS = [(1, 0), (-1, 0), (0, -1), (0, 1)]


def inside(pos, width, height):
    return 0 <= pos[0] < width and 0 <= pos[1] < height


def simulate_move(snake, direction, food, width, height):
    head = snake[0]
    new_head = (head[0] + direction[0], head[1] + direction[1])
    if not inside(new_head, width, height) or new_head in set(snake[:-1]):
        return None
    return [new_head] + snake if new_head == food else [new_head] + snake[:-1]


def bfs_path(snake, target, width, height):
    blocked = set(snake[:-1])
    queue = deque([snake[0]])
    previous = {snake[0]: None}
    while queue:
        current = queue.popleft()
        if current == target:
            path = []
            while current != snake[0]:
                path.append(current)
                current = previous[current]
            return path[::-1]
        for dx, dy in DIRECTIONS:
            nxt = (current[0] + dx, current[1] + dy)
            if inside(nxt, width, height) and nxt not in blocked and nxt not in previous:
                previous[nxt] = current
                queue.append(nxt)
    return None


def reachable_area(snake, width, height):
    blocked = set(snake[:-1])
    queue = deque([snake[0]])
    seen = {snake[0]}
    while queue:
        current = queue.popleft()
        for dx, dy in DIRECTIONS:
            nxt = (current[0] + dx, current[1] + dy)
            if inside(nxt, width, height) and nxt not in blocked and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return len(seen)


def best_direction(snake, food, current_direction, width, height):
    candidates = []
    for direction in DIRECTIONS:
        if direction == (-current_direction[0], -current_direction[1]):
            continue
        simulated = simulate_move(snake, direction, food, width, height)
        if simulated is None:
            continue
        path = bfs_path(simulated, food, width, height) if food else None
        value = reachable_area(simulated, width, height) * 12
        if path:
            value += 500 - len(path) * 6
        if simulated[0] == food:
            value += 5000
        candidates.append((value, direction))
    return max(candidates)[1] if candidates else current_direction
