#V1.1 修改了中枢的判断标准generate_zs_area函数



import pandas as pd
import json
from datetime import datetime

DRAW_GAP = 3

def generate_orignal_kindle_data(tmp_data):
    #返回只有开收低高的K线列表
    original_kline = []
    for index, row in tmp_data.iterrows():
        original_kline.append(list(row[['open', 'close', 'low', 'high']].values))
    return original_kline

def generate_noshadowkline(original_kline):
    #输出去除上下影线的数据noshadow_kline_data
    noshadow_kline_data = []
    for i in range(len(original_kline)):
        k_line_tmp = original_kline[i]
        day_open,day_close,day_low,day_high = k_line_tmp[0], k_line_tmp[1], k_line_tmp[2], k_line_tmp[3]
        if day_open <= day_close:
            ktmp = [day_low,day_high,day_low,day_high] #去除上影线下影线
        else:
            ktmp = [day_high,day_low,day_low,day_high] #去除上影线下影线
        noshadow_kline_data.append(ktmp)
    return noshadow_kline_data

def judge_kline_3_trend_type(pre_day,cur_day,last_day):
    #判断连续3跟K线的类别
    if (cur_day[3] > pre_day[3]) and (cur_day[2] > pre_day[2]):
        if (last_day[3] > cur_day[3]) and (last_day[2] > cur_day[2]):
            return 1
        elif (last_day[3] <= cur_day[3]) and (last_day[2] <= cur_day[2]):
            return 2
    elif (cur_day[3] <= pre_day[3]) and (cur_day[2] <= pre_day[2]):
        if (last_day[3] > cur_day[3]) and (last_day[2] > cur_day[2]):
            return 3
        elif (last_day[3] <= cur_day[3]) and (last_day[2] <= cur_day[2]):
            return 4
    else:
        return 0

def generate_containkline(noshadow_kline_data):
    #构造新的包含关系列表
    contain_kline_data = [noshadow_kline_data[0]]
    #基于包含关系列表构造每段的走势 0下 1上
    kline_trend = [1]
    #包含关系对应的原列表index
    contain_index = [0]
    for i in range(1,len(noshadow_kline_data)):
        k_line_tmp_day = noshadow_kline_data[i]
        #获取今天开高收底
        day_open,day_close,day_low,day_high = k_line_tmp_day[0], k_line_tmp_day[1], k_line_tmp_day[2], k_line_tmp_day[3]
        k_line_tmp_lastday = contain_kline_data[-1]
        #获取昨天开高收底
        lday_open,lday_close,lday_low,lday_high = k_line_tmp_lastday[0], k_line_tmp_lastday[1], k_line_tmp_lastday[2], k_line_tmp_lastday[3]
        #获取昨天相对前天的趋势
        last_trend = kline_trend[-1]
    
        #判断昨天今天状态（1上升、2今包昨、3昨包今、4下降）：
        flag = 0
        if (day_high > lday_high) and (day_low > lday_low):
            flag = 1
        elif ((day_high > lday_high) and (day_low <= lday_low)) or ((day_high == lday_high) and (day_low <= lday_low)):
            flag = 2
        elif ((day_high == lday_high) and (day_low > lday_low)) or ((day_high < lday_high) and (day_low >= lday_low)):
            flag = 3
        elif ((day_high < lday_high) and (day_low < lday_low)) or ((day_high < lday_low)):
            flag = 4     
    
        #基于不同情况构造今天数据
        if flag == 1:#上升趋势
            contain_kline_data.append(noshadow_kline_data[i])
            kline_trend.append(1)
            contain_index.append(i)
        elif flag == 4:#下降趋势
            contain_kline_data.append(noshadow_kline_data[i])
            kline_trend.append(0)
            contain_index.append(i)
        elif flag == 2:#今天包含昨天
            #构造新的高价低价
            if last_trend == 1:#昨天上升
                new_high = day_high
                new_low = lday_low
            elif last_trend == 0: #昨天下降
                new_high = lday_high
                new_low = day_low
            #基于今天判断阴阳线
            if day_close >= day_open:
                new_open = new_low
                new_close = new_high
            else:
                new_open = new_high
                new_close = new_low
            #生成新数据
            contain_kline_data.pop()
            contain_kline_data.append([new_open,new_close,new_low,new_high])
            contain_index.pop()
            contain_index.append(i)
        elif flag == 3:#昨天包含今天
            #构造新的高价低价
            if last_trend == 1:#昨天上升
                new_high = lday_high
                new_low = day_low
            elif last_trend == 0: #昨天下降
                new_high = day_high
                new_low = lday_low    
            #基于昨天判断阴阳线
            if lday_close >= lday_open:
                new_open = new_low
                new_close = new_high
            else:
                new_open = new_high
                new_close = new_low
            #生成新数据
            contain_kline_data.pop()
            contain_kline_data.append([new_open,new_close,new_low,new_high])
    #存储4种形态 1三连升 2顶 3底 4三连降 0开头结尾
    top_button = [0]
    for i in range(1,len(contain_kline_data)-1):
        pre_day = contain_kline_data[i-1]
        cur_day = contain_kline_data[i]
        last_day = contain_kline_data[i+1]
        top_button.append(judge_kline_3_trend_type(pre_day,cur_day,last_day))
    top_button.append(0)
    #存储每个顶或者低的最高最低值
    lowhigh_value = [[0,0]]
    for i in range(1,len(contain_kline_data)-1):
        # lowvalue = min(contain_kline_data[i-1][2],contain_kline_data[i][2],contain_kline_data[i+1][2])
        # highvalue = max(contain_kline_data[i-1][3],contain_kline_data[i][3],contain_kline_data[i+1][3])
        lowvalue = contain_kline_data[i][2]
        highvalue = contain_kline_data[i][3]
        lowhigh_value.append([lowvalue,highvalue])
    lowhigh_value.append([0,0])    
    
    #构造基于非包含关系的顶底及高低点列表
    contain_index.reverse()
    top_button.reverse()
    lowhigh_value.reverse()
    new_top_button = []
    new_lowhigh_value = []
    i = 0
    while contain_index != []:
        if i == contain_index[-1]:
            contain_index.pop()
            new_top_button.append(top_button.pop())
            new_lowhigh_value.append(lowhigh_value.pop())
        else:
            new_top_button.append(0)
            new_lowhigh_value.append([0,0])
        i = i + 1
    top_button = new_top_button + [0] * (len(noshadow_kline_data)-len(new_top_button))
    lowhigh_value = new_lowhigh_value + [[0,0]] * (len(noshadow_kline_data)-len(new_lowhigh_value))
    combine_list = list(zip(top_button, lowhigh_value))
    return contain_kline_data, combine_list

def generate_draw(noshadow_kline_data, combine_list):
    #生成笔的坐标列表
    current_flag = 0
    current_high = 0 #保存当前顶或者底的最高值
    current_low = 0 #保存当前顶或者底的最低值
    current_index = 0 #当前顶或者底的x坐标
    draw_line_data = [] #保存笔的坐标 [[x1,y1],[x2,y2]] 
    i = 0

    for each in combine_list:
        flagtype = each[0]
        lowv = each[1][0]
        highv = each[1][1]
        if draw_line_data == []: #最终结果里还没填数据
            if flagtype == 1: #三连升
                draw_line_data.append([i,lowv])
                current_flag = 0
                current_high = highv
                current_low = lowv
                current_index = i
            elif flagtype == 4: #三连降
                draw_line_data.append([i,highv])
                current_flag = 1
                current_high = highv
                current_low = lowv
                current_index = i

            elif flagtype == 2: #找到一个顶
                draw_line_data.append([i,highv])
                current_flag = 1
                current_high = highv
                current_low = lowv
                current_index = i
            elif flagtype == 3: #找到一个底
                draw_line_data.append([i,lowv])
                current_flag = 0
                current_high = highv
                current_low = lowv
                current_index = i
        else:
            if current_flag == 1: #前一个是顶
                if flagtype == 2: #找到一个新顶
                    if highv >= current_high: #新的顶比前一个顶高
                        current_high = highv
                        current_low = lowv
                        current_index = i
                        draw_line_data.pop()
                        draw_line_data.append([i,current_high])
                elif flagtype == 3: #找到一个底
                    if (i - current_index >= DRAW_GAP) and (lowv <= current_low):
                        current_high = highv
                        current_low = lowv
                        current_index = i
                        current_flag = 0
                        draw_line_data.append([i,current_low])
            elif current_flag == 0: #前一个是底
                if flagtype == 3: #找到一个新底
                    if lowv <= current_low: #新的底比前一个低
                        current_high = highv
                        current_low = lowv
                        current_index = i
                        draw_line_data.pop()
                        draw_line_data.append([i,current_low])
                elif flagtype == 2: #找到一个顶
                    if (i - current_index >= DRAW_GAP) and (highv >= current_high):
                        current_high = highv
                        current_low = lowv
                        current_index = i
                        current_flag = 1
                        draw_line_data.append([i,current_high])
        i =  i + 1
    
    highv = noshadow_kline_data[-1][3]
    lowv = noshadow_kline_data[-1][2]
    i = i-1
    #处理最后一笔
    if i-draw_line_data[-1][0] >= 2:
        #最后一笔向下
        if (draw_line_data[-1][1] < draw_line_data[-2][1]):
            #且最后一点高
            if (highv > draw_line_data[-1][1]) and (lowv > draw_line_data[-1][1]):
                draw_line_data.append([i,highv])
            else:
                draw_line_data.pop()
                draw_line_data.append([i,lowv])
        #最后一笔向上
        elif (draw_line_data[-1][1] > draw_line_data[-2][1]):
            #且最后一点低
            if (lowv < draw_line_data[-1][1]) and (highv < draw_line_data[-1][1]):
                draw_line_data.append([i,lowv])
            else:
                draw_line_data.pop()
                draw_line_data.append([i,highv])
    
    return draw_line_data

def gen_zs_pos(start_x,start_y,end_x,end_y):
    #构建中枢各个点的坐标
    tmp_list = []
    #构造起点坐标
    tmp_position_start = {'xAxis': 0, 'yAxis': 0}
    tmp_position_start['xAxis'] = start_x
    tmp_position_start['yAxis'] = start_y
    tmp_list.append(tmp_position_start)
    #构造终点坐标
    tmp_position_end = {'xAxis': 0, 'yAxis': 0}
    tmp_position_end['xAxis'] = end_x
    tmp_position_end['yAxis'] = end_y
    tmp_list.append(tmp_position_end)
    #print(tmp_list)
    #存储完成的中枢坐标
    return tmp_list


def generate_zs_area(draw):
    #生成中枢区域
    mark_areas = []
    last_zs = [] #存储上一个中枢的开始，高，结束，低
    #基于初始两笔计算zs开始位置和draw方向
    if (draw[1][1] > draw[0][1]) and (draw[2][1] <= draw[0][1]):
    #   |
    #  | |
    # |   |
    #      |
        zs_sx = 0
        zs_ex = 0
        zs_high = draw[1][1]
        zs_low = round((draw[0][1]+draw[2][1])/2,2)
        zs_lenth = 2
        segdir = 0

    elif (draw[1][1] > draw[0][1]) and (draw[2][1] > draw[0][1]):
    #    |
    #   | |
    #  |   |
    # |
        zs_sx = 1
        zs_ex = 1
        zs_high = draw[1][1]
        zs_low = draw[2][1]
        zs_lenth = 1
        segdir = 0

    elif (draw[1][1] < draw[0][1]) and (draw[2][1] > draw[0][1]):
    #      |
    # |   |
    #  | |
    #   |
        zs_sx = 0
        zs_ex = 0
        zs_high = round((draw[0][1]+draw[2][1])/2,2)
        zs_low = draw[1][1]
        zs_lenth = 2
        segdir = 1

    elif (draw[1][1] < draw[0][1]) and (draw[2][1] <= draw[0][1]):
    #|     
    # |   |
    #  | |
    #   |
        zs_sx = 1
        zs_ex = 1
        zs_high = draw[2][1]
        zs_low = draw[1][1]
        zs_lenth = 1
        segdir = 1
    
    for i in range(3,len(draw)):
        x0 = draw[i][0]
        v0 = draw[i][1]
        x1 = draw[i-1][0]
        v1 = draw[i-1][1]
        segdir = 1 - segdir
        
        #向下笔
        if segdir == 0:
            #比zs高点高 
            if (v0 >= zs_high):
                #保存中枢并结束
                if (zs_lenth >= 3):
                    zs_ex = i - 2
                    mark_areas.append(gen_zs_pos(draw[zs_sx][0],zs_high,draw[zs_ex][0],zs_low))
                    last_zs = [zs_sx,zs_high,zs_ex,zs_low]
                zs_sx = i - 1
                zs_ex = i - 1
                zs_high = v1
                zs_low  = v0
                zs_lenth = 1
            #比zs高点低
            elif (v0 < zs_high):
                zs_lenth = zs_lenth + 1
                zs_high = round((zs_high+v1)/2,2)
                
                #zs_high_lst.append(v1)

        #向上笔
        elif segdir == 1:
            #比zs低点低
            if (v0 <= zs_low):
                if (zs_lenth >= 3):
                    zs_ex = i - 2
                    mark_areas.append(gen_zs_pos(draw[zs_sx][0],zs_high,draw[zs_ex][0],zs_low))
                    last_zs = [zs_sx,zs_high,zs_ex,zs_low]
                zs_sx = i - 1
                zs_ex = i - 1
                zs_high = v0
                zs_low  = v1
                zs_lenth = 1
            #比zs低点高
            elif (v0 > zs_low):
                zs_lenth = zs_lenth + 1
                zs_low = round((zs_low+v1)/2,2)
                #zs_low_lst.append(v1)

    if zs_sx < len(draw) - 3:
        zs_ex = len(draw) - 2
        mark_areas.append(gen_zs_pos(draw[zs_sx][0],zs_high,draw[zs_ex][0],zs_low))

    return mark_areas

# ----------------------------------------------------------------
# -----------------------第二种生成中枢的方式-----------------------
# ----------------------------------------------------------------
#基于笔生成zs区间
def uplevel_zsbase(ddata):
    mark_areas = []
    zs_sx = 0
    zs_ex = 0
    zs_dir = 0
    zs_inf = 2
    seg_dir = 0
    zs_high = 0
    zs_low = 0
    reverse_h = 0
    reverse_l = 0
    judge_zs_reverse = 0
    
    if (ddata[1][1] > ddata[0][1]) and (ddata[2][1] <= ddata[0][1]):
        zs_dir = 0
        zs_sx = 0
        segdir = 0
        reverse_h = ddata[1][1]
        reverse_l = ddata[0][1]
    elif (ddata[1][1] > ddata[0][1]) and (ddata[2][1] > ddata[0][1]):
        zs_dir = 1
        zs_sx = 1
        segdir = 0
        reverse_h = ddata[1][1]
        reverse_l = ddata[2][1]
    elif (ddata[1][1] < ddata[0][1]) and (ddata[2][1] > ddata[0][1]):
        zs_dir = 1
        zs_sx = 0
        segdir = 1
        reverse_h = ddata[0][1]
        reverse_l = ddata[1][1]
    elif (ddata[1][1] < ddata[0][1]) and (ddata[2][1] <= ddata[0][1]):
        zs_dir = 0
        zs_sx = 1
        segdir = 1
        reverse_h = ddata[2][1]
        reverse_l = ddata[1][1]

    for i in range(3,len(ddata)):
        curx = ddata[i][0]
        v0 = ddata[i][1]
        v1 = ddata[i-1][1]
        v2 = ddata[i-2][1]
        v3 = ddata[i-3][1]
        v4 = ddata[i-4][1]
        segdir = 1 - segdir
        
        #zs direction = up
        if zs_dir == 1:  
            #笔向上
            if segdir == 1:
                #没有转折判断
                if judge_zs_reverse == 0:
                    #上一点比上一个转折点高
                    if v0 >= reverse_h:
                        #产生了新中枢
                        if (v1 >= zs_high) and (i > 3):
                            zs_ex = i-3
                            zs_high,zs_low = evenoddcheck(ddata,zs_sx,zs_ex+1,1)
                            mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))
                            zs_sx = i-2
                            zs_high,zs_low = evenoddcheck(ddata,zs_sx,i,1)
                            zs_inf = 2
                        #没有产生新中枢
                        elif v1 < zs_high:
                            zs_high,zs_low = evenoddcheck(ddata,zs_sx,i,1)
                            zs_inf += 1
                    #上一点比上一个转折点低，下面进入转折判断
                    elif (v0 < reverse_h) and (i > 3):
                        judge_zs_reverse = 1
                        zs_ex = i-3
                        zs_high,zs_low = evenoddcheck(ddata,zs_sx,zs_ex+1,1)
                #有转折判断：
                elif judge_zs_reverse == 1:
                    #此笔比转折高点高，则趋势延续
                    if v0 >= reverse_h:
                        tmphigh,tmplow = evenoddcheck(ddata,i-4,i,1)
                        #产生新中枢
                        if tmplow >= zs_high:
                            mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))
                            zs_sx = i-4
                            zs_high,zs_low = evenoddcheck(ddata,zs_sx,i,1)
                        #没产生新中枢
                        elif tmplow < zs_high:
                            zs_high,zs_low = evenoddcheck(ddata,zs_sx,i,1)
                    #此笔比转折点低，则变为向下趋势
                    elif v0 < reverse_h:
                        mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))
                        zs_sx = i-3
                        zs_high,zs_low = evenoddcheck(ddata,zs_sx,i-1,0)
                        reverse_h = v0
                        reverse_l = v1
                        zs_dir = 0
                    judge_zs_reverse = 0
            #笔向下
            elif segdir == 0:
                #有转折判断
                if judge_zs_reverse == 0:
                    #刷新转折点
                    reverse_h = v1
                    reverse_l = v0
                #转折判断过程中:
                elif judge_zs_reverse == 1:
                    if v0 <= v4:
                        mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))
                        zs_sx = i-2
                        zs_high,zs_low = evenoddcheck(ddata,zs_sx,i,0)
                        reverse_h = v1
                        reverse_l = v2
                        zs_dir = 0
                        judge_zs_reverse = 0
                    
        #zs direction = down
        elif zs_dir == 0:  
            #笔向上
            if segdir == 0:
                #没有转折判断
                if judge_zs_reverse == 0:
                    #比上一个转折点低
                    if v0 <= reverse_l:
                        #产生了新中枢
                        if (v1 <= zs_low) and (i > 3):
                            zs_ex = i-3
                            zs_high,zs_low = evenoddcheck(ddata,zs_sx,zs_ex+1,0)
                            mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))
                            zs_sx = i-2
                            zs_high,zs_low = evenoddcheck(ddata,zs_sx,i,0)
                            zs_inf = 2
                        #没有产生新中枢
                        elif v1 > zs_low:
                            zs_high,zs_low = evenoddcheck(ddata,zs_sx,i,0)
                            zs_inf += 1
                    #比上一个转折点低，下面进入转折判断
                    elif (v0 > reverse_l) and (i > 3):
                        judge_zs_reverse = 1
                        zs_ex = i-3
                        zs_high,zs_low = evenoddcheck(ddata,zs_sx,zs_ex+1,0)
                #有转折判断：
                elif judge_zs_reverse == 1:
                    #此笔比转折高点高，则趋势延续
                    if v0 <= reverse_l:
                        tmphigh,tmplow = evenoddcheck(ddata,i-4,i,0)
                        #产生新中枢
                        if tmphigh <= zs_low:
                            mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))
                            zs_sx = i-4
                            zs_high,zs_low = evenoddcheck(ddata,zs_sx,i,0)
                        #没产生新中枢
                        elif tmphigh > zs_low:
                            zs_high,zs_low = evenoddcheck(ddata,zs_sx,i,0)
                    #此笔比转折点低，则变为向下趋势
                    elif v0 > reverse_l:
                        mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))
                        zs_sx = i-3
                        zs_high,zs_low = evenoddcheck(ddata,zs_sx,i-1,1)
                        reverse_h = v1
                        reverse_l = v0
                        zs_dir = 1
                    judge_zs_reverse = 0
            #笔向下
            elif segdir == 1:
                #有转折判断
                if judge_zs_reverse == 0:
                    #刷新转折点
                    reverse_h = v0
                    reverse_l = v1
                #转折判断过程中
                elif judge_zs_reverse == 1:
                    if v0 >= v4:
                        mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))
                        zs_sx = i-2
                        zs_high,zs_low = evenoddcheck(ddata,zs_sx,i,1)
                        reverse_h = v2
                        reverse_l = v1
                        zs_dir = 1
                        judge_zs_reverse = 0

    #判断结尾的第一种方法
    # if zs_sx <= len(ddata) - 3:
    #     if segdir == zs_dir:
    #         if ((segdir==0) and (ddata[-1][1]<ddata[-3][1]) and (ddata[-5][1]<ddata[-2][1])) \
    #         or ((segdir==1) and (ddata[-1][1]>ddata[-3][1]) and (ddata[-5][1]>ddata[-2][1])):
    #                 zs_ex = len(ddata) - 2
    #         else:
    #             zs_ex = zs_sx + 1
    #         mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))
    #     elif segdir != zs_dir:
    #         if (ddata[-2] != ddata[zs_sx+2])\
    #         and ( ((segdir==1) and (ddata[-2][1]<ddata[zs_sx][1]) and (ddata[-2][1]<ddata[zs_sx+2][1]))\
    #             or((segdir==0) and (ddata[-2][1]>ddata[zs_sx][1]) and (ddata[-2][1]>ddata[zs_sx+2][1]))):
    #             zs_ex = len(ddata) - 3
    #         else:
    #             zs_ex = zs_sx + 1
    #         mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))

    #判断结尾的第二种方法
    if zs_sx < len(ddata) - 3:
        tmpddata = ddata[zs_sx:]
        tmpmin = tmpddata[0]
        tmpmax = tmpddata[0]
        for each in tmpddata:
            if each[1] < tmpmin[1]:
                tmpmin = each
            if each[1] > tmpmax[1]:
                tmpmax = each
        if zs_dir == 0:
            tmpendx = ddata.index(tmpmin) - 1
            zs_high = ddata[tmpendx][1]
            zs_low = ddata[zs_sx][1]
            mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[tmpendx][0],zs_low))
        elif zs_dir == 1:
            tmpendx = ddata.index(tmpmax) - 1
            zs_high = ddata[zs_sx][1]
            zs_low = ddata[tmpendx][1]
            mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[tmpendx][0],zs_low))
    else:
        zs_ex = zs_sx + 1
        mark_areas.append(gen_zs_pos(ddata[zs_sx][0],zs_high,ddata[zs_ex][0],zs_low))
    
    return mark_areas

#奇数偶数检查及zs高低点判断
def evenoddcheck(datalist, start, end,  direction):
    newlist = datalist[start:end]
    key = [sublist[0] for sublist in newlist]
    value = [sublist[1] for sublist in newlist]
    # print(start,end)
    # print(key,value)
    evenl = key[::2]
    oddl = key[1::2]
    # print(evenl,oddl)
    evelvalue = []
    oddvalue = []
    for each in evenl:
        evelvalue.append(value[key.index(each)])
    for each in oddl:
        oddvalue.append(value[key.index(each)])
    if direction == 1:
        high = min(evelvalue)
        low = max(oddvalue)
    elif direction == 0:
        high = min(oddvalue)
        low = max(evelvalue)
    return high, low

# --------------------------------------------------------------------
# -----------------------第二种生成中枢的方式结束-----------------------
# --------------------------------------------------------------------

def cl_base(df):
    original_kline = generate_orignal_kindle_data(df)
    noshadow_kline = generate_noshadowkline(original_kline)
    contain_kline, combine_list = generate_containkline(noshadow_kline)
    draw = generate_draw(noshadow_kline, combine_list)
    zs_area = generate_zs_area(draw)
    #zs_area = uplevel_zsbase(draw)
    return original_kline,draw,zs_area
