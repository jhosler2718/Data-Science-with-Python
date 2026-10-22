# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 13:10:24 2026

@author: jason.hosler
"""


import oracledb
import pandas as pd
import numpy as np
import dateutil
from datetime import datetime
from dateutil.parser import parse
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import duckdb



#step one was to pull transactions from data base, omitted here

#what is my date range
min_date = df['TRAN_DATE'].min()
max_date = df['TRAN_DATE'].max()

print("Earliest Date:", min_date)
print("Latest Date:", max_date)

#look at monthly performance overall
df['YEAR_MONTH'] = (df['TRAN_DATE'].dt.year)*100 + df['TRAN_DATE'].dt.month
df['YEAR_MONTH'].value_counts().sort_index()


#first we want to create a base table of monthly performance stats

perf_df = duckdb.sql("""select YEAR_MONTH 
                         ,sum(case when AUTH_IND = 'D' then 1 else 0 end)/count(txn_uid) as DECLINE_RATE
                         ,sum(case when AUTH_IND = 'A' then CLM_CHECK_AMT-CLM_SALVAGE_AMT else 0 end)/sum(case when AUTH_IND = 'A' then TRAN_AMOUNT else 0 end) as NLR
                         ,sum(case when AUTH_IND = 'A' then BAD else 0 end)/sum(case when AUTH_IND = 'A' then 1 else 0 end) as BAD_RATE
                         from df 
                         group by YEAR_MONTH 
                         order by YEAR_MONTH""").df()

#look at graph
ax = perf_df.plot(x='YEAR_MONTH', y=['NLR','BAD_RATE'], color=['red','purple'], label=['NLR','BAD RATE'])
perf_df.plot(x='YEAR_MONTH', y='DECLINE_RATE', secondary_y=True, color='black', ax=ax, label='DECLINE RATE')

# Labeling your axes
ax.set_ylabel('LOSS RATE', color='red')
ax.right_ax.set_ylabel('DECLINE RATE', color='black')

plt.show()

#monthly model performance
#create score deciles
month_list = perf_df['MONTH'].to_list()

def loop_through_months():
    
    perf_list = []
    
    for item in month_list:
        current_month_df = df[(df['MONTH'] == item) & (df['AUTH_IND'] == 'A')]
        current_month_df['DECILE'] = pd.qcut(current_month_df['DA_PRIMARY_SCORE'], q=20, labels=False)
        bad_count = current_month_df['BAD'].sum()
        bottom_decile_bad = current_month_df.loc[current_month_df['DECILE'] == 0, 'BAD'].sum()
        
        ks_df = current_month_df.groupby(['DECILE']).agg({'TXN_UID':'count', 'BAD':'sum'})
        ks_df['GOOD'] = ks_df['TXN_UID'] - ks_df['BAD']
        
        ks_df['CUM_PCT_BAD'] = 100 * (ks_df['BAD'].cumsum() / ks_df['BAD'].sum())
        ks_df['CUM_PCT_GOOD'] = 100 * (ks_df['GOOD'].cumsum() / ks_df['GOOD'].sum())
        ks_df['KS'] = ks_df['CUM_PCT_BAD'] - ks_df['CUM_PCT_GOOD']
        ks = ks_df['KS'].max()

        new_row = [item,bad_count,bottom_decile_bad,bottom_decile_bad/bad_count,ks]
        
        perf_list.append(new_row)

    perf_array = np.array(perf_list)          
    return perf_array
    
perf_array = loop_through_months()

report_df = pd.DataFrame(data=perf_array, columns=["MONTH","BAD_COUNT","BOTTOM_DECILE_BAD","PCNT_BAD_BOTTOM_DECILE", "KS"])

ax = report_df.plot(x='MONTH', y='PCNT_BAD_BOTTOM_DECILE', color='purple', label='PERCENT OF BAD BOTTOM DECILE')
report_df.plot(x='MONTH', y='KS', secondary_y=True, color='blue', ax=ax, label='KS')

# Labeling your axes
ax.set_ylabel('BOTTOM DECILE', color='black')
ax.right_ax.set_ylabel('KS', color='black')

plt.show()


#------------------------------------------------------------------------------manual checks
current_month_df = df[(df['MONTH'] == 2) & (df['AUTH_IND'] == 'A')]
current_month_df['DECILE'] = pd.qcut(current_month_df['DA_PRIMARY_SCORE'], q=20, labels=False)
bad_count = current_month_df['BAD'].sum()
bottom_decile_bad = current_month_df.loc[current_month_df['DECILE'] == 0, 'BAD'].sum()

print("BAD COUNT:", bad_count, "\nBOTTOM DECILE BAD:" ,bottom_decile_bad)


ks_df = current_month_df.groupby(['DECILE']).agg({'TXN_UID':'count', 'BAD':'sum', 'DA_PRIMARY_SCORE':['min','max']})
ks_df['GOOD'] = ks_df['TXN_UID'] - ks_df['BAD']

ks_df['CUM_PCT_BAD'] = 100 * (ks_df['BAD'].cumsum() / ks_df['BAD'].sum())
ks_df['CUM_PCT_GOOD'] = 100 * (ks_df['GOOD'].cumsum() / ks_df['GOOD'].sum())
ks_df['KS'] = ks_df['CUM_PCT_BAD'] - ks_df['CUM_PCT_GOOD']
ks = ks_df['KS'].max()