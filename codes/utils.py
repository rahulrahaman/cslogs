import numpy as np
import copy
from datetime import datetime as dt


def return_time(line):
    return dt.strptime(line[2:23], '%m/%d/%Y - %H:%M:%S')
    #return dt.strptime(line[2:23], '%d/%m/%Y - %H:%M:%S') - updated
    


def parse_player_info(info):
    '''
    Function to get player info from player string
    usual structure is "TEAM || PLAYER_NAME"<CT/T><PLAYER_ID><VALVE/STEAM:UNIQ_ID>
    parses the player string and puts info in a dictionary
    '''
    is_ct = True
    is_steam = True
    team_separater = max(info.find('||'), 0)
    if team_separater==0:
        team_separater = max(info.find('|'), 0)
    app_tag = info.find('<STEAM_')
    side_tag = info.find('><CT>')
    team = info[1:team_separater].strip()
    if side_tag < 0:
        is_ct = False
        side_tag = info.find('><TERRORIST>')
    if app_tag < 0:
        is_steam = False
        app_tag = info.find('<VALVE_')
    server_player_num = info[team_separater+2:app_tag].rfind('<')
    name = info[team_separater+2:app_tag][:server_player_num].strip()
    uniq_id = info[app_tag+7:side_tag]
    return {'name': name, 'team': team, 'steam': is_steam, 'ct': is_ct, 'id': uniq_id}


def get_frag_info(raw_kill_line):
    '''
    parses a frag line into killer, victim, weapon e.t.c
    '''
    infos = raw_kill_line[25:]
    killer_end = infos.find('" killed "')
    victim_end = infos.find('" with "')
    killer_str = infos[:killer_end]
    killer_info = parse_player_info(killer_str)
    victim_str = infos[killer_end+9:victim_end]
    victim_info = parse_player_info(victim_str)
    weapon_info = infos[victim_end+8:].replace('"','')
    return {'killer': killer_info, 'victim': victim_info, 'weapon': weapon_info}


def get_trigger_info(raw_kill_line):
    '''
    parses a trigger line into triggerer, event
    '''
    infos = raw_kill_line[25:]
    trigger_end = infos.find('" triggered "')
    triggerer_str = infos[:trigger_end]
    triggerer_info = parse_player_info(triggerer_str)
    event_info = infos[trigger_end+13:].replace('"','')
    return {'triggerer': triggerer_info, 'event': event_info}


def match_player_in_dict(dict_, player, idx):
    '''
    Given a dictionary and a player and its UNIQ_ID, matches the player
    with existing players inside dictionary, first name is searched, if not
    found then searched with idx, at last returned None if no match
    '''
    pos_match = []
    if player in dict_:
        return player
    else:
        for ex_player in dict_:
            if dict_[ex_player]['id'] == idx:
                pos_match.append(ex_player)
    if len(pos_match)==0:
        return None
    elif len(pos_match)==1:
        return pos_match[0]
    else:
        return pos_match


def scan_high_level_stat(raw_info):
    '''
    function to parse all raw lines and return player dictionary, team dictionary
    dynamics list, frag list and markers (for info on each of this items refer to
    classes.py)
    '''
    players = {}
    teams = {}
    markers = []
    dynamics = [[0, 0]]
    frag_list = []
    start_time = return_time(raw_info[0])
    killers = {}
    traded = []
    dead = []

    for lineno in range(len(raw_info)):
        line = raw_info[lineno]
        event_time = return_time(line)
        time_from_round_start = (event_time - start_time).seconds
        if '" killed "' in line:
            info = get_frag_info(line)
            kname = info['killer']['name']
            vname = info['victim']['name']
            weapon = info['weapon']
            kteam = info['killer']['team']
            vteam = info['victim']['team']
            kside = info['killer']['ct']
            vside = info['victim']['ct']
            frag_list.append([kname, vname, weapon, int(kside==vside)])
            if len(teams) == 0:
                if kside != vside:
                    teams[kteam], teams[vteam] = {}, {}
                    teams[kteam]['first_side'] = kside
                    teams[vteam]['first_side'] = vside
            ret_ = match_player_in_dict(players, kname, info['killer']['id'])
            if ret_ is None:
                players[kname] = info['killer']
            else:
                kname = ret_
            ret_ = match_player_in_dict(players, vname, info['victim']['id'])
            if ret_ is None:
                players[vname] = info['victim']
            else:
                vname = ret_
            players[kname]['killed'] = players[kname].get('killed', 0)+int(kside!=vside)
            dead.append(vname)
            if kname not in killers:
                players[kname]['rounds_killed'] = players[kname].get('rounds_killed', 0) + 1
                players[kname]['first_kill_time'] = players[kname].get('first_kill_time', 0) + time_from_round_start
            killers[kname] = killers.get(kname, []) + [[vname, event_time]]
            if vname in killers:
                for victim_, kill_time in killers[vname]:
                    if (event_time - kill_time).seconds < 5:
                        traded.append(victim_)
            players[vname]['death_time'] = players[kname].get('death_time', 0) + time_from_round_start
            players[vname]['dead'] = players[vname].get('dead', 0)+1
            players[kname]['tk'] = players[kname].get('tk', 0)+int(kside==vside)

        elif ' triggered ' in line:
            if 'World triggered' in line:
                if "Round_End" in line:
                    markers.append(lineno)
                    killed_or_traded = set(killers).union(set(traded))
                    killed_or_traded_and_dead = killed_or_traded.intersection(set(dead))
                    for player in killed_or_traded:
                        players[player]['rounds_K|T'] = players[player].get('rounds_K|T', 0) + 1
                    for player in killed_or_traded_and_dead:
                        players[player]['rounds_(K|T)&D'] = players[player].get('rounds_(K|T)&D', 0) + 1

                    killers = {}
                    dead = []
                    traded = []
                if "Round_Start" in line:
                    start_time = event_time
            elif 'Team "CT" triggered' in line:
                score = dynamics[-1].copy()
                score[0] += 1
                dynamics.append(score)
            elif 'Team "TERRORIST" triggered' in line:
                score = dynamics[-1].copy()
                score[1] += 1
                dynamics.append(score)
            else:
                info = get_trigger_info(line)
                pname = info['triggerer']['name']
                event = info['event']
                ret_ = match_player_in_dict(players, pname, info['triggerer']['id'])
                pname = pname if ret_ is None else ret_
                if ret_ is None:
                    players[pname] = info['triggerer']
                players[pname][event] = players[pname].get(event, 0)+1
    return players, teams, np.array(dynamics), frag_list, markers


def get_brownies(players, raw_info):
    '''
    scan a round and get pro plays, 
    INSERT NEW LOGICS HERE FOR MORE PRO PLAYS SECTION
    '''
    brownies = {}
    alive = dict([(player, True) for player in players])
    for lineno in range(len(raw_info)):
        line = raw_info[lineno]
        if '" killed "' in line:
            info = get_frag_info(line)
            kname = info['killer']['name']
            vname = info['victim']['name']
            kside = info['killer']['ct']
            vside = info['victim']['ct']
            alive[vname] = False
            kname = match_player_in_dict(players, kname, info['killer']['id'])
            vname = match_player_in_dict(players, vname, info['victim']['id'])
            
        ct_bool = [player for player in players if (alive[player] and players[player]['ct'])]
        t_bool = [player for player in players if (alive[player] and not players[player]['ct'])]
        
        if '1vMany' not in brownies:
            if (len(ct_bool)==1 and len(t_bool) > 2) or (len(t_bool)==1 and len(ct_bool) > 2):
                player = t_bool[0] if len(t_bool)==1 else ct_bool[0]
                num_alive = len(ct_bool) if len(t_bool)==1 else len(t_bool)
                brownies['1vMany'] = [player, num_alive]
        
        if '" triggered ' in line:
            if 'Defused_The_Bomb' in line and len(ct_bool)==1 and len(t_bool) > 1:
                info = get_trigger_info(line)
                pname = info['triggerer']['name']
                brownies['ninja'] = info['triggerer']['name']
        
    return brownies
