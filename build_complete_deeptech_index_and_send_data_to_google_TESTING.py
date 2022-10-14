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
#20220826 Change to use market caps from standalone market cap/FX script
#20220901 Change up reading market caps to also handle company parameters like EV/Revenue, etc
#20220920 Now read all the variables from a master file that keeps everything - master_ticker_list
#20220924 Get historical annual revenues from https://finance.yahoo.com using yahoo_fin 
#20221005 Maybe remove the Hyperscale AI sector - had to update for new format of master_marketcaps_list.csv
#20221006 Update graphs to have % on y-axis
#20221007 Now get stock data from 20190101
#20221008 Added 3 year graph generation, defined as 3 * 252 = 756 days (252 in 1 year view) 

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

#setup the list of tickers 

#from master_ticker_list import newspace_ticker_list
#from master_ticker_list import legacy_ticker_list
#from master_ticker_list import threedprinting_deeptech_index_list
#from master_ticker_list import robotics_deeptech_index_list
#from master_ticker_list import materials_chemical_deeptech_index_list
#from master_ticker_list import semiconductor_deeptech_index_list
#from master_ticker_list import semiconductor_equipment_deeptech_index_list
#from master_ticker_list import AR_XR_deeptech_index_list
#from master_ticker_list import automotive_deeptech_index_list
#from master_ticker_list import hyperscale_ai_deeptech_index_list
#from master_ticker_list import industry_40_deeptech_index_list
#from master_ticker_list import biotech_deeptech_index_list
#from master_ticker_list import index_ticker_list

from pv_category_ticker_list import index_ticker_list
from pv_category_ticker_list import newspace_ticker_list
from pv_category_ticker_list import manufacturing_deeptech_index_list
from pv_category_ticker_list import materials_energy_deeptech_index_list
from pv_category_ticker_list import built_environment_deeptech_index_list
from pv_category_ticker_list import health_deeptech_index_list
#from pv_category_ticker_list import hyperscale_ai_deeptech_index_list
from pv_category_ticker_list import mobility_deeptech_index_list

# list stocks woth very large market caps that might dominate index - generate views both with and without these
# decided to remove AAPL GOOG MSFT AMZN anyway, and incldue TSLA
#mega_cap_list = ['AAPL', 'GOOG', 'MSFT', 'TSLA'] 
mega_cap_list = ['APPL']

#Some variables for testing - make all the writes to Google Sheets dependent on share_data_to_google
share_data_to_google = 'False'
#share_data_to_google = 'True'

#For testing - small size lists 
#newspace_ticker_list =['ACHR', 'SATL']
#legacy_ticker_list = ['AJRD', 'AIR.PA', 'BA.L']
ticker_data = {}

#work with all components in the "ticker_list", but also have stocks in stock_ticker_list seperately for this script
#But get their data all at once to make sure that there are no gaps
ticker_list = []
stock_ticker_list = []
#Add Newspace
ticker_list.extend(newspace_ticker_list)
stock_ticker_list.extend(newspace_ticker_list)
#Add Manufacturing
ticker_list.extend(manufacturing_deeptech_index_list)
stock_ticker_list.extend(manufacturing_deeptech_index_list)
#Add Energy & Resources
ticker_list.extend(materials_energy_deeptech_index_list)
stock_ticker_list.extend(materials_energy_deeptech_index_list)
#Add Built Environment
ticker_list.extend(built_environment_deeptech_index_list)
stock_ticker_list.extend(built_environment_deeptech_index_list)
#Add Health
ticker_list.extend(health_deeptech_index_list)
stock_ticker_list.extend(health_deeptech_index_list)
#Add Hyperscale AI - removed 20221005
#ticker_list.extend(hyperscale_ai_deeptech_index_list)
#stock_ticker_list.extend(hyperscale_ai_deeptech_index_list)
#Add Mobility & Logistics
ticker_list.extend(mobility_deeptech_index_list)
stock_ticker_list.extend(mobility_deeptech_index_list)
#Add the index tickers for NASDAQ and S&P500
ticker_list.extend(index_ticker_list)
print(ticker_list)

#Now define new list without mega cap stocks
stock_ticker_list_no_mega_caps = []
for ticker in stock_ticker_list:
  if ticker not in mega_cap_list:
    stock_ticker_list_no_mega_caps.append(ticker)


#First define stock_sector{} and stock_color{} dict

stock_sector = {}
stock_color = {}
#Now define sector for various tickers here, and try colors as well
#Colors from https://www.color-hex.com/
for ticker in newspace_ticker_list:
        stock_sector[ticker] = 'Space Aerospace & Defense'
        stock_color[ticker] ='#E0B0FF'
for ticker in manufacturing_deeptech_index_list:
        stock_sector[ticker] = 'Advanced Manufacturing'
        stock_color[ticker] = '#84ae57'
for ticker in materials_energy_deeptech_index_list:
        stock_sector[ticker] = 'Energy & Resources'
        stock_color[ticker] = '#FF0000'
for ticker in built_environment_deeptech_index_list:
        stock_sector[ticker] = 'Built Environment'
        stock_color[ticker] = '#FF4207'
for ticker in health_deeptech_index_list:
        stock_sector[ticker] = 'Health'
        stock_color[ticker] = '#3954C8'
#for ticker in hyperscale_ai_deeptech_index_list:
#        stock_sector[ticker] = 'Hyperscale AI'
#        stock_color[ticker] = '#067EAA'
for ticker in mobility_deeptech_index_list:
        stock_sector[ticker] = 'Mobility & Logistics'
        stock_color[ticker] = '#66B266'

#data = yf.download(ticker_list, '2021-6-1', '2022-3-24')['Close']
#data = yf.download(ticker_list, '2021-6-1')['Close']
data = yf.download(ticker_list, '2019-1-1')['Close']

#First pad the closing price dataframe so no missing data (eg holidays in the US and not in Europe, etc)
#Had to add 'inplace = True' to get it to replace into the dataframe

data.fillna(method='pad', inplace=True)

#now look again
#print(july_five)

#data[::-1]
reversed_data = data.iloc[::-1]
#reversed_data = data
reversed_data.to_csv('deeptech_test_not_sorted.csv')
reversed_data = reversed_data[ticker_list]
reversed_data.to_csv('deeptech_test.csv')

##########
#
#Add some stuff from original script to make sure Google Sheets data and the graphs generated here are synced
#
##########

#Now try and write to Google Sheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(credentials)

spreadsheet = client.open('Deeptech_Index_Historical_Data__AutoUpdated')

with open('deeptech_test.csv', 'r') as file_obj:
    content = file_obj.read()
    client.import_csv(spreadsheet.id, data=content)

#Add some code to get historical revenues for all the tickers
#Need to figure out if use this here or not - comment out for now

#historical_revenues = {}
#
#for ticker in stock_ticker_list:
#  income_statement = yfin.get_income_statement(ticker)
#  revenues = income_statement.loc['totalRevenue',:].values.tolist()
#  #print(income_statement)
#  #print(ticker, revenues) 
#  historical_revenues[ticker] = revenues

#Change here to get market caps from golden reference - save execution time, and align everything in terms of index weights

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
# Now try and read FX data 
#
###########

fx_dataframe = pd.read_csv('master_fx_data.csv')
fx_ticker_list = ['EURUSD=X', 'GBPUSD=X']

# Now define golden_fx_data dict

golden_fx_data = {}

# Now use data from master_fx_data.csv to populate FX data dict

for (row_label, row_series) in fx_dataframe.iterrows():
	rate_name = row_series[0]
	rate_value = row_series[1]
	#rate_value = float(rate_value) # turn into float for math!a Turns out can not do that here due to pesky timestamp
	golden_fx_data[rate_name] = rate_value	
	print('Rate for ', rate_name, ' is ', rate_value)

###########
#
# Then try and build some dict structures that combine all of this dataframe data
#
###########

#First define a number of data structures:
# - golden_market_cap data structure as a python dict so we can track/use by ticker
# - golden_company_name data structure as a python dict so we can track/use by ticker
# - golden_company_currency data structure as a python dict again so can track/use by ticker
# - deeptech_market_cap as a python dict for deeptech caps for the heatmap
golden_market_cap = {}
golden_company_name = {}
golden_company_currency = {}
golden_company_ev_to_rev = {}
golden_company_trailing_eps = {}
golden_company_forward_eps= {}
golden_company_revenue_growth = {}
golden_company_gross_margin = {}
golden_company_average_volume = {}
golden_company_float = {}
golden_company_total_shares = {}
deeptech_market_cap = {}
# Now use data from master_marketcaps_list.csv to populate these dicts
for (row_label, row_series) in market_cap_dataframe.iterrows():
        ticker_value = row_series[0]
        market_cap_value = row_series[2]
        ticker_currency = row_series[4]
        company_name = row_series[1]
        company_ev_to_rev = row_series[4]
        company_trailing_eps = row_series[7]
        company_forward_eps = row_series[8]
        company_revenue_growth = row_series[9]
        company_gross_margin = row_series[10]
        company_average_volume = row_series[11]
        company_float = row_series[12]
        company_total_shares = row_series[13]
        golden_company_currency[ticker_value] = ticker_currency
        deeptech_market_cap[ticker_value] = market_cap_value
        golden_market_cap[ticker_value] = market_cap_value
        golden_company_name[ticker_value] = company_name
        golden_company_ev_to_rev[ticker_value] = company_ev_to_rev
        golden_company_trailing_eps[ticker_value] = company_trailing_eps
        golden_company_forward_eps[ticker_value] = company_forward_eps
        golden_company_revenue_growth[ticker_value] = company_revenue_growth
        golden_company_gross_margin[ticker_value] = company_gross_margin
        golden_company_average_volume[ticker_value] = company_average_volume
        golden_company_float[ticker_value] = company_float
        golden_company_total_shares[ticker_value] = company_total_shares
	# Use FX rate here to scale market caps all to USD
        if (golden_company_currency[ticker_value] == 'EUR'):
          print('Updating market cap for ', ticker_value, ' was ', golden_market_cap[ticker_value], '/', deeptech_market_cap[ticker_value])
          exchange_rate = float(golden_fx_data['EURUSD=X'])
          golden_market_cap[ticker_value] = golden_market_cap[ticker_value] * exchange_rate
          deeptech_market_cap[ticker_value] = deeptech_market_cap[ticker_value] * exchange_rate
          print('Market cap for ', ticker_value, ' is now ', golden_market_cap[ticker_value], '/', deeptech_market_cap[ticker_value])
        if (golden_company_currency[ticker_value] == 'GBp'):
          print('Updating market cap for ', ticker_value, ' was ', golden_market_cap[ticker_value], '/', deeptech_market_cap[ticker_value])
          exchange_rate = float(golden_fx_data['GBPUSD=X'])
          golden_market_cap[ticker_value] = golden_market_cap[ticker_value] * exchange_rate
          deeptech_market_cap[ticker_value] = deeptech_market_cap[ticker_value] * exchange_rate
          print('Market cap for ', ticker_value, ' is now ', golden_market_cap[ticker_value], '/', deeptech_market_cap[ticker_value])
        if (golden_company_currency[ticker_value] != 'USD'):
          print('Currency is ', golden_company_currency[ticker_value])
#quit()

# Now keep deeptech_marketcaps.csv file - just write out from these dicts

with open('deeptech_marketcaps.csv', 'w') as output_file:
  output = 'Ticker, Company Name, Market Cap, Subsector, Currency, EV/Revenue, Trailing EPS, Forward EPS, Revenue Growth, Gross Margin, Average Volume, Float, Total Shares\n'
  output_file.write(output)
  for ticker in stock_ticker_list:
    print ('Working on', ticker)
    output_name = golden_company_name[ticker]
    output_market_cap = str(golden_market_cap[ticker])
    output_currency = golden_company_currency[ticker] 
    output_sector = stock_sector[ticker]
    output_ev_to_rev = str(golden_company_ev_to_rev[ticker])
    output_trailing_eps = str(golden_company_trailing_eps[ticker])
    output_forward_eps = str(golden_company_forward_eps[ticker])
    output_revenue_growth = str(golden_company_revenue_growth[ticker])
    output_gross_margin = str(golden_company_gross_margin[ticker])
    output_average_volume = str(golden_company_average_volume[ticker])
    output_float = str(golden_company_float[ticker])
    output_total_shares = str(golden_company_total_shares[ticker])
    output = ticker + ',' + output_name + ',' + output_market_cap + ',' + output_sector + ',' + output_currency + ',' + output_ev_to_rev + ',' + output_trailing_eps + ',' + output_forward_eps + ',' + output_revenue_growth + ',' + output_gross_margin + ',' + output_average_volume + ',' + output_float + ',' + output_total_shares + '\n'
    output_file.write(output)

#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open ('deeptech_marketcaps.csv', 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(time_data)
        f_object.close

with open ('deeptech_test.csv', 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(time_data)
        f_object.close

#Try something a little different - update a specific sheet
spreadsheetId = 'Deeptech_Index_Market_Cap_Data__AutoUpdated'
#spreadsheetId = 'https://docs.google.com/spreadsheets/d/1NjRwaeHfOVO0aXcLv0h4y2WYeCZx0KXfkyhFVDIdWlI'
sheetName = 'Test_This_Sheet'
csvFile = 'deeptech_marketcaps.csv'

#sheet = client.open_by_key(spreadsheetId)
sheet = client.open(spreadsheetId)
sheet.values_update(
        sheetName,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': list(csv.reader(open(csvFile)))}
)

#Now Update Deeptech Master Spreadsheet Tabs
spreadsheetId = 'Deeptech_Index_Master_Spreadsheet_20220812'
#First Market Cap Data
sheetName = 'Market_Cap_Data'
csvFile = 'deeptech_marketcaps.csv'

sheet = client.open(spreadsheetId)
sheet.values_update (
        sheetName,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': list(csv.reader(open(csvFile)))}
)

# Now Historical Data
sheetName = 'Historical_Data'
csvFile = 'deeptech_test.csv'

sheet.values_update (
        sheetName,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': list(csv.reader(open(csvFile)))}
)

###########
#
# Now back to graphing script
#
##########

#Now try and get market caps for all deeptech companies
#Use a flag to spot bad market cap data
# Check if this is really needed - looks like script is just wrtng over deeptech_marketcaps.csv
bad_market_cap_data_flag = 'False'

with open('deeptech_marketcaps.csv', 'w') as output_file:
  output = 'Ticker, Company Name, Market Cap, Currency\n'
  output_file.write(output)
  for ticker in stock_ticker_list:
    print ('Working on', ticker)
    output_market_cap = str(golden_market_cap[ticker])
    output_name = golden_company_name[ticker]
    output_currency = golden_company_currency[ticker]
    if (output_market_cap == 'None'):
      print('In bad market cap loop for', output_name)
      bad_market_cap_data_flag = 'True'
    output = ticker + ',' + output_name + ',' + output_market_cap + ',' + output_currency + '\n'
    output_file.write(output)

#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open ('deeptech_marketcaps.csv', 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(time_data)
        f_object.close

if (bad_market_cap_data_flag == 'False'):
	print('Copying deeptech market cap data')
	shutil.copy('deeptech_marketcaps.csv', 'last_golden_deeptech_market_caps.csv')

#Now time to make sure we have good data for all deeptech market caps
if (bad_market_cap_data_flag == 'True'):
	marketcap_df = pd.read_csv('last_golden_deeptech_market_caps.csv')
	#print(marketcap_df)
	for ticker in ticker_list:
		if(deeptech_market_cap[ticker] == 'None'):
			print('Replacing market cap for', ticker)
			print('Was:', deeptech_market_cap[ticker])
			#marketcap_df.set_index('Ticker', inplace=True)
			deeptech_market_cap[ticker] = marketcap_df.loc[marketcap_df['Ticker']==ticker][' Market Cap'].values[0]
			print('Now:', deeptech_market_cap[ticker])


#Now get total market cap of all companies and build weights
total_deeptech_market_cap = 0

for ticker in stock_ticker_list:
#	deeptech_market_cap[ticker] = int(deeptech_market_cap[ticker])
	total_deeptech_market_cap = total_deeptech_market_cap + deeptech_market_cap[ticker]

print('Total Deeptech Market Cap:', total_deeptech_market_cap)

#Now get weights - but only use entities in stock_ticker_list as don't want NASDAQ/S&P
deeptech_index_weights = {}
weight_check = 0

for ticker in stock_ticker_list:
	deeptech_index_weights[ticker] = deeptech_market_cap[ticker]/total_deeptech_market_cap
	print(ticker, ':', deeptech_index_weights[ticker])
	weight_check = weight_check + deeptech_index_weights[ticker]

print('Weight check:', weight_check)

#Add a variable here to control for whether the weights get capped at a certain value
#Variable is cap_max_index_weights

#Add some code to try to make sure no weight > 10% in overall index
#Doesn't solve for subsectors like Hyperscale AI, or really anything with < 9 components as something will always be > 10%
#cap_max_index_weight = 'True'
cap_max_index_weight = 'False'
cap_max_index_weight_value = 0.1
total_weight_to_redistribute = 0
total_excess_weight = 0
weight_capped = {} # use to track tickers that have been capped
old_weights = {}
company_count = 0
original_weight_of_capped_companies = 0

for ticker in stock_ticker_list:
	company_count = company_count + 1
	weight_capped[ticker] = 'False' # Initialize everything to false

#Begin section that is controlled by cap_max_index_weight here
if (cap_max_index_weight == 'True'):
	for ticker in stock_ticker_list:
		old_weights[ticker] = deeptech_index_weights[ticker]
		if (deeptech_index_weights[ticker] > cap_max_index_weight_value):
			original_weight_of_capped_companies = original_weight_of_capped_companies + deeptech_index_weights[ticker]
			print('In excess weight loop for ', ticker)
			print('Original weight:', deeptech_index_weights[ticker])
			excess_weight_this_ticker = deeptech_index_weights[ticker] - cap_max_index_weight_value
			total_excess_weight = total_excess_weight + excess_weight_this_ticker
			weight_capped[ticker] = 'True' # track the tickers that have been capped
			deeptech_index_weights[ticker] = cap_max_index_weight_value
	print('Excess weight to redistribute is: ', total_excess_weight)
	
	#Now check everything that was not capped and build pro-rata for excess weight distribution
	
	total_non_capped_market_cap =0
	non_capped_company_count = 0
	for ticker in stock_ticker_list:
		if (weight_capped[ticker] == 'False'):
			non_capped_company_count = non_capped_company_count + 1
			total_non_capped_market_cap = total_non_capped_market_cap + deeptech_market_cap[ticker]
	
	# Quick check
	#non_capped_market_cap_ratio = 1 - (total_non_capped_market_cap/total_deeptech_market_cap)	
	non_capped_market_cap_ratio = (total_non_capped_market_cap/total_deeptech_market_cap)	
	summed_capped_and_non_capped = original_weight_of_capped_companies + non_capped_market_cap_ratio
	print('Quick check: ', original_weight_of_capped_companies, non_capped_market_cap_ratio, summed_capped_and_non_capped)
	print('Total companies:', company_count)
	print('Non capped company count:', non_capped_company_count)

	#Now figure out weight of the non-capped tickers with this new sub-total 
	deeptech_non_capped_index_weights = {}
	
	weight_check = 0	
	for ticker in stock_ticker_list:
		if (weight_capped[ticker] == 'False'):
			deeptech_non_capped_index_weights[ticker] = deeptech_market_cap[ticker]/total_non_capped_market_cap
			print(ticker, ':', deeptech_non_capped_index_weights[ticker])
			weight_check = weight_check + deeptech_non_capped_index_weights[ticker]
	print('Weight check after new weight calculation:', weight_check)			

	#Now distribute excess weights to these tickers proportionally
	total_of_excess_weight_being_redistributed = 0	
	for ticker in stock_ticker_list:
		if (weight_capped[ticker] == 'False'):
			deeptech_index_weights[ticker] = deeptech_index_weights[ticker] + (deeptech_non_capped_index_weights[ticker] * total_excess_weight)
			total_of_excess_weight_being_redistributed = total_of_excess_weight_being_redistributed + (deeptech_non_capped_index_weights[ticker] * total_excess_weight)
			#deeptech_index_weights[ticker] = deeptech_index_weights[ticker] + (deeptech_index_weights[ticker] * total_excess_weight)

	# Now final check to make sure weights add up to 1.0
	weight_check = 0
	old_weight_check = 0
	total_of_weight_buckets = 0.3 + non_capped_market_cap_ratio + total_excess_weight # hacky way to add the three components of total weight
	print('Added weight buckets: ', total_of_weight_buckets)
	print('Total weight that was redistributed: ', total_of_excess_weight_being_redistributed, total_excess_weight)
	print('Ticker : Old Weight: New Weight\n')
	for ticker in stock_ticker_list:
		print(ticker, ':', old_weights[ticker], ':', deeptech_index_weights[ticker])
		weight_check = weight_check + deeptech_index_weights[ticker]
		old_weight_check = old_weight_check + old_weights[ticker]
	print('Weight check after redistribution : ', old_weight_check, weight_check)

#And end section controlled by cap_max_index_weight here

#Now get weights for the deeptech index without the mega cap stocks defined in mega_cap_list
#First get total market cap of all companies (without mega caps) and build weights
total_deeptech_market_cap_no_mega_caps = 0

for ticker in stock_ticker_list_no_mega_caps:
#       deeptech_market_cap[ticker] = int(deeptech_market_cap[ticker])
        total_deeptech_market_cap_no_mega_caps = total_deeptech_market_cap_no_mega_caps + deeptech_market_cap[ticker]

print('Total Deeptech Market Cap:', total_deeptech_market_cap)

#Now get weights - but only use entities in stock_ticker_list as don't want NASDAQ/S&P
deeptech_index_weights_no_mega_caps = {}
weight_check_no_mega_caps = 0

for ticker in stock_ticker_list_no_mega_caps:
        deeptech_index_weights_no_mega_caps[ticker] = deeptech_market_cap[ticker]/total_deeptech_market_cap_no_mega_caps
        print(ticker, ':', deeptech_index_weights_no_mega_caps[ticker])
        weight_check_no_mega_caps = weight_check_no_mega_caps + deeptech_index_weights_no_mega_caps[ticker]

print('Weight check (no mega caps):', weight_check_no_mega_caps)

# Now try and get weights for a sub index - start with Newspace
total_newspace_market_cap = 0

for ticker in newspace_ticker_list:
	total_newspace_market_cap = total_newspace_market_cap + deeptech_market_cap[ticker]

newspace_index_weights = {} 
newspace_weight_check = 0

for ticker in newspace_ticker_list:
	newspace_index_weights[ticker] = deeptech_market_cap[ticker]/total_newspace_market_cap
	print(ticker,':', newspace_index_weights[ticker])
	newspace_weight_check = newspace_weight_check + newspace_index_weights[ticker]

print('Newspace Weight Check:', newspace_weight_check)

# Next Manufacturing

total_manufacturing_market_cap = 0

for ticker in manufacturing_deeptech_index_list:
	total_manufacturing_market_cap = total_manufacturing_market_cap + deeptech_market_cap[ticker]

manufacturing_index_weights = {} 
manufacturing_weight_check = 0

for ticker in manufacturing_deeptech_index_list:
        manufacturing_index_weights[ticker] = deeptech_market_cap[ticker]/total_manufacturing_market_cap
        print(ticker,':', manufacturing_index_weights[ticker])
        manufacturing_weight_check = manufacturing_weight_check + manufacturing_index_weights[ticker]

print('Manufacturing Weight Check:', manufacturing_weight_check)

# Next Energy & Resources
total_materials_energy_market_cap = 0

for ticker in materials_energy_deeptech_index_list:
	total_materials_energy_market_cap = total_materials_energy_market_cap + deeptech_market_cap[ticker]

materials_energy_index_weight = {}
materials_energy_index_weight_check = 0

for ticker in materials_energy_deeptech_index_list:
	materials_energy_index_weight[ticker] = deeptech_market_cap[ticker]/total_materials_energy_market_cap
	print(ticker,':', materials_energy_index_weight[ticker])
	materials_energy_index_weight_check = materials_energy_index_weight_check + materials_energy_index_weight[ticker]

print('Energy & Resources Weight Check:', materials_energy_index_weight_check)

# Next Built Environment
total_built_environment_market_cap = 0

for ticker in built_environment_deeptech_index_list:
        total_built_environment_market_cap = total_built_environment_market_cap + deeptech_market_cap[ticker]

built_environment_index_weight = {}
built_environment_index_weight_check = 0

for ticker in built_environment_deeptech_index_list:
        built_environment_index_weight[ticker] = deeptech_market_cap[ticker]/total_built_environment_market_cap
        print(ticker,':', built_environment_index_weight[ticker])
        built_environment_index_weight_check = built_environment_index_weight_check + built_environment_index_weight[ticker]

print('Built Environment Weight Check:', built_environment_index_weight_check)

# Next Health
total_health_market_cap = 0

for ticker in health_deeptech_index_list:
        total_health_market_cap = total_health_market_cap + deeptech_market_cap[ticker]

health_index_weight = {}
health_index_weight_check = 0

for ticker in health_deeptech_index_list:
        health_index_weight[ticker] = deeptech_market_cap[ticker]/total_health_market_cap
        print(ticker,':', health_index_weight[ticker])
        health_index_weight_check = health_index_weight_check + health_index_weight[ticker]

print('Health Weight Check:', health_index_weight_check)

# Next Hyperscale AI
#total_hyperscale_ai_market_cap = 0
#
#for ticker in hyperscale_ai_deeptech_index_list:
#        total_hyperscale_ai_market_cap = total_hyperscale_ai_market_cap + deeptech_market_cap[ticker]
#
#hyperscale_ai_index_weight = {}
#hyperscale_ai_index_weight_check = 0
#
#for ticker in hyperscale_ai_deeptech_index_list:
#        hyperscale_ai_index_weight[ticker] = deeptech_market_cap[ticker]/total_hyperscale_ai_market_cap
#        print(ticker,':', hyperscale_ai_index_weight[ticker])
#        hyperscale_ai_index_weight_check = hyperscale_ai_index_weight_check + hyperscale_ai_index_weight[ticker]
#
#print('Hyperscale AI Weight Check:', hyperscale_ai_index_weight_check)

# Next Mobility
total_mobility_market_cap = 0

for ticker in mobility_deeptech_index_list:
        total_mobility_market_cap = total_mobility_market_cap + deeptech_market_cap[ticker]

mobility_index_weight = {}
mobility_index_weight_check = 0

for ticker in mobility_deeptech_index_list:
        mobility_index_weight[ticker] = deeptech_market_cap[ticker]/total_mobility_market_cap
        print(ticker,':', mobility_index_weight[ticker])
        mobility_index_weight_check = mobility_index_weight_check + mobility_index_weight[ticker]

print('Mobility Weight Check:', mobility_index_weight_check)

#Try to dump these weights to a file
with open('deeptech_index_weight_data.csv', 'w') as output_file:
	output = 'Ticker, Weight\n'
	output_file.write(output)
	for ticker in stock_ticker_list:
		weight_text = str(deeptech_index_weights[ticker])
		output = ticker + ',' + weight_text + '\n'
		output_file.write(output) 

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

#Now time to build the deeptech index

deeptech_index = pd.DataFrame(columns = ['Date', 'Value'])
deeptech_index_no_mega_caps = pd.DataFrame(columns = ['Date', 'Value'])

#First do a hacky copy of the original data dataframe as it seems to be causing problems
newspace_data = data
manufacturing_data = data
materials_energy_data = data
built_environment_data = data
health_data = data
#hyperscale_ai_data = data
mobility_data = data

#Now try to add a calculated value for the deeptech index
#Note that old dataframe.append approach has been deprecated so change to dataframe.concat 20220927

data = data.reset_index()
for index, row in data.iterrows():
	deeptech_index_value = 0
	deeptech_index_value_no_mega_caps = 0
	for ticker in stock_ticker_list:
		if (type(row[ticker]) == int) or (type(row[ticker]) == float):
			#print ('here - 3!')
			current_row = row[ticker]
		else:
			print('Not a number')
			print('Date: ', row['Date'], ticker)
		contribution = row[ticker] * deeptech_index_weights[ticker]
		#print('Ticker:', ticker, 'Contribution:', contribution)
		#print(pd.isna(contribution))
		#if (pd.isna(contribution) == 'True'):
		if pd.isna(contribution):
			#print('into this loop')
			contribution = 0
		#print('Ticker:', ticker, 'Contribution:', contribution)
		deeptech_index_value = deeptech_index_value + contribution
	for ticker in stock_ticker_list_no_mega_caps:
		if (type(row[ticker]) == int) or (type(row[ticker]) == float):
			current_row = row[ticker]
		else: 
			print('Not a number')
			print('Date: ', row['Date'], ticker)
		contribution = row[ticker] * deeptech_index_weights_no_mega_caps[ticker]
		if pd.isna(contribution):
			contribution = 0
		deeptech_index_value_no_mega_caps = deeptech_index_value_no_mega_caps + contribution
	print(row['Date'], ':', deeptech_index_value)
	new_deeptech_row = {'Date':row['Date'], 'Value':deeptech_index_value}
	new_deeptech_row_no_mega_caps = {'Date':row['Date'], 'Value':deeptech_index_value_no_mega_caps}
	new_deeptech_dataframe = pd.DataFrame([new_deeptech_row])
	new_deeptech_no_mega_caps_dataframe = pd.DataFrame([new_deeptech_row_no_mega_caps])
	deeptech_index = pd.concat([deeptech_index, new_deeptech_dataframe], axis=0, ignore_index=True)
	deeptech_index_no_mega_caps = pd.concat([deeptech_index_no_mega_caps, new_deeptech_no_mega_caps_dataframe], axis=0, ignore_index=True)
	#deeptech_index = deeptech_index.append({'Date':row['Date'], 'Value': deeptech_index_value}, ignore_index=True)
	#deeptech_index_no_mega_caps = deeptech_index_no_mega_caps.append({'Date':row['Date'], 'Value': deeptech_index_value_no_mega_caps}, ignore_index=True)

#Now do all the subsectors - Newspace, Manufacturing, Energy & Resources, Built Environment, Health, Hyperscale AI, and Mobility & Logistics
#Start wth newspace (actually Space Aerospace & Defense once it gets reported out)
newspace_index = pd.DataFrame(columns = ['Date', 'Value'])

newspace_data = newspace_data.reset_index()
for index, row in newspace_data.iterrows():
	newspace_index_value = 0
	for ticker in newspace_ticker_list:
		if (type(row[ticker]) == int) or (type(row[ticker]) == float):
			current_row = row[ticker]
		else:
			print('Not a number')
			print('Date: ', row['Date'], ticker)
		contribution = row[ticker] * newspace_index_weights[ticker]
		if pd.isna(contribution):
			contribution = 0
		newspace_index_value = newspace_index_value + contribution
	print('Space/Aerospace data:', row['Date'], ':', newspace_index_value)
	new_row = {'Date':row['Date'], 'Value':newspace_index_value}
	new_dataframe = pd.DataFrame([new_row])
	newspace_index = pd.concat([newspace_index, new_dataframe], axis=0, ignore_index=True)
        #newspace_index = newspace_index.append({'Date':row['Date'], 'Value':newspace_index_value}, ignore_index=True)

#Next Manufacturing
manufacturing_index = pd.DataFrame(columns = ['Date', 'Value'])

manufacturing_data = manufacturing_data.reset_index()
for index, row in manufacturing_data.iterrows():
        manufacturing_index_value = 0
        for ticker in manufacturing_deeptech_index_list:
                if (type(row[ticker]) == int) or (type(row[ticker]) == float):
                        current_row = row[ticker]
                else:
                        print('Not a number')
                        print('Date: ', row['Date'], ticker)
                contribution = row[ticker] * manufacturing_index_weights[ticker]
                if pd.isna(contribution):
                  contribution = 0
                manufacturing_index_value = manufacturing_index_value + contribution
        print('Manufacturing data:', row['Date'], ':', manufacturing_index_value)
        new_row = {'Date':row['Date'], 'Value':manufacturing_index_value}
        new_dataframe = pd.DataFrame([new_row])
        manufacturing_index = pd.concat([manufacturing_index, new_dataframe], axis=0, ignore_index=True)
        #manufacturing_index = manufacturing_index.append({'Date':row['Date'], 'Value':manufacturing_index_value}, ignore_index=True)

#Next Energy & Resources
materials_energy_index = pd.DataFrame(columns = ['Date', 'Value'])

materials_energy_data = materials_energy_data.reset_index()
for index, row in materials_energy_data.iterrows():
	materials_energy_index_value = 0
	for ticker in materials_energy_deeptech_index_list:
		if (type(row[ticker]) == int) or (type(row[ticker]) == float):
			current_row = row[ticker]
		else:
			print('Not a number')
			print('Date: ', row['Date'], ticker)
		contribution = row[ticker] * materials_energy_index_weight[ticker]
		if pd.isna(contribution):
			contribution = 0
		materials_energy_index_value = materials_energy_index_value + contribution
	print('Energy & Resources data:', row['Date'], ':', materials_energy_index_value)
	new_row = {'Date':row['Date'], 'Value':materials_energy_index_value}
	new_dataframe = pd.DataFrame([new_row])
	materials_energy_index = pd.concat([materials_energy_index, new_dataframe], axis=0, ignore_index=True)
        #materials_energy_index = materials_energy_index.append({'Date':row['Date'], 'Value':materials_energy_index_value}, ignore_index=True)

#Next Built Environment
built_environment_index = pd.DataFrame(columns = ['Date', 'Value'])

built_environment_data = built_environment_data.reset_index()
for index, row in built_environment_data.iterrows():
        built_environment_index_value = 0
        for ticker in built_environment_deeptech_index_list:
                if (type(row[ticker]) == int) or (type(row[ticker]) == float):
                        current_row = row[ticker]
                else:
                        print('Not a number')
                        print('Date: ', row['Date'], ticker)
                contribution = row[ticker] * built_environment_index_weight[ticker]
                if pd.isna(contribution):
                  contribution = 0
                built_environment_index_value = built_environment_index_value + contribution
        print('Built Environment data:', row['Date'], ':', built_environment_index_value)
        new_row = {'Date':row['Date'], 'Value':built_environment_index_value}
        new_dataframe = pd.DataFrame([new_row])
        built_environment_index = pd.concat([built_environment_index, new_dataframe], axis=0, ignore_index=True)
        #built_environment_index = built_environment_index.append({'Date':row['Date'], 'Value':built_environment_index_value}, ignore_index=True)

#Next Health
health_index = pd.DataFrame(columns = ['Date', 'Value'])

health_data = health_data.reset_index()
for index, row in health_data.iterrows():
        health_index_value = 0
        for ticker in health_deeptech_index_list:
                if (type(row[ticker]) == int) or (type(row[ticker]) == float):
                        current_row = row[ticker]
                else:
                        print('Not a number')
                        print('Date: ', row['Date'], ticker)
                contribution = row[ticker] * health_index_weight[ticker]
                if pd.isna(contribution):
                  contribution = 0
                health_index_value = health_index_value + contribution
        print('Health data:', row['Date'], ':', health_index_value)
        new_row = {'Date':row['Date'], 'Value':health_index_value}
        new_dataframe = pd.DataFrame([new_row])
        health_index = pd.concat([health_index, new_dataframe], axis=0, ignore_index=True)
        #health_index = health_index.append({'Date':row['Date'], 'Value':health_index_value}, ignore_index=True)

#Next Hyperscale AI
#hyperscale_ai_index = pd.DataFrame(columns = ['Date', 'Value'])
#
#hyperscale_ai_data = hyperscale_ai_data.reset_index()
#for index, row in hyperscale_ai_data.iterrows():
#        hyperscale_ai_index_value = 0
#        for ticker in hyperscale_ai_deeptech_index_list:
#                if (type(row[ticker]) == int) or (type(row[ticker]) == float):
#                        current_row = row[ticker]
#                else:
#                        print('Not a number')
#                        print('Date: ', row['Date'], ticker)
#                contribution = row[ticker] * hyperscale_ai_index_weight[ticker]
#                if pd.isna(contribution):
#                  contribution = 0
#                hyperscale_ai_index_value = hyperscale_ai_index_value + contribution
#        print('Hyperscale AI data:', row['Date'], ':', hyperscale_ai_index_value)
#        new_row = {'Date':row['Date'], 'Value':hyperscale_ai_index_value}
#        new_dataframe = pd.DataFrame([new_row])
#        hyperscale_ai_index = pd.concat([hyperscale_ai_index, new_dataframe], axis=0, ignore_index=True)
#        #hyperscale_ai_index = hyperscale_ai_index.append({'Date':row['Date'], 'Value':hyperscale_ai_index_value}, ignore_index=True)

#Next Mobility
mobility_index = pd.DataFrame(columns = ['Date', 'Value'])

mobility_data = mobility_data.reset_index()
for index, row in mobility_data.iterrows():
        mobility_index_value = 0
        for ticker in mobility_deeptech_index_list:
                if (type(row[ticker]) == int) or (type(row[ticker]) == float):
                        current_row = row[ticker]
                else:
                        print('Not a number')
                        print('Date: ', row['Date'], ticker)
                contribution = row[ticker] * mobility_index_weight[ticker]
                if pd.isna(contribution):
                  contribution = 0
                mobility_index_value = mobility_index_value + contribution
        print('Mobility data:', row['Date'], ':', mobility_index_value)
        new_row = {'Date':row['Date'], 'Value':mobility_index_value}
        new_dataframe = pd.DataFrame([new_row])
        mobility_index = pd.concat([mobility_index, new_dataframe], axis=0, ignore_index=True)
        #mobility_index = mobility_index.append({'Date':row['Date'], 'Value':mobility_index_value}, ignore_index=True)

#Now try and dump out the NASDAQ and S&P500 as individual dataframes
nasdaq_index = data[['Date', '^IXIC']].copy()
sandp_index = data[['Date', '^GSPC']].copy()

#Now we have all the data, time to try and dump out the various .csv files for charting
#Turns out pd.merge can only manage two dataframes at once! So do this in steps
#left_dataframe = pd.merge(newspace_index, legacy_index, on='Date')
#left_dataframe = deeptech_index
left_dataframe = pd.merge(deeptech_index, deeptech_index_no_mega_caps, on='Date')
left_dataframe.rename(columns={'Value_x':'DeepTech Index', 'Value_y':'DeepTech Index - No Mega Caps'}, inplace=True)
left_dataframe = pd.merge(left_dataframe, newspace_index, on='Date')
left_dataframe.rename(columns={'Value':'Space, Aerospace & Defense Subsector'}, inplace=True)
left_dataframe = pd.merge(left_dataframe, manufacturing_index, on='Date')
left_dataframe.rename(columns={'Value':'Manufacturing Subsector'}, inplace=True)
left_dataframe = pd.merge(left_dataframe, materials_energy_index, on='Date')
left_dataframe.rename(columns={'Value':'Energy & Resources Subsector'}, inplace=True)
left_dataframe = pd.merge(left_dataframe, built_environment_index, on='Date')
left_dataframe.rename(columns={'Value':'Built Environment Subsector'}, inplace=True)
left_dataframe = pd.merge(left_dataframe, health_index, on='Date')
left_dataframe.rename(columns={'Value':'Health Subsector'}, inplace=True)
#left_dataframe = pd.merge(left_dataframe, hyperscale_ai_index, on='Date')
#left_dataframe.rename(columns={'Value':'Hyperscale AI Subsector'}, inplace=True)
left_dataframe = pd.merge(left_dataframe, mobility_index, on='Date')
left_dataframe.rename(columns={'Value':'Mobility & Logistics Subsector'}, inplace=True)
right_dataframe = pd.merge(nasdaq_index, sandp_index, on='Date')
master_dataframe = pd.merge(left_dataframe, right_dataframe, on='Date')
print(master_dataframe)
master_dataframe.rename(columns={'^IXIC':'NASDAQ', '^GSPC':'S&P500'}, inplace=True)
#master_dataframe.rename(columns={'Value_x':'DeepTech Index', 'Value_y':'Semiconductor Subsector', '^IXIC':'NASDAQ', '^GSPC':'S&P500'}, inplace=True)
print(master_dataframe)
master_dataframe.to_csv('deeptech_max_data.csv')


#quit()

###########
#
# Set up timeframe for all graphs here by carving out days from master_dataframe
#
###########


#1 Week of data - update 20220327 to match Google Sheet approach of 6 day window instead of 5
one_week_data = master_dataframe.tail(6)
one_week_data = one_week_data.reset_index()
one_week_data = one_week_data.drop('index', axis=1)
#print(one_week_data)
one_week_data.to_csv('deeptech_one_week_data.csv')

#1 month of data - estimate 22 trading days - https://www.dummies.com/article/business-careers-money/personal-finance/investing/investment-vehicles/stocks/stock-chart-attributes-starting-time-period-range-spacing-250596/
#Update on 20220327 to be 23 days to match Google Sheet timeframe - ripples through to all the data selection in the graphing as well
#one_month_data = master_dataframe.tail(22)
one_month_data = master_dataframe.tail(23)
one_month_data = one_month_data.reset_index()
one_month_data = one_month_data.drop('index', axis=1)
print(one_month_data)
one_month_data.to_csv('deeptech_one_month_data.csv')

#3 months of data - estimate 63 trading days
#Update 20220327 to 67 days to match Google Sheet flow
three_month_data = master_dataframe.tail(67)
three_month_data = three_month_data.reset_index()
three_month_data = three_month_data.drop('index', axis=1)
three_month_data.to_csv('deeptech_three_month_data.csv')

#6 months of data - 129 trading days
six_month_data = master_dataframe.tail(129)
six_month_data = six_month_data.reset_index()
six_month_data = six_month_data.drop('index', axis=1)
six_month_data.to_csv('deeptech_six_month_data.csv')

#1 Year of data - 252 trading days
one_year_data = master_dataframe.tail(252)
one_year_data = one_year_data.reset_index()
one_year_data = one_year_data.drop('index', axis=1)
one_year_data.to_csv('deeptech_one_year_data.csv')

#3 Years of data - 756 trading days
three_year_data = master_dataframe.tail(756)
three_year_data = three_year_data.reset_index()
three_year_data = three_year_data.drop('index', axis=1)
three_year_data.to_csv('deeptech_three_year_data.csv')


#Add more as dataset grows

#######
#
# Now dump out most recent close/previous close for New Space Index, NASDAQ, and S&P 500 to display on wesbite
#
#######

most_recent_data = master_dataframe.tail(2)
most_recent_data = most_recent_data.reset_index()
most_recent_data = most_recent_data.drop('index', axis=1)
most_recent_data.to_csv('deeptech_most_recent_data.csv')

#Now send this to Google
#quit()
#Update Master Spreadsheet Tabs
spreadsheetId = 'Deeptech_Index_Master_Spreadsheet_20220812'
#First Market Cap Data
sheetName = 'Data_From_Yahoo_Finance_For_Indices'
csvFile = 'deeptech_most_recent_data.csv'

sheet = client.open(spreadsheetId)
sheet.values_update (
        sheetName,
        params={'valueInputOption': 'USER_ENTERED'},
        body={'values': list(csv.reader(open(csvFile)))}
)

#######
#
#Start with 1 week chart
#
#######

#Get the value of each starting point
#newspace_start = one_week_data.loc[0]['PV New Space']
#semiconductor_start = one_week_data.loc[0]['Semiconductor Subsector']
#semiconductor_equipment_start = one_week_data.loc[0]['Semiconductor Equipment Subsector']
deeptech_start = one_week_data.loc[0]['DeepTech Index']
deeptech_no_mega_caps_start = one_week_data.loc[0]['DeepTech Index - No Mega Caps']
nasdaq_start = one_week_data.loc[0]['NASDAQ']
sandp_start = one_week_data.loc[0]['S&P500']
newspace_start = one_week_data.loc[0]['Space, Aerospace & Defense Subsector']
manufacturing_start = one_week_data.loc[0]['Manufacturing Subsector']
materials_energy_start = one_week_data.loc[0]['Energy & Resources Subsector']
built_environment_start = one_week_data.loc[0]['Built Environment Subsector']
health_start = one_week_data.loc[0]['Health Subsector']
#hyperscale_ai_start = one_week_data.loc[0]['Hyperscale AI Subsector']
mobility_start = one_week_data.loc[0]['Mobility & Logistics Subsector']


#normalized_one_week = pd.DataFrame(columns = ['Date', 'PV New Space', 'PV Legacy Space', 'NASDAQ', 'S&P500'])
normalized_one_week = one_week_data

def normalize_nasdaq_column(value):
	return((value/nasdaq_start)*100)
def normalize_sandp_column(value):
	return((value/sandp_start)*100)
def normalize_deeptech_column(value):
	return((value/deeptech_start)*100)
def normalize_deeptech_no_mega_caps_column(value):
	return((value/deeptech_no_mega_caps_start)*100)
def normalize_newspace_column(value):
	return((value/newspace_start)*100)
def normalize_manufacturing_column(value):
	return((value/manufacturing_start)*100)
def normalize_materials_energy_column(value):
	return((value/materials_energy_start)*100)
def normalize_built_environment_column(value):
	return((value/built_environment_start)*100)
def normalize_health_column(value):
	return((value/health_start)*100)
#def normalize_hyperscale_ai_column(value):
#	return(value/hyperscale_ai_start)
def normalize_mobility_column(value):
	return((value/mobility_start)*100)

normalized_one_week['NASDAQ'] = normalized_one_week['NASDAQ'].apply(normalize_nasdaq_column)
normalized_one_week['S&P500'] = normalized_one_week['S&P500'].apply(normalize_sandp_column)
normalized_one_week['DeepTech Index'] = normalized_one_week['DeepTech Index'].apply(normalize_deeptech_column)
normalized_one_week['DeepTech Index - No Mega Caps'] = normalized_one_week['DeepTech Index - No Mega Caps'].apply(normalize_deeptech_no_mega_caps_column)
normalized_one_week['Space, Aerospace & Defense Subsector'] = normalized_one_week['Space, Aerospace & Defense Subsector'].apply(normalize_newspace_column)
normalized_one_week['Manufacturing Subsector'] = normalized_one_week['Manufacturing Subsector'].apply(normalize_manufacturing_column)
normalized_one_week['Energy & Resources Subsector'] = normalized_one_week['Energy & Resources Subsector'].apply(normalize_materials_energy_column)
normalized_one_week['Built Environment Subsector'] = normalized_one_week['Built Environment Subsector'].apply(normalize_built_environment_column)
normalized_one_week['Health Subsector'] = normalized_one_week['Health Subsector'].apply(normalize_health_column)
#normalized_one_week['Hyperscale AI Subsector'] = normalized_one_week['Hyperscale AI Subsector'].apply(normalize_hyperscale_ai_column)
normalized_one_week['Mobility & Logistics Subsector'] = normalized_one_week['Mobility & Logistics Subsector'].apply(normalize_mobility_column)

#for index, row in one_week_data.iterrows():
#	current_pvnewspace_value = one_week_data.iloc[row]['PV New Space'].values[0] / newspace_start
#	current_pvlegacy_value = one_week_data.iloc[row]['PV Legacy Space'].values[0] / legacy_start
#	current_nasdaq_value = one_week_data.iloc[row]['NASDAQ'].values[0] / nasdaq_start
#	current_sandp_value = one_week_data.iloc[row]['S&P500'].values[0] / sandp_start
#	normalized_one_week = normalized_one_week.append({'Date':row['Date'], 'PV New Space':current_pvnewspace_value, 'PV Legacy Space':current_pvlegacy_space_value, 'NASDAQ':current_nasdaq_value, 'S&P500':current_sandp_value}, ignore_index=True)

print(normalized_one_week)
#Now add annotation for the graph - how much delta for the various things being tracked
def return_percentage(value):
	percentage = value - 100
	percentage = percentage * 10
	percentage = round(percentage)
	percentage = int(percentage) 
	percentage = float(percentage)
	percentage = percentage/10
	return(percentage)

nasdaq_sign = ''
nasdaq_annotation = normalized_one_week.loc[5]['NASDAQ']
print
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
	nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_one_week.loc[5]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
	sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%' 
print('S&P500 Annotation: ', sandp_annotation)

deeptech_sign = ''
deeptech_annotation = normalized_one_week.loc[5]['DeepTech Index']
deeptech_annotation = return_percentage(deeptech_annotation)
if (deeptech_annotation > 0):
	deeptech_sign = '+'
deeptech_annotation = str(deeptech_annotation)
deeptech_annotation = 'DeepTech Index ' + deeptech_sign + deeptech_annotation + '%' 
print('DeepTech Annotation: ', deeptech_annotation)

deeptech_no_mega_caps_sign = ''
deeptech_no_mega_caps_annotation = normalized_one_week.loc[5]['DeepTech Index - No Mega Caps']
deeptech_no_mega_caps_annotation = return_percentage(deeptech_no_mega_caps_annotation)
if (deeptech_no_mega_caps_annotation > 0):
        deeptech_no_mega_caps_sign = '+'
deeptech_no_mega_caps_annotation = str(deeptech_no_mega_caps_annotation)
deeptech_no_mega_caps_annotation = 'DeepTech Index - No Mega Caps ' + deeptech_no_mega_caps_sign + deeptech_no_mega_caps_annotation + '%' 
print('DeepTech Annotation - No Mega Caps: ', deeptech_no_mega_caps_annotation)

newspace_sign = ''
newspace_annotation = normalized_one_week.loc[5]['Space, Aerospace & Defense Subsector']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'Space, Aerospace & Defense Subsector ' + newspace_sign + newspace_annotation + '%'
print('Space, Aerospace & Defense Annotation: ', newspace_annotation)

manufacturing_sign = ''
manufacturing_annotation = normalized_one_week.loc[5]['Manufacturing Subsector']
manufacturing_annotation = return_percentage(manufacturing_annotation)
if (manufacturing_annotation > 0):
        manufacturing_sign = '+'
manufacturing_annotation = str(manufacturing_annotation)
manufacturing_annotation = 'Manufacturing Subsector ' + manufacturing_sign + manufacturing_annotation + '%'
print('Manufacturing Annotation: ', manufacturing_annotation)

materials_energy_sign = ''
materials_energy_annotation = normalized_one_week.loc[5]['Energy & Resources Subsector']
materials_energy_annotation = return_percentage(materials_energy_annotation)
if (materials_energy_annotation > 0):
        materials_energy_sign = '+'
materials_energy_annotation = str(materials_energy_annotation)
materials_energy_annotation = 'Energy & Resources Subsector ' + materials_energy_sign + materials_energy_annotation + '%'
print('Energy & Resources Annotation: ', materials_energy_annotation)

built_environment_sign = ''
built_environment_annotation = normalized_one_week.loc[5]['Built Environment Subsector']
built_environment_annotation = return_percentage(built_environment_annotation)
if (built_environment_annotation > 0):
        built_environment_sign = '+'
built_environment_annotation = str(built_environment_annotation)
built_environment_annotation = 'Built Environment Subsector ' + built_environment_sign + built_environment_annotation + '%'
print('Built Environment Annotation: ', built_environment_annotation)

health_sign = ''
health_annotation = normalized_one_week.loc[5]['Health Subsector']
health_annotation = return_percentage(health_annotation)
if (health_annotation > 0):
        health_sign = '+'
health_annotation = str(health_annotation)
health_annotation = 'Health Subsector ' + health_sign + health_annotation + '%'
print('Health Annotation: ', health_annotation)

#hyperscale_ai_sign = ''
#hyperscale_ai_annotation = normalized_one_week.loc[5]['Hyperscale AI Subsector']
#hyperscale_ai_annotation = return_percentage(hyperscale_ai_annotation)
#if (hyperscale_ai_annotation > 0):
#        hyperscale_ai_sign = '+'
#hyperscale_ai_annotation = str(hyperscale_ai_annotation)
#hyperscale_ai_annotation = 'Hyperscale AI Subsector ' + hyperscale_ai_sign + hyperscale_ai_annotation + '%'
#print('Hyperscale AI Annotation: ', hyperscale_ai_annotation)

mobility_sign = ''
mobility_annotation = normalized_one_week.loc[5]['Mobility & Logistics Subsector']
mobility_annotation = return_percentage(mobility_annotation)
if (mobility_annotation > 0):
        mobility_sign = '+'
mobility_annotation = str(mobility_annotation)
mobility_annotation = 'Mobility & Logistics Subsector ' + mobility_sign + mobility_annotation + '%'
print('Mobility & Logistics Annotation: ', mobility_annotation)

#Actual graphing starts here

figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd',
  },
  title='One Week Performance',
  template='plotly_white',
  width = 800,
  height = 600)

# Build large chart - Deeptech
large_figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
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

# Large chart with no title
large_figure_no_title = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd',
  },
  template='plotly_white',
  )


# Build large chart - Deeptech with no mega caps 
large_no_mega_caps_figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index - No Mega Caps'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index - No Mega Caps': '#18a1cd',
  },
  title='One Week Performance - Deeptech Index Without Mega Cap Companies',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )


# Try a really big graph with Space, Aerospace & Defense subsector called out
large_newspace_figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Space, Aerospace & Defense Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Space, Aerospace & Defense Subsector': '#0492C2'
  },
  title='One Week Performance - Space, Aerospace & Defense Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Manufacturing subsector called out
large_manufacturing_figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Manufacturing Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Manufacturing Subsector': '#0492C2'
  },
  title='One Week Performance - Manufacturing Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Energy & resources subsector called out
large_materials_energy_figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Energy & Resources Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Energy & Resources Subsector': '#0492C2'
  },
  title='One Week Performance - Energy & Resources Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Built Environment subsector called out
large_built_environment_figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Built Environment Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Built Environment Subsector': '#0492C2'
  },
  title='One Week Performance - Built Environment Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Health subsector called out
large_health_figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Health Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Health Subsector': '#0492C2'
  },
  title='One Week Performance - Health Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Hyperscale AI subsector called out
#large_hyperscale_ai_figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Hyperscale AI Subsector'],
#  color_discrete_map={
#    'NASDAQ': '#A6A6A6',
#    'S&P500': '#D9D9D9',
#    'DeepTech Index': '#BFBFBF',
#    'Hyperscale AI Subsector': '#0492C2'
#  },
#  title='One Week Performance - Hyperscale AI Subsector',
#  template='plotly_white',
#  #width = 1600,
#  #height = 1200
#  )

# Try a really big graph with Mobility & Logistics subsector called out
large_mobility_figure = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Mobility & Logistics Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Mobility & Logistics Subsector': '#0492C2'
  },
  title='One Week Performance - Mobility & Logistics Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )
  


#Build mobile chart at the same time - different form factor
figure_mobile = px.line(normalized_one_week, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd',
  },
  title='One Week Performance',
  template='plotly_white',
  width = 320, 
  height = 400) 

#Try to add annotations
figure_annotations = []
figure_annotations_grey = []
figure_no_mega_caps_annotations = []
mobile_figure_annotations = []
newspace_sector_annotations = []
manufacturing_sector_annotations = []
materials_energy_sector_annotations = []
built_environment_sector_annotations = []
health_sector_annotations = []
#hyperscale_ai_sector_annotations = []
mobility_sector_annotations = []

#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
deeptech_y_shift = 10

sandp_got_shifted = 'False'
deeptech_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_one_week['NASDAQ'].values[5]/normalized_one_week['S&P500'].values[5])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_one_week['NASDAQ'].values[5]/normalized_one_week['S&P500'].values[5])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20

#Next check NASDAQ vs DeepTech position - use relative % to see if we need to move
if (abs((normalized_one_week['NASDAQ'].values[5]/normalized_one_week['DeepTech Index'].values[5])-1) < 0.02):
  #Set the newspace_got_shifted flag
  deeptech_got_shifted = 'True'
  if(((normalized_one_week['NASDAQ'].values[5]/normalized_one_week['DeepTech Index'].values[5])-1) > 0):
    #NASDAQ Above PV New Space, shift PV New Space down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift PV New Space by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust deeptech by default
      deeptech_y_shift = 0
  else:
    #DeepTech above NASDAQ, shift DeepTech up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = 30
    else:
      deeptech_y_shift = 20


print(normalized_one_week.iloc[5]['Date'])

#annotation_one = dict(x=normalized_one_week.iloc[4]['Date'], y=normalized_one_week['NASDAQ'].values[4], xref='paper', yref='paper', yshift=10, xshift=45, showarrow=False, bgcolor='#000000',font_color='#FFFFFF', text=nasdaq_annotation)
#annotation_one = dict(x=normalized_one_week.iloc[5]['Date'], y=normalized_one_week['NASDAQ'].values[5], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, clicktoshow='onoff')
annotation_one = dict(x=1.01, y=normalized_one_week['NASDAQ'].values[5], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, clicktoshow='onoff')
annotation_one_grey = dict(x=1.01, y=normalized_one_week['NASDAQ'].values[5], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#A6A6A6',font_color='#FFFFFF', text=nasdaq_annotation, clicktoshow='onoff')
mobile_annotation_one = dict(x=1.01, y=normalized_one_week['NASDAQ'].values[5], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, clicktoshow='onoff', font=dict(size=5))
#annotation_one = dict(x=1, y=normalized_one_week['NASDAQ'].values[4], xref='x', yref='y', yshift=10, xshift=45, showarrow=False, bgcolor='#000000',font_color='#FFFFFF', text=nasdaq_annotation)
figure_annotations.append(annotation_one)
figure_annotations_grey.append(annotation_one_grey)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_one_week.iloc[5]['Date'], y=normalized_one_week['S&P500'].values[5], xref='x', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_one_week['S&P500'].values[5], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two_grey = dict(x=1.01, y=normalized_one_week['S&P500'].values[5], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#D9D9D9',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_one_week['S&P500'].values[5], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
figure_annotations_grey.append(annotation_two_grey)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_one_week.iloc[5]['Date'], y=normalized_one_week['PV New Space'].values[5], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_one_week['DeepTech Index'].values[5], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation)
annotation_three_grey = dict(x=1.01, y=normalized_one_week['DeepTech Index'].values[5], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#BFBFBF',font_color='#FFFFFF', text=deeptech_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_one_week['DeepTech Index'].values[5], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
figure_annotations_grey.append(annotation_three_grey)
mobile_figure_annotations.append(mobile_annotation_three)

#annotation_four = dict(x=normalized_max_data.iloc[-1]['Date'], y=normalized_max_data['PV Legacy Space'].values[-1], xref='x', yref='y', yshift=legacy_y_shift, xshift=5, showarrow=False, bgcolor='#2b5d7d',font_color='#FFFFFF', text=legacy_annotation)
annotation_four = dict(x=1.01, y=normalized_one_week['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_one_week['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation, font=dict(size=5))
figure_no_mega_caps_annotations.append(annotation_one)
figure_no_mega_caps_annotations.append(annotation_two)
figure_no_mega_caps_annotations.append(annotation_four)
#sector_mobile_figure_annotations.append(mobile_annotation_four)

annotation_five = dict(x=1.01, y=normalized_one_week['Space, Aerospace & Defense Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=newspace_annotation)
newspace_sector_annotations.append(annotation_five)

annotation_six = dict(x=1.01, y=normalized_one_week['Manufacturing Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=manufacturing_annotation)
manufacturing_sector_annotations.append(annotation_six)

annotation_seven = dict(x=1.01, y=normalized_one_week['Energy & Resources Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=materials_energy_annotation)
materials_energy_sector_annotations.append(annotation_seven)

annotation_eight = dict(x=1.01, y=normalized_one_week['Built Environment Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=built_environment_annotation)
built_environment_sector_annotations.append(annotation_eight)

annotation_nine = dict(x=1.01, y=normalized_one_week['Health Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=health_annotation)
health_sector_annotations.append(annotation_nine)

#annotation_10 = dict(x=1.01, y=normalized_one_week['Hyperscale AI Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=hyperscale_ai_annotation)
#hyperscale_ai_sector_annotations.append(annotation_10)

annotation_11 = dict(x=1.01, y=normalized_one_week['Mobility & Logistics Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=mobility_annotation)
mobility_sector_annotations.append(annotation_11)

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance (%)')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Now do for large_figure
large_figure.update_layout(annotations=figure_annotations)
large_figure.update_annotations(clicktoshow='onoff')
large_figure.update_annotations(xanchor='left')
large_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure.update_layout(hovermode='closest')
large_figure.update_layout(yaxis_title='Relative Performance (%)')
large_figure.update_layout(margin=dict(r=170))
large_figure.update_yaxes(fixedrange=True)

#Now do for large_figure_no_title
large_figure_no_title.update_layout(annotations=figure_annotations)
large_figure_no_title.update_annotations(clicktoshow='onoff')
large_figure_no_title.update_annotations(xanchor='left')
large_figure_no_title.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure_no_title.update_layout(hovermode='closest')
large_figure_no_title.update_layout(yaxis_title='Relative Performance (%)')
large_figure_no_title.update_layout(margin=dict(r=170))
large_figure_no_title.update_yaxes(fixedrange=True)

#Now do for large_no_mega_caps_figure
#figure_no_mega_caps_annotations = annotation_one + annotation_two + figure_no_mega_caps_annotations
large_no_mega_caps_figure.update_layout(annotations=figure_no_mega_caps_annotations)
large_no_mega_caps_figure.update_annotations(clicktoshow='onoff')
large_no_mega_caps_figure.update_annotations(xanchor='left')
large_no_mega_caps_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_no_mega_caps_figure.update_layout(hovermode='closest')
large_no_mega_caps_figure.update_layout(yaxis_title='Relative Performance (%)')
large_no_mega_caps_figure.update_layout(margin=dict(r=270))
large_no_mega_caps_figure.update_yaxes(fixedrange=True)


# And for all other figures - starting with Newspace sector
newspace_annotations = figure_annotations_grey + newspace_sector_annotations
large_newspace_figure.update_layout(annotations=newspace_annotations)
large_newspace_figure.update_annotations(clicktoshow='onoff')
large_newspace_figure.update_annotations(xanchor='left')
large_newspace_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_newspace_figure.update_layout(hovermode='closest')
large_newspace_figure.update_layout(yaxis_title='Relative Performance (%)')
large_newspace_figure.update_layout(margin=dict(r=350))
large_newspace_figure.update_yaxes(fixedrange=True)

# Now Manufacturing sector
manufacturing_annotations = figure_annotations_grey + manufacturing_sector_annotations
large_manufacturing_figure.update_layout(annotations=manufacturing_annotations)
large_manufacturing_figure.update_annotations(clicktoshow='onoff')
large_manufacturing_figure.update_annotations(xanchor='left')
large_manufacturing_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_manufacturing_figure.update_layout(hovermode='closest')
large_manufacturing_figure.update_layout(yaxis_title='Relative Performance (%)')
large_manufacturing_figure.update_layout(margin=dict(r=275))
large_manufacturing_figure.update_yaxes(fixedrange=True)

# Now Energy & Resources sector
materials_energy_annotations = figure_annotations_grey + materials_energy_sector_annotations
large_materials_energy_figure.update_layout(annotations=materials_energy_annotations)
large_materials_energy_figure.update_annotations(clicktoshow='onoff')
large_materials_energy_figure.update_annotations(xanchor='left')
large_materials_energy_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_materials_energy_figure.update_layout(hovermode='closest')
large_materials_energy_figure.update_layout(yaxis_title='Relative Performance (%)')
large_materials_energy_figure.update_layout(margin=dict(r=275))
large_materials_energy_figure.update_yaxes(fixedrange=True)

# Now Built Environment sector
built_environment_annotations = figure_annotations_grey + built_environment_sector_annotations
large_built_environment_figure.update_layout(annotations=built_environment_annotations)
large_built_environment_figure.update_annotations(clicktoshow='onoff')
large_built_environment_figure.update_annotations(xanchor='left')
large_built_environment_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_built_environment_figure.update_layout(hovermode='closest')
large_built_environment_figure.update_layout(yaxis_title='Relative Performance (%)')
large_built_environment_figure.update_layout(margin=dict(r=275))
large_built_environment_figure.update_yaxes(fixedrange=True)

# Now Health sector
health_annotations = figure_annotations_grey + health_sector_annotations
large_health_figure.update_layout(annotations=health_annotations)
large_health_figure.update_annotations(clicktoshow='onoff')
large_health_figure.update_annotations(xanchor='left')
large_health_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_health_figure.update_layout(hovermode='closest')
large_health_figure.update_layout(yaxis_title='Relative Performance (%)')
large_health_figure.update_layout(margin=dict(r=275))
large_health_figure.update_yaxes(fixedrange=True)

# Now Hyperscale AI sector
#hyperscale_ai_annotations = figure_annotations_grey + hyperscale_ai_sector_annotations
#large_hyperscale_ai_figure.update_layout(annotations=hyperscale_ai_annotations)
#large_hyperscale_ai_figure.update_annotations(clicktoshow='onoff')
#large_hyperscale_ai_figure.update_annotations(xanchor='left')
#large_hyperscale_ai_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#large_hyperscale_ai_figure.update_layout(hovermode='closest')
#large_hyperscale_ai_figure.update_layout(yaxis_title='Relative Performance')
#large_hyperscale_ai_figure.update_layout(margin=dict(r=275))
#large_hyperscale_ai_figure.update_yaxes(fixedrange=True)

# Now Mobility & Logistics sector
mobility_annotations = figure_annotations_grey + mobility_sector_annotations
large_mobility_figure.update_layout(annotations=mobility_annotations)
large_mobility_figure.update_annotations(clicktoshow='onoff')
large_mobility_figure.update_annotations(xanchor='left')
large_mobility_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_mobility_figure.update_layout(hovermode='closest')
large_mobility_figure.update_layout(yaxis_title='Relative Performance (%)')
large_mobility_figure.update_layout(margin=dict(r=275))
large_mobility_figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure_no_title.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_no_mega_caps_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_newspace_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_manufacturing_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_materials_energy_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_built_environment_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_health_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
#large_hyperscale_ai_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_mobility_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))



#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#don't show graphs in cron version in case it hangs the script
#Show while testing...
#figure.show(config=graph_config)
figure.write_html('testing_deeptech_one_week_graph.html', config=graph_config)
large_figure.write_html('testing_deeptech_one_week_graph_large.html', config=graph_config)
large_figure_no_title.write_html('testing_deeptech_one_week_graph_large_no_title.html', config=graph_config)
large_no_mega_caps_figure.write_html('testing_deeptech_one_week_graph_no_mega_caps_large.html', config=graph_config)
large_newspace_figure.write_html('testing_deeptech_with_space_aerospace_defense_sector_one_week_graph_large.html', config=graph_config)
large_manufacturing_figure.write_html('testing_deeptech_with_manufacturing_sector_one_week_graph_large.html', config=graph_config)
large_materials_energy_figure.write_html('testing_deeptech_with_energy_and_resources_sector_one_week_graph_large.html', config=graph_config)
large_built_environment_figure.write_html('testing_deeptech_with_built_environment_sector_one_week_graph_large.html', config=graph_config)
large_health_figure.write_html('testing_deeptech_with_health_sector_one_week_graph_large.html', config=graph_config)
#large_hyperscale_ai_figure.write_html('testing_deeptech_with_hyperscale_ai_sector_one_week_graph_large.html', config=graph_config)
large_mobility_figure.write_html('testing_deeptech_with_mobility_sector_one_week_graph_large.html', config=graph_config)

#Do exactly the same for mobile - except for annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance (%)', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('testing_deeptech_one_week_graph_mobile.html', config=graph_config)

#
# Temp crash out to see if everything works up to this point
#
#import sys
#sys.exit()

#quit()


##
#
# Now do 6 month graph
#
##

# Get starting points
deeptech_start = six_month_data.loc[0]['DeepTech Index']
deeptech_no_mega_caps_start = six_month_data.loc[0]['DeepTech Index - No Mega Caps']
nasdaq_start = six_month_data.loc[0]['NASDAQ']
sandp_start = six_month_data.loc[0]['S&P500']
newspace_start = six_month_data.loc[0]['Space, Aerospace & Defense Subsector']
manufacturing_start = six_month_data.loc[0]['Manufacturing Subsector']
materials_energy_start = six_month_data.loc[0]['Energy & Resources Subsector']
built_environment_start = six_month_data.loc[0]['Built Environment Subsector']
health_start = six_month_data.loc[0]['Health Subsector']
#hyperscale_ai_start = six_month_data.loc[0]['Hyperscale AI Subsector']
mobility_start = six_month_data.loc[0]['Mobility & Logistics Subsector']

normalized_six_month = six_month_data

normalized_six_month['NASDAQ'] = normalized_six_month['NASDAQ'].apply(normalize_nasdaq_column)
normalized_six_month['S&P500'] = normalized_six_month['S&P500'].apply(normalize_sandp_column)
normalized_six_month['DeepTech Index'] = normalized_six_month['DeepTech Index'].apply(normalize_deeptech_column)
normalized_six_month['DeepTech Index - No Mega Caps'] = normalized_six_month['DeepTech Index - No Mega Caps'].apply(normalize_deeptech_no_mega_caps_column)
normalized_six_month['Space, Aerospace & Defense Subsector'] = normalized_six_month['Space, Aerospace & Defense Subsector'].apply(normalize_newspace_column)
normalized_six_month['Manufacturing Subsector'] = normalized_six_month['Manufacturing Subsector'].apply(normalize_manufacturing_column)
normalized_six_month['Energy & Resources Subsector'] = normalized_six_month['Energy & Resources Subsector'].apply(normalize_materials_energy_column)
normalized_six_month['Built Environment Subsector'] = normalized_six_month['Built Environment Subsector'].apply(normalize_built_environment_column)
normalized_six_month['Health Subsector'] = normalized_six_month['Health Subsector'].apply(normalize_health_column)
#normalized_six_month['Hyperscale AI Subsector'] = normalized_six_month['Hyperscale AI Subsector'].apply(normalize_hyperscale_ai_column)
normalized_six_month['Mobility & Logistics Subsector'] = normalized_six_month['Mobility & Logistics Subsector'].apply(normalize_mobility_column)


print(normalized_six_month)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defiend above so reuse that

nasdaq_sign = ''
nasdaq_annotation = normalized_six_month.loc[128]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_six_month.loc[128]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

deeptech_sign = ''
deeptech_annotation = normalized_six_month.loc[128]['DeepTech Index']
deeptech_annotation = return_percentage(deeptech_annotation)
if (deeptech_annotation > 0):
        deeptech_sign = '+'
deeptech_annotation = str(deeptech_annotation)
deeptech_annotation = 'DeepTech Index ' + deeptech_sign + deeptech_annotation + '%'
print('DeepTech Annotation: ', deeptech_annotation)

deeptech_no_mega_caps_sign = ''
deeptech_no_mega_caps_annotation = normalized_six_month.loc[128]['DeepTech Index - No Mega Caps']
deeptech_no_mega_caps_annotation = return_percentage(deeptech_no_mega_caps_annotation)
if (deeptech_no_mega_caps_annotation > 0):
        deeptech_no_mega_caps_sign = '+'
deeptech_no_mega_caps_annotation = str(deeptech_no_mega_caps_annotation)
deeptech_no_mega_caps_annotation = 'DeepTech Index - No Mega Caps ' + deeptech_no_mega_caps_sign + deeptech_no_mega_caps_annotation + '%' 
print('DeepTech Annotation - No Mega Caps: ', deeptech_no_mega_caps_annotation)

newspace_sign = ''
newspace_annotation = normalized_six_month.loc[128]['Space, Aerospace & Defense Subsector']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'Space, Aerospace & Defense Subsector ' + newspace_sign + newspace_annotation + '%'
print('Space, Aerospace & Defense Annotation: ', newspace_annotation)

manufacturing_sign = ''
manufacturing_annotation = normalized_six_month.loc[128]['Manufacturing Subsector']
manufacturing_annotation = return_percentage(manufacturing_annotation)
if (manufacturing_annotation > 0):
        manufacturing_sign = '+'
manufacturing_annotation = str(manufacturing_annotation)
manufacturing_annotation = 'Manufacturing Subsector ' + manufacturing_sign + manufacturing_annotation + '%'
print('Manufacturing Annotation: ', manufacturing_annotation)

materials_energy_sign = ''
materials_energy_annotation = normalized_six_month.loc[128]['Energy & Resources Subsector']
materials_energy_annotation = return_percentage(materials_energy_annotation)
if (materials_energy_annotation > 0):
        materials_energy_sign = '+'
materials_energy_annotation = str(materials_energy_annotation)
materials_energy_annotation = 'Energy & Resources Subsector ' + materials_energy_sign + materials_energy_annotation + '%'
print('Energy & Resources Annotation: ', materials_energy_annotation)

built_environment_sign = ''
built_environment_annotation = normalized_six_month.loc[128]['Built Environment Subsector']
built_environment_annotation = return_percentage(built_environment_annotation)
if (built_environment_annotation > 0):
        built_environment_sign = '+'
built_environment_annotation = str(built_environment_annotation)
built_environment_annotation = 'Built Environment Subsector ' + built_environment_sign + built_environment_annotation + '%'
print('Built Environment Annotation: ', built_environment_annotation)

health_sign = ''
health_annotation = normalized_six_month.loc[128]['Health Subsector']
health_annotation = return_percentage(health_annotation)
if (health_annotation > 0):
        health_sign = '+'
health_annotation = str(health_annotation)
health_annotation = 'Health Subsector ' + health_sign + health_annotation + '%'
print('Health Annotation: ', health_annotation)

#hyperscale_ai_sign = ''
#hyperscale_ai_annotation = normalized_six_month.loc[128]['Hyperscale AI Subsector']
#hyperscale_ai_annotation = return_percentage(hyperscale_ai_annotation)
#if (hyperscale_ai_annotation > 0):
#        hyperscale_ai_sign = '+'
#hyperscale_ai_annotation = str(hyperscale_ai_annotation)
#hyperscale_ai_annotation = 'Hyperscale AI Subsector ' + hyperscale_ai_sign + hyperscale_ai_annotation + '%'
#print('Hyperscale AI Annotation: ', hyperscale_ai_annotation)

mobility_sign = ''
mobility_annotation = normalized_six_month.loc[128]['Mobility & Logistics Subsector']
mobility_annotation = return_percentage(mobility_annotation)
if (mobility_annotation > 0):
        mobility_sign = '+'
mobility_annotation = str(mobility_annotation)
mobility_annotation = 'Mobility & Logistics Subsector ' + mobility_sign + mobility_annotation + '%'
print('Mobility & Logistics Annotation: ', mobility_annotation)

#Actual graphing starts here

#Now chart six month data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Six Month Performance',
  template='plotly_white',
  width = 800,
  height = 600)

# Try a really big graph?
large_figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Six Month Performance - Deeptech Index With Mega Cap Companies',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Large chart with no title
large_figure_no_title = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd',
  },
  template='plotly_white',
  )

# Build large chart - Deeptech with no mega caps 
large_no_mega_caps_figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index - No Mega Caps'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index - No Mega Caps': '#18a1cd',
  },
  title='Six Month Performance - Deeptech Index Without Mega Cap Companies',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )


# Try a really big graph with Space, Aerospace & Defense subsector called out
large_newspace_figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Space, Aerospace & Defense Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Space, Aerospace & Defense Subsector': '#0492C2'
  },
  title='Six Month Performance - Space, Aerospace & Defense Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Manufacturing subsector called out
large_manufacturing_figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Manufacturing Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Manufacturing Subsector': '#0492C2'
  },
  title='Six Month Performance - Manufacturing Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Energy & resources subsector called out
large_materials_energy_figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Energy & Resources Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Energy & Resources Subsector': '#0492C2'
  },
  title='Six Month Performance - Energy & Resources Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Built Environment subsector called out
large_built_environment_figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Built Environment Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Built Environment Subsector': '#0492C2'
  },
  title='Six Month Performance - Built Environment Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Health subsector called out
large_health_figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Health Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Health Subsector': '#0492C2'
  },
  title='Six Month Performance - Health Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Hyperscale AI subsector called out
#large_hyperscale_ai_figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Hyperscale AI Subsector'],
#  color_discrete_map={
#    'NASDAQ': '#A6A6A6',
#    'S&P500': '#D9D9D9',
#    'DeepTech Index': '#BFBFBF',
#    'Hyperscale AI Subsector': '#0492C2'
#  },
#  title='Six Month Performance - Hyperscale AI Subsector',
#  template='plotly_white',
#  #width = 1600,
#  #height = 1200
#  )

# Try a really big graph with Mobility & Logistics subsector called out
large_mobility_figure = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Mobility & Logistics Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Mobility & Logistics Subsector': '#0492C2'
  },
  title='Six Month Performance - Mobility & Logistics Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )


figure_mobile = px.line(normalized_six_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Six Month Performance',
  template='plotly_white',
  width = 320, 
  height = 400) 

#Try to add annotations
figure_annotations = []
figure_annotations_grey = []
figure_no_mega_caps_annotations = []
mobile_figure_annotations = []
newspace_sector_annotations = []
manufacturing_sector_annotations = []
materials_energy_sector_annotations = []
built_environment_sector_annotations = []
health_sector_annotations = []
#hyperscale_ai_sector_annotations = []
mobility_sector_annotations = []


#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
deeptech_y_shift = 10
#newspace_y_shift = 10
#legacy_y_shift = 10

sandp_got_shifted = 'False'
deeptech_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['S&P500'].values[128])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['S&P500'].values[128])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20 

#Next check NASDAQ vs DeepTech position - use relative % to see if we need to move
if (abs((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['DeepTech Index'].values[128])-1) < 0.02):
  #Set the deeptech_got_shifted flag
  deeptech_got_shifted = 'True'  
  if(((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['DeepTech Index'].values[128])-1) > 0):
    #NASDAQ Above DeepTech, shift DeepTech down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift PV New Space by more
    #if (abs((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['S&P500'].values[128])-1) < 0.02):
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      deeptech_y_shift = 0 
  else:
    #DeepTech above NASDAQ, shift DeepTech up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift PV New Space by more
    #if (abs((normalized_six_month['S&P500'].values[128]/normalized_six_month['PV New Space'].values[128])-1) < 0.02):
    #  if(((normalized_six_month['S&P500'].values[128]/normalized_six_month['PV New Space'].values[128])-1) > 0):
    #    #S&P500 above PV New Space, shift both upwards
    #    newspace_y_shift = newspace_y_shift + 5
    #    sandp_y_shift = sandp_y_shift + 5
    #  else:
    #    #S&P500 below PV New Space, shift S&P500 up
    #sandp_y_shift = 15a
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = 30
    else:
      deeptech_y_shift = 20

#Finally check PV Legacy Space vs NASDAQ
#if (abs((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['PV Legacy Space'].values[128])-1) < 0.02):
#  if(((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['PV Legacy Space'].values[128])-1) > 0):
    #NASDAQ Above PV Legacy Space, shift PV Legacy Space down
    #But need to check NASDAQ vs others - if any of these guys overlapped then we need to shift PV Legacy Space by more
    #if (abs((normalized_six_month['NASDAQ'].values[128]/normalized_six_month['S&P500'].values[128])-1) < 0.02):
#    if(sandp_got_shifted == 'True'):
#      if(newspace_got_shifted == 'True'):
#        legacy_y_shift = -20
#      else:
#        legacy_y_shift = -10
#    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
#      legacy_y_shift = 0
#  else:
    #PV Legacy Space above NASDAQ, shift PV Legacy Space up
    #But need to check NASDAQ vs others - if these ones overlapped then shift PV Legacy Space by more
#    if(sandp_got_shifted == 'True'):
#      if(newspace_got_shifted == 'True'):
#        legacy_y_shift = 35
#      else:
#        legacy_y_shift = 25
#    else:
#      legacy_y_shift = 20


#annotation_one = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['NASDAQ'].values[128], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one = dict(x=1.01, y=normalized_six_month['NASDAQ'].values[128], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one_grey = dict(x=1.01, y=normalized_six_month['NASDAQ'].values[128], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#A6A6A6',font_color='#FFFFFF', text=nasdaq_annotation)
mobile_annotation_one = dict(x=1.01, y=normalized_six_month['NASDAQ'].values[128], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, font=dict(size=5))
nasdaq_y_position = normalized_six_month['NASDAQ'].values[128]
figure_annotations.append(annotation_one)
figure_annotations_grey.append(annotation_one_grey)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['S&P500'].values[128], xref='x', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_six_month['S&P500'].values[128], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two_grey = dict(x=1.01, y=normalized_six_month['S&P500'].values[128], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#D9D9D9',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_six_month['S&P500'].values[128], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
figure_annotations_grey.append(annotation_two_grey)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_six_month.iloc[128]['Date'], y=normalized_six_month['PV New Space'].values[128], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_six_month['DeepTech Index'].values[128], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation)
annotation_three_grey = dict(x=1.01, y=normalized_six_month['DeepTech Index'].values[128], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#BFBFBF',font_color='#FFFFFF', text=deeptech_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_six_month['DeepTech Index'].values[128], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
figure_annotations_grey.append(annotation_three_grey)
mobile_figure_annotations.append(mobile_annotation_three)

annotation_four = dict(x=1.01, y=normalized_six_month['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_six_month['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation, font=dict(size=5))
figure_no_mega_caps_annotations.append(annotation_one)
figure_no_mega_caps_annotations.append(annotation_two)
figure_no_mega_caps_annotations.append(annotation_four)
#sector_mobile_figure_annotations.append(mobile_annotation_four)

annotation_five = dict(x=1.01, y=normalized_six_month['Space, Aerospace & Defense Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=newspace_annotation)
newspace_sector_annotations.append(annotation_five)

annotation_six = dict(x=1.01, y=normalized_six_month['Manufacturing Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=manufacturing_annotation)
manufacturing_sector_annotations.append(annotation_six)

annotation_seven = dict(x=1.01, y=normalized_six_month['Energy & Resources Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=materials_energy_annotation)
materials_energy_sector_annotations.append(annotation_seven)

annotation_eight = dict(x=1.01, y=normalized_six_month['Built Environment Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=built_environment_annotation)
built_environment_sector_annotations.append(annotation_eight)

annotation_nine = dict(x=1.01, y=normalized_six_month['Health Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=health_annotation)
health_sector_annotations.append(annotation_nine)

#annotation_10 = dict(x=1.01, y=normalized_six_month['Hyperscale AI Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=hyperscale_ai_annotation)
#hyperscale_ai_sector_annotations.append(annotation_10)

annotation_11 = dict(x=1.01, y=normalized_six_month['Mobility & Logistics Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=mobility_annotation)
mobility_sector_annotations.append(annotation_11)

################

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance (%)')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Now do for large figure
large_figure.update_layout(annotations=figure_annotations)
large_figure.update_annotations(clicktoshow='onoff')
large_figure.update_annotations(xanchor='left')
large_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure.update_layout(hovermode='closest')
large_figure.update_layout(yaxis_title='Relative Performance (%)')
large_figure.update_layout(margin=dict(r=170))
large_figure.update_yaxes(fixedrange=True)

#Now do for large_figure_no_title
large_figure_no_title.update_layout(annotations=figure_annotations)
large_figure_no_title.update_annotations(clicktoshow='onoff')
large_figure_no_title.update_annotations(xanchor='left')
large_figure_no_title.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure_no_title.update_layout(hovermode='closest')
large_figure_no_title.update_layout(yaxis_title='Relative Performance (%)')
large_figure_no_title.update_layout(margin=dict(r=170))
large_figure_no_title.update_yaxes(fixedrange=True)

#Now do for large_no_mega_caps_figure
#figure_no_mega_caps_annotations = annotation_one + annotation_two + figure_no_mega_caps_annotations
large_no_mega_caps_figure.update_layout(annotations=figure_no_mega_caps_annotations)
large_no_mega_caps_figure.update_annotations(clicktoshow='onoff')
large_no_mega_caps_figure.update_annotations(xanchor='left')
large_no_mega_caps_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_no_mega_caps_figure.update_layout(hovermode='closest')
large_no_mega_caps_figure.update_layout(yaxis_title='Relative Performance (%)')
large_no_mega_caps_figure.update_layout(margin=dict(r=270))
large_no_mega_caps_figure.update_yaxes(fixedrange=True)


# And for all other figures - starting with Newspace sector
newspace_annotations = figure_annotations_grey + newspace_sector_annotations
large_newspace_figure.update_layout(annotations=newspace_annotations)
large_newspace_figure.update_annotations(clicktoshow='onoff')
large_newspace_figure.update_annotations(xanchor='left')
large_newspace_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_newspace_figure.update_layout(hovermode='closest')
large_newspace_figure.update_layout(yaxis_title='Relative Performance (%)')
large_newspace_figure.update_layout(margin=dict(r=350))
large_newspace_figure.update_yaxes(fixedrange=True)

# Now Manufacturing sector
manufacturing_annotations = figure_annotations_grey + manufacturing_sector_annotations
large_manufacturing_figure.update_layout(annotations=manufacturing_annotations)
large_manufacturing_figure.update_annotations(clicktoshow='onoff')
large_manufacturing_figure.update_annotations(xanchor='left')
large_manufacturing_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_manufacturing_figure.update_layout(hovermode='closest')
large_manufacturing_figure.update_layout(yaxis_title='Relative Performance (%)')
large_manufacturing_figure.update_layout(margin=dict(r=275))
large_manufacturing_figure.update_yaxes(fixedrange=True)

# Now Energy & Resources sector
materials_energy_annotations = figure_annotations_grey + materials_energy_sector_annotations
large_materials_energy_figure.update_layout(annotations=materials_energy_annotations)
large_materials_energy_figure.update_annotations(clicktoshow='onoff')
large_materials_energy_figure.update_annotations(xanchor='left')
large_materials_energy_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_materials_energy_figure.update_layout(hovermode='closest')
large_materials_energy_figure.update_layout(yaxis_title='Relative Performance (%)')
large_materials_energy_figure.update_layout(margin=dict(r=275))
large_materials_energy_figure.update_yaxes(fixedrange=True)

# Now Built Environment sector
built_environment_annotations = figure_annotations_grey + built_environment_sector_annotations
large_built_environment_figure.update_layout(annotations=built_environment_annotations)
large_built_environment_figure.update_annotations(clicktoshow='onoff')
large_built_environment_figure.update_annotations(xanchor='left')
large_built_environment_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_built_environment_figure.update_layout(hovermode='closest')
large_built_environment_figure.update_layout(yaxis_title='Relative Performance (%)')
large_built_environment_figure.update_layout(margin=dict(r=275))
large_built_environment_figure.update_yaxes(fixedrange=True)

# Now Health sector
health_annotations = figure_annotations_grey + health_sector_annotations
large_health_figure.update_layout(annotations=health_annotations)
large_health_figure.update_annotations(clicktoshow='onoff')
large_health_figure.update_annotations(xanchor='left')
large_health_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_health_figure.update_layout(hovermode='closest')
large_health_figure.update_layout(yaxis_title='Relative Performance (%)')
large_health_figure.update_layout(margin=dict(r=275))
large_health_figure.update_yaxes(fixedrange=True)

# Now Hyperscale AI sector
#hyperscale_ai_annotations = figure_annotations_grey + hyperscale_ai_sector_annotations
#large_hyperscale_ai_figure.update_layout(annotations=hyperscale_ai_annotations)
#large_hyperscale_ai_figure.update_annotations(clicktoshow='onoff')
#large_hyperscale_ai_figure.update_annotations(xanchor='left')
#large_hyperscale_ai_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#large_hyperscale_ai_figure.update_layout(hovermode='closest')
#large_hyperscale_ai_figure.update_layout(yaxis_title='Relative Performance')
#large_hyperscale_ai_figure.update_layout(margin=dict(r=275))
#large_hyperscale_ai_figure.update_yaxes(fixedrange=True)

# Now Mobility & Logistics sector
mobility_annotations = figure_annotations_grey + mobility_sector_annotations
large_mobility_figure.update_layout(annotations=mobility_annotations)
large_mobility_figure.update_annotations(clicktoshow='onoff')
large_mobility_figure.update_annotations(xanchor='left')
large_mobility_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_mobility_figure.update_layout(hovermode='closest')
large_mobility_figure.update_layout(yaxis_title='Relative Performance (%)')
large_mobility_figure.update_layout(margin=dict(r=275))
large_mobility_figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure_no_title.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_no_mega_caps_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_newspace_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_manufacturing_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_materials_energy_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_built_environment_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_health_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
#large_hyperscale_ai_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_mobility_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#don't show graphs in cron version in case it hangs the script
#Show while testing...
#figure.show(config=graph_config)
figure.write_html('testing_deeptech_six_month_graph.html', config=graph_config)
large_figure.write_html('testing_deeptech_six_month_graph_large.html', config=graph_config)
large_figure_no_title.write_html('testing_deeptech_six_month_graph_large_no_title.html', config=graph_config)
large_no_mega_caps_figure.write_html('testing_deeptech_six_month_graph_no_mega_caps_large.html', config=graph_config)
large_newspace_figure.write_html('testing_deeptech_with_space_aerospace_defense_sector_six_month_graph_large.html', config=graph_config)
large_manufacturing_figure.write_html('testing_deeptech_with_manufacturing_sector_six_month_graph_large.html', config=graph_config)
large_materials_energy_figure.write_html('testing_deeptech_with_energy_and_resources_sector_six_month_graph_large.html', config=graph_config)
large_built_environment_figure.write_html('testing_deeptech_with_built_environment_sector_six_month_graph_large.html', config=graph_config)
large_health_figure.write_html('testing_deeptech_with_health_sector_six_month_graph_large.html', config=graph_config)
#large_hyperscale_ai_figure.write_html('testing_deeptech_with_hyperscale_ai_sector_six_month_graph_large.html', config=graph_config)
large_mobility_figure.write_html('testing_deeptech_with_mobility_sector_six_month_graph_large.html', config=graph_config)

#Now do all of this for mobile
#Do exactly the same for mobile - except using mobile annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance (%)', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('testing_deeptech_six_month_graph_mobile.html', config=graph_config)

#quit()

##
#
# Now do 1 month graph
#
##

#Get the value of each starting point

deeptech_start = one_month_data.loc[0]['DeepTech Index']
deeptech_no_mega_caps_start = one_month_data.loc[0]['DeepTech Index - No Mega Caps']
nasdaq_start = one_month_data.loc[0]['NASDAQ']
sandp_start = one_month_data.loc[0]['S&P500']
newspace_start = one_month_data.loc[0]['Space, Aerospace & Defense Subsector']
manufacturing_start = one_month_data.loc[0]['Manufacturing Subsector']
materials_energy_start = one_month_data.loc[0]['Energy & Resources Subsector']
built_environment_start = one_month_data.loc[0]['Built Environment Subsector']
health_start = one_month_data.loc[0]['Health Subsector']
#hyperscale_ai_start = one_month_data.loc[0]['Hyperscale AI Subsector']
mobility_start = one_month_data.loc[0]['Mobility & Logistics Subsector']

normalized_one_month = one_month_data

normalized_one_month['NASDAQ'] = normalized_one_month['NASDAQ'].apply(normalize_nasdaq_column)
normalized_one_month['S&P500'] = normalized_one_month['S&P500'].apply(normalize_sandp_column)
normalized_one_month['DeepTech Index'] = normalized_one_month['DeepTech Index'].apply(normalize_deeptech_column)
normalized_one_month['DeepTech Index - No Mega Caps'] = normalized_one_month['DeepTech Index - No Mega Caps'].apply(normalize_deeptech_no_mega_caps_column)
normalized_one_month['Space, Aerospace & Defense Subsector'] = normalized_one_month['Space, Aerospace & Defense Subsector'].apply(normalize_newspace_column)
normalized_one_month['Manufacturing Subsector'] = normalized_one_month['Manufacturing Subsector'].apply(normalize_manufacturing_column)
normalized_one_month['Energy & Resources Subsector'] = normalized_one_month['Energy & Resources Subsector'].apply(normalize_materials_energy_column)
normalized_one_month['Built Environment Subsector'] = normalized_one_month['Built Environment Subsector'].apply(normalize_built_environment_column)
normalized_one_month['Health Subsector'] = normalized_one_month['Health Subsector'].apply(normalize_health_column)
#normalized_one_month['Hyperscale AI Subsector'] = normalized_one_month['Hyperscale AI Subsector'].apply(normalize_hyperscale_ai_column)
normalized_one_month['Mobility & Logistics Subsector'] = normalized_one_month['Mobility & Logistics Subsector'].apply(normalize_mobility_column)


print(normalized_one_month)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defined above so reuse that

nasdaq_sign = ''
nasdaq_annotation = normalized_one_month.loc[22]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_one_month.loc[22]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

deeptech_sign = ''
deeptech_annotation = normalized_one_month.loc[22]['DeepTech Index']
deeptech_annotation = return_percentage(deeptech_annotation)
if (deeptech_annotation > 0):
        deeptech_sign = '+'
deeptech_annotation = str(deeptech_annotation)
deeptech_annotation = 'DeepTech Index ' + deeptech_sign + deeptech_annotation + '%'
print('DeepTech Annotation: ', deeptech_annotation)

deeptech_no_mega_caps_sign = ''
deeptech_no_mega_caps_annotation = normalized_one_month.loc[22]['DeepTech Index - No Mega Caps']
deeptech_no_mega_caps_annotation = return_percentage(deeptech_no_mega_caps_annotation)
if (deeptech_no_mega_caps_annotation > 0):
        deeptech_no_mega_caps_sign = '+'
deeptech_no_mega_caps_annotation = str(deeptech_no_mega_caps_annotation)
deeptech_no_mega_caps_annotation = 'DeepTech Index - No Mega Caps ' + deeptech_no_mega_caps_sign + deeptech_no_mega_caps_annotation + '%' 
print('DeepTech Annotation - No Mega Caps: ', deeptech_no_mega_caps_annotation)

newspace_sign = ''
newspace_annotation = normalized_one_month.loc[22]['Space, Aerospace & Defense Subsector']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'Space, Aerospace & Defense Subsector ' + newspace_sign + newspace_annotation + '%'
print('Space, Aerospace & Defense Annotation: ', newspace_annotation)

manufacturing_sign = ''
manufacturing_annotation = normalized_one_month.loc[22]['Manufacturing Subsector']
manufacturing_annotation = return_percentage(manufacturing_annotation)
if (manufacturing_annotation > 0):
        manufacturing_sign = '+'
manufacturing_annotation = str(manufacturing_annotation)
manufacturing_annotation = 'Manufacturing Subsector ' + manufacturing_sign + manufacturing_annotation + '%'
print('Manufacturing Annotation: ', manufacturing_annotation)

materials_energy_sign = ''
materials_energy_annotation = normalized_one_month.loc[22]['Energy & Resources Subsector']
materials_energy_annotation = return_percentage(materials_energy_annotation)
if (materials_energy_annotation > 0):
        materials_energy_sign = '+'
materials_energy_annotation = str(materials_energy_annotation)
materials_energy_annotation = 'Energy & Resources Subsector ' + materials_energy_sign + materials_energy_annotation + '%'
print('Energy & Resources Annotation: ', materials_energy_annotation)

built_environment_sign = ''
built_environment_annotation = normalized_one_month.loc[22]['Built Environment Subsector']
built_environment_annotation = return_percentage(built_environment_annotation)
if (built_environment_annotation > 0):
        built_environment_sign = '+'
built_environment_annotation = str(built_environment_annotation)
built_environment_annotation = 'Built Environment Subsector ' + built_environment_sign + built_environment_annotation + '%'
print('Built Environment Annotation: ', built_environment_annotation)

health_sign = ''
health_annotation = normalized_one_month.loc[22]['Health Subsector']
health_annotation = return_percentage(health_annotation)
if (health_annotation > 0):
        health_sign = '+'
health_annotation = str(health_annotation)
health_annotation = 'Health Subsector ' + health_sign + health_annotation + '%'
print('Health Annotation: ', health_annotation)

#hyperscale_ai_sign = ''
#hyperscale_ai_annotation = normalized_one_month.loc[22]['Hyperscale AI Subsector']
#hyperscale_ai_annotation = return_percentage(hyperscale_ai_annotation)
#if (hyperscale_ai_annotation > 0):
#        hyperscale_ai_sign = '+'
#hyperscale_ai_annotation = str(hyperscale_ai_annotation)
#hyperscale_ai_annotation = 'Hyperscale AI Subsector ' + hyperscale_ai_sign + hyperscale_ai_annotation + '%'
#print('Hyperscale AI Annotation: ', hyperscale_ai_annotation)

mobility_sign = ''
mobility_annotation = normalized_one_month.loc[22]['Mobility & Logistics Subsector']
mobility_annotation = return_percentage(mobility_annotation)
if (mobility_annotation > 0):
        mobility_sign = '+'
mobility_annotation = str(mobility_annotation)
mobility_annotation = 'Mobility & Logistics Subsector ' + mobility_sign + mobility_annotation + '%'
print('Mobility & Logistics Annotation: ', mobility_annotation)

#Now chart one month data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='One Month Performance',
  template='plotly_white',
  width = 800,
  height = 600)

large_figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='One Month Performance',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Large chart with no title
large_figure_no_title = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd',
  },
  template='plotly_white',
  )

# Build large chart - Deeptech with no mega caps 
large_no_mega_caps_figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index - No Mega Caps'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index - No Mega Caps': '#18a1cd',
  },
  title='One Month Performance - Deeptech Index Without Mega Cap Companies',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )


# Try a really big graph with Space, Aerospace & Defense subsector called out
large_newspace_figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Space, Aerospace & Defense Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Space, Aerospace & Defense Subsector': '#0492C2'
  },
  title='One Month Performance - Space, Aerospace & Defense Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Manufacturing subsector called out
large_manufacturing_figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Manufacturing Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Manufacturing Subsector': '#0492C2'
  },
  title='One Month Performance - Manufacturing Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Energy & resources subsector called out
large_materials_energy_figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Energy & Resources Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Energy & Resources Subsector': '#0492C2'
  },
  title='One Month Performance - Energy & Resources Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Built Environment subsector called out
large_built_environment_figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Built Environment Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Built Environment Subsector': '#0492C2'
  },
  title='one Month Performance - Built Environment Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Health subsector called out
large_health_figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Health Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Health Subsector': '#0492C2'
  },
  title='One Month Performance - Health Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Hyperscale AI subsector called out
#large_hyperscale_ai_figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Hyperscale AI Subsector'],
#  color_discrete_map={
#    'NASDAQ': '#A6A6A6',
#    'S&P500': '#D9D9D9',
#    'DeepTech Index': '#BFBFBF',
#    'Hyperscale AI Subsector': '#0492C2'
#  },
#  title='One Month Performance - Hyperscale AI Subsector',
#  template='plotly_white',
#  #width = 1600,
#  #height = 1200
#  )

# Try a really big graph with Mobility & Logistics subsector called out
large_mobility_figure = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Mobility & Logistics Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Mobility & Logistics Subsector': '#0492C2'
  },
  title='One Month Performance - Mobility & Logistics Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

#Build mobile chart at the same time - different form factor
figure_mobile = px.line(normalized_one_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='One Month Performance',
  template='plotly_white',
  width = 320,
  height = 400)

#Try to add annotations
figure_annotations = []
figure_annotations_grey = []
figure_no_mega_caps_annotations = []
mobile_figure_annotations = []
newspace_sector_annotations = []
manufacturing_sector_annotations = []
materials_energy_sector_annotations = []
built_environment_sector_annotations = []
health_sector_annotations = []
#hyperscale_ai_sector_annotations = []
mobility_sector_annotations = []

#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
deeptech_y_shift = 10
#legacy_y_shift = 10

sandp_got_shifted = 'False'
deeptech_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_one_month['NASDAQ'].values[22]/normalized_one_month['S&P500'].values[22])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_one_month['NASDAQ'].values[22]/normalized_one_month['S&P500'].values[22])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20

#Next check NASDAQ vs DeepTech position - use relative % to see if we need to move
if (abs((normalized_one_month['NASDAQ'].values[22]/normalized_one_month['DeepTech Index'].values[22])-1) < 0.02):
  #Set the deeptech_got_shifted flag
  deeptech_got_shifted = 'True'
  if(((normalized_one_month['NASDAQ'].values[22]/normalized_one_month['DeepTech Index'].values[22])-1) > 0):
    #NASDAQ Above DeepTech, shift DeepTech down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust PV New Space by default
      deeptech_y_shift = 0
  else:
    #DeepTech above NASDAQ, shift DeepTech up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = 30
    else:
      deeptech_y_shift = 20

#annotation_one = dict(x=normalized_one_month.iloc[22]['Date'], y=normalized_one_month['NASDAQ'].values[22], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one = dict(x=1.01, y=normalized_one_month['NASDAQ'].values[22], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one_grey = dict(x=1.01, y=normalized_one_month['NASDAQ'].values[22], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#A6A6A6',font_color='#FFFFFF', text=nasdaq_annotation)
mobile_annotation_one = dict(x=1.01, y=normalized_one_month['NASDAQ'].values[22], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, font=dict(size=5))
figure_annotations.append(annotation_one)
figure_annotations_grey.append(annotation_one_grey)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_one_month.iloc[22]['Date'], y=normalized_one_month['S&P500'].values[22], xref='x', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_one_month['S&P500'].values[22], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two_grey = dict(x=1.01, y=normalized_one_month['S&P500'].values[22], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#D9D9D9',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_one_month['S&P500'].values[22], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
figure_annotations_grey.append(annotation_two_grey)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_one_month.iloc[22]['Date'], y=normalized_one_month['PV New Space'].values[22], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_one_month['DeepTech Index'].values[22], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation)
annotation_three_grey = dict(x=1.01, y=normalized_one_month['DeepTech Index'].values[22], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#BFBFBF',font_color='#FFFFFF', text=deeptech_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_one_month['DeepTech Index'].values[22], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
figure_annotations_grey.append(annotation_three_grey)
mobile_figure_annotations.append(mobile_annotation_three)

annotation_four = dict(x=1.01, y=normalized_one_month['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_one_month['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation, font=dict(size=5))
figure_no_mega_caps_annotations.append(annotation_one)
figure_no_mega_caps_annotations.append(annotation_two)
figure_no_mega_caps_annotations.append(annotation_four)
#sector_mobile_figure_annotations.append(mobile_annotation_four)

annotation_five = dict(x=1.01, y=normalized_one_month['Space, Aerospace & Defense Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=newspace_annotation)
newspace_sector_annotations.append(annotation_five)

annotation_six = dict(x=1.01, y=normalized_one_month['Manufacturing Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=manufacturing_annotation)
manufacturing_sector_annotations.append(annotation_six)

annotation_seven = dict(x=1.01, y=normalized_one_month['Energy & Resources Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=materials_energy_annotation)
materials_energy_sector_annotations.append(annotation_seven)

annotation_eight = dict(x=1.01, y=normalized_one_month['Built Environment Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=built_environment_annotation)
built_environment_sector_annotations.append(annotation_eight)

annotation_nine = dict(x=1.01, y=normalized_one_month['Health Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=health_annotation)
health_sector_annotations.append(annotation_nine)

#annotation_10 = dict(x=1.01, y=normalized_one_month['Hyperscale AI Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=hyperscale_ai_annotation)
#hyperscale_ai_sector_annotations.append(annotation_10)

annotation_11 = dict(x=1.01, y=normalized_one_month['Mobility & Logistics Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=mobility_annotation)
mobility_sector_annotations.append(annotation_11)



figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance (%)')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Now do for large_figure
large_figure.update_layout(annotations=figure_annotations)
large_figure.update_annotations(clicktoshow='onoff')
large_figure.update_annotations(xanchor='left')
large_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure.update_layout(hovermode='closest')
large_figure.update_layout(yaxis_title='Relative Performance (%)')
large_figure.update_layout(margin=dict(r=170))
large_figure.update_yaxes(fixedrange=True)

#Now do for large_figure_no_title
large_figure_no_title.update_layout(annotations=figure_annotations)
large_figure_no_title.update_annotations(clicktoshow='onoff')
large_figure_no_title.update_annotations(xanchor='left')
large_figure_no_title.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure_no_title.update_layout(hovermode='closest')
large_figure_no_title.update_layout(yaxis_title='Relative Performance (%)')
large_figure_no_title.update_layout(margin=dict(r=170))
large_figure_no_title.update_yaxes(fixedrange=True)

#Now do for large_no_mega_caps_figure
#figure_no_mega_caps_annotations = annotation_one + annotation_two + figure_no_mega_caps_annotations
large_no_mega_caps_figure.update_layout(annotations=figure_no_mega_caps_annotations)
large_no_mega_caps_figure.update_annotations(clicktoshow='onoff')
large_no_mega_caps_figure.update_annotations(xanchor='left')
large_no_mega_caps_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_no_mega_caps_figure.update_layout(hovermode='closest')
large_no_mega_caps_figure.update_layout(yaxis_title='Relative Performance (%)')
large_no_mega_caps_figure.update_layout(margin=dict(r=270))
large_no_mega_caps_figure.update_yaxes(fixedrange=True)


# And for all other figures - starting with Newspace sector
newspace_annotations = figure_annotations_grey + newspace_sector_annotations
large_newspace_figure.update_layout(annotations=newspace_annotations)
large_newspace_figure.update_annotations(clicktoshow='onoff')
large_newspace_figure.update_annotations(xanchor='left')
large_newspace_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_newspace_figure.update_layout(hovermode='closest')
large_newspace_figure.update_layout(yaxis_title='Relative Performance (%)')
large_newspace_figure.update_layout(margin=dict(r=200))
large_newspace_figure.update_yaxes(fixedrange=True)

# Now Manufacturing sector
manufacturing_annotations = figure_annotations_grey + manufacturing_sector_annotations
large_manufacturing_figure.update_layout(annotations=manufacturing_annotations)
large_manufacturing_figure.update_annotations(clicktoshow='onoff')
large_manufacturing_figure.update_annotations(xanchor='left')
large_manufacturing_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_manufacturing_figure.update_layout(hovermode='closest')
large_manufacturing_figure.update_layout(yaxis_title='Relative Performance (%)')
large_manufacturing_figure.update_layout(margin=dict(r=275))
large_manufacturing_figure.update_yaxes(fixedrange=True)

# Now Energy & Resources sector
materials_energy_annotations = figure_annotations_grey + materials_energy_sector_annotations
large_materials_energy_figure.update_layout(annotations=materials_energy_annotations)
large_materials_energy_figure.update_annotations(clicktoshow='onoff')
large_materials_energy_figure.update_annotations(xanchor='left')
large_materials_energy_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_materials_energy_figure.update_layout(hovermode='closest')
large_materials_energy_figure.update_layout(yaxis_title='Relative Performance (%)')
large_materials_energy_figure.update_layout(margin=dict(r=275))
large_materials_energy_figure.update_yaxes(fixedrange=True)

# Now Built Environment sector
built_environment_annotations = figure_annotations_grey + built_environment_sector_annotations
large_built_environment_figure.update_layout(annotations=built_environment_annotations)
large_built_environment_figure.update_annotations(clicktoshow='onoff')
large_built_environment_figure.update_annotations(xanchor='left')
large_built_environment_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_built_environment_figure.update_layout(hovermode='closest')
large_built_environment_figure.update_layout(yaxis_title='Relative Performance (%)')
large_built_environment_figure.update_layout(margin=dict(r=275))
large_built_environment_figure.update_yaxes(fixedrange=True)

# Now Health sector
health_annotations = figure_annotations_grey + health_sector_annotations
large_health_figure.update_layout(annotations=health_annotations)
large_health_figure.update_annotations(clicktoshow='onoff')
large_health_figure.update_annotations(xanchor='left')
large_health_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_health_figure.update_layout(hovermode='closest')
large_health_figure.update_layout(yaxis_title='Relative Performance (%)')
large_health_figure.update_layout(margin=dict(r=275))
large_health_figure.update_yaxes(fixedrange=True)

# Now Hyperscale AI sector
#hyperscale_ai_annotations = figure_annotations_grey + hyperscale_ai_sector_annotations
#large_hyperscale_ai_figure.update_layout(annotations=hyperscale_ai_annotations)
#large_hyperscale_ai_figure.update_annotations(clicktoshow='onoff')
#large_hyperscale_ai_figure.update_annotations(xanchor='left')
#large_hyperscale_ai_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#large_hyperscale_ai_figure.update_layout(hovermode='closest')
#large_hyperscale_ai_figure.update_layout(yaxis_title='Relative Performance')
#large_hyperscale_ai_figure.update_layout(margin=dict(r=275))
#large_hyperscale_ai_figure.update_yaxes(fixedrange=True)

# Now Mobility & Logistics sector
mobility_annotations = figure_annotations_grey + mobility_sector_annotations
large_mobility_figure.update_layout(annotations=mobility_annotations)
large_mobility_figure.update_annotations(clicktoshow='onoff')
large_mobility_figure.update_annotations(xanchor='left')
large_mobility_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_mobility_figure.update_layout(hovermode='closest')
large_mobility_figure.update_layout(yaxis_title='Relative Performance (%)')
large_mobility_figure.update_layout(margin=dict(r=275))
large_mobility_figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure_no_title.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_no_mega_caps_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_newspace_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_manufacturing_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_materials_energy_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_built_environment_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_health_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
#large_hyperscale_ai_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_mobility_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#don't show graphs in cron version in case it hangs the script
#Show while testing...
#figure.show(config=graph_config)
figure.write_html('testing_deeptech_one_month_graph.html', config=graph_config)
large_figure.write_html('testing_deeptech_one_month_graph_large.html', config=graph_config)
large_figure_no_title.write_html('testing_deeptech_one_month_graph_large_no_title.html', config=graph_config)
large_no_mega_caps_figure.write_html('testing_deeptech_one_month_graph_no_mega_caps_large.html', config=graph_config)
large_newspace_figure.write_html('testing_deeptech_with_space_aerospace_defense_sector_one_month_graph_large.html', config=graph_config)
large_manufacturing_figure.write_html('testing_deeptech_with_manufacturing_sector_one_month_graph_large.html', config=graph_config)
large_materials_energy_figure.write_html('testing_deeptech_with_energy_and_resources_sector_one_month_graph_large.html', config=graph_config)
large_built_environment_figure.write_html('testing_deeptech_with_built_environment_sector_one_month_graph_large.html', config=graph_config)
large_health_figure.write_html('testing_deeptech_with_health_sector_one_month_graph_large.html', config=graph_config)
#large_hyperscale_ai_figure.write_html('testing_deeptech_with_hyperscale_ai_sector_one_month_graph_large.html', config=graph_config)
large_mobility_figure.write_html('testing_deeptech_with_mobility_sector_one_month_graph_large.html', config=graph_config)

#Do exactly the same for mobile - except use mobile annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance (%)', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('testing_deeptech_one_month_graph_mobile.html', config=graph_config)


##
#
# Now do 3 month graph
#
##

#Get the value of each starting point
deeptech_start = three_month_data.loc[0]['DeepTech Index']
deeptech_no_mega_caps_start = three_month_data.loc[0]['DeepTech Index - No Mega Caps']
nasdaq_start = three_month_data.loc[0]['NASDAQ']
sandp_start = three_month_data.loc[0]['S&P500']
newspace_start = three_month_data.loc[0]['Space, Aerospace & Defense Subsector']
manufacturing_start = three_month_data.loc[0]['Manufacturing Subsector']
materials_energy_start = three_month_data.loc[0]['Energy & Resources Subsector']
built_environment_start = three_month_data.loc[0]['Built Environment Subsector']
health_start = three_month_data.loc[0]['Health Subsector']
#hyperscale_ai_start = three_month_data.loc[0]['Hyperscale AI Subsector']
mobility_start = three_month_data.loc[0]['Mobility & Logistics Subsector']

normalized_three_month = three_month_data

normalized_three_month['NASDAQ'] = normalized_three_month['NASDAQ'].apply(normalize_nasdaq_column)
normalized_three_month['S&P500'] = normalized_three_month['S&P500'].apply(normalize_sandp_column)
normalized_three_month['DeepTech Index'] = normalized_three_month['DeepTech Index'].apply(normalize_deeptech_column)
normalized_three_month['DeepTech Index - No Mega Caps'] = normalized_three_month['DeepTech Index - No Mega Caps'].apply(normalize_deeptech_no_mega_caps_column)
normalized_three_month['Space, Aerospace & Defense Subsector'] = normalized_three_month['Space, Aerospace & Defense Subsector'].apply(normalize_newspace_column)
normalized_three_month['Manufacturing Subsector'] = normalized_three_month['Manufacturing Subsector'].apply(normalize_manufacturing_column)
normalized_three_month['Energy & Resources Subsector'] = normalized_three_month['Energy & Resources Subsector'].apply(normalize_materials_energy_column)
normalized_three_month['Built Environment Subsector'] = normalized_three_month['Built Environment Subsector'].apply(normalize_built_environment_column)
normalized_three_month['Health Subsector'] = normalized_three_month['Health Subsector'].apply(normalize_health_column)
#normalized_three_month['Hyperscale AI Subsector'] = normalized_three_month['Hyperscale AI Subsector'].apply(normalize_hyperscale_ai_column)
normalized_three_month['Mobility & Logistics Subsector'] = normalized_three_month['Mobility & Logistics Subsector'].apply(normalize_mobility_column)

print(normalized_three_month)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defiend above so reuse that

nasdaq_sign = ''
nasdaq_annotation = normalized_three_month.loc[66]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_three_month.loc[66]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

deeptech_sign = ''
deeptech_annotation = normalized_three_month.loc[66]['DeepTech Index']
deeptech_annotation = return_percentage(deeptech_annotation)
if (deeptech_annotation > 0):
        deeptech_sign = '+'
deeptech_annotation = str(deeptech_annotation)
deeptech_annotation = 'DeepTech Index ' + deeptech_sign + deeptech_annotation + '%'
print('DeepTech Annotation: ', deeptech_annotation)

deeptech_no_mega_caps_sign = ''
deeptech_no_mega_caps_annotation = normalized_three_month.loc[66]['DeepTech Index - No Mega Caps']
deeptech_no_mega_caps_annotation = return_percentage(deeptech_no_mega_caps_annotation)
if (deeptech_no_mega_caps_annotation > 0):
        deeptech_no_mega_caps_sign = '+'
deeptech_no_mega_caps_annotation = str(deeptech_no_mega_caps_annotation)
deeptech_no_mega_caps_annotation = 'DeepTech Index - No Mega Caps ' + deeptech_no_mega_caps_sign + deeptech_no_mega_caps_annotation + '%' 
print('DeepTech Annotation - No Mega Caps: ', deeptech_no_mega_caps_annotation)

newspace_sign = ''
newspace_annotation = normalized_three_month.loc[66]['Space, Aerospace & Defense Subsector']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'Space, Aerospace & Defense Subsector ' + newspace_sign + newspace_annotation + '%'
print('Space, Aerospace & Defense Annotation: ', newspace_annotation)

manufacturing_sign = ''
manufacturing_annotation = normalized_three_month.loc[66]['Manufacturing Subsector']
manufacturing_annotation = return_percentage(manufacturing_annotation)
if (manufacturing_annotation > 0):
        manufacturing_sign = '+'
manufacturing_annotation = str(manufacturing_annotation)
manufacturing_annotation = 'Manufacturing Subsector ' + manufacturing_sign + manufacturing_annotation + '%'
print('Manufacturing Annotation: ', manufacturing_annotation)

materials_energy_sign = ''
materials_energy_annotation = normalized_three_month.loc[66]['Energy & Resources Subsector']
materials_energy_annotation = return_percentage(materials_energy_annotation)
if (materials_energy_annotation > 0):
        materials_energy_sign = '+'
materials_energy_annotation = str(materials_energy_annotation)
materials_energy_annotation = 'Energy & Resources Subsector ' + materials_energy_sign + materials_energy_annotation + '%'
print('Energy & Resources Annotation: ', materials_energy_annotation)

built_environment_sign = ''
built_environment_annotation = normalized_three_month.loc[66]['Built Environment Subsector']
built_environment_annotation = return_percentage(built_environment_annotation)
if (built_environment_annotation > 0):
        built_environment_sign = '+'
built_environment_annotation = str(built_environment_annotation)
built_environment_annotation = 'Built Environment Subsector ' + built_environment_sign + built_environment_annotation + '%'
print('Built Environment Annotation: ', built_environment_annotation)

health_sign = ''
health_annotation = normalized_three_month.loc[66]['Health Subsector']
health_annotation = return_percentage(health_annotation)
if (health_annotation > 0):
        health_sign = '+'
health_annotation = str(health_annotation)
health_annotation = 'Health Subsector ' + health_sign + health_annotation + '%'
print('Health Annotation: ', health_annotation)

#hyperscale_ai_sign = ''
#hyperscale_ai_annotation = normalized_three_month.loc[66]['Hyperscale AI Subsector']
#hyperscale_ai_annotation = return_percentage(hyperscale_ai_annotation)
#if (hyperscale_ai_annotation > 0):
#        hyperscale_ai_sign = '+'
#hyperscale_ai_annotation = str(hyperscale_ai_annotation)
#hyperscale_ai_annotation = 'Hyperscale AI Subsector ' + hyperscale_ai_sign + hyperscale_ai_annotation + '%'
#print('Hyperscale AI Annotation: ', hyperscale_ai_annotation)

mobility_sign = ''
mobility_annotation = normalized_three_month.loc[66]['Mobility & Logistics Subsector']
mobility_annotation = return_percentage(mobility_annotation)
if (mobility_annotation > 0):
        mobility_sign = '+'
mobility_annotation = str(mobility_annotation)
mobility_annotation = 'Mobility & Logistics Subsector ' + mobility_sign + mobility_annotation + '%'
print('Mobility & Logistics Annotation: ', mobility_annotation)

#Actual graphing starts here

#Now chart three month data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Three Month Performance',
  template='plotly_white',
  width = 800,
  height = 600)

#Do large_figure

large_figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Three Month Performance',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Large chart with no title
large_figure_no_title = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd',
  },
  template='plotly_white',
  )

# Build large chart - Deeptech with no mega caps 
large_no_mega_caps_figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index - No Mega Caps'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index - No Mega Caps': '#18a1cd',
  },
  title='Three Month Performance - Deeptech Index Without Mega Cap Companies',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )


# Try a really big graph with Space, Aerospace & Defense subsector called out
large_newspace_figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Space, Aerospace & Defense Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Space, Aerospace & Defense Subsector': '#0492C2'
  },
  title='Three Month Performance - Space, Aerospace & Defense Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Manufacturing subsector called out
large_manufacturing_figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Manufacturing Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Manufacturing Subsector': '#0492C2'
  },
  title='Three Month Performance - Manufacturing Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Energy & resources subsector called out
large_materials_energy_figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Energy & Resources Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Energy & Resources Subsector': '#0492C2'
  },
  title='Three Month Performance - Energy & Resources Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Built Environment subsector called out
large_built_environment_figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Built Environment Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Built Environment Subsector': '#0492C2'
  },
  title='Three Month Performance - Built Environment Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Health subsector called out
large_health_figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Health Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Health Subsector': '#0492C2'
  },
  title='Three Month Performance - Health Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Hyperscale AI subsector called out
#large_hyperscale_ai_figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Hyperscale AI Subsector'],
#  color_discrete_map={
#    'NASDAQ': '#A6A6A6',
#    'S&P500': '#D9D9D9',
#    'DeepTech Index': '#BFBFBF',
#    'Hyperscale AI Subsector': '#0492C2'
#  },
#  title='Three Month Performance - Hyperscale AI Subsector',
#  template='plotly_white',
#  #width = 1600,
#  #height = 1200
#  )

# Try a really big graph with Mobility & Logistics subsector called out
large_mobility_figure = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Mobility & Logistics Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Mobility & Logistics Subsector': '#0492C2'
  },
  title='Three Month Performance - Mobility & Logistics Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

#Mobile version
figure_mobile = px.line(normalized_three_month, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Three Month Performance',
  template='plotly_white',
  width = 320,
  height = 400)

#Try to add annotations
figure_annotations = []
figure_annotations_grey = []
figure_no_mega_caps_annotations = []
mobile_figure_annotations = []
newspace_sector_annotations = []
manufacturing_sector_annotations = []
materials_energy_sector_annotations = []
built_environment_sector_annotations = []
health_sector_annotations = []
#hyperscale_ai_sector_annotations = []
mobility_sector_annotations = []

#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
deeptech_y_shift = 10
#legacy_y_shift = 10

sandp_got_shifted = 'False'
deeptech_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_three_month['NASDAQ'].values[66]/normalized_three_month['S&P500'].values[66])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_three_month['NASDAQ'].values[66]/normalized_three_month['S&P500'].values[66])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20

#Next check NASDAQ vs DeepTech position - use relative % to see if we need to move
if (abs((normalized_three_month['NASDAQ'].values[66]/normalized_three_month['DeepTech Index'].values[66])-1) < 0.02):
  #Set the deeptech_got_shifted flag
  deeptech_got_shifted = 'True'
  if(((normalized_three_month['NASDAQ'].values[66]/normalized_three_month['DeepTech Index'].values[66])-1) > 0):
    #NASDAQ Above DeepTech, shift DeepTech down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust DeepTech by default
      deeptech_y_shift = 0
  else:
    #DeepTech above NASDAQ, shift DeepTech up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = 30
    else:
      deeptech_y_shift = 20


#annotation_one = dict(x=normalized_three_month.iloc[65]['Date'], y=normalized_three_month['NASDAQ'].values[65], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one = dict(x=1.01, y=normalized_three_month['NASDAQ'].values[66], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one_grey = dict(x=1.01, y=normalized_three_month['NASDAQ'].values[66], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#A6A6A6',font_color='#FFFFFF', text=nasdaq_annotation)
mobile_annotation_one = dict(x=1.01, y=normalized_three_month['NASDAQ'].values[66], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, font=dict(size=5))
figure_annotations.append(annotation_one)
figure_annotations_grey.append(annotation_one_grey)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_three_month.iloc[65]['Date'], y=normalized_three_month['S&P500'].values[65], xref='x', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_three_month['S&P500'].values[66], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two_grey = dict(x=1.01, y=normalized_three_month['S&P500'].values[66], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#D9D9D9',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_three_month['S&P500'].values[66], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
figure_annotations_grey.append(annotation_two_grey)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_three_month.iloc[65]['Date'], y=normalized_three_month['PV New Space'].values[65], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_three_month['DeepTech Index'].values[66], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation)
annotation_three_grey = dict(x=1.01, y=normalized_three_month['DeepTech Index'].values[66], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#BFBFBF',font_color='#FFFFFF', text=deeptech_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_three_month['DeepTech Index'].values[66], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
figure_annotations_grey.append(annotation_three_grey)
mobile_figure_annotations.append(mobile_annotation_three)

annotation_four = dict(x=1.01, y=normalized_three_month['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_three_month['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation, font=dict(size=5))
figure_no_mega_caps_annotations.append(annotation_one)
figure_no_mega_caps_annotations.append(annotation_two)
figure_no_mega_caps_annotations.append(annotation_four)
#sector_mobile_figure_annotations.append(mobile_annotation_four)

annotation_five = dict(x=1.01, y=normalized_three_month['Space, Aerospace & Defense Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=newspace_annotation)
newspace_sector_annotations.append(annotation_five)

annotation_six = dict(x=1.01, y=normalized_three_month['Manufacturing Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=manufacturing_annotation)
manufacturing_sector_annotations.append(annotation_six)

annotation_seven = dict(x=1.01, y=normalized_three_month['Energy & Resources Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=materials_energy_annotation)
materials_energy_sector_annotations.append(annotation_seven)

annotation_eight = dict(x=1.01, y=normalized_three_month['Built Environment Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=built_environment_annotation)
built_environment_sector_annotations.append(annotation_eight)

annotation_nine = dict(x=1.01, y=normalized_three_month['Health Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=health_annotation)
health_sector_annotations.append(annotation_nine)

#annotation_10 = dict(x=1.01, y=normalized_three_month['Hyperscale AI Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=hyperscale_ai_annotation)
#hyperscale_ai_sector_annotations.append(annotation_10)

annotation_11 = dict(x=1.01, y=normalized_three_month['Mobility & Logistics Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=mobility_annotation)
mobility_sector_annotations.append(annotation_11)

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance (%)')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Now do for large figure
large_figure.update_layout(annotations=figure_annotations)
large_figure.update_annotations(clicktoshow='onoff')
large_figure.update_annotations(xanchor='left')
large_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure.update_layout(hovermode='closest')
large_figure.update_layout(yaxis_title='Relative Performance (%)')
large_figure.update_layout(margin=dict(r=170))
large_figure.update_yaxes(fixedrange=True)

#Now do for large_figure_no_title
large_figure_no_title.update_layout(annotations=figure_annotations)
large_figure_no_title.update_annotations(clicktoshow='onoff')
large_figure_no_title.update_annotations(xanchor='left')
large_figure_no_title.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure_no_title.update_layout(hovermode='closest')
large_figure_no_title.update_layout(yaxis_title='Relative Performance (%)')
large_figure_no_title.update_layout(margin=dict(r=170))
large_figure_no_title.update_yaxes(fixedrange=True)

#Now do for large_no_mega_caps_figure
#figure_no_mega_caps_annotations = annotation_one + annotation_two + figure_no_mega_caps_annotations
large_no_mega_caps_figure.update_layout(annotations=figure_no_mega_caps_annotations)
large_no_mega_caps_figure.update_annotations(clicktoshow='onoff')
large_no_mega_caps_figure.update_annotations(xanchor='left')
large_no_mega_caps_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_no_mega_caps_figure.update_layout(hovermode='closest')
large_no_mega_caps_figure.update_layout(yaxis_title='Relative Performance (%)')
large_no_mega_caps_figure.update_layout(margin=dict(r=270))
large_no_mega_caps_figure.update_yaxes(fixedrange=True)


# And for all other figures - starting with Newspace sector
newspace_annotations = figure_annotations_grey + newspace_sector_annotations
large_newspace_figure.update_layout(annotations=newspace_annotations)
large_newspace_figure.update_annotations(clicktoshow='onoff')
large_newspace_figure.update_annotations(xanchor='left')
large_newspace_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_newspace_figure.update_layout(hovermode='closest')
large_newspace_figure.update_layout(yaxis_title='Relative Performance (%)')
large_newspace_figure.update_layout(margin=dict(r=200))
large_newspace_figure.update_yaxes(fixedrange=True)

# Now Manufacturing sector
manufacturing_annotations = figure_annotations_grey + manufacturing_sector_annotations
large_manufacturing_figure.update_layout(annotations=manufacturing_annotations)
large_manufacturing_figure.update_annotations(clicktoshow='onoff')
large_manufacturing_figure.update_annotations(xanchor='left')
large_manufacturing_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_manufacturing_figure.update_layout(hovermode='closest')
large_manufacturing_figure.update_layout(yaxis_title='Relative Performance (%)')
large_manufacturing_figure.update_layout(margin=dict(r=275))
large_manufacturing_figure.update_yaxes(fixedrange=True)

# Now Energy & Resources sector
materials_energy_annotations = figure_annotations_grey + materials_energy_sector_annotations
large_materials_energy_figure.update_layout(annotations=materials_energy_annotations)
large_materials_energy_figure.update_annotations(clicktoshow='onoff')
large_materials_energy_figure.update_annotations(xanchor='left')
large_materials_energy_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_materials_energy_figure.update_layout(hovermode='closest')
large_materials_energy_figure.update_layout(yaxis_title='Relative Performance (%)')
large_materials_energy_figure.update_layout(margin=dict(r=275))
large_materials_energy_figure.update_yaxes(fixedrange=True)

# Now Built Environment sector
built_environment_annotations = figure_annotations_grey + built_environment_sector_annotations
large_built_environment_figure.update_layout(annotations=built_environment_annotations)
large_built_environment_figure.update_annotations(clicktoshow='onoff')
large_built_environment_figure.update_annotations(xanchor='left')
large_built_environment_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_built_environment_figure.update_layout(hovermode='closest')
large_built_environment_figure.update_layout(yaxis_title='Relative Performance (%)')
large_built_environment_figure.update_layout(margin=dict(r=275))
large_built_environment_figure.update_yaxes(fixedrange=True)

# Now Health sector
health_annotations = figure_annotations_grey + health_sector_annotations
large_health_figure.update_layout(annotations=health_annotations)
large_health_figure.update_annotations(clicktoshow='onoff')
large_health_figure.update_annotations(xanchor='left')
large_health_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_health_figure.update_layout(hovermode='closest')
large_health_figure.update_layout(yaxis_title='Relative Performance (%)')
large_health_figure.update_layout(margin=dict(r=275))
large_health_figure.update_yaxes(fixedrange=True)

# Now Hyperscale AI sector
#hyperscale_ai_annotations = figure_annotations_grey + hyperscale_ai_sector_annotations
#large_hyperscale_ai_figure.update_layout(annotations=hyperscale_ai_annotations)
#large_hyperscale_ai_figure.update_annotations(clicktoshow='onoff')
#large_hyperscale_ai_figure.update_annotations(xanchor='left')
#large_hyperscale_ai_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#large_hyperscale_ai_figure.update_layout(hovermode='closest')
#large_hyperscale_ai_figure.update_layout(yaxis_title='Relative Performance')
#large_hyperscale_ai_figure.update_layout(margin=dict(r=275))
#large_hyperscale_ai_figure.update_yaxes(fixedrange=True)

# Now Mobility & Logistics sector
mobility_annotations = figure_annotations_grey + mobility_sector_annotations
large_mobility_figure.update_layout(annotations=mobility_annotations)
large_mobility_figure.update_annotations(clicktoshow='onoff')
large_mobility_figure.update_annotations(xanchor='left')
large_mobility_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_mobility_figure.update_layout(hovermode='closest')
large_mobility_figure.update_layout(yaxis_title='Relative Performance (%)')
large_mobility_figure.update_layout(margin=dict(r=275))
large_mobility_figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure_no_title.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_no_mega_caps_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_newspace_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_manufacturing_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_materials_energy_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_built_environment_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_health_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
#large_hyperscale_ai_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_mobility_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#don't show graphs in cron version in case it hangs the script
#Show while testing...
#figure.show(config=graph_config)
figure.write_html('testing_deeptech_three_month_graph.html', config=graph_config)
large_figure.write_html('testing_deeptech_three_month_graph_large.html', config=graph_config)
large_figure_no_title.write_html('testing_deeptech_three_month_graph_large_no_title.html', config=graph_config)
large_no_mega_caps_figure.write_html('testing_deeptech_three_month_graph_no_mega_caps_large.html', config=graph_config)
large_newspace_figure.write_html('testing_deeptech_with_space_aerospace_defense_sector_three_month_graph_large.html', config=graph_config)
large_manufacturing_figure.write_html('testing_deeptech_with_manufacturing_sector_three_month_graph_large.html', config=graph_config)
large_materials_energy_figure.write_html('testing_deeptech_with_energy_and_resources_sector_three_month_graph_large.html', config=graph_config)
large_built_environment_figure.write_html('testing_deeptech_with_built_environment_sector_three_month_graph_large.html', config=graph_config)
large_health_figure.write_html('testing_deeptech_with_health_sector_three_month_graph_large.html', config=graph_config)
#large_hyperscale_ai_figure.write_html('testing_deeptech_with_hyperscale_ai_sector_three_month_graph_large.html', config=graph_config)
large_mobility_figure.write_html('testing_deeptech_with_mobility_sector_three_month_graph_large.html', config=graph_config)

#Do exactly the same for mobile - except for annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance (%)', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('testing_deeptech_three_month_graph_mobile.html', config=graph_config)

##
#
# Now do 1 Year graph
#
##

#Get the value of each starting point
deeptech_start = one_year_data.loc[0]['DeepTech Index']
deeptech_no_mega_caps_start = one_year_data.loc[0]['DeepTech Index - No Mega Caps']
nasdaq_start = one_year_data.loc[0]['NASDAQ']
sandp_start = one_year_data.loc[0]['S&P500']
newspace_start = one_year_data.loc[0]['Space, Aerospace & Defense Subsector']
manufacturing_start = one_year_data.loc[0]['Manufacturing Subsector']
materials_energy_start = one_year_data.loc[0]['Energy & Resources Subsector']
built_environment_start = one_year_data.loc[0]['Built Environment Subsector']
health_start = one_year_data.loc[0]['Health Subsector']
#hyperscale_ai_start = one_year_data.loc[0]['Hyperscale AI Subsector']
mobility_start = one_year_data.loc[0]['Mobility & Logistics Subsector']

normalized_one_year = one_year_data

normalized_one_year['NASDAQ'] = normalized_one_year['NASDAQ'].apply(normalize_nasdaq_column)
normalized_one_year['S&P500'] = normalized_one_year['S&P500'].apply(normalize_sandp_column)
normalized_one_year['DeepTech Index'] = normalized_one_year['DeepTech Index'].apply(normalize_deeptech_column)
normalized_one_year['DeepTech Index - No Mega Caps'] = normalized_one_year['DeepTech Index - No Mega Caps'].apply(normalize_deeptech_no_mega_caps_column)
normalized_one_year['Space, Aerospace & Defense Subsector'] = normalized_one_year['Space, Aerospace & Defense Subsector'].apply(normalize_newspace_column)
normalized_one_year['Manufacturing Subsector'] = normalized_one_year['Manufacturing Subsector'].apply(normalize_manufacturing_column)
normalized_one_year['Energy & Resources Subsector'] = normalized_one_year['Energy & Resources Subsector'].apply(normalize_materials_energy_column)
normalized_one_year['Built Environment Subsector'] = normalized_one_year['Built Environment Subsector'].apply(normalize_built_environment_column)
normalized_one_year['Health Subsector'] = normalized_one_year['Health Subsector'].apply(normalize_health_column)
#normalized_one_year['Hyperscale AI Subsector'] = normalized_one_year['Hyperscale AI Subsector'].apply(normalize_hyperscale_ai_column)
normalized_one_year['Mobility & Logistics Subsector'] = normalized_one_year['Mobility & Logistics Subsector'].apply(normalize_mobility_column)

print(normalized_one_year)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defiend above so reuse that

nasdaq_sign = ''
nasdaq_annotation = normalized_one_year.loc[251]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_one_year.loc[251]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

deeptech_sign = ''
deeptech_annotation = normalized_one_year.loc[251]['DeepTech Index']
deeptech_annotation = return_percentage(deeptech_annotation)
if (deeptech_annotation > 0):
        deeptech_sign = '+'
deeptech_annotation = str(deeptech_annotation)
deeptech_annotation = 'DeepTech Index ' + deeptech_sign + deeptech_annotation + '%'
print('DeepTech Annotation: ', deeptech_annotation)

deeptech_no_mega_caps_sign = ''
deeptech_no_mega_caps_annotation = normalized_one_year.loc[251]['DeepTech Index - No Mega Caps']
deeptech_no_mega_caps_annotation = return_percentage(deeptech_no_mega_caps_annotation)
if (deeptech_no_mega_caps_annotation > 0):
        deeptech_no_mega_caps_sign = '+'
deeptech_no_mega_caps_annotation = str(deeptech_no_mega_caps_annotation)
deeptech_no_mega_caps_annotation = 'DeepTech Index - No Mega Caps ' + deeptech_no_mega_caps_sign + deeptech_no_mega_caps_annotation + '%' 
print('DeepTech Annotation - No Mega Caps: ', deeptech_no_mega_caps_annotation)

newspace_sign = ''
newspace_annotation = normalized_one_year.loc[251]['Space, Aerospace & Defense Subsector']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'Space, Aerospace & Defense Subsector ' + newspace_sign + newspace_annotation + '%'
print('Space, Aerospace & Defense Annotation: ', newspace_annotation)

manufacturing_sign = ''
manufacturing_annotation = normalized_one_year.loc[251]['Manufacturing Subsector']
manufacturing_annotation = return_percentage(manufacturing_annotation)
if (manufacturing_annotation > 0):
        manufacturing_sign = '+'
manufacturing_annotation = str(manufacturing_annotation)
manufacturing_annotation = 'Manufacturing Subsector ' + manufacturing_sign + manufacturing_annotation + '%'
print('Manufacturing Annotation: ', manufacturing_annotation)

materials_energy_sign = ''
materials_energy_annotation = normalized_one_year.loc[251]['Energy & Resources Subsector']
materials_energy_annotation = return_percentage(materials_energy_annotation)
if (materials_energy_annotation > 0):
        materials_energy_sign = '+'
materials_energy_annotation = str(materials_energy_annotation)
materials_energy_annotation = 'Energy & Resources Subsector ' + materials_energy_sign + materials_energy_annotation + '%'
print('Energy & Resources Annotation: ', materials_energy_annotation)

built_environment_sign = ''
built_environment_annotation = normalized_one_year.loc[251]['Built Environment Subsector']
built_environment_annotation = return_percentage(built_environment_annotation)
if (built_environment_annotation > 0):
        built_environment_sign = '+'
built_environment_annotation = str(built_environment_annotation)
built_environment_annotation = 'Built Environment Subsector ' + built_environment_sign + built_environment_annotation + '%'
print('Built Environment Annotation: ', built_environment_annotation)

health_sign = ''
health_annotation = normalized_one_year.loc[251]['Health Subsector']
health_annotation = return_percentage(health_annotation)
if (health_annotation > 0):
        health_sign = '+'
health_annotation = str(health_annotation)
health_annotation = 'Health Subsector ' + health_sign + health_annotation + '%'
print('Health Annotation: ', health_annotation)

#hyperscale_ai_sign = ''
#hyperscale_ai_annotation = normalized_one_year.loc[251]['Hyperscale AI Subsector']
#hyperscale_ai_annotation = return_percentage(hyperscale_ai_annotation)
#if (hyperscale_ai_annotation > 0):
#        hyperscale_ai_sign = '+'
#hyperscale_ai_annotation = str(hyperscale_ai_annotation)
#hyperscale_ai_annotation = 'Hyperscale AI Subsector ' + hyperscale_ai_sign + hyperscale_ai_annotation + '%'
#print('Hyperscale AI Annotation: ', hyperscale_ai_annotation)

mobility_sign = ''
mobility_annotation = normalized_one_year.loc[251]['Mobility & Logistics Subsector']
mobility_annotation = return_percentage(mobility_annotation)
if (mobility_annotation > 0):
        mobility_sign = '+'
mobility_annotation = str(mobility_annotation)
mobility_annotation = 'Mobility & Logistics Subsector ' + mobility_sign + mobility_annotation + '%'
print('Mobility & Logistics Annotation: ', mobility_annotation)

#Actual graphing starts here

#Now chart one year data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='One Year Performance',
  template='plotly_white',
  width = 800,
  height = 600)

#Do large figure
large_figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='One Year Performance',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Large chart with no title
large_figure_no_title = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd',
  },
  template='plotly_white',
  )

# Build large chart - Deeptech with no mega caps 
large_no_mega_caps_figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index - No Mega Caps'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index - No Mega Caps': '#18a1cd',
  },
  title='One Year Performance - Deeptech Index Without Mega Cap Companies',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )


# Try a really big graph with Space, Aerospace & Defense subsector called out
large_newspace_figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Space, Aerospace & Defense Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Space, Aerospace & Defense Subsector': '#0492C2'
  },
  title='One Year Performance - Space, Aerospace & Defense Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Manufacturing subsector called out
large_manufacturing_figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Manufacturing Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Manufacturing Subsector': '#0492C2'
  },
  title='One Year Performance - Manufacturing Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Energy & resources subsector called out
large_materials_energy_figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Energy & Resources Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Energy & Resources Subsector': '#0492C2'
  },
  title='One Year Performance - Energy & Resources Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Built Environment subsector called out
large_built_environment_figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Built Environment Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Built Environment Subsector': '#0492C2'
  },
  title='One Year Performance - Built Environment Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Health subsector called out
large_health_figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Health Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Health Subsector': '#0492C2'
  },
  title='One Year Performance - Health Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Hyperscale AI subsector called out
#large_hyperscale_ai_figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Hyperscale AI Subsector'],
#  color_discrete_map={
#    'NASDAQ': '#A6A6A6',
#    'S&P500': '#D9D9D9',
#    'DeepTech Index': '#BFBFBF',
#    'Hyperscale AI Subsector': '#0492C2'
#  },
#  title='One Year Performance - Hyperscale AI Subsector',
#  template='plotly_white',
#  #width = 1600,
#  #height = 1200
#  )

# Try a really big graph with Mobility & Logistics subsector called out
large_mobility_figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Mobility & Logistics Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Mobility & Logistics Subsector': '#0492C2'
  },
  title='One Year Performance - Mobility & Logistics Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

#Mobile version
figure_mobile = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='One Year Performance',
  template='plotly_white',
  width = 320,
  height = 400)

#Try to add annotations
figure_annotations = []
figure_annotations_grey = []
figure_no_mega_caps_annotations = []
mobile_figure_annotations = []
newspace_sector_annotations = []
manufacturing_sector_annotations = []
materials_energy_sector_annotations = []
built_environment_sector_annotations = []
health_sector_annotations = []
#hyperscale_ai_sector_annotations = []
mobility_sector_annotations = []

#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
deeptech_y_shift = 10
#legacy_y_shift = 10

sandp_got_shifted = 'False'
deeptech_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_one_year['NASDAQ'].values[251]/normalized_one_year['S&P500'].values[251])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_one_year['NASDAQ'].values[251]/normalized_one_year['S&P500'].values[251])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20

#Next check NASDAQ vs DeepTech position - use relative % to see if we need to move
if (abs((normalized_one_year['NASDAQ'].values[251]/normalized_one_year['DeepTech Index'].values[251])-1) < 0.02):
  #Set the deeptech_got_shifted flag
  deeptech_got_shifted = 'True'
  if(((normalized_one_year['NASDAQ'].values[251]/normalized_one_year['DeepTech Index'].values[251])-1) > 0):
    #NASDAQ Above DeepTech, shift DeepTech down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust DeepTech by default
      deeptech_y_shift = 0
  else:
    #DeepTech above NASDAQ, shift DeepTech up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = 30
    else:
      deeptech_y_shift = 20


#annotation_one = dict(x=normalized_three_month.iloc[65]['Date'], y=normalized_three_month['NASDAQ'].values[65], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one = dict(x=1.01, y=normalized_one_year['NASDAQ'].values[251], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one_grey = dict(x=1.01, y=normalized_one_year['NASDAQ'].values[251], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#A6A6A6',font_color='#FFFFFF', text=nasdaq_annotation)
mobile_annotation_one = dict(x=1.01, y=normalized_one_year['NASDAQ'].values[251], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, font=dict(size=5))
figure_annotations.append(annotation_one)
figure_annotations_grey.append(annotation_one_grey)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_three_month.iloc[65]['Date'], y=normalized_three_month['S&P500'].values[65], xref='x', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_one_year['S&P500'].values[251], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two_grey = dict(x=1.01, y=normalized_one_year['S&P500'].values[251], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#D9D9D9',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_one_year['S&P500'].values[251], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
figure_annotations_grey.append(annotation_two_grey)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_three_month.iloc[65]['Date'], y=normalized_three_month['PV New Space'].values[65], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_one_year['DeepTech Index'].values[251], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation)
annotation_three_grey = dict(x=1.01, y=normalized_one_year['DeepTech Index'].values[251], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#BFBFBF',font_color='#FFFFFF', text=deeptech_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_one_year['DeepTech Index'].values[251], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
figure_annotations_grey.append(annotation_three_grey)
mobile_figure_annotations.append(mobile_annotation_three)

annotation_four = dict(x=1.01, y=normalized_one_year['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_one_year['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation, font=dict(size=5))
figure_no_mega_caps_annotations.append(annotation_one)
figure_no_mega_caps_annotations.append(annotation_two)
figure_no_mega_caps_annotations.append(annotation_four)
#sector_mobile_figure_annotations.append(mobile_annotation_four)

annotation_five = dict(x=1.01, y=normalized_one_year['Space, Aerospace & Defense Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=newspace_annotation)
newspace_sector_annotations.append(annotation_five)

annotation_six = dict(x=1.01, y=normalized_one_year['Manufacturing Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=manufacturing_annotation)
manufacturing_sector_annotations.append(annotation_six)

annotation_seven = dict(x=1.01, y=normalized_one_year['Energy & Resources Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=materials_energy_annotation)
materials_energy_sector_annotations.append(annotation_seven)

annotation_eight = dict(x=1.01, y=normalized_one_year['Built Environment Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=built_environment_annotation)
built_environment_sector_annotations.append(annotation_eight)

annotation_nine = dict(x=1.01, y=normalized_one_year['Health Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=health_annotation)
health_sector_annotations.append(annotation_nine)

#annotation_10 = dict(x=1.01, y=normalized_one_year['Hyperscale AI Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=hyperscale_ai_annotation)
#hyperscale_ai_sector_annotations.append(annotation_10)

annotation_11 = dict(x=1.01, y=normalized_one_year['Mobility & Logistics Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=mobility_annotation)
mobility_sector_annotations.append(annotation_11)

##################

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance (%)')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Now do for large figure
large_figure.update_layout(annotations=figure_annotations)
large_figure.update_annotations(clicktoshow='onoff')
large_figure.update_annotations(xanchor='left')
large_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure.update_layout(hovermode='closest')
large_figure.update_layout(yaxis_title='Relative Performance (%)')
large_figure.update_layout(margin=dict(r=170))
large_figure.update_yaxes(fixedrange=True)

#Now do for large_figure_no_title
large_figure_no_title.update_layout(annotations=figure_annotations)
large_figure_no_title.update_annotations(clicktoshow='onoff')
large_figure_no_title.update_annotations(xanchor='left')
large_figure_no_title.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure_no_title.update_layout(hovermode='closest')
large_figure_no_title.update_layout(yaxis_title='Relative Performance (%)')
large_figure_no_title.update_layout(margin=dict(r=170))
large_figure_no_title.update_yaxes(fixedrange=True)

#Now do for large_no_mega_caps_figure
#figure_no_mega_caps_annotations = annotation_one + annotation_two + figure_no_mega_caps_annotations
large_no_mega_caps_figure.update_layout(annotations=figure_no_mega_caps_annotations)
large_no_mega_caps_figure.update_annotations(clicktoshow='onoff')
large_no_mega_caps_figure.update_annotations(xanchor='left')
large_no_mega_caps_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_no_mega_caps_figure.update_layout(hovermode='closest')
large_no_mega_caps_figure.update_layout(yaxis_title='Relative Performance (%)')
large_no_mega_caps_figure.update_layout(margin=dict(r=270))
large_no_mega_caps_figure.update_yaxes(fixedrange=True)


# And for all other figures - starting with Newspace sector
newspace_annotations = figure_annotations_grey + newspace_sector_annotations
large_newspace_figure.update_layout(annotations=newspace_annotations)
large_newspace_figure.update_annotations(clicktoshow='onoff')
large_newspace_figure.update_annotations(xanchor='left')
large_newspace_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_newspace_figure.update_layout(hovermode='closest')
large_newspace_figure.update_layout(yaxis_title='Relative Performance (%)')
large_newspace_figure.update_layout(margin=dict(r=200))
large_newspace_figure.update_yaxes(fixedrange=True)

# Now Manufacturing sector
manufacturing_annotations = figure_annotations_grey + manufacturing_sector_annotations
large_manufacturing_figure.update_layout(annotations=manufacturing_annotations)
large_manufacturing_figure.update_annotations(clicktoshow='onoff')
large_manufacturing_figure.update_annotations(xanchor='left')
large_manufacturing_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_manufacturing_figure.update_layout(hovermode='closest')
large_manufacturing_figure.update_layout(yaxis_title='Relative Performance (%)')
large_manufacturing_figure.update_layout(margin=dict(r=275))
large_manufacturing_figure.update_yaxes(fixedrange=True)

# Now Energy & Resources sector
materials_energy_annotations = figure_annotations_grey + materials_energy_sector_annotations
large_materials_energy_figure.update_layout(annotations=materials_energy_annotations)
large_materials_energy_figure.update_annotations(clicktoshow='onoff')
large_materials_energy_figure.update_annotations(xanchor='left')
large_materials_energy_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_materials_energy_figure.update_layout(hovermode='closest')
large_materials_energy_figure.update_layout(yaxis_title='Relative Performance (%)')
large_materials_energy_figure.update_layout(margin=dict(r=275))
large_materials_energy_figure.update_yaxes(fixedrange=True)

# Now Built Environment sector
built_environment_annotations = figure_annotations_grey + built_environment_sector_annotations
large_built_environment_figure.update_layout(annotations=built_environment_annotations)
large_built_environment_figure.update_annotations(clicktoshow='onoff')
large_built_environment_figure.update_annotations(xanchor='left')
large_built_environment_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_built_environment_figure.update_layout(hovermode='closest')
large_built_environment_figure.update_layout(yaxis_title='Relative Performance (%)')
large_built_environment_figure.update_layout(margin=dict(r=275))
large_built_environment_figure.update_yaxes(fixedrange=True)

# Now Health sector
health_annotations = figure_annotations_grey + health_sector_annotations
large_health_figure.update_layout(annotations=health_annotations)
large_health_figure.update_annotations(clicktoshow='onoff')
large_health_figure.update_annotations(xanchor='left')
large_health_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_health_figure.update_layout(hovermode='closest')
large_health_figure.update_layout(yaxis_title='Relative Performance (%)')
large_health_figure.update_layout(margin=dict(r=275))
large_health_figure.update_yaxes(fixedrange=True)

# Now Hyperscale AI sector
#hyperscale_ai_annotations = figure_annotations_grey + hyperscale_ai_sector_annotations
#large_hyperscale_ai_figure.update_layout(annotations=hyperscale_ai_annotations)
#large_hyperscale_ai_figure.update_annotations(clicktoshow='onoff')
#large_hyperscale_ai_figure.update_annotations(xanchor='left')
#large_hyperscale_ai_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#large_hyperscale_ai_figure.update_layout(hovermode='closest')
#large_hyperscale_ai_figure.update_layout(yaxis_title='Relative Performance')
#large_hyperscale_ai_figure.update_layout(margin=dict(r=275))
#large_hyperscale_ai_figure.update_yaxes(fixedrange=True)

# Now Mobility & Logistics sector
mobility_annotations = figure_annotations_grey + mobility_sector_annotations
large_mobility_figure.update_layout(annotations=mobility_annotations)
large_mobility_figure.update_annotations(clicktoshow='onoff')
large_mobility_figure.update_annotations(xanchor='left')
large_mobility_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_mobility_figure.update_layout(hovermode='closest')
large_mobility_figure.update_layout(yaxis_title='Relative Performance (%)')
large_mobility_figure.update_layout(margin=dict(r=275))
large_mobility_figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure_no_title.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_no_mega_caps_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_newspace_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_manufacturing_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_materials_energy_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_built_environment_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_health_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
#large_hyperscale_ai_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_mobility_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#don't show graphs in cron version in case it hangs the script
#Show while testing...
#figure.show(config=graph_config)
figure.write_html('testing_deeptech_one_year_graph.html', config=graph_config)
large_figure.write_html('testing_deeptech_one_year_graph_large.html', config=graph_config)
large_figure_no_title.write_html('testing_deeptech_one_year_graph_large_no_title.html', config=graph_config)
large_no_mega_caps_figure.write_html('testing_deeptech_one_year_graph_no_mega_caps_large.html', config=graph_config)
large_newspace_figure.write_html('testing_deeptech_with_space_aerospace_defense_sector_one_year_graph_large.html', config=graph_config)
large_manufacturing_figure.write_html('testing_deeptech_with_manufacturing_sector_one_year_graph_large.html', config=graph_config)
large_materials_energy_figure.write_html('testing_deeptech_with_energy_and_resources_sector_one_year_graph_large.html', config=graph_config)
large_built_environment_figure.write_html('testing_deeptech_with_built_environment_sector_one_year_graph_large.html', config=graph_config)
large_health_figure.write_html('testing_deeptech_with_health_sector_one_year_graph_large.html', config=graph_config)
#large_hyperscale_ai_figure.write_html('testing_deeptech_with_hyperscale_ai_sector_one_year_graph_large.html', config=graph_config)
large_mobility_figure.write_html('testing_deeptech_with_mobility_sector_one_year_graph_large.html', config=graph_config)

#Do exactly the same for mobile - except for annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance (%)', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('testing_deeptech_one_year_graph_mobile.html', config=graph_config)


##
#
# Now do 3 Year graph
#
##

#Get the value of each starting point
deeptech_start = three_year_data.loc[0]['DeepTech Index']
deeptech_no_mega_caps_start = three_year_data.loc[0]['DeepTech Index - No Mega Caps']
nasdaq_start = three_year_data.loc[0]['NASDAQ']
sandp_start = three_year_data.loc[0]['S&P500']
newspace_start = three_year_data.loc[0]['Space, Aerospace & Defense Subsector']
manufacturing_start = three_year_data.loc[0]['Manufacturing Subsector']
materials_energy_start = three_year_data.loc[0]['Energy & Resources Subsector']
built_environment_start = three_year_data.loc[0]['Built Environment Subsector']
health_start = three_year_data.loc[0]['Health Subsector']
#hyperscale_ai_start = one_year_data.loc[0]['Hyperscale AI Subsector']
mobility_start = three_year_data.loc[0]['Mobility & Logistics Subsector']

normalized_three_year = three_year_data

normalized_three_year['NASDAQ'] = normalized_three_year['NASDAQ'].apply(normalize_nasdaq_column)
normalized_three_year['S&P500'] = normalized_three_year['S&P500'].apply(normalize_sandp_column)
normalized_three_year['DeepTech Index'] = normalized_three_year['DeepTech Index'].apply(normalize_deeptech_column)
normalized_three_year['DeepTech Index - No Mega Caps'] = normalized_three_year['DeepTech Index - No Mega Caps'].apply(normalize_deeptech_no_mega_caps_column)
normalized_three_year['Space, Aerospace & Defense Subsector'] = normalized_three_year['Space, Aerospace & Defense Subsector'].apply(normalize_newspace_column)
normalized_three_year['Manufacturing Subsector'] = normalized_three_year['Manufacturing Subsector'].apply(normalize_manufacturing_column)
normalized_three_year['Energy & Resources Subsector'] = normalized_three_year['Energy & Resources Subsector'].apply(normalize_materials_energy_column)
normalized_three_year['Built Environment Subsector'] = normalized_three_year['Built Environment Subsector'].apply(normalize_built_environment_column)
normalized_three_year['Health Subsector'] = normalized_three_year['Health Subsector'].apply(normalize_health_column)
#normalized_one_year['Hyperscale AI Subsector'] = normalized_one_year['Hyperscale AI Subsector'].apply(normalize_hyperscale_ai_column)
normalized_three_year['Mobility & Logistics Subsector'] = normalized_three_year['Mobility & Logistics Subsector'].apply(normalize_mobility_column)

print(normalized_one_year)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defiend above so reuse that

nasdaq_sign = ''
nasdaq_annotation = normalized_three_year.loc[755]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_three_year.loc[755]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

deeptech_sign = ''
deeptech_annotation = normalized_three_year.loc[755]['DeepTech Index']
deeptech_annotation = return_percentage(deeptech_annotation)
if (deeptech_annotation > 0):
        deeptech_sign = '+'
deeptech_annotation = str(deeptech_annotation)
deeptech_annotation = 'DeepTech Index ' + deeptech_sign + deeptech_annotation + '%'
print('DeepTech Annotation: ', deeptech_annotation)

deeptech_no_mega_caps_sign = ''
deeptech_no_mega_caps_annotation = normalized_three_year.loc[755]['DeepTech Index - No Mega Caps']
deeptech_no_mega_caps_annotation = return_percentage(deeptech_no_mega_caps_annotation)
if (deeptech_no_mega_caps_annotation > 0):
        deeptech_no_mega_caps_sign = '+'
deeptech_no_mega_caps_annotation = str(deeptech_no_mega_caps_annotation)
deeptech_no_mega_caps_annotation = 'DeepTech Index - No Mega Caps ' + deeptech_no_mega_caps_sign + deeptech_no_mega_caps_annotation + '%' 
print('DeepTech Annotation - No Mega Caps: ', deeptech_no_mega_caps_annotation)

newspace_sign = ''
newspace_annotation = normalized_three_year.loc[755]['Space, Aerospace & Defense Subsector']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'Space, Aerospace & Defense Subsector ' + newspace_sign + newspace_annotation + '%'
print('Space, Aerospace & Defense Annotation: ', newspace_annotation)

manufacturing_sign = ''
manufacturing_annotation = normalized_three_year.loc[755]['Manufacturing Subsector']
manufacturing_annotation = return_percentage(manufacturing_annotation)
if (manufacturing_annotation > 0):
        manufacturing_sign = '+'
manufacturing_annotation = str(manufacturing_annotation)
manufacturing_annotation = 'Manufacturing Subsector ' + manufacturing_sign + manufacturing_annotation + '%'
print('Manufacturing Annotation: ', manufacturing_annotation)

materials_energy_sign = ''
materials_energy_annotation = normalized_three_year.loc[755]['Energy & Resources Subsector']
materials_energy_annotation = return_percentage(materials_energy_annotation)
if (materials_energy_annotation > 0):
        materials_energy_sign = '+'
materials_energy_annotation = str(materials_energy_annotation)
materials_energy_annotation = 'Energy & Resources Subsector ' + materials_energy_sign + materials_energy_annotation + '%'
print('Energy & Resources Annotation: ', materials_energy_annotation)

built_environment_sign = ''
built_environment_annotation = normalized_three_year.loc[755]['Built Environment Subsector']
built_environment_annotation = return_percentage(built_environment_annotation)
if (built_environment_annotation > 0):
        built_environment_sign = '+'
built_environment_annotation = str(built_environment_annotation)
built_environment_annotation = 'Built Environment Subsector ' + built_environment_sign + built_environment_annotation + '%'
print('Built Environment Annotation: ', built_environment_annotation)

health_sign = ''
health_annotation = normalized_three_year.loc[755]['Health Subsector']
health_annotation = return_percentage(health_annotation)
if (health_annotation > 0):
        health_sign = '+'
health_annotation = str(health_annotation)
health_annotation = 'Health Subsector ' + health_sign + health_annotation + '%'
print('Health Annotation: ', health_annotation)

#hyperscale_ai_sign = ''
#hyperscale_ai_annotation = normalized_one_year.loc[251]['Hyperscale AI Subsector']
#hyperscale_ai_annotation = return_percentage(hyperscale_ai_annotation)
#if (hyperscale_ai_annotation > 0):
#        hyperscale_ai_sign = '+'
#hyperscale_ai_annotation = str(hyperscale_ai_annotation)
#hyperscale_ai_annotation = 'Hyperscale AI Subsector ' + hyperscale_ai_sign + hyperscale_ai_annotation + '%'
#print('Hyperscale AI Annotation: ', hyperscale_ai_annotation)

mobility_sign = ''
mobility_annotation = normalized_three_year.loc[755]['Mobility & Logistics Subsector']
mobility_annotation = return_percentage(mobility_annotation)
if (mobility_annotation > 0):
        mobility_sign = '+'
mobility_annotation = str(mobility_annotation)
mobility_annotation = 'Mobility & Logistics Subsector ' + mobility_sign + mobility_annotation + '%'
print('Mobility & Logistics Annotation: ', mobility_annotation)

#Actual graphing starts here

#Now chart three year data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Three Year Performance',
  template='plotly_white',
  width = 800,
  height = 600)

#Do large figure
large_figure = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Three Year Performance',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Large chart with no title
large_figure_no_title = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd',
  },
  template='plotly_white',
  )

# Build large chart - Deeptech with no mega caps 
large_no_mega_caps_figure = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index - No Mega Caps'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index - No Mega Caps': '#18a1cd',
  },
  title='Three Year Performance - Deeptech Index Without Mega Cap Companies',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )


# Try a really big graph with Space, Aerospace & Defense subsector called out
large_newspace_figure = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Space, Aerospace & Defense Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Space, Aerospace & Defense Subsector': '#0492C2'
  },
  title='Three Year Performance - Space, Aerospace & Defense Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Manufacturing subsector called out
large_manufacturing_figure = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Manufacturing Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Manufacturing Subsector': '#0492C2'
  },
  title='Three Year Performance - Manufacturing Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Energy & resources subsector called out
large_materials_energy_figure = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Energy & Resources Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Energy & Resources Subsector': '#0492C2'
  },
  title='Three Year Performance - Energy & Resources Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Built Environment subsector called out
large_built_environment_figure = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Built Environment Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Built Environment Subsector': '#0492C2'
  },
  title='Three Year Performance - Built Environment Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Health subsector called out
large_health_figure = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Health Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Health Subsector': '#0492C2'
  },
  title='Three Year Performance - Health Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Hyperscale AI subsector called out
#large_hyperscale_ai_figure = px.line(normalized_one_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Hyperscale AI Subsector'],
#  color_discrete_map={
#    'NASDAQ': '#A6A6A6',
#    'S&P500': '#D9D9D9',
#    'DeepTech Index': '#BFBFBF',
#    'Hyperscale AI Subsector': '#0492C2'
#  },
#  title='One Year Performance - Hyperscale AI Subsector',
#  template='plotly_white',
#  #width = 1600,
#  #height = 1200
#  )

# Try a really big graph with Mobility & Logistics subsector called out
large_mobility_figure = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Mobility & Logistics Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Mobility & Logistics Subsector': '#0492C2'
  },
  title='Three Year Performance - Mobility & Logistics Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

#Mobile version
figure_mobile = px.line(normalized_three_year, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Three Year Performance',
  template='plotly_white',
  width = 320,
  height = 400)

#Try to add annotations
figure_annotations = []
figure_annotations_grey = []
figure_no_mega_caps_annotations = []
mobile_figure_annotations = []
newspace_sector_annotations = []
manufacturing_sector_annotations = []
materials_energy_sector_annotations = []
built_environment_sector_annotations = []
health_sector_annotations = []
#hyperscale_ai_sector_annotations = []
mobility_sector_annotations = []

#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
deeptech_y_shift = 10
#legacy_y_shift = 10

sandp_got_shifted = 'False'
deeptech_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_three_year['NASDAQ'].values[755]/normalized_three_year['S&P500'].values[755])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_three_year['NASDAQ'].values[755]/normalized_three_year['S&P500'].values[755])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20

#Next check NASDAQ vs DeepTech position - use relative % to see if we need to move
if (abs((normalized_three_year['NASDAQ'].values[755]/normalized_three_year['DeepTech Index'].values[755])-1) < 0.02):
  #Set the deeptech_got_shifted flag
  deeptech_got_shifted = 'True'
  if(((normalized_three_year['NASDAQ'].values[755]/normalized_three_year['DeepTech Index'].values[755])-1) > 0):
    #NASDAQ Above DeepTech, shift DeepTech down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust DeepTech by default
      deeptech_y_shift = 0
  else:
    #DeepTech above NASDAQ, shift DeepTech up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = 30
    else:
      deeptech_y_shift = 20


annotation_one = dict(x=1.01, y=normalized_three_year['NASDAQ'].values[755], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one_grey = dict(x=1.01, y=normalized_three_year['NASDAQ'].values[755], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#A6A6A6',font_color='#FFFFFF', text=nasdaq_annotation)
mobile_annotation_one = dict(x=1.01, y=normalized_three_year['NASDAQ'].values[755], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, font=dict(size=5))
figure_annotations.append(annotation_one)
figure_annotations_grey.append(annotation_one_grey)
mobile_figure_annotations.append(mobile_annotation_one)

annotation_two = dict(x=1.01, y=normalized_three_year['S&P500'].values[755], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two_grey = dict(x=1.01, y=normalized_three_year['S&P500'].values[755], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#D9D9D9',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_three_year['S&P500'].values[755], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
figure_annotations_grey.append(annotation_two_grey)
mobile_figure_annotations.append(mobile_annotation_two)

annotation_three = dict(x=1.01, y=normalized_three_year['DeepTech Index'].values[755], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation)
annotation_three_grey = dict(x=1.01, y=normalized_three_year['DeepTech Index'].values[755], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#BFBFBF',font_color='#FFFFFF', text=deeptech_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_three_year['DeepTech Index'].values[755], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
figure_annotations_grey.append(annotation_three_grey)
mobile_figure_annotations.append(mobile_annotation_three)

annotation_four = dict(x=1.01, y=normalized_three_year['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_three_year['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation, font=dict(size=5))
figure_no_mega_caps_annotations.append(annotation_one)
figure_no_mega_caps_annotations.append(annotation_two)
figure_no_mega_caps_annotations.append(annotation_four)
#sector_mobile_figure_annotations.append(mobile_annotation_four)

annotation_five = dict(x=1.01, y=normalized_three_year['Space, Aerospace & Defense Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=newspace_annotation)
newspace_sector_annotations.append(annotation_five)

annotation_six = dict(x=1.01, y=normalized_three_year['Manufacturing Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=manufacturing_annotation)
manufacturing_sector_annotations.append(annotation_six)

annotation_seven = dict(x=1.01, y=normalized_three_year['Energy & Resources Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=materials_energy_annotation)
materials_energy_sector_annotations.append(annotation_seven)

annotation_eight = dict(x=1.01, y=normalized_three_year['Built Environment Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=built_environment_annotation)
built_environment_sector_annotations.append(annotation_eight)

annotation_nine = dict(x=1.01, y=normalized_three_year['Health Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=health_annotation)
health_sector_annotations.append(annotation_nine)

#annotation_10 = dict(x=1.01, y=normalized_one_year['Hyperscale AI Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=hyperscale_ai_annotation)
#hyperscale_ai_sector_annotations.append(annotation_10)

annotation_11 = dict(x=1.01, y=normalized_three_year['Mobility & Logistics Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=mobility_annotation)
mobility_sector_annotations.append(annotation_11)

##################

figure.update_layout(annotations=figure_annotations)
figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance (%)')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Now do for large figure
large_figure.update_layout(annotations=figure_annotations)
large_figure.update_annotations(clicktoshow='onoff')
large_figure.update_annotations(xanchor='left')
large_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure.update_layout(hovermode='closest')
large_figure.update_layout(yaxis_title='Relative Performance (%)')
large_figure.update_layout(margin=dict(r=170))
large_figure.update_yaxes(fixedrange=True)

#Now do for large_figure_no_title
large_figure_no_title.update_layout(annotations=figure_annotations)
large_figure_no_title.update_annotations(clicktoshow='onoff')
large_figure_no_title.update_annotations(xanchor='left')
large_figure_no_title.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure_no_title.update_layout(hovermode='closest')
large_figure_no_title.update_layout(yaxis_title='Relative Performance (%)')
large_figure_no_title.update_layout(margin=dict(r=170))
large_figure_no_title.update_yaxes(fixedrange=True)

#Now do for large_no_mega_caps_figure
#figure_no_mega_caps_annotations = annotation_one + annotation_two + figure_no_mega_caps_annotations
large_no_mega_caps_figure.update_layout(annotations=figure_no_mega_caps_annotations)
large_no_mega_caps_figure.update_annotations(clicktoshow='onoff')
large_no_mega_caps_figure.update_annotations(xanchor='left')
large_no_mega_caps_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_no_mega_caps_figure.update_layout(hovermode='closest')
large_no_mega_caps_figure.update_layout(yaxis_title='Relative Performance (%)')
large_no_mega_caps_figure.update_layout(margin=dict(r=270))
large_no_mega_caps_figure.update_yaxes(fixedrange=True)


# And for all other figures - starting with Newspace sector
newspace_annotations = figure_annotations_grey + newspace_sector_annotations
large_newspace_figure.update_layout(annotations=newspace_annotations)
large_newspace_figure.update_annotations(clicktoshow='onoff')
large_newspace_figure.update_annotations(xanchor='left')
large_newspace_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_newspace_figure.update_layout(hovermode='closest')
large_newspace_figure.update_layout(yaxis_title='Relative Performance (%)')
large_newspace_figure.update_layout(margin=dict(r=200))
large_newspace_figure.update_yaxes(fixedrange=True)

# Now Manufacturing sector
manufacturing_annotations = figure_annotations_grey + manufacturing_sector_annotations
large_manufacturing_figure.update_layout(annotations=manufacturing_annotations)
large_manufacturing_figure.update_annotations(clicktoshow='onoff')
large_manufacturing_figure.update_annotations(xanchor='left')
large_manufacturing_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_manufacturing_figure.update_layout(hovermode='closest')
large_manufacturing_figure.update_layout(yaxis_title='Relative Performance (%)')
large_manufacturing_figure.update_layout(margin=dict(r=275))
large_manufacturing_figure.update_yaxes(fixedrange=True)

# Now Energy & Resources sector
materials_energy_annotations = figure_annotations_grey + materials_energy_sector_annotations
large_materials_energy_figure.update_layout(annotations=materials_energy_annotations)
large_materials_energy_figure.update_annotations(clicktoshow='onoff')
large_materials_energy_figure.update_annotations(xanchor='left')
large_materials_energy_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_materials_energy_figure.update_layout(hovermode='closest')
large_materials_energy_figure.update_layout(yaxis_title='Relative Performance (%)')
large_materials_energy_figure.update_layout(margin=dict(r=275))
large_materials_energy_figure.update_yaxes(fixedrange=True)

# Now Built Environment sector
built_environment_annotations = figure_annotations_grey + built_environment_sector_annotations
large_built_environment_figure.update_layout(annotations=built_environment_annotations)
large_built_environment_figure.update_annotations(clicktoshow='onoff')
large_built_environment_figure.update_annotations(xanchor='left')
large_built_environment_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_built_environment_figure.update_layout(hovermode='closest')
large_built_environment_figure.update_layout(yaxis_title='Relative Performance (%)')
large_built_environment_figure.update_layout(margin=dict(r=275))
large_built_environment_figure.update_yaxes(fixedrange=True)

# Now Health sector
health_annotations = figure_annotations_grey + health_sector_annotations
large_health_figure.update_layout(annotations=health_annotations)
large_health_figure.update_annotations(clicktoshow='onoff')
large_health_figure.update_annotations(xanchor='left')
large_health_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_health_figure.update_layout(hovermode='closest')
large_health_figure.update_layout(yaxis_title='Relative Performance (%)')
large_health_figure.update_layout(margin=dict(r=275))
large_health_figure.update_yaxes(fixedrange=True)

# Now Hyperscale AI sector
#hyperscale_ai_annotations = figure_annotations_grey + hyperscale_ai_sector_annotations
#large_hyperscale_ai_figure.update_layout(annotations=hyperscale_ai_annotations)
#large_hyperscale_ai_figure.update_annotations(clicktoshow='onoff')
#large_hyperscale_ai_figure.update_annotations(xanchor='left')
#large_hyperscale_ai_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#large_hyperscale_ai_figure.update_layout(hovermode='closest')
#large_hyperscale_ai_figure.update_layout(yaxis_title='Relative Performance')
#large_hyperscale_ai_figure.update_layout(margin=dict(r=275))
#large_hyperscale_ai_figure.update_yaxes(fixedrange=True)

# Now Mobility & Logistics sector
mobility_annotations = figure_annotations_grey + mobility_sector_annotations
large_mobility_figure.update_layout(annotations=mobility_annotations)
large_mobility_figure.update_annotations(clicktoshow='onoff')
large_mobility_figure.update_annotations(xanchor='left')
large_mobility_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_mobility_figure.update_layout(hovermode='closest')
large_mobility_figure.update_layout(yaxis_title='Relative Performance (%)')
large_mobility_figure.update_layout(margin=dict(r=275))
large_mobility_figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure_no_title.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_no_mega_caps_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_newspace_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_manufacturing_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_materials_energy_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_built_environment_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_health_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
#large_hyperscale_ai_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_mobility_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#don't show graphs in cron version in case it hangs the script
#Show while testing...
#figure.show(config=graph_config)
figure.write_html('testing_deeptech_three_year_graph.html', config=graph_config)
large_figure.write_html('testing_deeptech_three_year_graph_large.html', config=graph_config)
large_figure_no_title.write_html('testing_deeptech_three_year_graph_large_no_title.html', config=graph_config)
large_no_mega_caps_figure.write_html('testing_deeptech_three_year_graph_no_mega_caps_large.html', config=graph_config)
large_newspace_figure.write_html('testing_deeptech_with_space_aerospace_defense_sector_three_year_graph_large.html', config=graph_config)
large_manufacturing_figure.write_html('testing_deeptech_with_manufacturing_sector_three_year_graph_large.html', config=graph_config)
large_materials_energy_figure.write_html('testing_deeptech_with_energy_and_resources_sector_three_year_graph_large.html', config=graph_config)
large_built_environment_figure.write_html('testing_deeptech_with_built_environment_sector_three_year_graph_large.html', config=graph_config)
large_health_figure.write_html('testing_deeptech_with_health_sector_three_year_graph_large.html', config=graph_config)
#large_hyperscale_ai_figure.write_html('testing_deeptech_with_hyperscale_ai_sector_one_year_graph_large.html', config=graph_config)
large_mobility_figure.write_html('testing_deeptech_with_mobility_sector_three_year_graph_large.html', config=graph_config)

#Do exactly the same for mobile - except for annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance (%)', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('testing_deeptech_one_year_graph_mobile.html', config=graph_config)

##
#
# Now do max graph
#
##

max_data = master_dataframe

#Get the value of each starting point
deeptech_start = max_data.loc[0]['DeepTech Index']
deeptech_no_mega_caps_start = max_data.loc[0]['DeepTech Index - No Mega Caps']
nasdaq_start = max_data.loc[0]['NASDAQ']
sandp_start = max_data.loc[0]['S&P500']
newspace_start = max_data.loc[0]['Space, Aerospace & Defense Subsector']
manufacturing_start = max_data.loc[0]['Manufacturing Subsector']
materials_energy_start = max_data.loc[0]['Energy & Resources Subsector']
built_environment_start = max_data.loc[0]['Built Environment Subsector']
health_start = max_data.loc[0]['Health Subsector']
#hyperscale_ai_start = max_data.loc[0]['Hyperscale AI Subsector']
mobility_start = max_data.loc[0]['Mobility & Logistics Subsector']

normalized_max_data = max_data

normalized_max_data['NASDAQ'] = normalized_max_data['NASDAQ'].apply(normalize_nasdaq_column)
normalized_max_data['S&P500'] = normalized_max_data['S&P500'].apply(normalize_sandp_column)
normalized_max_data['DeepTech Index'] = normalized_max_data['DeepTech Index'].apply(normalize_deeptech_column)
normalized_max_data['DeepTech Index - No Mega Caps'] = normalized_max_data['DeepTech Index - No Mega Caps'].apply(normalize_deeptech_no_mega_caps_column)
normalized_max_data['Space, Aerospace & Defense Subsector'] = normalized_max_data['Space, Aerospace & Defense Subsector'].apply(normalize_newspace_column)
normalized_max_data['Manufacturing Subsector'] = normalized_max_data['Manufacturing Subsector'].apply(normalize_manufacturing_column)
normalized_max_data['Energy & Resources Subsector'] = normalized_max_data['Energy & Resources Subsector'].apply(normalize_materials_energy_column)
normalized_max_data['Built Environment Subsector'] = normalized_max_data['Built Environment Subsector'].apply(normalize_built_environment_column)
normalized_max_data['Health Subsector'] = normalized_max_data['Health Subsector'].apply(normalize_health_column)
#normalized_max_data['Hyperscale AI Subsector'] = normalized_max_data['Hyperscale AI Subsector'].apply(normalize_hyperscale_ai_column)
normalized_max_data['Mobility & Logistics Subsector'] = normalized_max_data['Mobility & Logistics Subsector'].apply(normalize_mobility_column)

print(normalized_max_data)
#Now add annotation for the graph - how much delta for the various things being tracked
#The function return_percentage is defiend above so reuse that

nasdaq_sign = ''
nasdaq_annotation = normalized_max_data.iloc[-1]['NASDAQ']
nasdaq_annotation = return_percentage(nasdaq_annotation)
if (nasdaq_annotation > 0):
        nasdaq_sign = '+'
nasdaq_annotation = str(nasdaq_annotation)
nasdaq_annotation = 'NASDAQ ' + nasdaq_sign + nasdaq_annotation + '%'
print('NASDAQ Annotation: ', nasdaq_annotation)

sandp_sign = ''
sandp_annotation = normalized_max_data.iloc[-1]['S&P500']
sandp_annotation = return_percentage(sandp_annotation)
if (sandp_annotation > 0):
        sandp_sign = '+'
sandp_annotation = str(sandp_annotation)
sandp_annotation = 'S&P500 ' + sandp_sign + sandp_annotation + '%'
print('S&P500 Annotation: ', sandp_annotation)

deeptech_sign = ''
deeptech_annotation = normalized_max_data.iloc[-1]['DeepTech Index']
deeptech_annotation = return_percentage(deeptech_annotation)
if (deeptech_annotation > 0):
        deeptech_sign = '+'
deeptech_annotation = str(deeptech_annotation)
deeptech_annotation = 'DeepTech Index ' + deeptech_sign + deeptech_annotation + '%'
print('DeepTech Annotation: ', deeptech_annotation)

deeptech_no_mega_caps_sign = ''
deeptech_no_mega_caps_annotation = normalized_max_data.iloc[-1]['DeepTech Index - No Mega Caps']
deeptech_no_mega_caps_annotation = return_percentage(deeptech_no_mega_caps_annotation)
if (deeptech_no_mega_caps_annotation > 0):
        deeptech_no_mega_caps_sign = '+'
deeptech_no_mega_caps_annotation = str(deeptech_no_mega_caps_annotation)
deeptech_no_mega_caps_annotation = 'DeepTech Index - No Mega Caps ' + deeptech_no_mega_caps_sign + deeptech_no_mega_caps_annotation + '%' 
print('DeepTech Annotation - No Mega Caps: ', deeptech_no_mega_caps_annotation)

newspace_sign = ''
newspace_annotation = normalized_max_data.iloc[-1]['Space, Aerospace & Defense Subsector']
newspace_annotation = return_percentage(newspace_annotation)
if (newspace_annotation > 0):
        newspace_sign = '+'
newspace_annotation = str(newspace_annotation)
newspace_annotation = 'Space, Aerospace & Defense Subsector ' + newspace_sign + newspace_annotation + '%'
print('Space, Aerospace & Defense Annotation: ', newspace_annotation)

manufacturing_sign = ''
manufacturing_annotation = normalized_max_data.iloc[-1]['Manufacturing Subsector']
manufacturing_annotation = return_percentage(manufacturing_annotation)
if (manufacturing_annotation > 0):
        manufacturing_sign = '+'
manufacturing_annotation = str(manufacturing_annotation)
manufacturing_annotation = 'Manufacturing Subsector ' + manufacturing_sign + manufacturing_annotation + '%'
print('Manufacturing Annotation: ', manufacturing_annotation)

materials_energy_sign = ''
materials_energy_annotation = normalized_max_data.iloc[-1]['Energy & Resources Subsector']
materials_energy_annotation = return_percentage(materials_energy_annotation)
if (materials_energy_annotation > 0):
        materials_energy_sign = '+'
materials_energy_annotation = str(materials_energy_annotation)
materials_energy_annotation = 'Energy & Resources Subsector ' + materials_energy_sign + materials_energy_annotation + '%'
print('Energy & Resources Annotation: ', materials_energy_annotation)

built_environment_sign = ''
built_environment_annotation = normalized_max_data.iloc[-1]['Built Environment Subsector']
built_environment_annotation = return_percentage(built_environment_annotation)
if (built_environment_annotation > 0):
        built_environment_sign = '+'
built_environment_annotation = str(built_environment_annotation)
built_environment_annotation = 'Built Environment Subsector ' + built_environment_sign + built_environment_annotation + '%'
print('Built Environment Annotation: ', built_environment_annotation)

health_sign = ''
health_annotation = normalized_max_data.iloc[-1]['Health Subsector']
health_annotation = return_percentage(health_annotation)
if (health_annotation > 0):
        health_sign = '+'
health_annotation = str(health_annotation)
health_annotation = 'Health Subsector ' + health_sign + health_annotation + '%'
print('Health Annotation: ', health_annotation)

#hyperscale_ai_sign = ''
#hyperscale_ai_annotation = normalized_max_data.iloc[-1]['Hyperscale AI Subsector']
#hyperscale_ai_annotation = return_percentage(hyperscale_ai_annotation)
#if (hyperscale_ai_annotation > 0):
#        hyperscale_ai_sign = '+'
#hyperscale_ai_annotation = str(hyperscale_ai_annotation)
#hyperscale_ai_annotation = 'Hyperscale AI Subsector ' + hyperscale_ai_sign + hyperscale_ai_annotation + '%'
#print('Hyperscale AI Annotation: ', hyperscale_ai_annotation)

mobility_sign = ''
mobility_annotation = normalized_max_data.iloc[-1]['Mobility & Logistics Subsector']
mobility_annotation = return_percentage(mobility_annotation)
if (mobility_annotation > 0):
        mobility_sign = '+'
mobility_annotation = str(mobility_annotation)
mobility_annotation = 'Mobility & Logistics Subsector ' + mobility_sign + mobility_annotation + '%'
print('Mobility & Logistics Annotation: ', mobility_annotation)

#Actual graphing starts here

#Now chart max/all data before we do anything more as saves having to figure out how to annotate these things into the dataframe

figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Max Historical Performance',
  template='plotly_white',
  width = 800,
  height = 600)

# Try a really big graph?
large_figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd'
  },
  title='Max Historical Performance',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Large chart with no title
large_figure_no_title = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index': '#18a1cd',
  },
  template='plotly_white',
  )

# Build large chart - Deeptech with no mega caps 
large_no_mega_caps_figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index - No Mega Caps'],
  color_discrete_map={
    'NASDAQ': '#68d8ff',
    'S&P500': '#006d97',
    'DeepTech Index - No Mega Caps': '#18a1cd',
  },
  title='Max Historical Performance - Deeptech Index Without Mega Cap Companies',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )


# Try a really big graph with Space, Aerospace & Defense subsector called out
large_newspace_figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Space, Aerospace & Defense Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Space, Aerospace & Defense Subsector': '#0492C2'
  },
  title='Max Historical Performance - Space, Aerospace & Defense Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Manufacturing subsector called out
large_manufacturing_figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Manufacturing Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Manufacturing Subsector': '#0492C2'
  },
  title='Max Historical Performance - Manufacturing Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Energy & resources subsector called out
large_materials_energy_figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Energy & Resources Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Energy & Resources Subsector': '#0492C2'
  },
  title='Max Historical Performance - Energy & Resources Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Built Environment subsector called out
large_built_environment_figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Built Environment Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Built Environment Subsector': '#0492C2'
  },
  title='Max Historical Performance - Built Environment Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Health subsector called out
large_health_figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Health Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Health Subsector': '#0492C2'
  },
  title='Max Historical Performance - Health Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

# Try a really big graph with Hyperscale AI subsector called out
#large_hyperscale_ai_figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Hyperscale AI Subsector'],
#  color_discrete_map={
#    'NASDAQ': '#A6A6A6',
#    'S&P500': '#D9D9D9',
#    'DeepTech Index': '#BFBFBF',
#    'Hyperscale AI Subsector': '#0492C2'
#  },
#  title='Max Historical Performance - Hyperscale AI Subsector',
#  template='plotly_white',
#  #width = 1600,
#  #height = 1200
#  )

# Try a really big graph with Mobility & Logistics subsector called out
large_mobility_figure = px.line(normalized_max_data, x='Date', y=['NASDAQ', 'S&P500', 'DeepTech Index', 'Mobility & Logistics Subsector'],
  color_discrete_map={
    'NASDAQ': '#A6A6A6',
    'S&P500': '#D9D9D9',
    'DeepTech Index': '#BFBFBF',
    'Mobility & Logistics Subsector': '#0492C2'
  },
  title='Max Historical Performance - Mobility & Logistics Subsector',
  template='plotly_white',
  #width = 1600,
  #height = 1200
  )

#Try to add annotations
figure_annotations = []
figure_annotations_grey = []
figure_no_mega_caps_annotations = []
mobile_figure_annotations = []
newspace_sector_annotations = []
manufacturing_sector_annotations = []
materials_energy_sector_annotations = []
built_environment_sector_annotations = []
health_sector_annotations = []
#hyperscale_ai_sector_annotations = []
mobility_sector_annotations = []

#First define the default y-shifts for the annotations and then try to avoid any overlap
nasdaq_y_shift = 10
sandp_y_shift = 10
deeptech_y_shift = 10
#legacy_y_shift = 10

sandp_got_shifted = 'False'
deeptech_got_shifted = 'False'

#First check NASDAQ vs S&P500 position - use relative % to see if we need to move
if (abs((normalized_max_data['NASDAQ'].values[-1]/normalized_max_data['S&P500'].values[-1])-1) < 0.02):
  #Brute force approach to the problem - if S&P500 got shifted set a flag, and adjust everything else based on that flag 
  sandp_got_shifted = 'True'
  if(((normalized_max_data['NASDAQ'].values[-1]/normalized_max_data['S&P500'].values[-1])-1) > 0):
    #NASDAQ Above S&P500, shift S&P500 down
    sandp_y_shift = 0
  else:
    #S&P500 above NASDAQ, shift S&P500 up
    sandp_y_shift = 20

#Next check NASDAQ vs DeepTech position - use relative % to see if we need to move
if (abs((normalized_max_data['NASDAQ'].values[-1]/normalized_max_data['DeepTech Index'].values[-1])-1) < 0.02):
  #Set the deeptech_got_shifted flag
  deeptech_got_shifted = 'True'
  if(((normalized_max_data['NASDAQ'].values[-1]/normalized_max_data['DeepTech Index'].values[-1])-1) > 0):
    #NASDAQ Above DeepTech, shift DeepTech down
    #But need to check NASDAQ vs S&P500 - if these guys overlapped then we need to shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = -10
    else:
      #If no NASDAQ/S&P500 overlap then can just adjust DeepTech by default
      deeptech_y_shift = 0
  else:
    #DeepTech above NASDAQ, shift DeepTech up
    #But need to check NASDAQ vs S&P500 - if these ones overlapped then shift DeepTech by more
    if(sandp_got_shifted == 'True'):
      deeptech_y_shift = 30
    else:
      deeptech_y_shift = 20

#annotation_one = dict(x=normalized_max_data.iloc[-1]['Date'], y=normalized_max_data['NASDAQ'].values[-1], xref='x', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one = dict(x=1.01, y=normalized_max_data['NASDAQ'].values[-1], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation)
annotation_one_grey = dict(x=1.01, y=normalized_max_data['NASDAQ'].values[-1], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#A6A6A6',font_color='#FFFFFF', text=nasdaq_annotation)
mobile_annotation_one = dict(x=1.01, y=normalized_max_data['NASDAQ'].values[-1], xref='paper', yref='y', yshift=nasdaq_y_shift, xshift=5, showarrow=False, bgcolor='#68d8ff',font_color='#FFFFFF', text=nasdaq_annotation, font=dict(size=5))
figure_annotations.append(annotation_one)
figure_annotations_grey.append(annotation_one_grey)
mobile_figure_annotations.append(mobile_annotation_one)

#annotation_two = dict(x=normalized_max_data.iloc[-1]['Date], y=normalized_max_data['S&P500'].values[-1], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two = dict(x=1.01, y=normalized_max_data['S&P500'].values[-1], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation)
annotation_two_grey = dict(x=1.01, y=normalized_max_data['S&P500'].values[-1], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#D9D9D9',font_color='#FFFFFF', text=sandp_annotation)
mobile_annotation_two = dict(x=1.01, y=normalized_max_data['S&P500'].values[-1], xref='paper', yref='y', yshift=sandp_y_shift, xshift=5, showarrow=False, bgcolor='#006d97',font_color='#FFFFFF', text=sandp_annotation, font=dict(size=5))
figure_annotations.append(annotation_two)
figure_annotations_grey.append(annotation_two_grey)
mobile_figure_annotations.append(mobile_annotation_two)

#annotation_three = dict(x=normalized_max_data.iloc[-1]['Date'], y=normalized_max_data['PV New Space'].values[-1], xref='x', yref='y', yshift=newspace_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=newspace_annotation)
annotation_three = dict(x=1.01, y=normalized_max_data['DeepTech Index'].values[-1], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation)
annotation_three_grey = dict(x=1.01, y=normalized_max_data['DeepTech Index'].values[-1], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#BFBFBF',font_color='#FFFFFF', text=deeptech_annotation)
mobile_annotation_three = dict(x=1.01, y=normalized_max_data['DeepTech Index'].values[-1], xref='paper', yref='y', yshift=deeptech_y_shift, xshift=5, showarrow=False, bgcolor='#18a1cd',font_color='#FFFFFF', text=deeptech_annotation, font=dict(size=5))
figure_annotations.append(annotation_three)
figure_annotations_grey.append(annotation_three_grey)
mobile_figure_annotations.append(mobile_annotation_three)

annotation_four = dict(x=1.01, y=normalized_max_data['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation)
mobile_annotation_four = dict(x=1.01, y=normalized_max_data['DeepTech Index - No Mega Caps'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#A020F0',font_color='#FFFFFF', text=deeptech_no_mega_caps_annotation, font=dict(size=5))
figure_no_mega_caps_annotations.append(annotation_one)
figure_no_mega_caps_annotations.append(annotation_two)
figure_no_mega_caps_annotations.append(annotation_four)
#sector_mobile_figure_annotations.append(mobile_annotation_four)

#annotation_five = dict(x=1.01, y=normalized_max_data['Space, Aerospace & Defense Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#FF26F0',font_color='#FFFFFF', text=newspace_annotation)
annotation_five = dict(x=1.01, y=normalized_max_data['Space, Aerospace & Defense Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=newspace_annotation)
newspace_sector_annotations.append(annotation_five)

annotation_six = dict(x=1.01, y=normalized_max_data['Manufacturing Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=manufacturing_annotation)
manufacturing_sector_annotations.append(annotation_six)

annotation_seven = dict(x=1.01, y=normalized_max_data['Energy & Resources Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=materials_energy_annotation)
materials_energy_sector_annotations.append(annotation_seven)

annotation_eight = dict(x=1.01, y=normalized_max_data['Built Environment Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=built_environment_annotation)
built_environment_sector_annotations.append(annotation_eight)

annotation_nine = dict(x=1.01, y=normalized_max_data['Health Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=health_annotation)
health_sector_annotations.append(annotation_nine)

#annotation_10 = dict(x=1.01, y=normalized_max_data['Hyperscale AI Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=hyperscale_ai_annotation)
#hyperscale_ai_sector_annotations.append(annotation_10)

annotation_11 = dict(x=1.01, y=normalized_max_data['Mobility & Logistics Subsector'].values[-1], xref='paper', yref='y', yshift=5, xshift=5, showarrow=False, bgcolor='#0492C2',font_color='#FFFFFF', text=mobility_annotation)
mobility_sector_annotations.append(annotation_11)

figure.update_annotations(clicktoshow='onoff')
figure.update_annotations(xanchor='left')
figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#figure.update_layout(hovermode='x unified')
#figure.update_layout(hovermode='x')
figure.update_layout(hovermode='closest')
figure.update_layout(yaxis_title='Relative Performance (%)')
figure.update_layout(margin=dict(r=170))
figure.update_yaxes(fixedrange=True)

#Now try to do the same for the large figure
large_figure.update_layout(annotations=figure_annotations)
large_figure.update_annotations(clicktoshow='onoff')
large_figure.update_annotations(xanchor='left')
large_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure.update_layout(hovermode='closest')
large_figure.update_layout(yaxis_title='Relative Performance (%)')
large_figure.update_layout(margin=dict(r=200))
large_figure.update_yaxes(fixedrange=True)

#Now do for large_figure_no_title
large_figure_no_title.update_layout(annotations=figure_annotations)
large_figure_no_title.update_annotations(clicktoshow='onoff')
large_figure_no_title.update_annotations(xanchor='left')
large_figure_no_title.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_figure_no_title.update_layout(hovermode='closest')
large_figure_no_title.update_layout(yaxis_title='Relative Performance (%)')
large_figure_no_title.update_layout(margin=dict(r=170))
large_figure_no_title.update_yaxes(fixedrange=True)

#Now do for large_no_mega_caps_figure
#figure_no_mega_caps_annotations = annotation_one + annotation_two + figure_no_mega_caps_annotations
large_no_mega_caps_figure.update_layout(annotations=figure_no_mega_caps_annotations)
large_no_mega_caps_figure.update_annotations(clicktoshow='onoff')
large_no_mega_caps_figure.update_annotations(xanchor='left')
large_no_mega_caps_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_no_mega_caps_figure.update_layout(hovermode='closest')
large_no_mega_caps_figure.update_layout(yaxis_title='Relative Performance (%)')
large_no_mega_caps_figure.update_layout(margin=dict(r=270))
large_no_mega_caps_figure.update_yaxes(fixedrange=True)


# And for all other figures - starting with Newspace sector
newspace_annotations = figure_annotations_grey + newspace_sector_annotations
large_newspace_figure.update_layout(annotations=newspace_annotations)
large_newspace_figure.update_annotations(clicktoshow='onoff')
large_newspace_figure.update_annotations(xanchor='left')
large_newspace_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_newspace_figure.update_layout(hovermode='closest')
large_newspace_figure.update_layout(yaxis_title='Relative Performance (%)')
large_newspace_figure.update_layout(margin=dict(r=320))
large_newspace_figure.update_yaxes(fixedrange=True)

# Now Manufacturing sector
manufacturing_annotations = figure_annotations_grey + manufacturing_sector_annotations
large_manufacturing_figure.update_layout(annotations=manufacturing_annotations)
large_manufacturing_figure.update_annotations(clicktoshow='onoff')
large_manufacturing_figure.update_annotations(xanchor='left')
large_manufacturing_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_manufacturing_figure.update_layout(hovermode='closest')
large_manufacturing_figure.update_layout(yaxis_title='Relative Performance (%)')
large_manufacturing_figure.update_layout(margin=dict(r=275))
large_manufacturing_figure.update_yaxes(fixedrange=True)

# Now Energy & Resources sector
materials_energy_annotations = figure_annotations_grey + materials_energy_sector_annotations
large_materials_energy_figure.update_layout(annotations=materials_energy_annotations)
large_materials_energy_figure.update_annotations(clicktoshow='onoff')
large_materials_energy_figure.update_annotations(xanchor='left')
large_materials_energy_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_materials_energy_figure.update_layout(hovermode='closest')
large_materials_energy_figure.update_layout(yaxis_title='Relative Performance (%)')
large_materials_energy_figure.update_layout(margin=dict(r=275))
large_materials_energy_figure.update_yaxes(fixedrange=True)

# Now Built Environment sector
built_environment_annotations = figure_annotations_grey + built_environment_sector_annotations
large_built_environment_figure.update_layout(annotations=built_environment_annotations)
large_built_environment_figure.update_annotations(clicktoshow='onoff')
large_built_environment_figure.update_annotations(xanchor='left')
large_built_environment_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_built_environment_figure.update_layout(hovermode='closest')
large_built_environment_figure.update_layout(yaxis_title='Relative Performance (%)')
large_built_environment_figure.update_layout(margin=dict(r=275))
large_built_environment_figure.update_yaxes(fixedrange=True)

# Now Health sector
health_annotations = figure_annotations_grey + health_sector_annotations
large_health_figure.update_layout(annotations=health_annotations)
large_health_figure.update_annotations(clicktoshow='onoff')
large_health_figure.update_annotations(xanchor='left')
large_health_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_health_figure.update_layout(hovermode='closest')
large_health_figure.update_layout(yaxis_title='Relative Performance (%)')
large_health_figure.update_layout(margin=dict(r=275))
large_health_figure.update_yaxes(fixedrange=True)

# Now Hyperscale AI sector
#hyperscale_ai_annotations = figure_annotations_grey + hyperscale_ai_sector_annotations
#large_hyperscale_ai_figure.update_layout(annotations=hyperscale_ai_annotations)
#large_hyperscale_ai_figure.update_annotations(clicktoshow='onoff')
#large_hyperscale_ai_figure.update_annotations(xanchor='left')
#large_hyperscale_ai_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
#large_hyperscale_ai_figure.update_layout(hovermode='closest')
#large_hyperscale_ai_figure.update_layout(yaxis_title='Relative Performance')
#large_hyperscale_ai_figure.update_layout(margin=dict(r=275))
#large_hyperscale_ai_figure.update_yaxes(fixedrange=True)

# Now Mobility & Logistics sector
mobility_annotations = figure_annotations_grey + mobility_sector_annotations
large_mobility_figure.update_layout(annotations=mobility_annotations)
large_mobility_figure.update_annotations(clicktoshow='onoff')
large_mobility_figure.update_annotations(xanchor='left')
large_mobility_figure.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
large_mobility_figure.update_layout(hovermode='closest')
large_mobility_figure.update_layout(yaxis_title='Relative Performance (%)')
large_mobility_figure.update_layout(margin=dict(r=275))
large_mobility_figure.update_yaxes(fixedrange=True)

#Try and set legend on top
figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_figure_no_title.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_no_mega_caps_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_newspace_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_manufacturing_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_materials_energy_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_built_environment_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_health_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
#large_hyperscale_ai_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
large_mobility_figure.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#don't show graphs in cron version in case it hangs the script
#Show while testing...
#figure.show(config=graph_config)
figure.write_html('testing_deeptech_max_graph.html', config=graph_config)
large_figure.write_html('testing_deeptech_max_graph_large.html', config=graph_config)
large_figure_no_title.write_html('testing_deeptech_max_graph_large_no_title.html', config=graph_config)
large_no_mega_caps_figure.write_html('testing_deeptech_max_graph_no_mega_caps_large.html', config=graph_config)
large_newspace_figure.write_html('testing_deeptech_with_space_aerospace_defense_sector_max_graph_large.html', config=graph_config)
large_manufacturing_figure.write_html('testing_deeptech_with_manufacturing_sector_max_graph_large.html', config=graph_config)
large_materials_energy_figure.write_html('testing_deeptech_with_energy_and_resources_sector_max_graph_large.html', config=graph_config)
large_built_environment_figure.write_html('testing_deeptech_with_built_environment_sector_max_graph_large.html', config=graph_config)
large_health_figure.write_html('testing_deeptech_with_health_sector_max_graph_large.html', config=graph_config)
#large_hyperscale_ai_figure.write_html('testing_deeptech_with_hyperscale_ai_sector_max_graph_large.html', config=graph_config)
large_mobility_figure.write_html('testing_deeptech_with_mobility_sector_max_graph_large.html', config=graph_config)


#large_newspace_figure.show()
#large_manufacturing_figure.show()
#large_materials_energy_figure.show()
#large_built_environment_figure.show()
#large_health_figure.show()
#large_hyperscale_ai_figure.show()
#large_mobility_figure.show()
#large_figure.show()
#large_no_mega_caps_figure.show()

#Do exactly the same for mobile - except using mobile annotations
figure_mobile.update_layout(annotations=mobile_figure_annotations)
figure_mobile.update_annotations(clicktoshow='onoff')
figure_mobile.update_annotations(xanchor='left')
figure_mobile.update_traces(hovertemplate='Date: %{x}<br>Value: %{y}')
figure_mobile.update_layout(hovermode='closest')
figure_mobile.update_layout(yaxis_title='Relative Performance (%)', font=dict(size=5))
figure_mobile.update_layout(margin=dict(l=20))
figure_mobile.update_yaxes(fixedrange=True)
figure_mobile.update_xaxes(fixedrange=True)

#Try and set legend on top
figure_mobile.update_layout(legend=dict(title='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=4)))

#print the figure
#print(figure)
graph_config = {'displayModeBar':False}
#figure_mobile.show(config=graph_config)
#figure.show()
figure_mobile.write_html('testing_deeptech_max_graph_mobile.html', config=graph_config)

# Try a heatmap
heatmap_dataframe = pd.read_csv('deeptech_heatmap_data.csv')

print('Heatmap dataframe:')
print(heatmap_dataframe)
heatmap_dataframe['All'] = 'All'

heatmap_figure_two = px.treemap(
  heatmap_dataframe,
  path = ['All', 'Sector', 'Ticker'],
  values = 'Market Cap',
  color = 'Market Cap',
  #color = 'Color',
  color_continuous_scale = 'Blugrn'
  )

heatmap_figure_two.update_traces(root_color = 'lightgrey') 
heatmap_figure_two.update_layout(margin = dict(t=50, l=25, r=25, b=25)) 

# Try to do some colors 
sector_color_map = {
	'New Space':'#E0B0FF',
	'Legacy Space & Aerospace':'#4287F5',
	'Additive Manufacturing':'#AE5787',
	'Robotics':'#88B7B5',
	'Materials - Chemicals':'#475B63',
	'Semiconductor':'#3954C8',
	'Semiconductor Equipment':'#067EAA',
	'AR & XR':'#FECEF1',
	'Automotive':'#FECBF9',
	'Hyperscale AI':'#33B233',
	'Industry 4.0':'#22B222',
	'Biotech':'#11B211',
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

heatmap_figure_two.write_html('testing_deeptech_heatmap_hardcode.html', config = graph_config)
heatmap_figure_two.show()


##
#
#All graphs generated, time to commit new graph .html files to GitHub
#Commit done in shell script as easier
#
##

# First copy the various .html graph files to the stuff that gets committed to GitHub

shutil.copy('testing_deeptech_one_week_graph.html', './graphing_scripts/graph_repository/testing_latest_deeptech_one_week_graph.html')
shutil.copy('testing_deeptech_one_month_graph.html', './graphing_scripts/graph_repository/testing_latest_deeptech_one_month_graph.html')
shutil.copy('testing_deeptech_three_month_graph.html', './graphing_scripts/graph_repository/testing_latest_deeptech_three_month_graph.html')
shutil.copy('testing_deeptech_six_month_graph.html', './graphing_scripts/graph_repository/testing_latest_deeptech_six_month_graph.html')
shutil.copy('testing_deeptech_max_graph.html', './graphing_scripts/graph_repository/testing_latest_deeptech_max_graph.html')
shutil.copy('testing_deeptech_three_month_graph_allow_zoom.html', './graphing_scripts/graph_repository/testing_latest_deeptech_three_month_graph_allow_zoom.html')
shutil.copy('testing_deeptech_one_year_graph_allow_zoom.html', './graphing_scripts/graph_repository/testing_latest_deeptech_one_year_graph_allow_zoom.html')
shutil.copy('testing_deeptech_one_year_graph.html', './graphing_scripts/graph_repository/testing_latest_deeptech_one_year_graph.html')

#############
#
# Now try and do a smaller mobile graph - work on three month for starters
#
#############

#Actually do this up with the 3 month graph as all the setup is already there

shutil.copy('testing_deeptech_one_week_graph_mobile.html', './graphing_scripts/graph_repository/testing_latest_deeptech_one_week_graph_mobile.html')
shutil.copy('testing_deeptech_one_month_graph_mobile.html', './graphing_scripts/graph_repository/testing_latest_deeptech_one_month_graph_mobile.html')
shutil.copy('testing_deeptech_three_month_graph_mobile.html', './graphing_scripts/graph_repository/testing_latest_deeptech_three_month_graph_mobile.html')
shutil.copy('testing_deeptech_six_month_graph_mobile.html', './graphing_scripts/graph_repository/testing_latest_deeptech_six_month_graph_mobile.html')
shutil.copy('testing_deeptech_max_graph_mobile.html', './graphing_scripts/graph_repository/testing_latest_deeptech_max_graph_mobile.html')
shutil.copy('testing_deeptech_one_year_graph_mobile.html', './graphing_scripts/graph_repository/testing_latest_deeptech_one_year_graph_mobile.html')

#Import some more modules
#import os
#import subprocess

#def execute_shell_command(cmd, work_dir):
#    """Executes a shell command in a subprocess, waiting until it has completed.
# 
#    :param cmd: Command to execute.
#    :param work_dir: Working directory path.
#    """
#    pipe = subprocess.Popen(cmd, shell=True, cwd=work_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#    (out, error) = pipe.communicate()
#    print out, error
#    pipe.wait()
# 
# 
#def git_add(file_path, repo_dir):
#    """Adds the file at supplied path to the Git index.
#    File will not be copied to the repository directory.
#    No control is performed to ensure that the file is located in the repository directory.
# 
#    :param file_path: Path to file to add to Git index.
#    :param repo_dir: Repository directory.
#    """
#    cmd = 'git add ' + file_path
#    execute_shell_command(cmd, repo_dir)
# 
# 
#def git_commit(commit_message, repo_dir):
#    """Commits the Git repository located in supplied repository directory with the supplied commit message.
# 
#    :param commit_message: Commit message.
#    :param repo_dir: Directory containing Git repository to commit.
#    """
#    cmd = 'git commit -am "%s"' % commit_message
#    execute_shell_command(cmd, repo_dir)
# 
# 
#def git_push(repo_dir):
#    """Pushes any changes in the Git repository located in supplied repository directory to remote git repository.
# 
#    :param repo_dir: Directory containing git repository to push.
#    """
#    cmd = 'git push '
#    execute_shell_command(cmd, repo_dir)
# 
# 
#def git_clone(repo_url, repo_dir):
#    """Clones the remote Git repository at supplied URL into the local directory at supplied path.
#    The local directory to which the repository is to be clone is assumed to be empty.
# 
#    :param repo_url: URL of remote git repository.
#    :param repo_dir: Directory which to clone the remote repository into.
#    """
#    cmd = 'git clone ' + repo_url + ' ' + repo_dir
#    execute_shell_command(cmd, repo_dir)
#
#def update_date_file_in_remote_git_repository(in_repo_url):
#    """Clones the remote Git repository at supplied URL and adds/updates a .date file
#    containing the current date and time. The changes are then pushed back to the remote Git repository.
#    """
#    # Create temporary directory to clone the Git project into.
#    repo_path = tempfile.mkdtemp()
#    print("Repository path: " + repo_path)
#    date_file_path = repo_path + '/.date'
# 
#    try:
#        # Clone the remote GitHub repository.
#        git_clone(in_repo_url, repo_path)
# 
#        # Create/update file with current date and time.
#        if os.path.exists(date_file_path):
#            os.remove(date_file_path)
#        execute_shell_command('date > ' + date_file_path, repo_path)
# 
#        # Add new .date file to repository, commit and push the changes.
#        git_add(date_file_path, repo_path)
#        git_commit('Updated .date file', repo_path)
#        git_push(repo_path)
#    finally:
#        # Delete the temporary directory holding the cloned project.
#        shutil.rmtree(repo_path)
