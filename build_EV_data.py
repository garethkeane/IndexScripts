#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
#Revision tracker
#20221002 - First attempt to build historical EV using AAPL as an example
#20221003 - Added way to do multiple tickers, calculate EV and dump to an output file


import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer
import shutil
import plotly.express as px
import requests
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

ticker_list = ['AAPL', 'GOOG', 'AMZN'] # Simple ticker list right now
ticker_lookup = {
  'AAPL':'Apple',
  'AMZN':'Amazon',
  'GOOG':'Alphabet',
  }

data = yf.download(ticker_list, '2020-6-1')['Close']

data.fillna(method='pad', inplace=True)
data = data.reset_index()

#Get Treasury Data
treasury_index = ['^TNX', '^FVX', '^IRX', 'IXIC']
treasury_data = yf.download(treasury_index, '2020-6-1')['Close']
treasury_data.reset_index(inplace=True)
treasury_data.fillna(method='pad', inplace=True)
treasury_data.rename(columns={'^TNX':'10-Year Treasury Yield', '^FVX':'5-Year Treasury Yield', '^IRX':'13-Week Treasury Yield'}, inplace=True)
#Now define a treasury dataframe that is 500 entries to match for graphing
graph_treasury_data =  treasury_data.tail(500)
graph_treasury_data.reset_index(inplace=True)


for ticker in ticker_list:
  local_ticker_list = [ticker, '^IXIC']
  data = yf.download(local_ticker_list, '2020-6-1')['Close']
  data.fillna(method='pad', inplace=True)
  data = data.reset_index()
  input_file = 'Data_For_DeepTech_' + ticker + '.csv'
  output_file = 'dumped_data/output_for_' + ticker + '.csv'
  #print('Working on ', ticker, 'with', input_file)
  financials_dataframe = pd.read_csv(input_file)
  financials_dataframe = financials_dataframe.iloc[::-1]
  #print('Financials Dataframe:\n', financials_dataframe)
  #print('Financials datatypes:\n', financials_dataframe.dtypes)
  #print('Prices Dataframe:\n', data)
  #print('Prices datatypes:\n', data.dtypes)
  financials_dataframe = financials_dataframe.astype({'Date':'datetime64[ns]'})
  #print('Financials datatypes:\n', financials_dataframe.dtypes)
  merged_dataframe = pd.merge(financials_dataframe, data, how='right')
  merged_dataframe.fillna(method='pad', inplace=True)
  merged_dataframe.fillna(method='bfill', inplace=True)
  #print('Merged:\n ', merged_dataframe)
  #merged_dataframe.to_csv(output_file)
  # Now do EV calculaitons and append them to this merged_dataframe structure
  enterprise_value_index = pd.DataFrame(columns = ['Date', 'EV', 'EV/LTM Rev'])
  for index, row in merged_dataframe.iterrows():
    enterprise_value = 0
    ev_over_ltm = 0
    closing_price = float(row[ticker])
    debt = row['Total Debt']
    #print('Debt:', debt)
    #debt = debt.replace(',','')
    #print('Debt:', debt)
    debt = float(debt)
    cash = row['Total Cash']
    #cash = cash.replace(',','')
    cash = float(cash)
    share_count = row['Share Count']
    #share_count = share_count.replace(',', '')
    share_count = float(share_count)
    ltm_revenue = row['LTM Revenue']
    #ltm_revenue = ltm_revenue.replace(',', '')
    ltm_revenue = float(ltm_revenue)
    enterprise_value = (closing_price * share_count) + debt - cash
    ev_over_ltm = enterprise_value/ltm_revenue
    new_ev_index_row = {'Date':row['Date'], 'EV':enterprise_value, 'EV/LTM Rev':ev_over_ltm}
    new_ev_index_row_dataframe = pd.DataFrame([new_ev_index_row])
    enterprise_value_index = pd.concat([enterprise_value_index, new_ev_index_row_dataframe], axis=0, ignore_index=True)
  final_dataframe = pd.merge(merged_dataframe, enterprise_value_index)
  print('Final Dataframe\n', final_dataframe)
  
  final_dataframe.to_csv(output_file)

#Now read in each output data file from ./dumped_data/output_for_XXXX.csv
#First define where everything lives
input_files = {
  'AAPL':'output_for_AAPL.csv',
  'AMZN':'output_for_AMZN.csv',
  'GOOG':'output_for_GOOG.csv',
  }

input_dataframe_list = {
  'AAPL':'AAPL_dataframe',
  'AMZN':'AMZN_dataframe',
  'GOOG':'GOOG_dataframe',
  }

#Set up paths
paths, dirs, files = next(os.walk('./dumped_data'))
file_count= len(files)
#Make empty list
dataframes_list = []
#Put each dataframe in the list
for i in range(file_count):
  temp_df = pd.read_csv('./dumped_data/'+files[i])
  dataframes_list.append(temp_df)

#define length of time since 2020-06-01 - same as graphs generated for index performance
date_one = date(2020, 6, 1)
date_two = date.today()
date_delta = date_two - date_one
print('Days:', date_delta)

#Define average EV/LTM dataframe

ev_ltm_average = pd.DataFrame(columns = ['Date', 'EV/LTM Average'])
ev_ltm_average['Date'] = dataframes_list[0]['Date']
ev_ltm_average['EV/LTM Average'] = dataframes_list[0]['EV/LTM Rev']

#Now add all EV/LTMs to this  superset of EV/LTM Revenue columns
#created the macor-index with dataframes_list[0] so not iterate through all other dataframes
#Also want to track how many dataframes to be able to get average
number_of_company_dataframes = 1
for dataset in dataframes_list[1:]:
  #print(dataset)
  ev_ltm_average['EV/LTM Average'] = ev_ltm_average['EV/LTM Average'] + dataset['EV/LTM Rev']
  number_of_company_dataframes = number_of_company_dataframes + 1
print(ev_ltm_average)  
ev_ltm_average['EV/LTM Average'] = ev_ltm_average['EV/LTM Average']/3
print(ev_ltm_average)
graph_ev_average = ev_ltm_average.tail(500)
graph_ev_average.reset_index(inplace=True)

#Now try to graph?

for dataset in dataframes_list: 
  graph_dataframe = dataset.tail(500)
  graph_dataframe.reset_index(inplace=True)
  ticker_name = graph_dataframe.columns[9]
  mapped_ticker_name = ticker_lookup[ticker_name]
  #quick hack to show demo graph - fix soon
  if (ticker_name == 'AMZN'):
    print('Got to here!')
    graph_title = 'Built Enviroment Sector - Average EV/LTM vs Deeptech Index Average EV/LTM'
  else:
    #graph_title = mapped_ticker_name + ' EV/LTM Revenue vs Sector Average EV/LTM Revenue'
    graph_title = '<Built Environment component name>  EV/LTM Revenue vs Built Environment Sector Average EV/LTM Revenue'

  print('Graph dataframe:\n', graph_dataframe)

  large_figure_two = make_subplots(specs=[[{'secondary_y':True}]])
  #Now add traces
  large_figure_two.add_trace(go.Scatter(
    x=graph_dataframe['Date'], 
    y=graph_dataframe['EV/LTM Rev'],
    name = ticker_name + ' EV/LTM Revenue',
    line=dict(color='royalblue', width=2)),
    secondary_y =False
    )

  large_figure_two.add_trace(go.Scatter(
    x=graph_ev_average['Date'],
    y=graph_ev_average['EV/LTM Average'],
    name = 'EV/LTM Average for Subsector',
    line=dict(color='lightgrey', width=2)),
    secondary_y =False
    )

  large_figure_two.add_trace(go.Scatter(
    #graph_dataframe,
    x=graph_treasury_data['Date'],
    y=graph_treasury_data['10-Year Treasury Yield'],
    name = '10-Year Treasury Yield',
    line=dict(color='lightblue', width=2)),
    secondary_y=True
    )

  graph_config = {'displayModeBar':False}

  #large_figure.update_layout(annotations=figure_annotations)
  large_figure_two.update_annotations(clicktoshow='onoff')
  large_figure_two.update_annotations(xanchor='left')
  large_figure_two.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
  large_figure_two.update_layout(hovermode='closest')
  large_figure_two.update_yaxes(title_text='EV/LTM Revenue', secondary_y=False)
  large_figure_two.update_yaxes(title_text='10-Year Treasury', secondary_y=True)
  large_figure_two.update_layout(margin=dict(r=170))
  large_figure_two.update_yaxes(fixedrange=True)
  large_figure_two.update_layout(plot_bgcolor = '#FFFFFF')
  large_figure_two.update_layout(title_text=graph_title)
  #Try and put legend on top
  large_figure_two.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

  large_figure_two.show(config=graph_config)

  output_file = ticker_name + '_output_graph.html'
  large_figure_two.write_html(output_file, config=graph_config)
