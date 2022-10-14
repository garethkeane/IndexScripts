#Trying some Yahoo Finance stuff - first setup yfinance, pandas (data), and re (regex) 
#Revision tracker
#20220824 Pulling out market cap code to stand alone - will become a CSV that is an input for everything else - main motiviation is reduce run time for testing
#         Idea is that this gets run once a day (eventually automatically) and then all scripts using the data have consistent market cap starting point

import yfinance as yf
import pandas as pd
import re
import csv
import datetime
from csv import writer
import shutil
import plotly.express as px
import requests

#Try to get analyst estimates as well

import yahoo_fin.stock_info as yfin

#setup the list of tickers 
from ticker_list import long_ticker_list
index_ticker_list = ['^IXIP', '^GSPC']

# Get forward looking revenues right here based on get_forward flag
#get_forward = 'True'
get_forward = 'False'

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

forward_revenue = {}

if (get_forward == 'True'):
  with open('master_forward_revenue_data.csv', 'w') as output_file:
    for ticker in long_ticker_list:
      print('Working on ', ticker)
      analyst_table = yfin.get_analysts_info(ticker)
      #print('Data from analysts:\n', analyst_table)
      revenue_table = analyst_table['Revenue Estimate']
      #print('Next year revenue table :\n', revenue_table)
      next_year_revenue_column = revenue_table.iloc[:,4]
      next_year_revenue = next_year_revenue_column[1]
      #Try to strip out Yahoo k/M/B/T notation
      next_year_revenue = text_to_num(next_year_revenue) 
      next_year_revenue = str(next_year_revenue)
      print('Next year revenue for ', ticker, ' is ', next_year_revenue)
      output = ticker + ',' + next_year_revenue + '\n'
      forward_revenue[ticker] = next_year_revenue
      output_file.write(output)


ticker_data = {}

#work with all components in the "ticker_list", but also have stocks in stock_ticker_list seperately for this script
#But get their data all at once to make sure that there are no gaps
ticker_list = []
stock_ticker_list = []
ticker_list.extend(long_ticker_list)
stock_ticker_list.extend(long_ticker_list)

ticker_list.extend(index_ticker_list)
print(ticker_list)

bad_company_count = 0

#Try to get some info from yfin on market cap, ev
#cControl with a flag
get_yfin_market_caps = 'True'
use_yfin_market_caps = 'True'
#Define the dicts to store this
yfin_ev = {}
yfin_market_cap = {}
yfin_forward_pe = {}
yfin_trailing_pe = {}

if (get_yfin_market_caps == 'True'):
 for ticker in stock_ticker_list:
  print('Working on ', ticker)
  dataframe = yfin.get_stats_valuation(ticker)
  dataframe = dataframe.iloc[:,:2]
  print(dataframe)
  #test_dataframe = yfin.get_stats(ticker)
  #print(test_dataframe)
  #data_column = dataframe.iloc[2]
  ev = dataframe.iloc[1][1]
  if pd.isna(ev):
    #quit()
    print('EV for', ticker, 'is NaN')
  ev = str(text_to_num(ev))
  print('EV: ', ev)
  market_cap = dataframe.iloc[0][1]
  if pd.isna(market_cap):
    #quit()
    print('Market Cap for', ticker, 'is NaN')
    use_yfin_market_caps = 'False'
  market_cap = str(text_to_num(market_cap))
  print('Market Cap:', market_cap)
  trailing_pe = dataframe.iloc[2][1]
  forward_pe = dataframe.iloc[3][1]
  print('Trailing PE:', trailing_pe)
  print('Forward PE:', forward_pe)
   
  yfin_ev[ticker] = ev
  yfin_market_cap[ticker] = market_cap
  #quote_table = yfin.get_quote_table(ticker)
  yfin_forward_pe[ticker] = forward_pe
  yfin_trailing_pe[ticker] = trailing_pe
  #print('PE Ratio:', yfin_pe[ticker])

#Now dump these lists as a dataframe to csv?
yfin_data = {'Ticker':stock_ticker_list, 'Market Cap':yfin_market_cap, 'EV':yfin_ev, 'Forward PE Ratio':yfin_forward_pe, 'Trailing PE Ratio':yfin_trailing_pe}
#yfin_dataframe = pd.DataFrame(yfin_data)
#yfin_dataframe.ts_csv('yfin_market_cap_output.csv')



#First define a couple of data structures:
# - golden market cap data structure as a python dict so we can track/use by ticker
# - golden company name data structure as a python dict so we can track/use by ticker
# - golden company currency data structure as a python dict again so can track/use by ticker
golden_market_caps = {}
golden_company_names = {}
golden_company_currency = {}

with open('master_marketcaps_list.csv', 'w') as output_file:
  output = 'Ticker,Company Name,Market Cap,EV,Currency,TTM Revenue,EV/Revenue,Trailing EPS,Forward EPS,Revenue Growth Rate,Gross Margin,Average Volume,Float,Total Shares,Forward PE,Trailing PE\n'
  #output = 'Ticker,Company Name,Market Cap,Currency,TTM Revenue,Next Year Revenue,EV/Revenue,Trailing EPS,Forward EPS,Revenue Growth Rate,Gross Margin,Average Volume,Float,Total Shares\n'
  output_file.write(output)
  for ticker in stock_ticker_list:
    print ('Working on', ticker)
    ticker_object = yf.Ticker(ticker)
    output_market_cap = str(ticker_object.info['marketCap'])
    print('Setting market cap for ', ticker, ' to ', output_market_cap)
    output_currency = ticker_object.info['currency']
    #output_forward_revenue = str(forward_revenue[ticker])
    try:
      ticker_object.info['enterpriseValue']
    except KeyError:
      output_ev = 'None'
    else:
      output_ev = str(ticker_object.info['enterpriseValue'])
    try:
      ticker_object.info['totalRevenue']
    except KeyError:
      output_revenue = 'None'
    else:
      output_revenue = str(ticker_object.info['totalRevenue'])
    try:
      ticker_object.info['enterpriseToRevenue']
    except KeyError: 
      output_ev_to_revenue = 'None'
    else:
      output_ev_to_revenue = str(ticker_object.info['enterpriseToRevenue'])
    try:
      ticker_object.info['grossMargins']
    except KeyError:
      output_gm = 'None'
    else:
      output_gm = str(ticker_object.info['grossMargins'])
    try:
      ticker_object.info['revenueGrowth']
    except KeyError:
      output_revenue_growth_rate = 'None'
    else:
      output_revenue_growth_rate = str(ticker_object.info['revenueGrowth'])
    try:
      ticker_object.info['trailingEps']
    except KeyError:
      output_trailing_eps = 'None'
    else:
      output_trailing_eps = str(ticker_object.info['trailingEps'])
    try:
      ticker_object.info['forwardEps']
    except KeyError:
      output_forward_eps = 'None'
    else:
      output_forward_eps = str(ticker_object.info['forwardEps'])
    try:
      ticker_object.info['forwardPE']
    except KeyError:
      output_forwardPE = 'None'
    else:
      output_forwardPE = str(ticker_object.info['forwardPE'])
    try:
      ticker_object.info['averageVolume']
    except KeyError:
      output_average_volume ='None'
    else:
      output_average_volume = str(ticker_object.info['averageVolume'])
    try:
      ticker_object.info['floatShares']
    except KeyError:
      output_float = 'None'
    else:
      output_float = str(ticker_object.info['floatShares'])
    try:
      ticker_object.info['sharesOutstanding']
    except KeyError:
      output_total_shares = 'None'
    else:
      output_total_shares = str(ticker_object.info['sharesOutstanding'])
    try:
      ticker_object.info['shortName']
    except KeyError:
      output_short_name = 'None'
    else:
      output_short_name = str(ticker_object.info['shortName'])
    try: 
      ticker_object.info['longName']
    except KeyError:
      output_name = 'None'
      print('KeyError for: ', ticker)
    else:
      output_name = str(ticker_object.info['longName'])
      if (output_name == 'None'):
        print('No longName for ', ticker)
        output_name = output_short_name
        print('Setting to ', output_name)
      print ('Old Name: ', output_name)
      output_name = re.sub(',', '', output_name)
      print ('New Name: ', output_name)
      if (output_market_cap == 'None'):
        if (ticker != '^IXIC') and (ticker != '^GSPC'):
          print('In bad market cap loop for', output_name)
          #Try to find market cap somewhere else - if this fails go for the backup of "golden" data
          #Going to use Alpha Vantage
          url = 'https://www.alphavantage.co/query?function=OVERVIEW&symbol=' + ticker +'&apikey=4UNUCLWS3KMG8J0J'
          r = requests.get(url)
          url_data = r.json()
          output_market_cap = url_data['MarketCapitalization']
          print('Setting market cap for ', ticker, ' to ', output_market_cap)
      #Add some code to try and verify market cap is correct - calculate [last close price] * [number of shares outstanding] and this should be pretty close to the market cap reported

      #Check for forwardPE
      try:
        ticker_object.info['forwardPE']
      except KeyError:
        output_forwardpe = 'None'
      else:
        output_forwardpe = str(ticker_object.info['forwardPE'])
      try:
        ticker_object.info['trailingPE']
      except KeyError:
        output_trailingpe = 'None'
      else:
        output_trailingpe = str(ticker_object.info['trailingPE'])

      closing_price = ticker_object.history()
      last_quote = closing_price['Close'].iloc[-1]
      last_quote = float(last_quote)
      yahoo_market_cap = float(output_market_cap)
      if(output_total_shares != 'None'):
        yahoo_share_count = float(output_total_shares)
      else:
        yahoo_share_count = 0
      print('Last quote: ', last_quote)
      calculated_market_cap = yahoo_share_count * last_quote
      delta_to_market_cap = (calculated_market_cap/yahoo_market_cap) - 1
      if (abs(delta_to_market_cap) > 0.02): # Flag if this delta is > 1%
        print('Looks like a problem with market cap for ', ticker)
        print('Yahoo reports    : ', output_market_cap)
        print('Calculated value : ', calculated_market_cap)
        print('Delta is         : ', delta_to_market_cap, '%')
        bad_company_count = bad_company_count + 1
        #quit() 
      else:
        print('Market cap check is good for ', ticker)
      
      #Quick change here to use yfin data for EV and Market Cap
      if (use_yfin_market_caps == 'True'):
        output_market_cap = str(yfin_market_cap[ticker])
        output_ev = str(yfin_ev[ticker])
        output_forwardpe = str(yfin_forward_pe[ticker])
        output_trailingpe = str(yfin_trailing_pe[ticker])
#      output_pe = yfin_pe[ticker]

#      output = ticker + ',' + output_name + ',' + output_market_cap + ',' + output_ev + ',' + output_currency + ',' + output_revenue + ',' + output_ev_to_revenue + ',' + output_trailing_eps + ',' + output_forward_eps + ',' + output_revenue_growth_rate + ',' + output_gm + ',' + output_average_volume + ',' + output_float + ',' + output_total_shares + ',' + output_pe + '\n'
      output = ticker + ',' + output_name + ',' + output_market_cap + ',' + output_ev + ',' + output_currency + ',' + output_revenue + ',' + output_ev_to_revenue + ',' + output_trailing_eps + ',' + output_forward_eps + ',' + output_revenue_growth_rate + ',' + output_gm + ',' + output_average_volume + ',' + output_float + ',' + output_total_shares + ',' + output_forwardpe + ',' + output_trailingpe + '\n'
      #now add this output_market_cap to golden_market_caps{} and add output_name to golden_company_names{}
      golden_market_caps[ticker] = output_market_cap
      golden_company_names[ticker] = output_name
      golden_company_currency[ticker] = output_currency
      output_file.write(output)

#Dump a timestamp to the CSV file every time this script runs
current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open ('master_marketcaps_list_timestamp.csv', 'a', newline='') as f_object:
        writer_object = writer(f_object)
        writer_object.writerow(time_data)
        f_object.close


###########
#
# Now get FX data from Yahoo Finance
#
##########

fx_ticker_list = ['EURUSD=X', 'GBPUSD=X']
bad_exchange_rate_flag = 'False'
exchange_rates = {}

with open('master_fx_data.csv', 'w') as output_file:
        output = 'Type,Rate\n'
        output_file.write(output)
        for ticker in fx_ticker_list:
                ticker_object = yf.Ticker(ticker)
                exchange_rate = str(ticker_object.history(period='1d')['Close'])
                exchange_rate = exchange_rate.split()
                exchange_rate = exchange_rate[2]
                if (exchange_rate == 'Close,'):
                        #bad_exchange_rate_flag = 'True'
                        #exchange_rates[ticker] = 'None'
                        #Try getting last close instead if Yahoo has an issue with 1d Close
                        exchange_rates[ticker] = ticker_object.info['regularMarketPreviousClose']
                        exchange_rates[ticker] = float(exchange_rates[ticker])
                        exchange_rate = exchange_rates[ticker]
                        print('Changing exchange rate to previous close:', exchange_rate)
                        exchange_rate = str(exchange_rate) # make sure that the exchange rate can be printed out
                        #exchange_rates[ticker] = float(exchange_rate) #make sure we can do arithmetic with this - needs to be a number
                else:
                        exchange_rates[ticker] = float(exchange_rate) #make sure we can do arithmetic with this - needs to be a number
                output = ticker + ',' + exchange_rate + '\n'
                output_file.write(output)

current_time = datetime.datetime.now()
time_data =['Timestamp', current_time]

with open('master_fx_data.csv', 'a',newline='') as f_object:
        write_object = writer(f_object)
        write_object.writerow(time_data)
        f_object.close

#Now check and get good exchange rate data if needed
if (bad_exchange_rate_flag == 'True'):
        exchangerate_df = pd.read_csv('last_golden_deeptech_fx_data.csv')
        for ticker in fx_ticker_list:
                if (exchange_rates[ticker] == 'None'):
                        print('Replacing exchange rate for:', ticker)
                        exchange_rates[ticker] = exchangerate_df.loc[exchangerate_df['Type']==ticker]['Rate'].values=0
                        print('Now:', exchange_rates[ticker])

#Maybe try and replace golden_fx_data.csv if exchange rate data is good?
if (bad_exchange_rate_flag == 'False'):
        print('Copying exchange rate data to golden')
        shutil.copy('master_fx_data.csv', 'last_golden_deeptech_fx_data.csv')


print('Number of bad companies:', bad_company_count)
