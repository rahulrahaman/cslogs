from fpdf import FPDF
import numpy as np
import csv
from codes.config import weapon_dict


def set_color(pdf, bad=1):
    if bad==1:
        pdf.set_fill_color(r=255, g=51, b=51)
        pdf.set_text_color(r=255, g=255, b=255)
    elif bad==0:
        pdf.set_fill_color(r=76, g=153, b=0)
        pdf.set_text_color(r=255, g=255, b=255)
    else:
        pdf.set_fill_color(r=255, g=178, b=102)
        pdf.set_text_color(r=0, g=0, b=0)


def reset(pdf):
    pdf.set_fill_color(r=255, g=255, b=255)
    pdf.set_text_color(r=0, g=0, b=0)


def generate_report(final_KDA, final_frag_list, brownies, match_tags, team_players):

    # with open('myfile.csv', 'wb') as myfile:
    #     wr = csv.writer(myfile)
    #     for row in final_KDA:
    #         wr.writerrow()

    KDA_data = []
    for key in final_KDA:
        num_round = final_KDA[key]['rounds']
        num_kill = final_KDA[key].get('killed', 0)
        num_death = final_KDA[key].get('dead', 0)
        num_defuse = final_KDA[key].get('Defused_The_Bomb', 0)
        num_plant = final_KDA[key].get('Planted_The_Bomb', 0)
        num_tk = final_KDA[key].get('tk', 0)
        kill_time = final_KDA[key].get('first_kill_time', 0)
        rounds_killed = final_KDA[key].get('rounds_killed', 0)
        death_time = final_KDA[key].get('death_time', 0)
        killed_or_traded = final_KDA[key].get('rounds_K|T', 0)
        killed_or_traded_and_dead = final_KDA[key].get('rounds_(K|T)&D', 0)
        KST = killed_or_traded + (num_round - num_death) - (killed_or_traded - killed_or_traded_and_dead)
        row = [key, num_round, num_kill, num_kill/num_round, num_death, num_death/num_round, 
               num_plant, num_defuse, num_tk, kill_time/rounds_killed, death_time/num_death, 100*KST/num_round]
        KDA_data.append(row)
    
    KDA_data = sorted(KDA_data, key=lambda x: x[3], reverse=True)
    maxes = [max([item[i+1] for item in KDA_data]) for i in range(11)]
    mins = [min([item[i+1] for item in KDA_data]) for i in range(11)]

    max_cells = 13
    cell_width = 20
    KDA_cell_width = 18.9
    pdf = FPDF(unit='mm', format=(max_cells*cell_width, 297))
    pdf.add_page()
    header = ['Name', 'Rounds', 'Kills', 'K/R', 'Death', 'D/R', 'Planted', 'Defused', 'Friendly',
              'K time', 'D time', 'KST %']

    pdf.set_font('Arial', 'B', 13)
    # epw = pdf.w - 2*pdf.l_margin
    th = pdf.font_size
    
    # Match info in the report is created here
    for match in match_tags:
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(r=192, g=57, b=43)
        pdf.cell(w=cell_width*max_cells, h=2*th, txt=match, align='C')
        pdf.ln(2*th)
    pdf.ln(2*th)

    # Team and player names
    team_width = 4
    for team in team_players:
        pdf.set_text_color(r=192, g=57, b=43)
        pdf.set_font('Arial', 'B', 15)
        pdf.cell(cell_width * team_width, 2 * th, str(team), align='R', border=0, fill=False)
        pdf.cell(3)
        pdf.set_font('Arial', '', 14)
        pdf.set_text_color(r=0, g=0, b=0)
        player_names = ', '.join(team_players[team])
        pdf.cell(cell_width * (max_cells - team_width), 2 * th, str(player_names), align='L', border=0, fill=False)
        pdf.ln(2*th)
    pdf.ln(2*th)

    # weapons section starts here (PISTOL PRO, ...)
    pdf.set_text_color(r=0, g=0, b=0)
    
    for item in range(len(weapon_dict)):
        weapon_details = weapon_dict[item]
        weapons = weapon_details['weapon']
        text2put = weapon_details['name']
        imwidth = weapon_details['imwidth']
        imname = weapon_details['image']

        wfrags = [item for item in final_frag_list if (item[2] in weapons and item[3]==0)]
        if len(wfrags)==0:
            continue
        ret = np.unique([item[0] for item in wfrags], return_counts=True)
        wfrags_permatch = [(ret[1][num]/final_KDA[ret[0][num]]['matches']) for num in range(len(ret[0]))]
        data = sorted(list(zip(ret[0], wfrags_permatch)), key=lambda x:x[1], reverse=True)

        pdf.set_font('Arial', 'B', 20)
        pdf.cell(w=cell_width*2, h=2*th, txt=text2put)
        pdf.cell(5)
        pdf.image(imname, w=imwidth*th)
        pdf.ln(th)
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(w=cell_width*2, h=2*th, txt=data[0][0], align='R')
        pdf.set_text_color(r=76, g=153, b=0)
        pdf.cell(w=cell_width*2, h=2*th, txt='(%.1f Kills)'%data[0][1])
        if len(data) > 1:
            pdf.cell(w=cell_width*0.5)
            pdf.set_text_color(r=0, g=0, b=0)
            pdf.cell(w=cell_width*2, h=2*th, txt=data[1][0], align='R')
            pdf.set_text_color(r=76, g=153, b=0)
            pdf.cell(w=cell_width*2, h=2*th, txt='(%.1f Kills)'%data[1][1])
            pdf.set_text_color(r=0, g=0, b=0)
        pdf.ln(3*th)

    # Humiliation section starts here
    wfrags = [item for item in final_frag_list if (item[2]=='knife' and item[3]==0)]
    if len(wfrags) > 0:
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(w=cell_width*2, h=2*th, txt='Humiliation')
        pdf.ln(2*th)
        for frag in wfrags:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(w=cell_width*2, h=2*th, txt=frag[0], align='R')
            pdf.cell(3)
            pdf.set_text_color(r=255, g=0, b=0)
            pdf.cell(w=cell_width*2, h=2*th, txt='knifed', align='C')
            # pdf.image('images/knife.png', w=3*th)
            pdf.set_text_color(r=0, g=0, b=0)
            pdf.cell(5)
            pdf.cell(w=cell_width*2, h=2*th, txt=frag[1], align='L')
            pdf.ln(th)

    # KDA table starts here
    pdf.add_page()
    pdf.set_text_color(r=255, g=255, b=255)

    # HEADER
    pdf.set_font('Arial', 'B', 13)
    for itemno in range(len(header)):
        # Enter data in colums
        datum = header[itemno]
        if itemno == 0:
            pdf.set_fill_color(r=255, g=153,b=153)
            pdf.cell(cell_width*2, 2*th, str(datum), align='C', border=1, fill=True)
            pdf.set_fill_color(r=255, g=255,b=255)
        else:
            pdf.set_fill_color(r=255, g=153,b=153)
            pdf.cell(KDA_cell_width, 2*th, str(datum), align='C', border=1, fill=True)
            pdf.set_fill_color(r=255, g=255,b=255)
    pdf.ln(2*th)

    # CELLS
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(r=0, g=0, b=0)
    for row in KDA_data:
        for itemno in range(len(row)):
            # Enter data in columns
            datum = row[itemno]

            if datum==maxes[itemno-1]:
                if itemno in [2, 3, 6, 7, 11]:
                    set_color(pdf, bad=0)
                elif itemno in [5, 8]:
                    set_color(pdf, bad=1)
                elif itemno in [9, 10]:
                    set_color(pdf, bad=2)

            elif datum==mins[itemno-1]:
                if itemno in [4, 5]:
                    set_color(pdf, bad=0)
                elif itemno in [11]:
                    set_color(pdf, bad=1)
                elif itemno in [9, 10]:
                    set_color(pdf, bad=2)

            if itemno in [3, 5]:
                datum = '%.2f'%datum
            elif itemno in [9, 10, 11]:
                datum = '%.1f'%datum

            if itemno == 0:
                pdf.cell(cell_width*2, 2*th, str(datum), border=1, fill=True)
            else:
                pdf.cell(KDA_cell_width, 2*th, str(datum), align='C', border=1, fill=True)
            reset(pdf)
        pdf.ln(2*th)

    # pdf.add_page()
    pdf.set_text_color(r=0, g=0, b=0)
    # Pro plays section starts here
    if len(brownies) > 0:
        pdf.ln(3 * th)
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(w=cell_width * 2, h=2 * th, txt='Pro plays')
        pdf.ln(2 * th)
        for brownie in brownies:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(w=cell_width * 2, h=2 * th, txt=brownie[0], align='L')
            pdf.cell(3)
            pdf.cell(w=cell_width * 2, h=2 * th, txt=brownie[1], align='C')
            pdf.cell(3)
            pdf.set_font('Arial', '', 14)
            pdf.cell(w=cell_width * 5, h=2 * th, txt=brownie[2], align='C')
            pdf.cell(3)
            pdf.cell(w=cell_width * 1, h=2 * th, txt=brownie[3], align='C')
            pdf.cell(3)
            pdf.cell(w=cell_width * 1, h=2 * th, txt='Round ' + str(brownie[4]), align='C')
            pdf.ln(2 * th)

    pdf.ln(th)

    pdf.output('Final_report.pdf', 'F')

