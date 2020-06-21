from fpdf import FPDF
import numpy as np
import copy


def set_color(pdf, bad=True):
    if bad:
        pdf.set_fill_color(r=255, g=51, b=51)
    else:
        pdf.set_fill_color(r=76, g=153, b=0)
    pdf.set_text_color(r=255, g=255, b=255)

def reset(pdf):
    pdf.set_fill_color(r=255, g=255, b=255)
    pdf.set_text_color(r=0, g=0, b=0)

def generate_report(final_KDA, final_frag_list, brownies, match_tags):
    
    KDA_data = []
    for key in final_KDA:
        num_round = final_KDA[key]['rounds']
        num_kill = final_KDA[key].get('killed', 0)
        num_death = final_KDA[key].get('dead', 0)
        num_defuse = final_KDA[key].get('Defused_The_Bomb', 0)
        num_plant = final_KDA[key].get('Planted_The_Bomb', 0)
        num_tk = final_KDA[key].get('tk', 0)
        row = [key, num_round, num_kill, num_kill/num_round, num_death, num_death/num_round, 
               num_plant, num_defuse, num_tk]
        KDA_data.append(row)
    
    KDA_data = sorted(KDA_data, key=lambda x: x[3], reverse=True)
    maxes = [max([item[i+1] for item in KDA_data]) for i in range(8)]
    mins = [min([item[i+1] for item in KDA_data]) for i in range(8)]    
    
    pdf = FPDF()
    pdf.add_page()
    header = ['Name', 'Rounds', 'Kills', 'K/R', 'Death', 'D/R', 'Planted', 'Defused', 'Friendly']

    pdf.set_font('Arial', 'B', 13)
    epw = pdf.w - 2*pdf.l_margin
    cell_width = epw/10
    th = pdf.font_size
    
    # Match info in the report is created here
    for match in match_tags:
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(r=192, g=57, b=43)
        pdf.cell(w=cell_width*10, h=2*th, txt=match, align='C')
        pdf.ln(2*th)
    pdf.ln(2*th)

    # weapons section starts here (PISTOL PRO, ...)
    wlist = [['glock18', 'deagle', 'usp', 'p228'],
             ['m4a1'],
             ['ak47'],
             ['awp']
            ]

    image_list = ['images/handgun.jpg', 'images/m4a1.jpg', 'images/ak47.jpg', 'images/sniper.jpg']
    image_width = [3, 4, 4, 4]
    texts = ['Pistol pros', 'M4A1 pros', 'AK47 pros', 'AWP pros']
    pdf.set_text_color(r=0, g=0, b=0)
    
    for item in range(len(wlist)):
        weapons = wlist[item]
        text2put = texts[item]
        imwidth = image_width[item]
        imname = image_list[item]

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

    pdf.set_text_color(r=0, g=0, b=0)
    # Pro plays section starts here
    if len(brownies) > 0:
        pdf.ln(3*th)
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(w=cell_width*2, h=2*th, txt='Pro plays')
        pdf.ln(2*th)
        for brownie in brownies:
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(w=cell_width*1.5, h=2*th, txt=brownie[0], align='L')
            pdf.cell(3)
            pdf.cell(w=cell_width*2, h=2*th, txt=brownie[1], align='C')
            pdf.cell(3)
            pdf.set_font('Arial', '', 14)
            pdf.cell(w=cell_width*4, h=2*th, txt=brownie[2], align='C')
            pdf.cell(3)
            pdf.cell(w=cell_width*1, h=2*th, txt=brownie[3], align='C')
            pdf.cell(3)
            pdf.cell(w=cell_width*1, h=2*th, txt='Round ' + str(brownie[4]), align='C')
            pdf.ln(2*th)

    pdf.ln(th)

    # KDA table starts here
#     pdf.add_page()
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
            pdf.cell(cell_width, 2*th, str(datum), align='C', border=1, fill=True)
            pdf.set_fill_color(r=255, g=255,b=255)
    pdf.ln(2*th)

    # CELLS
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(r=0, g=0, b=0)
    for row in KDA_data:
        for itemno in range(len(row)):
            # Enter data in colums
            datum = row[itemno]
            if itemno in [2, 3]:
                if datum==maxes[itemno-1]:
                    set_color(pdf, bad=False)
                # if datum==mins[itemno-1] and itemno==3:
                #     set_color(pdf, bad=True)
            elif itemno in [6, 7]:      
                if datum==maxes[itemno-1]:
                    set_color(pdf, bad=False)

            elif itemno in [4, 5]:
                if datum==mins[itemno-1]:
                    set_color(pdf, bad=False)
                # if datum==maxes[itemno-1] and itemno==5:
                #     set_color(pdf, bad=True)
            elif itemno in [8]:
                if datum==maxes[itemno-1]:
                    set_color(pdf, bad=True)

            if itemno in [3, 5]:
                datum = '%.2f'%datum
            if itemno == 0:
                pdf.cell(cell_width*2, 2*th, str(datum), border=1, fill=True)
            else:
                pdf.cell(cell_width, 2*th, str(datum), align='C', border=1, fill=True)
            reset(pdf)
        pdf.ln(2*th)

    pdf.output('Final_report.pdf','F')
