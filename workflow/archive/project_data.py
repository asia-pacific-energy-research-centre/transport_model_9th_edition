#we will use this to test and then produce projections using macro data and other inputs on the activity and stocks data in the transport data sets

#for now lets just ignore fuels and blending ratios for now.
activity = pd.read_csv('../intermediate_data/activity.csv')


turnover_rate = pd.read_excel('../input_data/dummy_database.xlsx', sheet_name='Turnover_Rate')

df_Vehicle_sales_share_ref = pd.read_excel("../input_data/Vehicle_sales_share_mod.xlsx",sheet_name= 'Reference' ,skiprows=32, usecols="C:BH",index_col=[0,1,2,3])

df_Vehicle_sales_share_cn = pd.read_excel("../input_data/Vehicle_sales_share_mod.xlsx",sheet_name= 'Net-zero' ,skiprows=32, usecols="C:BH",index_col=[0,1,2,3])