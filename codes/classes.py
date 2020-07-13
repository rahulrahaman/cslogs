import numpy as np
import copy
from codes.utils import *
from codes.classes import *
from codes.config import *


class Match:
    def __init__(self, raw_info):
        '''
        Called when first half is finished
        raw_info is the server raw logs for the first half
        players: dictionary with key as player name, keys: ['name', 'team', 'steam', 'ct', 'id', 'Dropped_The_Bomb',
            'dead', 'killed', 'tk'] and any other additional events that the player triggered with event name as key 
            and count as value
        teams: dictionary with team name as key, contains keys: ['first_side', 'first_score', 'final_score']
        dynamics: list with match score dynamics, first item [0, 0] then progresses to [16, *] or [*, 16]
        frag_list: list with all frags (list with elements killer, victim, weapon, same_side)
        markers: list with checkpoints indices where each round ended
        brownies: list with "pro plays", each element is a list with ('pro play tag', 'player name', match, half, round)
        '''
        self.players, self.teams, self.dynamics, self.frag_list, self.markers = scan_high_level_stat(raw_info)
        self.log = raw_info
        self.brownies = []
        self.team_list = list(self.teams.keys())
        self.tag = self.team_list[0] + ' vs. ' + self.team_list[1]
        for team in self.teams:
            first_side = self.teams[team]['first_side']
            self.teams[team]['first_score'] = self.dynamics[-1][1-int(first_side)]
        for player in self.players:
            self.players[player]['rounds'] = len(self.dynamics)-1
        self.get_brownie_scores(self.players, self.markers, raw_info, '1st Half')
            
    def update_stats(self, raw_info):
        '''
        Called when second half is finished. Same structure as __init__ but need to take care of
        few things like, players changing name in second half
        '''
        players, teams, dynamics, frag_list, markers = scan_high_level_stat(raw_info)
        combined_score = dynamics[:,::-1] + self.dynamics[-1][None,:]
        self.dynamics = np.concatenate([self.dynamics, combined_score], axis=0)
        self.frag_list.extend(frag_list)
        self.markers += [len(self.log)+marker for marker in markers]
        self.log += raw_info
        self.get_brownie_scores(players, markers, raw_info, '2nd Half')

        for team in self.teams:
            first_side = self.teams[team]['first_side']
            self.teams[team]['final_score'] = self.dynamics[-1][1-int(first_side)]
        for player in players:
            ret_ = match_player_in_dict(self.players, player, players[player]['id'])
            if ret_ is None:
                self.players[player] = players[player]
                self.players[player]['rounds'] = len(dynamics)-1
                self.players[player]['ct'] = not self.players[player]['ct']
            else:
                for frag_no in range(len(self.frag_list)):
                    for j in range(2):
                        if self.frag_list[frag_no][j]==player:
                            self.frag_list[frag_no][j] = ret_
                self.players[ret_]['rounds'] += len(dynamics)-1
                for num in range(len(self.brownies)):
                    if self.brownies[num][1] == player:
                        self.brownies[num][1] = ret_
                for key in players[player]:
                    if key not in ['name', 'team', 'steam', 'ct', 'id']:
                        self.players[ret_][key] = self.players[ret_].get(key, 0) + players[player][key]

        for team in self.teams:
            self.teams[team]['win'] = self.teams[team]['final_score']==RACE_TO

        self.final_score = str(self.teams[self.team_list[0]]['final_score']) + '-' + str(self.teams[self.team_list[1]]['final_score'])
        self.tag += '  (' + self.final_score + ')'
        return

    def get_brownie_scores(self, plist, markers, raw_info, half):
        '''
        gather brownie points of a match, each round is revisited
        ADD NEW PRO PLAYS LOGICS HERE AND IN "get_brownies" from utils
        '''
        last_marker = 0
        match_count = 1
        for marker in markers:
            p, _, dyn, _, _ = scan_high_level_stat(raw_info[last_marker:marker+1])
            brownies = get_brownies(plist, raw_info[last_marker:marker+1])
            if 'ninja' in brownies:
                pname = brownies['ninja']
                self.brownies.append(['Ninja defuse', pname, self.tag, half, match_count])
            elif '1vMany' in brownies:
                pname = brownies['1vMany'][0]
                vs = brownies['1vMany'][1]
                side = plist[pname]['ct']
                if dyn[-1][1-int(side)]==1:
                    self.brownies.append(['1 v '+str(vs), pname, self.tag, half, match_count])
            for player in p:
                killed = p[player].get('killed',0)
                if killed > 3 and player != brownies.get('1vMany', [''])[0]: #len(plist)//2:
                    self.brownies.append([str(killed) + ' Kills', player, self.tag, half, match_count])
            last_marker = marker+1
            match_count += 1

