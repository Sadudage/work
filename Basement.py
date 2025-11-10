#数据分析相关的库
import pandas as pd
import numpy as np
import time
import re
from datetime import datetime, timedelta
import random
import statistics
#网络API调用库
import tushare as ts
import baostock as bs
#其他库
import logging
import os

#设置token
ts.set_token('2e7adb11584089e1560db3041ce85f5818bc138750c95b0a0f67e284')
pro = ts.pro_api()
#-----------------------------------------------------------API数据获取相关--------------------------------------------------
##基于tushare获取指定日期区间的日历
def get_toshare_trade_cal(startdate, enddate):
    trade_date_df = pro.trade_cal(**{
        "exchange": "",
        "cal_date": "",
        "start_date": startdate,
        "end_date": enddate,
        "is_open": "",
        "limit": "",
        "offset": ""
    }, fields=[
        "exchange",
        "cal_date",
        "is_open",
        "pretrade_date"
    ])
    trade_date_list = trade_date_df[trade_date_df['is_open'] == 1]['cal_date'].to_list()
    return trade_date_list

#基于tushare获取指定股票的开始结束日期数据
def tushare_code_sddate(code,sdate,edate):
    df = pro.daily(**{
        "ts_code": code,
        "trade_date": "",
        "start_date": sdate,
        "end_date": edate,
        "offset": "",
        "limit": ""
    }, fields=[
        "ts_code",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "vol",
        "amount",
        "pct_chg"
    ])
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d %H:%M')
    df.columns = ['code','datetime','open','high','low','close','volume','amount','pct_chg']
    df = df.sort_values(by = 'datetime')
    df = df.reset_index(drop = True)
    return df

def baostock_code_sddate(ostockcode, startdate, enddate,freq):
    number, suffix = ostockcode.split('.')
    stockcode = f"{suffix.lower()}.{number}"
    # sdate = startdate.strftime('%Y-%m-%d')
    # edate = enddate.strftime('%Y-%m-%d')
    
    lg = bs.login()
    rs = bs.query_history_k_data_plus(stockcode,
        "date,time,code,open,high,low,close,volume,amount,adjustflag",
        start_date=startdate, end_date=enddate, 
        frequency=freq, adjustflag="2") 
    data_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)
    result['time'] = result['time'].astype(str)
    result['time'] = pd.to_datetime(result['time'], format='%Y%m%d%H%M%S%f').dt.strftime('%Y-%m-%d %H:%M')
    cols = ['open', 'high', 'low', 'close','volume','amount']
    for c in cols:
        # 去掉千位分隔符或空格等可再补充处理
        result[c] = pd.to_numeric(result[c], errors='coerce').round(2)
    result = result[['code','time','open','high','low','close','volume','amount']]
    result.columns = ['code','datetime','open','high','low','close','volume','amount']
    result['pct_chg'] = (result['close'].pct_change() * 100).round(2)
    result['pct_chg'] = result['pct_chg'].fillna(0)
    bs.logout()
    return result


#------------------------------------------------------------本地读取数据相关---------------------------------------------------
def read_data_local(filepath):
    result = pd.read_csv(filepath)
    if 'datetime' in result.columns:
        result.rename(columns={'datetime': 'trade_datetime'}, inplace=True)
        result = result[['code','trade_datetime','open','close','low','high','volume','amount']]
    result['trade_datetime'] = pd.to_datetime(result['trade_datetime'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%Y-%m-%d %H:%M:%S')
    cols = ['open', 'high', 'low', 'close','volume','amount']
    for c in cols:
        # 去掉千位分隔符或空格等可再补充处理
        result[c] = pd.to_numeric(result[c], errors='coerce').round(2)
    result.columns = ['code','datetime','open','close','low','high','volume','amount']
    result = result[['code','datetime','open','high','low','close','volume','amount']]
    result['pct_chg'] = (result['close'].pct_change() * 100).round(2)
    result['pct_chg'] = result['pct_chg'].fillna(0)
    result = result[result['volume'] != 0]
    result = result.reset_index(drop=True)
    
    return result

def resample_to_xmin(df, rows_per_group):
    # 计算需要的组数
    num_groups = len(df) // rows_per_group
    # 使用 list comprehension 创建聚合的 DataFrame
    aggregated_data = []
    for i in range(num_groups):
        group = df.iloc[i * rows_per_group : (i + 1) * rows_per_group]
        aggregated_data.append({
            'code': group['code'].iloc[0],  # 假设取第一个
            'trade_datetime': group['datetime'].iloc[-1],
            'open': group['open'].iloc[0],
            'close': group['close'].iloc[-1],
            'low': group['low'].min(),
            'high': group['high'].max(),
            'volume': group['volume'].sum(),
            'amount': group['amount'].sum(),
        })
    return pd.DataFrame(aggregated_data)


