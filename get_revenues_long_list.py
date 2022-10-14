# 20220923 First cut at using yahoo_fin module to get revenues from https://finance.yahoo.com

import yahoo_fin.stock_info as yfin

#ticker_list = ['AAPL', 'GOOG']

#from pv_platform_ticker_list import connectivity_and_compute_list
#from pv_platform_ticker_list import enhanced_production_list
#from pv_platform_ticker_list import automation_list
from test_ticker_list import long_list

ticker_list = []
stock_ticker_list = []
#ticker_list.extend(connectivity_and_compute_list)
#ticker_list.extend(enhanced_production_list)
#ticker_list.extend(automation_list)
ticker_list.extend(long_list)

with open('master_revenue_data.csv', 'w') as output_file:
  for ticker in ticker_list:
    print('Working on ', ticker)
    income_statement = yfin.get_income_statement(ticker)
    revenues = income_statement.loc['totalRevenue',:].values.tolist()
    #print(income_statement)
    #print(ticker, revenues)
    revenues = ','.join(map(str, revenues))
    output = ticker + ',' + revenues + '\n'
    output_file.write(output)

with open('master_market_cap_data.csv', 'w') as output_file:
  for ticker in ticker_list:
    data_table = yfin.get_quote_table(ticker, dict_result = False)
    print(data_table)
    output_market_cap = data_table["Market Cap"]
    output = ticker + ',' + output_market_cap
    output_file.write(output) 
