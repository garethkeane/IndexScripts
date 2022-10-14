#20201004 - Collect data from the following two sources:
#           master_marketcaps_list.csv - most data
#           master_forward_revenue_data.csv - Forward revenue from Yahoo Finance
#20201005 - Add another data source: category_map.py
#           Maps all the tickers to the categories we are using
#           Also remove Market Cap from output 

import pandas as pd
#import re
import csv
#import datetime
from csv import writer
from natsort import natsorted
from natsort import natsort_keygen

from category_map import category_map
from company_name_map import company_name_map

#import shutil
#import plotly.express as px
#import requests

#Define multiple_limit - output NM for naything > than this in terms of EV/TTM, EV/Forward, etc
multiple_limit = 300


ticker_data = pd.read_csv('master_marketcaps_list.csv')
forward_revenue_data = pd.read_csv('master_forward_revenue_data.csv')
print('Ticker data:\n', ticker_data)
print('Revenue data:\n', forward_revenue_data)

merged_data = pd.merge(ticker_data, forward_revenue_data)
print('here!')
print(merged_data)
print(merged_data.dtypes)
merged_data.to_csv('merged_data.csv')
#merged_data = merged_data.astype({'EV':'float', 'TTM Revenue':'float', 'Forward Revenue':'float'})
#print(merged_data.dytpes)

#Convert numbers from B/M/k
def text_to_num(text, bad_data_val = 0):
    d = {
        'K': 1000,
        'k': 1000,
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


calculated_ev_ltm_column = []
calculated_ev_ftm_column = []

for index,row in merged_data.iterrows():
  calculated_ev_to_ltm = '0'
  calculated_ev_to_ftm = '0'
  ev = row[3]
  ttm_revenue = row[5]
  ftm_revenue = row[16]
  print(row[0], 'EV:', ev, 'TTM:', ttm_revenue, 'FTM:', ftm_revenue, '\n')
  if (ev == 'None'):
     calculated_ev_to_ltm = 'None'
     calculated_ev_to_ttm = 'none'
  elif (ttm_revenue == 'None'):
     calculated_ev_to_ltm = 'None'
  elif (ftm_revenue == 0):
     calculated_ev_to_ltm = 'None'
  elif(ftm_revenue == 'None'):
     calculated_ev_to_ltm = 'None'
  else:
     ev = float(ev)
     ttm_revenue = float(ttm_revenue)
     ftm_revenue = float(ftm_revenue)
     if(ttm_revenue != 0):
       calculated_ev_to_ltm = ev/ttm_revenue
     else:
       calculated_ev_to_ltm = 'None'
     if(ftm_revenue != 0):
       calculated_ev_to_ftm = ev/ftm_revenue
     else:
       calculated_ev_to_ftm = 'None'
  calculated_ev_ltm_column.append(calculated_ev_to_ltm)
  calculated_ev_ftm_column.append(calculated_ev_to_ftm)

merged_data['Calculated EV/LTM'] = calculated_ev_ltm_column
merged_data['Calculated EV/FTM'] = calculated_ev_ftm_column

#merged_data['Calculated EV/LTM'] = merged_data['EV']/merged_data['TTM Revenue']
#merged_data['Calculated EV/FTM'] = merged_data['EV']/merged_data['Forward Revenue']

print(merged_data)

#Now build table to send to HTMl generating script

output_dataframe = merged_data
output_dataframe = output_dataframe.drop(['Currency', 'TTM Revenue', 'Trailing EPS', 'Forward EPS', 'Revenue Growth Rate', 'Gross Margin', 'Average Volume', 'Float', 'Total Shares', 'Forward Revenue', 'Calculated EV/LTM'], axis=1)
output_dataframe = output_dataframe.rename(columns={'Market Cap':'Market Cap ($)', 'EV':'Enterprise Value ($)', 'EV/Revenue':'EV/TTM Revenue', 'Calculated EV/FTM':'EV/Forward Revenue'})
format_dict = {'Market Cap ($)':'{0:,.0f}', 'Enterprise Value ($)':'{0:,.0f}', 'EV/Revenue':'{0:,.1f}', 'EV/Forward Revenue':'{0:,.1f}'}
output_dataframe.style.format(format_dict).hide_index() 
print(output_dataframe)

output_dataframe.to_csv('generated_html_table_input.csv')

output_dataframe = output_dataframe.sort_values(by='Company Name', key=lambda col: col.str.lower())
print(output_dataframe)

#Define six sub-sector dataframes for dumping individual tables for each subsector

built_environment_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','EV/TTM Rev Mult','EV/2023 Rev Mult','Rev Growth Rate (%)','Subsector'])
energy_and_resources_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','EV/TTM Rev Mult','EV/2023 Rev Mult','Rev Growth Rate (%)','Subsector'])
health_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','EV/TTM Rev Mult','EV/2023 Rev Mult','Rev Growth Rate (%)','Subsector'])
manufacturing_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','EV/TTM Rev Mult','EV/2023 Rev Mult','Rev Growth Rate (%)','Subsector'])
mobility_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','EV/TTM Rev Mult','EV/2023 Rev Mult','Rev Growth Rate (%)','Subsector'])
space_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','EV/TTM Rev Mult','EV/2023 Rev Mult','Rev Growth Rate (%)','Subsector'])

#Define another six dataframes for PE Ratios
built_environment_pe_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','Forward PE Ratio','Trailing PE Ratio','Rev Growth Rate (%)','Subsector'])
energy_and_resources_pe_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','Forward PE Ratio','Trailing PE Ratio','Rev Growth Rate (%)','Subsector'])
health_pe_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','Forward PE Ratio','Trailing PE Ratio','Rev Growth Rate (%)','Subsector'])
manufacturing_pe_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','Forward PE Ratio','Trailing PE Ratio','Rev Growth Rate (%)','Subsector'])
mobility_pe_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','Forward PE Ratio','Trailing PE Ratio','Rev Growth Rate (%)','Subsector'])
space_pe_dataframe = pd.DataFrame(columns= ['Ticker','Company Name','Market Cap ($M)','Forward PE Ratio','Trailing PE Ratio','Rev Growth Rate (%)','Subsector'])


with open('generate_html_table_input.csv', 'w') as output_file:
  output = 'Ticker,Company Name,Market Cap ($M),EV/TTM Rev Mult,EV/2023 Rev Mult,Rev Growth Rate (%),Subsector\n'
  output_file.write(output)
  for index,row in output_dataframe.iterrows():
    ticker = row[0]
    company_name = row[1]
    market_cap = row[2]
    ev = row[3]
    ev_ttm_revenue = row[4]
    ev_ftm_revenue = row[8]
    forward_pe = row[5]
    trailing_pe = row[6]
    #Now try and make everything pretty

    #market_cap 
    if (market_cap == 'None'):
      market_cap = 'None'
    else:
      market_cap = float(market_cap)
      market_cap = market_cap/1000000
      market_cap = '{:,.0f}'.format(market_cap)
      market_cap = '\"' + market_cap + '\"'
      print('market Cap:', market_cap)
    
    #ev
    if (ev == 'None'):
      ev = 'None'
    else:
      print('EV:', ev)
      ev=float(ev)
      ev=ev/1000000
      ev = float(ev)
      ev = '{:,.0f}'.format(ev)
      ev = '\"' + ev + '\"'
    
    #ev_ttm_revenue
    if (ev_ttm_revenue == 'None'):
      ev_ttm_revenue = 'NM'
    else:
      ev_ttm_revenue = float(ev_ttm_revenue)
      if (ev_ttm_revenue > multiple_limit):
        ev_ttm_revenue = 'NM'
      elif (ev_ttm_revenue < 0):
        ev_ttm_revenue = 'NM'
      else:
         ev_ttm_revenue = float(ev_ttm_revenue)
         ev_ttm_revenue = '{:,.1f}'.format(ev_ttm_revenue)
         if ',' in ev_ttm_revenue:
           ev_ttm_revenue = '\"' + ev_ttm_revenue + '\"'
    
    #ev_ftm_revenue
    if (ev_ftm_revenue == 'None'):
      ev_ftm_revenue = 'NM'
    else:
      ev_ftm_revenue = float(ev_ftm_revenue)
      if (ev_ftm_revenue > multiple_limit):
        ev_ftm_revenue = 'NM'
      #elif (ev_ftm_revenue < 0):
      #  ev_ftm_revenue = 'NM' - this causes problems when you try to convert EV/FTM column to a float further down
      else:
        print('EV/FTM:', ev_ftm_revenue)
        ev_ftm_revenue = float(ev_ftm_revenue)
        ev_ftm_revenue = '{:,.1f}'.format(ev_ftm_revenue) 
        if ',' in ev_ftm_revenue:
          ev_ftm_revenue = '\"' + ev_ftm_revenue + '\"' 

    #forward_pe
    if (forward_pe == 'None'):
      forward_pe = 'NM'
    elif pd.isna(forward_pe):
      forward_pe = 'NM'
    else:
      forward_pe = text_to_num(forward_pe)
      forward_pe = float(forward_pe)
      forward_pe = '{:,.1f}'.format(forward_pe)
      if ',' in forward_pe:
        forward_pe = '\"' + forward_pe + '\"'
  
    #trailing_pe
    if (trailing_pe == 'None'):
      trailing_pe = 'NM'
    elif pd.isna(trailing_pe):
      trailing_pe = 'NM'
    else:
      trailing_pe = float(trailing_pe)
      trailing_pe = '{:,.1f}'.format(trailing_pe) 
      if ',' in trailing_pe:
        trailing_pe = '\"' + trailing_pe + '\"'

    output_market_cap = str(market_cap)
    output_ev = str(ev)
    output_ev_ttm = str(ev_ttm_revenue)
    output_ev_ftm = str(ev_ftm_revenue)
    output_category = str(category_map[ticker])
    if ',' in output_category:
      output_category = '\"' + output_category + '\"'
    
    output_rev_growth = row[7]  
    if ',' in output_rev_growth:
      output_rev_growth = output_rev_growth.replace(',','') 
    output_rev_growth = output_rev_growth.replace('%','')
    if (output_rev_growth == 'None'):
      output_rev_growth = 'None'
    else:
      output_rev_growth = float(output_rev_growth)
      output_rev_growth = '{:,.1f}'.format(output_rev_growth)
    if ',' in output_rev_growth:
      output_rev_growth = '\"' + output_rev_growth + '\"' 
    
    #Map company name for the output tables using company_name_map
    company_name = company_name_map[company_name]

    #output = ticker + ',' + company_name + ',' + output_market_cap + ',' + output_ev + ',' + output_ev_ttm + ',' + output_ev_ftm + '\n'
    #output = ticker + ',' + company_name + ',' + output_ev + ',' + output_ev_ttm + ',' + output_ev_ftm + ',' + output_rev_growth + ',' + output_category + '\n'
    output = ticker + ',' + company_name + ',' + output_market_cap + ',' + output_ev_ttm + ',' + output_ev_ftm + ',' + output_rev_growth + ',' + output_category + '\n'
    output_file.write(output)
    #Fix for variables having multiple sets of "
    output_market_cap = output_market_cap.replace('\"','')
    output_category = output_category.replace('\"','')
    output_rev_growth = output_rev_growth.replace('\"','')
    output_ev_ttm = output_ev_ttm.replace('\"','')
    output_ev_ftm = output_ev_ftm.replace('\"','')
    forward_pe = forward_pe.replace('\"','')
    trailing_pe = trailing_pe.replace('\"','')
    output_for_dataframe = {
      'Ticker':ticker, 
      'Company Name':company_name,
      'Market Cap ($M)':output_market_cap, 
      'EV/TTM Rev Mult':output_ev_ttm, 
      'EV/2023 Rev Mult':output_ev_ftm, 
      'Rev Growth Rate (%)':output_rev_growth, 
      'Subsector':output_category
      }

    #Now dump this output line to whatever sector table it belongs to
    output_dataframe = pd.DataFrame([output_for_dataframe])
    if (output_category == 'Built Environment'):
      built_environment_dataframe = pd.concat([built_environment_dataframe, output_dataframe], axis=0, ignore_index=True)
    elif (output_category == 'Energy & Resources'):
      energy_and_resources_dataframe = pd.concat([energy_and_resources_dataframe, output_dataframe], axis=0, ignore_index=True)
    elif (output_category == 'Health'):
      health_dataframe = pd.concat([health_dataframe, output_dataframe], axis=0, ignore_index=True)
    elif (output_category == 'Manufacturing'):
      manufacturing_dataframe = pd.concat([manufacturing_dataframe, output_dataframe], axis=0, ignore_index=True)
    elif (output_category == 'Mobility & Logistics'):
      mobility_dataframe = pd.concat([mobility_dataframe, output_dataframe], axis=0, ignore_index=True)
    elif (output_category == 'Space, Aerospace & Defense'):
      space_dataframe = pd.concat([space_dataframe, output_dataframe], axis=0, ignore_index=True)
    else:
      print('Could not find:', output_category)

    #Now build dataframes for PE Ratios
    output_for_pe_dataframe = {
      'Ticker':ticker,
      'Company Name':company_name,
      'Market Cap ($M)':output_market_cap,
      'Forward PE Ratio':forward_pe,
      'Trailing PE Ratio':trailing_pe,
      'Rev Growth Rate (%)':output_rev_growth,
      'Subsector':output_category,
      }

    #Now dump this output line to whatever sector table it belongs to
    output_pe_dataframe = pd.DataFrame([output_for_pe_dataframe])
    if (output_category == 'Built Environment'):
      built_environment_pe_dataframe = pd.concat([built_environment_pe_dataframe, output_pe_dataframe], axis=0, ignore_index=True)
    elif (output_category == 'Energy & Resources'):
      energy_and_resources_pe_dataframe = pd.concat([energy_and_resources_pe_dataframe, output_pe_dataframe], axis=0, ignore_index=True)
    elif (output_category == 'Health'):
      health_pe_dataframe = pd.concat([health_pe_dataframe, output_pe_dataframe], axis=0, ignore_index=True)
    elif (output_category == 'Manufacturing'):
      manufacturing_pe_dataframe = pd.concat([manufacturing_pe_dataframe, output_pe_dataframe], axis=0, ignore_index=True)
    elif (output_category == 'Mobility & Logistics'):
      mobility_pe_dataframe = pd.concat([mobility_pe_dataframe, output_pe_dataframe], axis=0, ignore_index=True)
    elif (output_category == 'Space, Aerospace & Defense'):
      space_pe_dataframe = pd.concat([space_pe_dataframe, output_pe_dataframe], axis=0, ignore_index=True)
    else:
      print('Could not find:', output_category)
 
    built_environment_dataframe.to_csv('built_environment_table_data.csv', index=False) 
    energy_and_resources_dataframe.to_csv('energy_and_resources_table_data.csv', index=False) 
    health_dataframe.to_csv('health_table_data.csv', index=False) 
    manufacturing_dataframe.to_csv('manufacturing_table_data.csv', index=False) 
    mobility_dataframe.to_csv('mobility_table_data.csv', index=False) 
    space_dataframe.to_csv('space_table_data.csv', index=False) 

    # Now do some sorting of these subsector dataframes and dump to other .html files
    # Maybe first have to convert the columns I am sorting on to floats?
    
    built_environment_dataframe = built_environment_dataframe.astype({'EV/2023 Rev Mult':'float'})
    energy_and_resources_dataframe = energy_and_resources_dataframe.astype({'EV/2023 Rev Mult':'float'})
    health_dataframe = health_dataframe.astype({'EV/2023 Rev Mult':'float'})
    manufacturing_dataframe = manufacturing_dataframe.astype({'EV/2023 Rev Mult':'float'})
    mobility_dataframe = mobility_dataframe.astype({'EV/2023 Rev Mult':'float'})
    space_dataframe = space_dataframe.astype({'EV/2023 Rev Mult':'float'})
 
    built_environment_dataframe = built_environment_dataframe.sort_values(by='EV/2023 Rev Mult', ascending=False)
    built_environment_dataframe.to_csv('built_environment_table_sort_on_ev_ftm.csv', index=False)
    energy_and_resources_dataframe = energy_and_resources_dataframe.sort_values(by='EV/2023 Rev Mult', ascending=False)
    energy_and_resources_dataframe.to_csv('energy_and_resources_table_sort_on_ev_ftm.csv', index=False)
    health_dataframe = health_dataframe.sort_values(by='EV/2023 Rev Mult', ascending=False)
    health_dataframe.to_csv('health_table_sort_on_ev_ftm.csv', index=False)
    manufacturing_dataframe = manufacturing_dataframe.sort_values(by='EV/2023 Rev Mult', ascending=False)
    manufacturing_dataframe.to_csv('manufacturing_table_sort_on_ev_ftm.csv', index=False)
    mobility_dataframe = mobility_dataframe.sort_values(by='EV/2023 Rev Mult', ascending=False)
    mobility_dataframe.to_csv('mobility_table_sort_on_ev_ftm.csv', index=False)
    space_dataframe = space_dataframe.sort_values(by='EV/2023 Rev Mult', ascending=False)
    space_dataframe.to_csv('space_table_sort_on_ev_ftm.csv', index=False)

    # Now do some sorting of the PE dataframes
    # First convert columns to a float? May cause issues with non-numeric entries - it does indeed so need to remove all " first 

    #health_pe_dataframe['Forward PE Ratio'] = health_pe_dataframe['Forward PE Ratio'].str.replace('"', '')
    #print(health_pe_dataframe)
    #health_pe_dataframe['Forward PE Ratio'] = health_pe_dataframe['Forward PE Ratio'].str.replace(',', '')

 
    #built_environment_pe_dataframe = built_environment_pe_dataframe.astype({'Forward PE Ratio':'float'})
    #energy_and_resources_pe_dataframe = energy_and_resources_pe_dataframe.astype({'Forward PE Ratio':'float'})
    #health_pe_dataframe = health_pe_dataframe.astype({'Forward PE Ratio':'float'})
    #manufacturing_pe_dataframe = manufacturing_pe_dataframe.astype({'Forward PE Ratio':'float'})
    #mobility_pe_dataframe = mobility_pe_dataframe.astype({'Forward PE Ratio':'float'})
    #space_pe_dataframe = space_pe_dataframe.astype({'Forward PE Ratio':'float'})

    # And now dump them out
    #built_environment_pe_dataframe = built_environment_pe_dataframe.sort_values(by='Forward PE Ratio', key=natsort_keygen)
    built_environment_pe_dataframe.to_csv('built_environment_table_sort_on_forward_pe.csv', index=False)
    #energy_and_resources_pe_dataframe = energy_and_resources_pe_dataframe.sort_values(by='Forward PE Ratio', ascending=False)
    energy_and_resources_pe_dataframe.to_csv('energy_and_resources_table_sort_on_forward_pe.csv', index=False)
    #health_pe_dataframe = health_pe_dataframe.sort_values(by='Forward PE Ratio', ascending=False)
    health_pe_dataframe.to_csv('health_table_sort_on_forward_pe.csv', index=False)
    #manufacturing_pe_dataframe = manufacturing_pe_dataframe.sort_values(by='Forward PE Ratio', ascending=False)
    manufacturing_pe_dataframe.to_csv('manufacturing_table_sort_on_forward_pe.csv', index=False)
    #mobility_pe_dataframe = mobility_pe_dataframe.sort_values(by='Forward PE Ratio', ascending=False)
    mobility_pe_dataframe.to_csv('mobility_table_sort_on_forward_pe.csv', index=False)
    #space_pe_dataframe = space_pe_dataframe.sort_values(by='Forward PE Ratio', ascending=False)
    space_pe_dataframe.to_csv('space_table_sort_on_forward_pe.csv', index=False)
