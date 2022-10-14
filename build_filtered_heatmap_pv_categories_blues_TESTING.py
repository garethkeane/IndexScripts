#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
#Revision tracker
#20220206 Added SATL to New Space list
#20220318 Fork and get last 60 days of 15m data
#20220322 Move back to closing price once daily - change of plan!
#20220326 Update to merge some of the code that is run daily to drive the Google Sheet flow with the graphing flow - want to make sure data matches
#20220404 Update to also spit out some metrics for various indices to include as a table in the website
#20220413 Dump a .csv of the various new and legacy index weights for making sure there are no discrepancies
#20220601 Add Alpha Vantage API as a data source to get market cap data - SATL still being a pain to get through Yahoo Finance
#20220812 Add deeptech index tickers as well
#20220823 Trying out some heat maps for market mapping
#20220921 New PV Categories for heatmap

import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer
import shutil
import plotly.express as px
import requests

from pv_category_ticker_list import newspace_ticker_list
#from master_ticker_list import legacy_ticker_list
from pv_category_ticker_list import manufacturing_deeptech_index_list
from pv_category_ticker_list import mobility_deeptech_index_list
from pv_category_ticker_list import materials_energy_deeptech_index_list
#from master_ticker_list import semiconductor_deeptech_index_list
#from master_ticker_list import semiconductor_equipment_deeptech_index_list
#from master_ticker_list import AR_XR_deeptech_index_list
#from pv_category_ticker_list import mobility_deeptech_index_list
from pv_category_ticker_list import hyperscale_ai_deeptech_index_list
#from master_ticker_list import industry_40_deeptech_index_list
from pv_category_ticker_list import health_deeptech_index_list
from pv_category_ticker_list import built_environment_deeptech_index_list
from pv_category_ticker_list import index_ticker_list


#setup the list of tickers 
ticker_data = {}

#work with all components in the "ticker_list", but also have stocks in stock_ticker_list seperately for this script
#But get their data all at once to make sure that there are no gaps
ticker_list = []
stock_ticker_list = []
ticker_list.extend(newspace_ticker_list)
stock_ticker_list.extend(newspace_ticker_list)
#ticker_list.extend(legacy_ticker_list)
#stock_ticker_list.extend(legacy_ticker_list)
ticker_list.extend(manufacturing_deeptech_index_list)
stock_ticker_list.extend(manufacturing_deeptech_index_list)
#ticker_list.extend(lidar_deeptech_index_list)
#stock_ticker_list.extend(lidar_deeptech_index_list)
#ticker_list.extend(quantum_deeptech_index_list)
#stock_ticker_list.extend(quantum_deeptech_index_list)
ticker_list.extend(mobility_deeptech_index_list)
stock_ticker_list.extend(mobility_deeptech_index_list)
#ticker_list.extend(materials_battery_deeptech_index_list)
#stock_ticker_list.extend(materials_battery_deeptech_index_list)
ticker_list.extend(materials_energy_deeptech_index_list)
stock_ticker_list.extend(materials_energy_deeptech_index_list)
#ticker_list.extend(semiconductor_deeptech_index_list)
#stock_ticker_list.extend(semiconductor_deeptech_index_list)
#ticker_list.extend(semiconductor_equipment_deeptech_index_list)
#stock_ticker_list.extend(semiconductor_equipment_deeptech_index_list)
#ticker_list.extend(AR_XR_deeptech_index_list)
#stock_ticker_list.extend(AR_XR_deeptech_index_list)
#ticker_list.extend(automotive_deeptech_index_list)
#stock_ticker_list.extend(automotive_deeptech_index_list)
ticker_list.extend(hyperscale_ai_deeptech_index_list)
stock_ticker_list.extend(hyperscale_ai_deeptech_index_list)
ticker_list.extend(health_deeptech_index_list)
stock_ticker_list.extend(health_deeptech_index_list)
ticker_list.extend(built_environment_deeptech_index_list)
stock_ticker_list.extend(built_environment_deeptech_index_list)

ticker_list.extend(index_ticker_list)

print(ticker_list)


#First define sector{} dict
stock_sector = {}
stock_color = {}
#Now define sector for various tickers here, and try colors as well
#Colors from https://www.color-hex.com/
for ticker in newspace_ticker_list:
	stock_sector[ticker] = 'Space & Defense'
	stock_color[ticker] ='#0E4C92'
for ticker in manufacturing_deeptech_index_list:
	stock_sector[ticker] = 'Advanced Manufacturing'
	stock_color[ticker] = '#95C8D8'
for ticker in materials_energy_deeptech_index_list:
	stock_sector[ticker] = 'Materials & Energy'
	stock_color[ticker] = '#598BAF'
for ticker in mobility_deeptech_index_list:
        stock_sector[ticker] = 'Mobility & Logistics'
        stock_color[ticker] = '#5097A4'
for ticker in hyperscale_ai_deeptech_index_list:
        stock_sector[ticker] = 'Hyperscale AI'
        stock_color[ticker] = '#73C2FB'
for ticker in health_deeptech_index_list:
        stock_sector[ticker] = 'Health'
        stock_color[ticker] = '#6693F5'
for ticker in built_environment_deeptech_index_list:
        stock_sector[ticker] = 'Built Environment'
        stock_color[ticker] = '#008ECC'
###########
#
# First try and read master market cap list
#
###########

market_cap_dataframe = pd.read_csv('master_marketcaps_list.csv')
print('Market Caps:\n')
print(market_cap_dataframe)

###########
#
# Then try and build some dict structures that contain this dataframe data
#
###########

test_dict = market_cap_dataframe.to_dict('dict')
for key in test_dict:
	print(key)
#print(test_dict)
deeptech_market_cap = {}
for (row_label, row_series) in market_cap_dataframe.iterrows():
	ticker_value = row_series[0]
	market_cap_value = row_series[2]
#	market_cap_value = market_cap_dataframe.loc[row_label, 'Market Cap']
	deeptech_market_cap[ticker_value] = market_cap_value
	

#print(deeptech_market_cap)
#quit()

#Now try to build another CSV file that can be used later for a heatmap

with open('deeptech_heatmap_data.csv', 'w') as output_file:
	output = 'Ticker,Market Cap,Sector,Color\n'
	output_file.write(output)
	for ticker in stock_ticker_list:
		output_market_cap = str(deeptech_market_cap[ticker])
		output_sector = stock_sector[ticker]
		output_color = stock_color[ticker]
		output = ticker + ',' + output_market_cap + ',' + output_sector + ',' + output_color + '\n'
		output_file.write(output)

graph_config = {'displayModeBar':False}

# Try a heatmap
heatmap_dataframe = pd.read_csv('deeptech_heatmap_data.csv')

print('Heatmap dataframe:')
print(heatmap_dataframe)
heatmap_dataframe['All'] = 'All'


heatmap_figure_two = px.treemap(
	heatmap_dataframe,
	path = ['All', 'Sector', 'Ticker'],
	values = 'Market Cap',
	color = 'Color',
	#color = 'Market Cap',
#	color_continuous_scale = 'Inferno'
#	color_continuous_scale = ['Blues', 'Reds', 'Yellows']
	#color_continuous_scale = 'Blugrn'
	)
heatmap_figure_two.update_traces(root_color = 'lightgrey') 
heatmap_figure_two.update_layout(margin = dict(t=50, l=25, r=25, b=25)) 

# Try to do some colors 
sector_color_map = {
        'Space & Defense':'#0E4C92',
        'Advanced Manufacturing':'#95C8D8',
        'Materials & Energy':'#598BAF',
        'Mobility & Logistics':'#5097A4',
        'Hyperscale AI':'#73C2FB',
        'Health':'#6693F5',
        'Built Environment':'#008ECC',
        }

#From https://mdigi.tools/color-shades
company_color_map = {
	'NTR':'#D4E1EA',
	'BAYN.DE':'#B7CDDC',
	'CTVA':'#9BB9CF',
	'DOW':'#7EA5C1',
	'DD':'#6191B3',
	'ASTS':'#ECF4FD',
	'BKSY':'#C5DEF9',
	'BLDE':'#9EC7F6',
	'IONQ':'#77B1F2',
	'PL':'#509BEE',
	'RDW':'#2A84EB',
	'RKLB':'#146FD5',
	'SPIR':'#115BAF',
	'IRDM':'#D8DDE6',
	'HO.PA':'#A4B0C5',
	'SSYS':'#D0E7EE',
	'MKFG':'#B1D7E2',
	'DM':'#92C7D7',
	'VLD':'#73B6CC',
	'SYM':'#DADBE5',
	'OMCL':'#C1C3D3',
	'FANUY':'#A8ABC1',
	'QCOM':'#C7E8F7',
	'NVDA':'#A1D9F2',
	'AMD':'#7CCAED',
	'AMBA':'#57BAE8',
	'AMAT':'#D1E0ED',
	'ASML':'#94B8D5',
	'MTTR':'#CDE3F2',
	'U':'#ABD0E9',
	'RBLX':'#8ABDE0',
	'TSLA':'#D4E7EA',
	'LCID':'#B8D6DC',
	'BYDDY':'#9BC6CE',
	'GOOG':'#C1E4FD',
	'NFLX':'#98D2FC',
	'MSFT':'#6EC0FB',
	'PLTR':'#45AEFA',
	'PTC':'#C3D5FB',
	'SIE.DE':'#9BB9F8',
	'SU.PA':'#739CF6',
	'ROK':'#4B80F3',
	'CRSP':'#BFECFF',
	'BEAM':'#95DFFF',
	'DNA':'#6AD2FF',
	'TWST':'#40C5FF',
	'BNTX':'#15B8FF',
	'MRNA':'#00A3EA'
	}

#Now try to do each sector with this color
heatmap_figure_two.for_each_trace(
  lambda t: t.update(
    marker_colors = [
      sector_color_map[id.split("/")[1]] if len(id.split("/")) == 2 else c
      for c, id in zip(t.marker.colors, t.ids)
    ]
  )
)

#And now do the individual stock colors
heatmap_figure_two.for_each_trace(
  lambda t: t.update(
    marker_colors = [
      company_color_map[id.split("/")[2]] if len(id.split("/")) == 3 else c
      for c, id in zip(t.marker.colors, t.ids)
    ]
  )
)

#May have to map top level color explicityly as well?
top_level_color_map = {
	'All':'lightgrey'
	}

#And now map to the root
heatmap_figure_two.for_each_trace(
  lambda t: t.update(
    marker_colors = [
      top_level_color_map[id.split("/")[0]] if len(id.split("/")) == 1 else c
      for c, id in zip(t.marker.colors, t.ids)
    ]
  )
)

heatmap_figure_two.update_traces(root_color = 'lightgrey')
heatmap_figure_two.write_html('testing_deeptech_heatmap_filtered_colors.html', config = graph_config)
heatmap_figure_two.show()

