#20221010 Turn some inputs into a csv to suck into Wix
# 

import csv
import pandas as pd

from category_ticker_list import newspace_ticker_list
from category_ticker_list import manufacturing_deeptech_index_list
from category_ticker_list import materials_energy_deeptech_index_list
from category_ticker_list import built_environment_deeptech_index_list
from category_ticker_list import health_deeptech_index_list
from category_ticker_list import mobility_deeptech_index_list

from company_ticker_to_name_map import company_name_map

with open ('category_list_for_wix.csv', 'w') as output_file:
  for ticker in newspace_ticker_list:
    output = ticker + ',' + company_name_map[ticker] + ',' + 'SpaceAerospaceDefense\n'
    output_file.write(output)
  for ticker in manufacturing_deeptech_index_list:
    output = ticker + ',' + company_name_map[ticker] + ',' + 'Manufacturing\n'
    output_file.write(output)
  for ticker in materials_energy_deeptech_index_list:
    output = ticker + ',' + company_name_map[ticker] + ',' + 'EnergyResources\n'
    output_file.write(output)
  for ticker in built_environment_deeptech_index_list:
    output = ticker + ',' + company_name_map[ticker] + ',' + 'BuiltEnvironment\n'
    output_file.write(output)
  for ticker in health_deeptech_index_list:
    output = ticker + ',' + company_name_map[ticker] + ',' + 'Health\n'
    output_file.write(output)
  for ticker in mobility_deeptech_index_list:
    output = ticker + ',' + company_name_map[ticker] + ',' + 'MobilityLogistics\n'
    output_file.write(output)

