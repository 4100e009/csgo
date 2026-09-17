import random

ALPHA = 0.20
GAMMA = 0.90
EPSILON_MIN = 0.03
EPSILON_DECAY = 0.995


def q_values(table, state):
    if state not in table:
        table[state] = [0.0, 0.0, 0.0]
    return table[state]


def choose_action(table, state, epsilon):
    values = q_values(table, state)
    if random.random() < epsilon:
        return random.randrange(3)
    best = max(values)
    choices = [i for i, value in enumerate(values) if value == best]
    return random.choice(choices)


def learn(table, state, action, reward, next_state, done=False):
    values = q_values(table, state)
    target = reward if done else reward + GAMMA * max(q_values(table, next_state))
    values[action] += ALPHA * (target - values[action])


def decay_epsilon(epsilon):
    return max(EPSILON_MIN, epsilon * EPSILON_DECAY)
