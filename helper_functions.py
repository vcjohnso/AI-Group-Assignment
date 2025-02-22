import random
from re import sub

import numpy as np
import random
from datetime import datetime

import os
import pygame

import math

import sys

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

base_path = os.path.dirname(os.path.abspath(__file__))

font_path = os.path.join(base_path, "./font/Joystix.ttf")
font = pygame.font.Font(font_path, 35)

font_details = pygame.font.Font(font_path, 12)


# Stores the settings for each experiment. The first element in each experiment's array represents the first action it takes, 2nd element represents the 2nd.
# The 3rd (in the case of experiment 3) represents the learning rate and discount factor
experiment_settings = {
    '1a' : [
        [500, "PRandom"],
        [7500, "PRandom"]
    ],
    '1b' : [
        [500, "PRandom"],
        [7500, "PGreedy"],
    ],
    '1c' : [
        [500, "PRandom"],
        [7500, "PExploit"]
    ],
    '2' : [
        [500,"PRandom"],
        [7500, "PExploit"]
    ],
    '3' : [
        [500, "PRandom"],
        [7500, "PExploit"],
        [0.15, 0.45]
    ],
    '4' : [
        [500,"PRandom"],
        [7500, "PExploit"]
    ],
}


def set_points_pickup(points_map, points_to_change_arr):
    for point in points_to_change_arr:
        points_map[point]["pickup"] = True

    return points_map


def set_points_dropoff(points_map, points_to_change_arr):
    for point in points_to_change_arr:
        points_map[point]["dropoff"] = True

    return points_map


def policy_verify(current_policy):
    if not isinstance(current_policy, (str)):
        return False
    elif current_policy == "PRandom":
        return True
    elif current_policy == "PExploit":
        return True
    elif current_policy == "PGreedy":
        return True
    else:
        return False


def step_verify(steps):
    if not isinstance(steps, int):
        return False
    elif steps < 1:
        return False
    else:
        return True


def return_position_reward(agent, pos_in_state_map):
    if pos_in_state_map["pickup"] == True:
        if pos_in_state_map["special_block"].get_block_count() > 0 and agent.get_block_count() == 0:
            return 13
    elif pos_in_state_map["dropoff"] == True:
        if pos_in_state_map["special_block"].get_block_count() < pos_in_state_map["special_block"].get_capacity() and agent.get_block_count() == 1:
            return 13
    return -1


def check_possible_actions(agent_pos, state_map):
    actions = []
    blocked_direction = ""
    if agent_pos[0] < 4:
        if not state_map["{},{}".format(agent_pos[0] + 1, agent_pos[1])]["occupied"]:
            actions.append("east")
        else:
            blocked_direction = "east"
    if agent_pos[0] > 0:
        if not state_map["{},{}".format(agent_pos[0] - 1, agent_pos[1])]["occupied"]:
            actions.append("west")
        else:
            blocked_direction = "west"
    if agent_pos[1] < 4:
        if not state_map["{},{}".format(agent_pos[0], agent_pos[1] + 1)]["occupied"]:
            actions.append("south")
        else:
            blocked_direction = "south"
    if agent_pos[1] > 0:
        if not state_map["{},{}".format(agent_pos[0], agent_pos[1] - 1)]["occupied"]:
            actions.append("north")
        else:
            blocked_direction = "north"
    return actions, blocked_direction


def get_best_action(agent_pos, actions, q_table):
    max_val = -99
    prev_max_val = max_val
    best_action = ""

    duplicate_actions = [best_action]

    seed_value = random.randrange(sys.maxsize)
    random.seed(seed_value)

    # Gets the agent with the max q value while collecting a list of actions 
    # that have duplicate q values
    for action in actions:
        max_val = max(max_val, q_table[agent_pos[0]][agent_pos[1]][action])
        if max_val > prev_max_val:
            prev_max_val = max_val
            best_action = action
            duplicate_actions = [best_action]
        elif max_val == q_table[agent_pos[0]][agent_pos[1]][action]:
            duplicate_actions.append(action)
        
    if len(duplicate_actions) > 1 and max_val == prev_max_val:
        best_action = random.choice(duplicate_actions)

    return best_action


def check_if_best_blocked(agent, q_table, blocked_direction):
    agent_pos = agent.get_coor()
    actions = ["east", "west", "south", "north"]
    if blocked_direction == get_best_action(agent_pos, actions, q_table):
        agent.increment_blocked_counter()
        agent.add_to_blocked_list()


def q_learning(mode, agent, q_table, state_map, learning_rate, discount_factor):
    agent_pos = agent.get_coor()
    actions, blocked_direction = check_possible_actions(agent_pos, state_map)
    # check if other agent is blocking the best action
    if blocked_direction != "": # and mode != "PRandom"
        check_if_best_blocked(agent, q_table, blocked_direction)

    action_to_perform = ""
    best_action = get_best_action(agent_pos, actions, q_table)

    seed_value = random.randrange(sys.maxsize)
    random.seed(seed_value)

    if mode == "PRandom":
        action_to_perform = random.choice(actions)
    else:
        if mode == "PGreedy":
            action_to_perform = best_action

        elif mode == "PExploit":
            if len(actions) > 1:
                actions.remove(best_action)
                random_action = random.choice(actions)

                exploit_choice = random.randint(1,100)
                if exploit_choice <= 80:
                    action_to_perform = best_action
                else:
                    action_to_perform = random_action
            else:
                action_to_perform = best_action

    # Applys the q learning equation
    temp_reward = -1

    # Checks to see if current position is a pickup spot or dropoff spot
    # If so, it checks to see if it should give a reward of 13 if it's able to
    # dropoff/pickup a block
    
    new_agent_pos = calculate_new_coor(action_to_perform, agent_pos)
    actions_for_new_state, null_block_direction = check_possible_actions(new_agent_pos, state_map)
    second_action_to_perform = get_best_action(new_agent_pos, actions_for_new_state, q_table)

    if state_map["{},{}".format(new_agent_pos[0], new_agent_pos[1])]["pickup"] == True or state_map["{},{}".format(new_agent_pos[0], new_agent_pos[1])]["dropoff"] == True:
        temp_reward = return_position_reward(agent, state_map["{},{}".format(new_agent_pos[0], new_agent_pos[1])])

    temporal_difference = temp_reward + discount_factor * q_table[new_agent_pos[0]][new_agent_pos[1]][second_action_to_perform] - q_table[agent_pos[0]][agent_pos[1]][action_to_perform]
    new_q_value = q_table[agent_pos[0]][agent_pos[1]][action_to_perform] + learning_rate * temporal_difference

    q_table[agent_pos[0]][agent_pos[1]][action_to_perform] = new_q_value

    # Returns updated q table, updated map containing the information about each point, as well as the action that is to be performed by the agent
    return q_table, state_map, action_to_perform


def sarsa_learning(agent, q_table, state_map, learning_rate, discount_factor, policy, steps, action_to_perform):
    agent_pos = agent.get_coor()
    actions = []
    agent_start = agent_pos[:]
    actions = check_available_moves(agent, agent_pos, state_map)

    
    if steps <= 500: #PRandom
        if action_to_perform in actions:
            current_q_value = q_table[agent_start[0]][agent_start[1]][action_to_perform]
        else:
            current_q_value, action_to_perform = PRandom(actions,q_table, agent_pos)

        next_q_value, reward, next_action, state_map = Random_Q(action_to_perform, q_table, state_map, agent_pos,agent)
    else: #PExploit
        if action_to_perform in actions:
            current_q_value = q_table[agent_start[0]][agent_start[1]][action_to_perform]
        else:
            current_q_value, action_to_perform = PExploit(actions,q_table,agent_pos, policy)
        
        next_q_value, reward, next_action, state_map = Exploit_Q(action_to_perform, q_table, state_map, agent_pos, policy,agent)
    
    #apply sarsa
    temporal_difference = reward + discount_factor * next_q_value - current_q_value
    new_q_value = current_q_value + learning_rate * temporal_difference
    q_table[agent_start[0]][agent_start[1]][action_to_perform] = new_q_value

    return q_table, state_map, action_to_perform, next_action


def check_available_moves(agent, agent_pos, state_map):
    actions = []
    move_up = agent_pos[1]-1
    move_down = agent_pos[1]+1
    move_left = agent_pos[0]-1
    move_right = agent_pos[0]+1
    # Checks to see what actions are possible for the current agent
    if move_right <= 4 and state_map["{},{}".format(move_right, agent_pos[1])]["occupied"] == False:
        actions.append("east")
    if move_left >= 0 and state_map["{},{}".format(move_left, agent_pos[1])]["occupied"] == False:
        actions.append("west")
    if move_down <= 4 and state_map["{},{}".format(agent_pos[0], move_down)]["occupied"] == False:
        actions.append("south")
    if move_up >= 0 and state_map["{},{}".format(agent_pos[0], move_up)]["occupied"] == False:
        actions.append("north")
    
    
    return actions


def PRandom(actions, q_table, agent_pos):
    num = len(actions)
    
    random.seed(datetime.now())
    index = random.randrange(0,num)
    
    q_value = q_table[agent_pos[0]][agent_pos[1]][actions[index]]
    direction = actions[index]

    return q_value, direction


def Random_Q(action_to_perform, q_table, state_map, agent_pos,agent):
    agent_next_pos = agent_pos[:]
    if action_to_perform == "north":
        agent_next_pos[1] -= 1
    elif action_to_perform == "south":
        agent_next_pos[1] += 1
    elif action_to_perform == "east":
        agent_next_pos[0] += 1
    elif action_to_perform == "west":
        agent_next_pos[0] -= 1

    actions = check_available_moves(agent,agent_next_pos, state_map)
    
    random.seed(datetime.now())
    index = random.randrange(0,len(actions))
    
    temp_reward = -1
    
    if state_map["{},{}".format(agent_next_pos[0], agent_next_pos[1])]["pickup"] == True or state_map["{},{}".format(agent_next_pos[0], agent_next_pos[1])]["dropoff"] == True:
        temp_reward = return_position_reward(agent, state_map["{},{}".format(agent_next_pos[0], agent_next_pos[1])])
    
    direction = actions[index]
    next_q_value = q_table[agent_next_pos[0]][agent_next_pos[1]][direction]
    current_pos_as_key = "{},{}".format(agent_next_pos[0], agent_next_pos[1])
    state_map[current_pos_as_key]["occupied"] = True
    return next_q_value, temp_reward, direction, state_map


def Exploit_Q(action_to_perform, q_table, state_map, agent_pos, epsilon,agent):
    #Moves agent to action "a" and gets Q(a',s') value
    agent_next_pos = agent_pos[:]
    if action_to_perform == "north":
        agent_next_pos[1] -= 1
    elif action_to_perform == "south":
        agent_next_pos[1] += 1
    elif action_to_perform == "east":
        agent_next_pos[0] += 1
    elif action_to_perform == "west":
        agent_next_pos[0] -= 1
    
    actions = check_available_moves(agent, agent_next_pos, state_map)
    
    random.seed(datetime.now())
    
    probability = random.uniform(0,1)
    
    max_action = get_best_action(agent_next_pos, actions, q_table)
    max_q_value = q_table[agent_next_pos[0]][agent_next_pos[1]][max_action]

    if len(actions) > 1:
        if probability <= epsilon:
            actions.remove(max_action)
            next_q_value, action_to_perform = PRandom(actions, q_table, agent_pos) 
        else:
            next_q_value = max_q_value
            action_to_perform = max_action
    else:
        action_to_perform = actions[0]
        next_q_value = q_table[agent_pos[0]][agent_pos[1]][action_to_perform]
    
    temp_reward = -1
    
    if state_map["{},{}".format(agent_next_pos[0], agent_next_pos[1])]["pickup"] == True or state_map["{},{}".format(agent_next_pos[0], agent_next_pos[1])]["dropoff"] == True:
        temp_reward = return_position_reward(agent, state_map["{},{}".format(agent_next_pos[0], agent_next_pos[1])])
    
    current_pos_as_key = "{},{}".format(agent_next_pos[0], agent_next_pos[1])
    state_map[current_pos_as_key]["occupied"] = True
    return next_q_value, temp_reward, action_to_perform, state_map


def PExploit(actions, q_table, agent_pos, epsilon):
    random.seed(datetime.now())
    
    probability = random.uniform(0,1)
    
    max_action = get_best_action(agent_pos, actions, q_table)
    max_q_value = q_table[agent_pos[0]][agent_pos[1]][max_action]
    
    if len(actions) > 1:
        if probability <= epsilon:
            actions.remove(max_action)
            current_q_value, action_to_perform = PRandom(actions, q_table, agent_pos) 
        else:
            current_q_value = max_q_value
            action_to_perform = max_action
    else:
        action_to_perform = actions[0]
        current_q_value = q_table[agent_pos[0]][agent_pos[1]][action_to_perform]
        
    return current_q_value, action_to_perform


def choose_max_action(actions,q_table,agent_pos):
    max_val = -99
    prev_max_val = max_val
    val_to_use = 0
    best_action = ""
    action_to_perform = ""
    duplicate_actions = [best_action]
        
    seed_value = random.randrange(sys.maxsize)
    random.seed(seed_value)

    for action in actions:
        max_val = max(max_val, q_table[agent_pos[0]][agent_pos[1]][action])
        if max_val > prev_max_val:
            prev_max_val = max_val
            best_action = action
            duplicate_actions = [best_action]
        elif max_val == q_table[agent_pos[0]][agent_pos[1]][action]:
            duplicate_actions.append(action)
        
    if len(duplicate_actions) > 1 and max_val == prev_max_val:
        best_action = random.choice(duplicate_actions)
    
    
    return best_action, max_val


def generate_qtable():
    q_table = []

    for x in range(0, 5):
        q_table.append([])
        for y in range(0, 5):
            q_table[x].append({
                "north": 0,
                "south": 0,
                "east": 0,
                "west": 0
            })

    return q_table


def generate_heatMap():
    heatmap = np.zeros((5, 5), dtype=int)
    return heatmap


def update_heatmap(pos, heatmap):
    heatmap[pos[0]][pos[1]] += 1
    return heatmap


def check_dropoff_capacity(state_map, dropoff_pos):
    for pos in dropoff_pos:
        if state_map['{},{}'.format(pos[0], pos[1])]["special_block"].get_capacity() != state_map['{},{}'.format(pos[0], pos[1])]["special_block"].get_block_count():
            return False
    return True


def reset_world(male, female, state_map, pickup_positions, dropoff_positions, pickup_max_count, init_positions):
    # Resets the block count for the pickup spots
    for pos in pickup_positions:
        state_map['{},{}'.format(pos[0], pos[1])]["special_block"].set_block_count(pickup_max_count)

    # Resets block count back to 0 for the dropoff spots
    for pos in dropoff_positions:
        state_map['{},{}'.format(pos[0], pos[1])]["special_block"].set_block_count(0)

    for key in state_map:
        state_map[key]["occupied"] = False

    # Resets the agent's position back to its initial spot
    male.set_block_count(0)
    male.set_coor(init_positions[0])
    state_map["{},{}".format(init_positions[0][0], init_positions[0][1])]["occupied"] = True

    female.set_block_count(0)
    female.set_coor(init_positions[1])
    state_map["{},{}".format(init_positions[1][0], init_positions[1][1])]["occupied"] = True

    return male, female, state_map


def display_game_details(male, female, dropoff_capacity, pickup_capacity, games_count, window):
    male_count = font_details.render("Male block count = {}".format(male.get_block_count()), 1, (255, 255, 255))
    female_count = font_details.render("Female block count = {}".format(female.get_block_count()), 1, (255, 255, 255))

    games_count_details = font_details.render("Game: {}".format(games_count), 1, (255, 255, 255))

    dropoff_capacity_details = font_details.render("Dropoff capacity = {}".format(dropoff_capacity), 1, (255, 255, 255))
    pickup_capacity_details = font_details.render("Pickup max count = {}".format(pickup_capacity), 1, (255, 255, 255))

    male_details = font_details.render("Male = Blue", 1, (0, 0, 255))
    female_details = font_details.render("Female = Pink", 1, (255, 105, 180))
    pickup_details = font_details.render("Pickup = Green", 1, (50, 205, 50))
    dropoff_details = font_details.render("Dropoff = Purple", 1, (138, 43, 226))

    window.blit(male_count, (20,420))
    window.blit(female_count, (20, 440))
    window.blit(games_count_details, (20, 460))

    window.blit(dropoff_capacity_details, (280, 420))
    window.blit(pickup_capacity_details, (280, 440))

    window.blit(pickup_details, (80, 40))
    window.blit(dropoff_details, (80, 60))
    window.blit(male_details, (290, 40))
    window.blit(female_details, (290, 60))


def draw_arrow(screen, color, start, end):
    pygame.draw.line(screen, color, start, end, 2)
    rotation = math.degrees(math.atan2(start[1]-end[1], end[0]-start[0])) + 90
    pygame.draw.polygon(screen, color, ((end[0] + 5 * math.sin(math.radians(rotation)), end[1] + 5 * math.cos(math.radians(rotation))), (end[0] + 5 * math.sin(math.radians(rotation - 120)), end[1]+ 5 *math.cos(math.radians(rotation-120))), (end[0]+ 5 *math.sin(math.radians(rotation+120)), end[1]+ 5 *math.cos(math.radians(rotation+120)))))


def calculate_new_pos(action, pos):
    x = pos[0]
    y = pos[1]

    if action == "north":
        return ((165 + x * 40), (155 + (y - 0.25) * 40))
    if action == "south":
        return ((165 + x * 40), (155 + (y + 0.25) * 40))
    if action == "east":
        return ((165 + (x + 0.25) * 40), (155 + y * 40))
    return ((165+ (x - 0.25) * 40), (155 + y * 40))


def calculate_new_coor(action, coor):
    x = coor[0]
    y = coor[1]

    if action == "north":
        return (x, y - 1)
    if action == "south":
        return (x, y + 1)
    if action == "east":
        return (x + 1, y)
    return (x - 1, y)


def display_arrows(win, q_table):
    for x in range(0, len(q_table)):
        for y in range(0, len(q_table)):
            actions = []
            if x != 0:
                actions.append("west")
            if y != 0:
                actions.append("north")
            if x != 4:
                actions.append("east")
            if y != 4:
                actions.append("south")

            if len(actions) > 0:
                max_val = -99
                prev_max_val = max_val
                duplicate_actions = [max_val]

                for action in actions:
                    max_val = max(max_val, q_table[x][y][action])
                    if max_val > prev_max_val:
                        prev_max_val = max_val
                        best_action = action
                        duplicate_actions = [best_action]
                    elif max_val == q_table[x][y][action]:
                        duplicate_actions.append(action)

                if len(duplicate_actions) > 1:
                    for action in duplicate_actions:
                        pos_after_action = calculate_new_pos(action, (x, y))
                        draw_arrow(win, (255, 0, 0), ((165 + x * 40), (155 + y * 40)), pos_after_action)
                else:
                    pos_after_action = calculate_new_pos(best_action, (x,y))
                    draw_arrow(win, (255, 0, 0), ((165 + x * 40), (155 + y * 40)), pos_after_action)


def display_dropoff_pickup_locations(win, pickup_positions, dropoff_positions, state_map):
    for pos in pickup_positions:
            win.blit(
                state_map['{},{}'.format(pos[0], pos[1])]["special_block"].get_symbol(),
                state_map['{},{}'.format(pos[0], pos[1])]["special_block"].get_pos()
            )

    for pos in dropoff_positions:
        win.blit(
            state_map['{},{}'.format(pos[0], pos[1])]["special_block"].get_symbol(),
            state_map['{},{}'.format(pos[0], pos[1])]["special_block"].get_pos()
        )


def display_male_female_agents(win, male, female):
    win.blit(male.get_symbol(), male.get_pos())
    win.blit(female.get_symbol(), female.get_pos())


def display_game_board(win, game_board):
    win.blit(game_board, (125, 125))


def generate_attractive_paths_image(win, male, female, state_map, game_board, 
            pickup_positions, dropoff_positions, 
            q_table_male_pickup, q_table_male_dropoff, 
            q_table_female_pickup, q_table_female_dropoff, path="./test/"):

        # print("Male Q-Table Dropoff\n", q_table_male_dropoff, "\n")
        # print("Male Q-Table Pickup\n", q_table_male_pickup, "\n")

        # print("Female Q-Table Dropoff\n", q_table_female_dropoff, "\n")
        # print("Female Q-Table Pickup\n", q_table_female_pickup, "\n")
        
        display_dropoff_pickup_locations(win, pickup_positions, dropoff_positions, state_map)
        display_arrows(win, q_table_male_pickup)

        pygame.image.save(win, "./{}/attractive_paths_pickup_male.jpeg".format(path))

        display_game_board(win, game_board)
        display_dropoff_pickup_locations(win, pickup_positions, dropoff_positions, state_map)
        display_male_female_agents(win, male, female)
        display_arrows(win, q_table_male_dropoff)

        pygame.image.save(win, "./{}/attractive_paths_dropoff_male.jpeg".format(path))

        display_game_board(win, game_board)
        display_dropoff_pickup_locations(win, pickup_positions, dropoff_positions, state_map)
        display_male_female_agents(win, male, female)
        display_arrows(win, q_table_female_pickup)

        pygame.image.save(win, "./{}/attractive_paths_pickup_female.jpeg".format(path))
        

        display_game_board(win, game_board)
        display_dropoff_pickup_locations(win, pickup_positions, dropoff_positions, state_map)
        display_male_female_agents(win, male, female)
        display_arrows(win, q_table_female_dropoff)

        pygame.image.save(win, "./{}/attractive_paths_dropoff_female.jpeg".format(path))


def save_qtables_in_text_file(q_table, filedir="test", filename="test.txt"):
    try:
        os.mkdir(filedir)
    except:
        print("Directory {} already exists, saving q-table there".format(filedir))
    updated_filedir = "./{}/{}".format(filedir, filename)
    with open(updated_filedir, "w") as f:
        for x in range(0, len(q_table)):
            for y in range(0, len(q_table)):
                f.write("({}, {}) = {}\n".format(x, y, q_table[x][y]))


def save_heatmaps_in_text_file(male_dropoff, male_pickup, female_dropoff, female_pickup, filedir="test"):
    heatmaps = [male_dropoff, male_pickup, female_dropoff, female_pickup]
    heatmap_names = ["---Male Dropoff HeatMap---", "---Male Pickup HeatMap---", "---Female Dropoff HeatMap---", "---Female Pickup HeatMap---"]
    heatmap_filenmaes = ["male_dropoff_heatmap.jpeg", "male_pickup_heatmap.jpeg","female_dropoff_heatmap.jpeg", "female_pickup_heatmap.jpeg"]
    filename = "heatmaps.txt"
    try:
        os.mkdir(filedir)
    except:
        print("Directory {} already exists, saving heatmaps there".format(filedir))
    updated_filedir = "./{}/{}".format(filedir, filename)
    with open(updated_filedir, "w") as f:
        for i in range(len(heatmaps)):
            f.write("{}\n".format(heatmap_names[i]))
            f.write("{}\n\n".format(heatmaps[i]))
            total_steps, heatmap_dist = find_heatmap_distribution(heatmaps[i])
            f.write("Total Steps: {}\n".format(total_steps))
            f.write("Distribution:\n")
            f.write("{}\n\n\n".format(heatmap_dist))
            make_heatmap(heatmap_names[i], heatmap_dist, filedir, heatmap_filenmaes[i])
        f.close


def make_heatmap(title, heatmap, filedir, filename):
    plt.clf()
    sns.heatmap(heatmap, linewidth=0.3)
    plt.title(title)
    plt.savefig("./{}/{}".format(filedir, filename))


def find_heatmap_distribution(heatmap):
    maxval = 0
    total = 0
    for x in range(heatmap.shape[0]):
        for y in range(heatmap.shape[1]):
            total += heatmap[x][y]
            maxval = max(maxval, heatmap[x][y])

    distribution_map = np.zeros((heatmap.shape[0], heatmap.shape[1]), dtype=float)
    for x in range(heatmap.shape[0]):
        for y in range(heatmap.shape[1]):
            distribution_map[x][y] = (heatmap[x][y] / maxval)

    return total, distribution_map

def wipe_experiment_stats(filedir):
    filename = "experiment_statistics.txt"
    location = "./{}/{}".format(filedir, filename)
    try:
        os.mkdir(filedir)
    except:
        print("Making Directory: {}".format(filedir))
    if os.path.exists(location):
        f = open(location, "r+")
        f.truncate(0)
    else:
        with open(location, "x") as f:
            f.write("Stats File!")


def write_run_stats(agentM, agentF, runnum, filedir, dropoff_locations):
    filename = "experiment_statistics.txt"
    agents = [agentM, agentF]
    try:
        os.mkdir(filedir)
    except:
        print("Finishing Run {}".format(runnum))
    updated_filedir = "./{}/{}".format(filedir, filename)
    with open(updated_filedir, "a") as f:
        f.write("\n\n---Run: {}---\n".format(runnum))
        for agent in agents:
            if agent == agentM:
                f.write("Male Values:\n")
            else:
                f.write("Female Values:\n")
            f.write("Steps taken: {}\n".format(agent.get_steps()))
            f.write("Pickups Happen at Steps: {}\n".format(agent.get_steps_to_pickup()))
            f.write("Drop-offs Happen at Steps: {}\n".format(agent.get_steps_to_dropoff()))
            f.write("Agent Did {} Drop-offs! By Location:\n".format(agent.get_dropoffs()))
            f.write("{}: {}\n{}: {}\n{}: {}\n{}: {}\n".format(dropoff_locations[0], agent.get_visit()[0],
                                                            dropoff_locations[1], agent.get_visit()[1],
                                                            dropoff_locations[2], agent.get_visit()[2],
                                                            dropoff_locations[3], agent.get_visit()[3],))

            if agent.get_blocked_counter() == 0:
                f.write("This agent was not blocked :)\n")
            else:
                f.write("Agent was blocked {} times!\n".format(agent.get_blocked_counter()))
                f.write("Blocking happened at steps: {}\n".format(agent.get_steps_blocked_at()))


def write_final_stats(agentM, agentF, filedir, dropoff_locations):
    filename = "experiment_statistics.txt"
    agents = [agentM, agentF]
    try:
        os.mkdir(filedir)
    except:
        print("Directory {} already exists, saving final stats there".format(filedir))
    updated_filedir = "./{}/{}".format(filedir, filename)
    with open(updated_filedir, "a") as f:
        f.write("\n\n---Final Stats---\n")
        for agent in agents:
            if agent == agentM:
                f.write("Male Stats:\n")
                name = "Male"
            else:
                f.write("Female Stats:\n")
                name = "Female"
            f.write("{} dropoff total: {}\n".format(name, str(agent.get_total_dropoffs())))
            f.write("{}: {}\n{}: {}\n{}: {}\n{}: {}\n".format(dropoff_locations[0], agent.get_total_visits()[0],
                                                              dropoff_locations[1], agent.get_total_visits()[1],
                                                              dropoff_locations[2], agent.get_total_visits()[2],
                                                              dropoff_locations[3], agent.get_total_visits()[3], ))

            f.write("{} total steps: {}\n".format(name, str(agent.get_total_steps())))
            steps_list = agent.get_steps_list()
            f.write("{} steps in each round: {}\n".format(name, str(steps_list)))
            f.write("Total terminal states: {}\n".format(str(len(steps_list))))
            f.write("{} average steps to reach terminal state : {}\n".format(name, str(agent.get_avg_steps_per_terminal_state())))
            blocked_list = agent.get_blocked_list()
            f.write("{} times blocked each round: {}\n".format(name, blocked_list))
            f.write("Total times blocked: {}\n".format(agent.get_total_blocked_counter()))
            f.write("\n")
        print("All results available in the {} directory!".format(filedir))

def make_steps_time_each_run_graph(male, female):
    plt.clf()

    sns.set_style("dark")
    inputArraySteps = male.get_steps_list()
    
    print("loading steps per terminal step on to graph...")
    
    
    df_dict = {"terminal states":[],"steps":[]}
    for i in range(0,len(inputArraySteps)):
        df_dict["terminal states"].append(i+1)
    
    for terminal_steps in inputArraySteps:
        df_dict["steps"].append(terminal_steps)

    df = pd.DataFrame(df_dict)
    
    graph = sns.lineplot(data=df, x="terminal states", y="steps",estimator=None,)
    
    plt.ylabel("steps per terminal state")
    plt.title("Male Steps per Terminal State")

    


    graph.get_figure().savefig("./exp-2/male_steps_graph.jpeg", transparent=True)
    plt.clf()
    inputArraySteps = female.get_steps_list()
    
    
    df_dict["steps"].clear()
    for terminal_steps in inputArraySteps:
        df_dict["steps"].append(terminal_steps)
    
    df = pd.DataFrame(df_dict)
    
    graph_female = sns.lineplot(data=df, x="terminal states", y="steps",estimator=None,color='r')
    plt.ylabel("steps per terminal state")
    plt.title("Female Steps per Terminal State")

    graph_female.get_figure().savefig("./exp-2/female_steps_graph.jpeg", transparent=True)

    #print("exporting results in exp-2 directory....")

def make_dropoffs_per_terminal_state_graph(male,female):
    plt.clf()
    df_dict = {"dropoffs":[],"steps":[]}
    sns.set_style("dark")

    input = male.get_dropoffs_list()
    terminal_steps = male.get_steps_list()

    for steps in terminal_steps:
        df_dict["steps"].append(steps)

    for dropoffs in input:
        df_dict["dropoffs"].append(dropoffs)

    df = pd.DataFrame(df_dict)
    graph = sns.lineplot(data=df, x = "dropoffs", y = "steps",color="b")

    plt.ylabel("steps")
    plt.title("Male Steps per Dropoffs")

    graph.get_figure().savefig("./exp-2/male_dropoffs_graph.jpeg", transparent=True)
    plt.clf()
    input = female.get_dropoffs_list()
    terminal_steps = female.get_steps_list()

    for dropoffs in input:
        df_dict["dropoffs"].append(dropoffs)
    
    for steps in terminal_steps:
        df_dict["steps"].append(steps)
    

    df = pd.DataFrame(df_dict)
    graph_female = sns.lineplot(data=df, x = "dropoffs", y = "steps",color="r")

    plt.ylabel("steps")
    plt.title("Female Steps per Dropoffs")

    graph_female.get_figure().savefig("./exp-2/female_dropoffs_graph.jpeg", transparent=True)
    
def make_collision_graph(male,female,experiment):
    plt.clf()
    fig, ax1 = plt.subplots(figsize=(12,6))

    

    input = male.get_blocked_list()
    
    df_dict = {"times_blocked": [],"terminal states":[]}
    i =1
    for count in input:
        df_dict["times_blocked"].append(count)
        df_dict["terminal states"].append(i)
        i += 1
    
    df = pd.DataFrame(df_dict)

    ax1.set_title("Male vs Female Collisions per Terminal State")
    ax1.set_xlabel("terminal states")
    ax1.set_ylabel("times blocked")
    ax1 = sns.lineplot(data=df, x = "terminal states", y ="times_blocked")
    ax1.tick_params(axis='y')
    

    input = female.get_blocked_list()

    i =1
    for count in input:
        df_dict["times_blocked"].append(count)
        df_dict["terminal states"].append(i)
        i += 1

    df = pd.DataFrame(df_dict)

    ax1 = sns.lineplot(data=df, x = "terminal states", y ="times_blocked", color = 'r')
    ax1.tick_params(axis='y')
    ax1.legend(labels=["Male","Female"])
    if experiment == '2':

        fig.savefig("./exp-2/SARSA/Collision-Graph-Run.jpeg", transparent = True)
    elif experiment == '1c':
        fig.savefig("./exp-2/Q-Learning/Collision-Graph-Run.jpeg", transparent = True)


def make_graphs_exp2(male,female,experiment):
    make_collision_graph(male,female,experiment)
