# 20221004 - Use Yahoo Fiannce APIs to get analyst estimates for a ticker list
#            Output is a file called master_forward_revenue_data.csv

import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer
import shutil
import plotly.express as px
import requests
import yahoo_fin.stock_info as yfin

#Try to get analyst estimates as well

from ticker_list import long_ticker_list
index_ticker_list = ['^IXIP', '^GSPC']

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

with open('master_forward_revenue_data.csv', 'w') as output_file:
  output = 'Ticker,Forward Revenue,Revenue Growth Estimate\n'
  output_file.write(output)
  for ticker in long_ticker_list:
    print('Working on ', ticker)
    try:
      analyst_table = yfin.get_analysts_info(ticker)
    except ValueError:
      print('Ticker ', ticker, 'had a problem with table retrieval - setting revenue to 0')
      next_year_revenue = 0
    else:
      #print('Data from analysts:\n', analyst_table)
      revenue_table = analyst_table['Revenue Estimate']
      #print('Next year revenue table :\n', revenue_table)
      next_year_revenue_column = revenue_table.iloc[:,4]
      next_year_revenue = next_year_revenue_column[1]
      revenue_growth_estimate = next_year_revenue_column[5]
      if pd.isna(revenue_growth_estimate):
        revenue_growth_estimate = 'None'
      #Try to strip out Yahoo k/M/B/T notation
      next_year_revenue = text_to_num(next_year_revenue) 
    next_year_revenue = str(next_year_revenue)
    print('Next year revenue for ', ticker, ' is ', next_year_revenue)
    print('Next year revenue growth for ', ticker, ' is ', revenue_growth_estimate)
    if ',' in revenue_growth_estimate:
      revenue_growth_estimate = '\"' + revenue_growth_estimate + '\"'
    output = ticker + ',' + next_year_revenue + ',' + revenue_growth_estimate + '\n'
    output_file.write(output)


