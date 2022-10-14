#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
#Revision tracker
#20220206 Dump Yahoo Finance yTicker info for a single ticker symbol - testing due to issues with SATL
#		- Needed more than one ticker for the historical price stuff to work so added RKLB
#20221005 Now using yfin to generate market cap data

import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer

import yahoo_fin.stock_info as yfin

from ticker_list import long_ticker_list

#setup the list of tickers 
#newspace_ticker_list = ['ACHR', 'ARQQ', 'ASTR', 'ASTS', 'BKSY', 'BLDE', 'IONQ', 'JOBY', 'LILM', 'MNTS', 'PL', 'RDW', 'RKLB', 'SATL', 'SPIR', 'SPCE', 'VORB']
#newspace_ticker_list = ['RKLB', 'SATL']
#newspace_ticker_list = ['SATL', 'BA', 'FANUY']
#legacy_ticker_list = ['AJRD', 'AVAV', 'AIR.PA', 'BA', 'BA.L', 'GRMN', 'HON', 'IRDM', 'LHX', 'LMT', 'MAXR', 'NOC', 'OHB.F', 'RTX', 'SESG.PA', 'HO.PA', 'TRMB', 'VSAT']
#index_ticker_list = ['^IXIC', '^GSPC']

ticker_data = {}

def text_to_num(text, bad_data_val = 0):
    d = {
        'K': 1000,
        'M': 1000000,
        'B': 1000000000
    }
    if not isinstance(text, str):
        # Non-strings are bad are missing data in poster's submission
        return bad_data_val

    elif text[-1] in d:
        # separate out the K, M, or B
        num, magnitude = text[:-1], text[-1]
        return int(float(num) * d[magnitude])
    else:
        return float(text)

#Combine newspace and legacy tickers to get everything in one shot

#This seems to sort the list entries alphabetically so mixes newspace and legacy
#ticker_list = newspace_ticker_list + legacy_ticker_list

#Try to extend the list instead
ticker_list = []
ticker_list.extend(long_ticker_list)
#ticker_list.extend(legacy_ticker_list)
#ticker_list.extend(index_ticker_list)
print(ticker_list)

with open ('test_market_cap_data.csv', 'w') as output_file:
 output = 'Ticker,Market Cap,EV\n'
 output_file.write(output)
 for ticker in ticker_list:
  print('Working on ', ticker)
  dataframe = yfin.get_stats_valuation(ticker)
  dataframe = dataframe.iloc[:,:2]
  print(dataframe)
  #data_column = dataframe.iloc[2]
  ev = dataframe.iloc[1][1]
  ev = str(text_to_num(ev))
  print('EV: ', ev)
  market_cap = dataframe.iloc[0][1]
  market_cap = str(text_to_num(market_cap))
  print('Market Cap:', market_cap)
  output = ticker + ',' + market_cap + ',' + ev + '\n'
  output_file.write(output)

