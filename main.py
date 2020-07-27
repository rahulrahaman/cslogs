import numpy as np
import copy
from codes.utils import *
from codes.classes import *
from codes.reporter import *
import os
from codes.config import *

# Search for log files in the 'logs/' folder. Place ones with the matches only
# No need to separate each games into different log file.

file_list = ['logs/' + file for file in os.listdir('logs/')]
matches = []
match = None

# Parse logs and get matches

for file in file_list:
    print("New File")
    print(file)
    with open(file, 'r') as openf:
        lines = openf.readlines()

    lines = [line.strip() for line in lines]
    lines = np.array(lines)

    num_round = -1
    temp = []
    last_score = np.zeros(2)
    current_score = np.zeros(2)
    special_tag_start = ''

    for numline in range(len(lines)):
        item = lines[numline]
        temp.append(item)
        if '"sv_restart"' in item:
            num_round = -1
            temp = []
        if 'say "live' in item.lower() and num_round==-1:
            num_round = 0
            # print('potential start at ', numline)
        if '"Round_End"' in item and num_round > -1:
            num_round += 1
            players, teams, dynamics, frag_list, markers = scan_high_level_stat(temp)
            current_score = dynamics[-1] + last_score
            if num_round==RACE_TO-1 and sum(last_score)==0:
                print('1st half end at', numline)
                num_round = -1
                match = Match(temp)
                print(match.tag)
                last_score = match.dynamics[-1][::-1]
                temp = []
            elif np.max(current_score)==RACE_TO or sum(current_score)==2*(RACE_TO-1):
                print('2nd half end at', numline)
                match.update_stats(temp)
                matches.append(match)            
                num_round = -1
                temp = []
                last_score = np.zeros(2)


# Accumulate match info into concise tables to generate report
final_KDA = {}
brownies = []
final_frag_list = []
match_tags = []
team_players = {}

for match in matches:
    for player in match.players:
        # Player matching across matches
        player_team = match.players[player]['team']
        ret_ = match_player_in_dict(final_KDA, player, match.players[player]['id'])
        if ret_ != player and ret_ is not None:
            matched = None
            ret_ = ret_ if isinstance(ret_, list) else [ret_]
            for p in ret_:
                confirm = input('Match "%s" with "%s"\t'%(p, player))
                if "y" in confirm.lower():
                    matched = p
                    break
        else:
            matched = player
        if ret_ is None or matched is None:
            final_KDA[player] = match.players[player]
            final_KDA[player]['matches'] = 1
            if player not in team_players.get(player_team, []):
                team_players[player_team] = team_players.get(player_team, []) + [player]
        else:
            for frag_no in range(len(match.frag_list)):
                for j in range(2):
                    if match.frag_list[frag_no][j]==player:
                        match.frag_list[frag_no][j] = matched

            for num in range(len(match.brownies)):
                if match.brownies[num][1]==player:
                    match.brownies[num][1] = matched

            if matched not in team_players.get(player_team, []):
                team_players[player_team] = team_players.get(player_team, []) + [matched]

            final_KDA[matched]['matches'] += 1
            for key in match.players[player]:
                if key not in ['name', 'team', 'steam', 'ct', 'id']:
                    final_KDA[matched][key] = final_KDA[matched].get(key, 0) + match.players[player][key]

    final_frag_list.extend(match.frag_list)
    brownies.extend(match.brownies)
    match_tags.append(match.tag)

# Report generation
generate_report(final_KDA, final_frag_list, brownies, match_tags, team_players)