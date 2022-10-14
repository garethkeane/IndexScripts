#20220925 Turn dump from CSV into a python list
# 

import csv
import pandas as pd

dumped_dataframe = pd.read_csv('deeptech_index_draft.csv')

tickers = dumped_dataframe[dumped_dataframe.columns[1]].values.tolist()
#print(dumped_dataframe)
#print(tickers)

#Define categories
space_category_list = []
manufacturing_category_list = []
energy_category_list = []
built_category_list = []
health_category_list = []
hyperscale_ai_category_list = []
mobility_category_list = []
test_list = []

#Define Index tickers
index_list = ['^IXIC', '^GSPC']

dumped_dataframe = dumped_dataframe.reset_index()

for index, row in dumped_dataframe.iterrows():
  category = row[5]
  ticker = str(row[2])
  print('Working on', ticker)
  print('Category:', category)
  if (category == 'Space, Aerospace & Defense'):
    space_category_list.append(ticker)
    #print('Space list:', space_category_list)
  elif (category == 'Manufacturing'):
    manufacturing_category_list.append(ticker)
    print('Manufacturing list:', manufacturing_category_list)
  elif (category == 'Energy & Resources'): 
    energy_category_list.append(ticker)
  elif (category == 'Built Environment'):
    built_category_list.append(ticker)
  elif (category == 'Health'):
    health_category_list.append(ticker)
  elif (category == 'Hyperscale AI'):
    hyperscale_ai_category_list.append(ticker)
  else: #Onlty one left is Mobility & Logistics
    mobility_category_list.append(ticker)

with open ('category_ticker_list.py', 'w') as output_file:
  output = 'newspace_ticker_list = ['
  output_file.write(output)
  for ticker in space_category_list:
    output = '\'' + ticker + '\'' + ', '
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

  output = 'manufacturing_deeptech_index_list = ['
  output_file.write(output)
  for ticker in manufacturing_category_list:
    output = '\'' + ticker + '\'' + ', '
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

  output = 'materials_energy_deeptech_index_list = ['
  output_file.write(output)
  for ticker in energy_category_list:
    output = '\'' + ticker + '\'' + ', '
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

  output = 'built_environment_deeptech_index_list = ['
  output_file.write(output)
  for ticker in built_category_list:
    output = '\'' + ticker + '\'' + ', '
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

  output = 'health_deeptech_index_list = ['
  output_file.write(output)
  for ticker in health_category_list:
    output = '\'' + ticker + '\'' + ', '
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

  output = 'hyperscale_ai_deeptech_index_list = ['
  output_file.write(output)
  for ticker in hyperscale_ai_category_list:
    output = '\'' + ticker + '\'' + ', '
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

  output = 'mobility_deeptech_index_list = ['
  output_file.write(output)
  for ticker in mobility_category_list:
    output = '\'' + ticker + '\'' + ', '
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

  output = 'index_ticker_list = ['
  output_file.write(output)
  for ticker in index_list:
    output = '\'' + ticker + '\'' + ','
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

