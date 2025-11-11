import pyecharts.options as opts
from pyecharts.charts import Line, Bar, Grid,Candlestick,Kline,Page,EffectScatter
from pyecharts.globals import CurrentConfig, NotebookType, SymbolType
from pyecharts.commons.utils import JsCode
CurrentConfig.NOTEBOOK_TYPE = NotebookType.JUPYTER_LAB

import CLbasement
import pandas as pd

def cau_macd(close_price):
    ema12 = close_price[:1]
    ema26 = close_price[:1]
    for close_p in close_price[1:]:
        ema12new = (ema12[-1]*11/13)+(close_p*2/13)
        ema26new = (ema26[-1]*25/27)+(close_p*2/27)
        ema12.append(ema12new)
        ema26.append(ema26new)
    dif = list(map(lambda a, b: a - b, ema12, ema26))
    dea = dif[:1]
    for each in dif[1:]:
        new = (dea[-1]*0.8)+(each*0.2)
        dea.append(new)
    tmp = list(map(lambda a, b: 2*(a - b), dif, dea))
    macdbar = [round(num, 3) for num in tmp]
    dif = [round(num, 3) for num in dif]
    dea = [round(num, 3) for num in dea]
    return macdbar,dif,dea

def calculate_ma(prices_list, x):
    """
    简单移动平均（SMA）
    :param prices_list: 按时间顺序的收盘价列表 [float]
    :param x: 周期
    :return: 与 prices_list 等长，前 x-1 个元素保持原值，之后为对应均线
    """
    if x <= 0:
        raise ValueError('周期 x 必须为正整数')

    n = len(prices_list)
    ma = prices_list.copy()          # 先复制一份，前 x-1 个位置保留原值

    for i in range(x, n + 1):        # 从第 x 个元素开始算
        window = prices_list[i - x:i]
        ma[i - 1] = round(sum(window) / x, 2)
    return ma


#生成蜡烛图
def generate_kindle_chart(kindledata,date_data,codename):
    kindle_line = Kline()
    kindle_line.add_xaxis(date_data)
    kindle_line.add_yaxis(codename, kindledata)
    kindle_line.set_global_opts(
                title_opts=opts.TitleOpts(title="Stock Price"),
                xaxis_opts=opts.AxisOpts(type_="category", is_scale=True),
                yaxis_opts=opts.AxisOpts(is_scale=True),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),  # 鼠标悬停显示浮窗
                datazoom_opts=[
                    opts.DataZoomOpts(range_start = 50, range_end = 100, type_="inside", xaxis_index=[0, 1, 2]),  # 同步到两个图表
                    opts.DataZoomOpts(range_start = 50, range_end = 100, type_="slider", xaxis_index=[0, 1, 2])   # 同步到两个图表
                ]
    )
    return kindle_line

def generate_maline_chart(df,datelist,ma):
    pricelist = df['close'].tolist()
    line = Line()
    line.add_xaxis(datelist)
    for each in ma:
        ma_value = calculate_ma(pricelist, each)
        maname = 'ma' + str(each)
        line.add_yaxis(maname,ma_value, yaxis_index=1,symbol="none",label_opts=opts.LabelOpts(is_show=False),is_smooth=True)
    return line

def generate_line_chart(datas,datelist,chartname='默认'):
    line = Line()
    line.set_global_opts(title_opts=opts.TitleOpts(title="Line-smooth"))
    line.add_xaxis(datelist)
    line.add_yaxis(chartname,datas, is_smooth=True,label_opts=opts.LabelOpts(is_show=False),)
    return line



#生成成交量图
def generate_volbar_chart(voldata, date_data):
    vol_bar = Bar()
    vol_bar.add_xaxis(date_data)
    vol_bar.add_yaxis(
        "vol", voldata, yaxis_index=1, color="green", label_opts=opts.LabelOpts(is_show=False),
                    itemstyle_opts=opts.ItemStyleOpts(
                        color=JsCode(
                            """
                                function(params) {
                                    var colorList;
                                    colorList = '#4EA9F0';
                                    return colorList;
                                }
                                """))  
                     )
    vol_bar.set_global_opts(
            xaxis_opts=opts.AxisOpts(type_="category", is_scale=True,axislabel_opts=opts.LabelOpts(is_show=False)),
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitline_opts=opts.SplitLineOpts(is_show=True),
                position="right",
                axislabel_opts=opts.LabelOpts(is_show=False)  # 隐藏Y轴刻度
            ),
            datazoom_opts=[
                opts.DataZoomOpts(range_start = 50, range_end = 100, type_="inside", xaxis_index=[0, 1, 2]),  # 同步到两个图表
                opts.DataZoomOpts(range_start = 50, range_end = 100, type_="slider", xaxis_index=[0, 1, 2])   # 同步到两个图表
            ],
            legend_opts=opts.LegendOpts(is_show=False),  # 隐藏图例
        )
    return vol_bar

def generate_line_chart_square_area(line_data,name,colors,markarea=[]):
    xaxis = []
    yaxis = []
    for each in line_data:
        xaxis.append(each[0])
        yaxis.append(each[1])

    line_chart = Line()
    line_chart.add_xaxis(xaxis_data=xaxis)
    line_chart.add_yaxis(series_name=name, y_axis=yaxis)
    line_chart.set_series_opts(
        linestyle_opts=opts.LineStyleOpts(width=2, color=colors)
    )
    if markarea != []:
        line_chart.set_series_opts(
            markarea_opts=opts.MarkAreaOpts(is_silent=True, data=markarea,itemstyle_opts=opts.ItemStyleOpts(color=colors,opacity=0.5))
        )
    return line_chart

def generate_macdbar_chart(macd_data,dif,dea,date_data):
    macd_bar = Bar()
    macd_bar.add_xaxis(date_data)
    macd_bar.add_yaxis(
        "macd", macd_data, yaxis_index=1, color="green", label_opts=opts.LabelOpts(is_show=False),
        itemstyle_opts=opts.ItemStyleOpts(
                        color=JsCode(
                            """
                                function(params) {
                                    var colorList;
                                    if (params.data >= 0) {
                                      colorList = '#ef232a';
                                    } else {
                                      colorList = '#14b143';
                                    }
                                    return colorList;
                                }
                                """))        
    )
    macd_bar.set_global_opts(
            xaxis_opts=opts.AxisOpts(type_="category", is_scale=True,axislabel_opts=opts.LabelOpts(is_show=False)),
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitline_opts=opts.SplitLineOpts(is_show=True),
                position="right",
                axislabel_opts=opts.LabelOpts(is_show=False)  # 隐藏Y轴刻度
            ),
            datazoom_opts=[
                opts.DataZoomOpts(range_start = 50, range_end = 100,type_="inside", xaxis_index=[0, 1, 2]),  # 同步到两个图表
                opts.DataZoomOpts(range_start = 50, range_end = 100,type_="slider", xaxis_index=[0, 1, 2])   # 同步到两个图表
            ],
            legend_opts=opts.LegendOpts(is_show=False),  # 隐藏图例
        ) 
    line = Line()
    line.add_xaxis(date_data)
    line.add_yaxis("dif", dif, yaxis_index=1, color="orange", symbol="none", label_opts=opts.LabelOpts(is_show=False),is_smooth=True)  
    line.add_yaxis("dea", dea, yaxis_index=1, color="black", symbol="none", label_opts=opts.LabelOpts(is_show=False),is_smooth=True)
    macd_bar.overlap(line)
    
    return macd_bar

def create_point(marks):
    buyppoint = []
    sellpoint = []
    for each in marks:
        if each[2] == 1:
            buyppoint.append(each)
        elif each[2] == 0:
            sellpoint.append(each)
    
    #构造买点
    if buyppoint != []:
        markpointx = []
        markpointy = []
        for each in buyppoint:
            markpointx.append(each[0])
            markpointy.append(each[1])
        ang=180,
        pcolors = 'red'
        buy_mark_point = (
        EffectScatter()
        .add_xaxis(markpointx)
        .add_yaxis(
            series_name='buypoint',
            y_axis=markpointy,
            symbol=SymbolType.ARROW,  # 使用箭头符号
            symbol_size=10,
            symbol_rotate = ang,
            itemstyle_opts=opts.ItemStyleOpts(color=pcolors),  # 红色箭头
            )
        )
    #构造卖点
    if sellpoint != []:
        markpointx = []
        markpointy = []
        for each in sellpoint:
            markpointx.append(each[0])
            markpointy.append(each[1])
        ang=0,
        pcolors = 'green'
        sell_mark_point = (
        EffectScatter()
        .add_xaxis(markpointx)
        .add_yaxis(
            series_name='sellpoint',
            y_axis=markpointy,
            symbol=SymbolType.ARROW,  # 使用箭头符号
            symbol_size=10,
            symbol_rotate = ang,
            itemstyle_opts=opts.ItemStyleOpts(color=pcolors),
            )
        )
    #返回结果
    if (buyppoint != []) and (sellpoint != []):
        buy_mark_point.overlap(sell_mark_point)
        return buy_mark_point
    elif (buyppoint == []) and (sellpoint != []):
        return sell_mark_point
    elif (buyppoint != []) and (sellpoint == []):
        return buy_mark_point
    else:
        return False



def generate_pic_by_df(tmpdata, buypoint = [], ma=[20]):
    codename = str(tmpdata.head(1)['code'].values[0])
    original_kline,draw,zs_area = CLbasement.cl_base(tmpdata)
    vol_data = tmpdata['volume'].tolist()
    datelist = tmpdata['datetime'].astype(str).tolist()
    macd_data,dif,dea = cau_macd(tmpdata['close'].tolist())
    
    kindle_chart = generate_kindle_chart(original_kline,datelist,codename)
    maline_chart = generate_maline_chart(tmpdata,datelist,ma)
    draw_chart = generate_line_chart_square_area(draw,'draw','blue',zs_area)
    vol_chart = generate_volbar_chart(vol_data, datelist)
    macd_chart = generate_macdbar_chart(macd_data,dif,dea,datelist)
    
    kindle_chart.overlap(draw_chart)
    kindle_chart.overlap(maline_chart)
    if buypoint != []:
        buy_chart = create_point(buypoint)
        if buy_chart:
            kindle_chart.overlap(buy_chart)
    
    grid = Grid()
    grid.add(kindle_chart, grid_opts=opts.GridOpts(pos_bottom="50%"))
    grid.add(vol_chart, grid_opts=opts.GridOpts(pos_top="55%",pos_bottom="30%"))
    grid.add(macd_chart, grid_opts=opts.GridOpts(pos_top="75%"))
    return grid











