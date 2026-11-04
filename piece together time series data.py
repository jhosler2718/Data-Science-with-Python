# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 07:48:08 2026

@author: jason.hosler
"""

import oracledb
import pandas as pd
import numpy as np
import os
import dateutil
from datetime import datetime
from dateutil.parser import parse
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import duckdb

print("Before:", os.getcwd())
os.chdir('C:/Users/jason.hosler/OneDrive - Certegy Payment Solution, LLC/Analysis/Time Series Research')
print("After:", os.getcwd())

#monthly CPI data
cpi_df = pd.read_csv('CPI.csv')
cpi_df.dtypes

cpi_df['YEAR'] = cpi_df['observation_date'].str[0:4].astype('int')
cpi_df['MONTH'] = cpi_df['observation_date'].str[5:7].astype('int')

cpi_df['YEAR_MONTH'] = cpi_df['YEAR']*100 + cpi_df['MONTH']
cpi_df = cpi_df.rename(columns = {'CORESTICKM159SFRBATL':'CPI'})

cpi_df = cpi_df.drop(columns = ['observation_date','YEAR','MONTH'])
cpi_df.set_index('YEAR_MONTH', inplace=True)




#monthly gas prices
gas_df = pd.read_csv('Monthly Gas Prices.csv')
gas_df.dtypes

gas_df['date_col'] = pd.to_datetime(gas_df['Date'])

gas_df['YEAR'] = gas_df['date_col'].dt.year
gas_df['MONTH'] = gas_df['date_col'].dt.month

gas_df['YEAR_MONTH'] = gas_df['YEAR']*100 + gas_df['MONTH']

gas_df.dropna(subset=['YEAR_MONTH'], inplace=True)

gas_df['YEAR_MONTH'] = gas_df['YEAR_MONTH'].astype('int')


gas_df = gas_df.rename(columns = {'PRICE':'PRICE_OF_GAS'})

gas_df = gas_df.drop(columns = ['Date','date_col','YEAR','MONTH'])
gas_df.set_index('YEAR_MONTH', inplace=True)


#monthly unemployment rate

ue_rate_df = pd.read_csv('Unemployment rate.csv')
ue_rate_df.dtypes

ue_rate_df['YEAR'] = ue_rate_df['observation_date'].str[0:4].astype('int')
ue_rate_df['MONTH'] = ue_rate_df['observation_date'].str[5:7].astype('int')

ue_rate_df['YEAR_MONTH'] = ue_rate_df['YEAR']*100 + ue_rate_df['MONTH']

ue_rate_df = ue_rate_df.rename(columns = {'UNRATE':'UE_RATE'})

ue_rate_df = ue_rate_df.drop(columns = ['observation_date','YEAR','MONTH'])
ue_rate_df.set_index('YEAR_MONTH', inplace=True)

monthly_df = pd.concat([cpi_df,gas_df,ue_rate_df], axis=1, join='inner')
monthly_df.dtypes

corr_matrix = monthly_df[['CPI','PRICE_OF_GAS','UE_RATE']].corr()
print(corr_matrix)

#for gas need the month over month increase
monthly_df['GAS_PRIOR_MONTH'] = monthly_df['PRICE_OF_GAS'].shift()
monthly_df['GAS_PRIOR_YEAR'] = monthly_df['PRICE_OF_GAS'].shift(12)

monthly_df.dropna(subset=['GAS_PRIOR_YEAR'], inplace=True)

monthly_df['GAS_MOM_PCNT'] = (monthly_df['PRICE_OF_GAS'] - monthly_df['GAS_PRIOR_MONTH'])/monthly_df['GAS_PRIOR_MONTH']
monthly_df['GAS_YOY_PCNT'] = (monthly_df['PRICE_OF_GAS'] - monthly_df['GAS_PRIOR_YEAR'])/monthly_df['GAS_PRIOR_YEAR']


corr_matrix = monthly_df[['CPI','PRICE_OF_GAS','UE_RATE','GAS_MOM_PCNT','GAS_YOY_PCNT']].corr()
print(corr_matrix)

#NOW PULL IN THE CERTEGY MONTHLY

certegy_df = pd.read_csv('Certegy Monthly.csv')
certegy_df.dtypes

certegy_df.set_index('YEAR_MONTH', inplace=True)

monthly_cert_df = pd.concat([monthly_df,certegy_df], axis=1, join='inner')
monthly_cert_df.dtypes

monthly_cert_df.to_pickle('certegy_monthly.pkl')















