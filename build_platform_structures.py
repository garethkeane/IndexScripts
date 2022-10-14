#20220925 Turn dump from CSV into a python list
#20220928 Forked from build_category_structures.py to cover platforms - Compute & Connectivity, Enhanced Production, Automation 

import csv
import pandas as pd

dumped_dataframe = pd.read_csv('deeptech_index_draft.csv')

tickers = dumped_dataframe[dumped_dataframe.columns[1]].values.tolist()
#print(dumped_dataframe)
#print(tickers)

#Define categories
connectivity_and_compute_platform_list = []
enhanced_production_platform_list = []
automation_platform_list = []

dumped_dataframe = dumped_dataframe.reset_index()

for index, row in dumped_dataframe.iterrows():
  platform = row[6]
  ticker = str(row[2])
  print('Working on', ticker)
  print('Platform:', platform)
  if (platform == 'Connectivity & Compute'):
    #print('Assignign to Connectiv
    connectivity_and_compute_platform_list.append(ticker)
  elif(platform == 'Connectivity and Compute'):
    connectivity_and_compute_platform_list.append(ticker)
  elif (platform == 'Enhanced Production'):
    enhanced_production_platform_list.append(ticker)
  else: #Only one left is Automation
    automation_platform_list.append(ticker)

with open ('platform_ticker_list.py', 'w') as output_file:
  output = 'connectivity_and_compute_list = ['
  output_file.write(output)
  for ticker in connectivity_and_compute_platform_list:
    output = '\'' + ticker + '\'' + ', '
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

  output = 'enhanced_production_list = ['
  output_file.write(output)
  for ticker in enhanced_production_platform_list:
    output = '\'' + ticker + '\'' + ', '
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

  output = 'automation_list = ['
  output_file.write(output)
  for ticker in automation_platform_list:
    output = '\'' + ticker + '\'' + ', '
    output_file.write(output)
  output = ']\n'
  output_file.write(output)

