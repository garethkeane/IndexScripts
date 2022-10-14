#20220925 Turn dump from CSV into a python list
#20221005 Also use dump from CSV to generate a ticker -> category map 

import csv
import pandas as pd

dumped_dataframe = pd.read_csv('deeptech_index_draft.csv')

tickers = dumped_dataframe[dumped_dataframe.columns[1]].values.tolist()
categories = dumped_dataframe[dumped_dataframe.columns[4]].values.tolist()
#print(dumped_dataframe)
#print(tickers)

with open ('ticker_list.py', 'w') as output_file:
  output = 'long_ticker_list = ['
  output_file.write(output)
  for ticker in tickers:
    output_ticker = str(ticker)
    output = '\'' + output_ticker + '\'' + ',' + '\n'
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

with open('category_map.py', 'w') as output_file:
  output = 'category_map = {\n'
  output_file.write(output)
  for (ticker, category) in zip(tickers, categories):
    print('Ticker:',ticker,'\nCategory:',category,'\n')
    output = '\'' + ticker + '\'' + ':' + '\'' + category + '\',\n'
    output_file.write(output)
  output = '}\n'
  output_file.write(output)
    

