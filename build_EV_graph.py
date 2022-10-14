#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
#Revision tracker
#20221003 - First attempt to build historical EV graph


import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer
import shutil
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

data_for_graph = pd.read_csv('stock_price_data.csv', index_col=False)

data_for_graph.fillna(method='pad', inplace=True)
data_for_graph.fillna(method = 'bfill', inplace=True)
#data_for_graph = data_for_graph.reset_index()
#print('Data for graph:', data_for_graph)

data_for_graph = data_for_graph.reset_index(drop=True)
data_for_graph = data_for_graph.drop('Unnamed: 0', axis=1)
data_for_graph = data_for_graph.reset_index(drop=True)
print('Data for graph:\n', data_for_graph)
data_for_graph.to_csv('padded_stock_price.csv')
#data_for_graph = data_for_graph.Date.astype('datetime64[ns]')
#data_for_graph.Date.astype('datetime64[ns]')
#data_for_graph = data_for_graph.astype({'Date':'datetime64[ns]', 'Share Count':'int', 'Total Debt':'int'})
data_for_graph = data_for_graph.astype({'Date':'datetime64[ns]'})
print('Date dtype is: ', data_for_graph.Date.dtypes)
#data_for_graph.set_index('Date')
treasury_index = ['^TNX', '^FVX', '^IRX']

print('Data for graph:', data_for_graph)

print('Data types:\n', data_for_graph.dtypes)

treasury_data = yf.download(treasury_index, '2020-6-1')['Close']
treasury_data.reset_index(inplace=True)

treasury_data.fillna(method='pad', inplace=True)
print('Treasury Data:', treasury_data)
print('Data types:\n', treasury_data.dtypes)

merged_data = pd.merge(data_for_graph, treasury_data)
merged_data.to_csv('merged_data.csv')

enterprise_value_index = pd.DataFrame(columns = ['Date', 'EV', 'EV/LTM Rev'])

for index, row in merged_data.iterrows():
  enterprise_value = 0
  ev_over_ltm = 0
  closing_price = float(row['Close'])
  debt = row['Total Debt']
  #print('Debt:', debt)
  debt = debt.replace(',','')
  #print('Debt:', debt)
  debt = float(debt)
  cash = row['Total Cash']
  cash = cash.replace(',','')
  cash = float(cash)
  share_count = row['Share Count']
  share_count = share_count.replace(',', '')
  share_count = float(share_count)
  ltm_revenue = row['LTM Revenue']
  ltm_revenue = ltm_revenue.replace(',', '')
  ltm_revenue = float(ltm_revenue)
  enterprise_value = (closing_price * share_count) + debt - cash
  ev_over_ltm = enterprise_value/ltm_revenue
  new_ev_index_row = {'Date':row['Date'], 'EV':enterprise_value, 'EV/LTM Rev':ev_over_ltm}
  new_ev_index_row_dataframe = pd.DataFrame([new_ev_index_row])
  enterprise_value_index = pd.concat([enterprise_value_index, new_ev_index_row_dataframe], axis=0, ignore_index=True)

print('EV Index: \n', enterprise_value_index)

final_dataframe = pd.merge(merged_data, enterprise_value_index)
print('Final Dataframe\n', final_dataframe)

final_dataframe.to_csv('final_dataframe.csv')

graph_dataframe = final_dataframe.tail(500)
graph_dataframe.reset_index(inplace=True)
graph_dataframe.rename(columns={'EV/LTM Rev':'EV/LTM Revenue', '^TNX':'10-Year Treasury Yield'}, inplace=True)

graph_dataframe.to_csv('graph_dataframe.csv')

# Build large chart - EV/LTM vs 10 year
large_figure = px.line(graph_dataframe, x='Date', y=['EV/LTM Revenue', '10-Year Treasury Yield'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd',
  },
  title='One Week Performance - Deeptech Index With Mega Cap Companies',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

#Figure with secodnary y-axes not possible in plotly.express so need to try another way

large_figure_two = make_subplots(specs=[[{'secondary_y':True}]])
#Now add traces
large_figure_two.add_trace(go.Scatter(
  x=graph_dataframe['Date'], 
  y=graph_dataframe['EV/LTM Revenue'],
  name = 'EV/LTM Revenue',
  line=dict(color='royalblue', width=2)),
  secondary_y =False
  )

large_figure_two.add_trace(go.Scatter(
  #graph_dataframe,
  x=graph_dataframe['Date'],
  y=graph_dataframe['10-Year Treasury Yield'],
  name = '10-Year Treasury Yield',
  line=dict(color='lightblue', width=2)),
  secondary_y=True
  )
  

#large_figure.update_layout(annotations=figure_annotations)
large_figure.update_annotations(clicktoshow='onoff')
large_figure.update_annotations(xanchor='left')
large_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure.update_layout(hovermode='closest')
large_figure.update_layout(yaxis_title='Relative Performance')
large_figure.update_layout(margin=dict(r=170))
large_figure.update_yaxes(fixedrange=True)

graph_config = {'displayModeBar':False}

#large_figure.show(config=graph_config)

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

large_figure_two.show(config=graph_config)
