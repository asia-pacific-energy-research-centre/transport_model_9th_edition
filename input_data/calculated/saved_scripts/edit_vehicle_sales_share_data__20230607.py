#we will take in the vehicle sales from historical data, then adjust them according to the patterns we expect to see. i.e. nz moves to 100% ev's by 2030.

#we will also create a vehicle sales distribution that replicates what each scenario in the 8th edition shows. We can use this to help also load all stocks data so that we can test the model works like the 8th edition
#%%
#set working directory as one folder back so that config works
import os
import re
import shutil
from turtle import title
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
###IMPORT GLOBAL VARIABLES FROM config.py
import sys
sys.path.append("./config/utilities")
from config import *
####usae this to load libraries and set variables. Feel free to edit that file as you need
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive 
# notebook in vscode #or set to notebook
import plotly
import plotly.express as px
pd.options.plotting.backend = "matplotlib"
import plotly.io as pio
pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook

#%%

#load data
new_sales_shares = pd.read_csv('input_data/from_8th/reformatted/vehicle_stocks_change_share_normalised.csv')
#%%
#first we need to separate the sales share of vehicle types from the sales share of drives, by transport type. Since the way the values were created was simply mutliplication, we can jsut reverse that, i think.
#so sum by vehicle type to get the total sales share of each vehicle type
#then if we divide this by the final sales share values for each v-type/drive we can recreate the shares by drive type, witihin each vehicle type.
#now for shares by drive type, witihin each vehicle type, we can create the shares we want.
#sum by vtype economy year and scenario
new_sales_shares_sum = new_sales_shares.copy()

#set phevd and phevg to phev in drive col
new_sales_shares_sum.loc[new_sales_shares_sum['Drive']=='phevd', 'Drive'] = 'phev'
new_sales_shares_sum.loc[new_sales_shares_sum['Drive']=='phevg', 'Drive'] = 'phev'
#set lv and lt to ldv in vehicle type col
new_sales_shares_sum.loc[new_sales_shares_sum['Vehicle Type']=='lv', 'Vehicle Type'] = 'ldv'
new_sales_shares_sum.loc[new_sales_shares_sum['Vehicle Type']=='lt', 'Vehicle Type'] = 'ldv'
#set g and d to ice in drive col
new_sales_shares_sum.loc[new_sales_shares_sum['Drive']=='g', 'Drive'] = 'ice'
new_sales_shares_sum.loc[new_sales_shares_sum['Drive']=='d', 'Drive'] = 'ice'

#RENAME YEAR TO DATE
new_sales_shares_sum = new_sales_shares_sum.rename(columns={'Year':'Date'})

#filter for only the Reference scenario and then duplicate the rows for each different scenario in SCENARIOS_LIST
new_sales_shares_sum = new_sales_shares_sum[new_sales_shares_sum['Scenario']=='Reference']
new_sales_shares_sum_dummy  = new_sales_shares_sum.copy()
for scenario in SCENARIOS_LIST:
    if scenario != 'Reference':
        new_sales_shares_sum_2 = new_sales_shares_sum_dummy.copy()
        new_sales_shares_sum_2['Scenario'] = scenario
        new_sales_shares_sum = new_sales_shares_sum.append(new_sales_shares_sum_2)
#%%
#PLEASE NOTE THAT VALUE IS THE % OF THE TRANSPORT TYPE FOR THAT VEHICLE TYPE AND DRIVE TYPE. SO IF WE SUM BY VEHICLE TYPE WE GET THE TOTAL SHARE OF EACH VEHICLE TYPE. IF WE DIVIDE BY THIS WE GET THE SHARE OF EACH DRIVE TYPE WITHIN EACH VEHICLE TYPE
#reaplce Value with Transport_type_share
new_sales_shares_sum = new_sales_shares_sum.rename(columns={'Value':'Transport_type_share'})
new_sales_shares_sum['Vehicle_type_share_sum'] = new_sales_shares_sum.groupby(['Economy', 'Scenario', 'Vehicle Type', 'Transport Type', 'Date'])['Transport_type_share'].transform('sum')

new_sales_shares_sum['Drive_share'] = new_sales_shares_sum['Transport_type_share']/new_sales_shares_sum['Vehicle_type_share_sum']

#now we can create the shares we want

#%%

#first create a clean dataframe with all values set to NA after 2019 and annoying cols removed
new_sales_shares_sum_clean = new_sales_shares_sum[['Economy', 'Scenario',  'Transport Type', 'Date', 'Vehicle Type', 'Drive', 'Drive_share']]

new_sales_shares_sum_0 = new_sales_shares_sum_clean.copy()

new_sales_shares_sum_0.loc[new_sales_shares_sum_0['Date']>2019, 'Drive_share'] = np.nan

#sort
new_sales_shares_sum_0 = new_sales_shares_sum_0.sort_values(by=['Economy', 'Scenario', 'Date', 'Vehicle Type', 'Transport Type', 'Drive'])

#%%
################################################################################
#for this we will perfrom the hcanges on passenger and freight separately. So here we will separate them and then combine them at the end
new_sales_shares_passenger_0 = new_sales_shares_sum_0[new_sales_shares_sum_0['Transport Type']=='passenger']
new_sales_shares_freight_0 = new_sales_shares_sum_0[new_sales_shares_sum_0['Transport Type']=='freight']

#CHANGE ALL PHEVD AND PHEVG TO PHEV. FOR NOW THIS IS NEEDED AS WE ARE CONVERTING PHEV TO G OR D IN DEMAND MIXING

#for all values we wil interpolate between them with a spline. To set values we will just set the value for the year we want to the value we want, then interpolate between the values we have set and the values in 2017, 2018, 2019. At the end of this we will also normalise all values by vehicle type to sum to 1. Then we will apply growth rates to define how much of each vehicle type we see growth in compared to the others for that transport type
#extract dictionary from csv
#for later, load in vehicle_type_growth_regions sheet and vehicle_type_growth sheet
vehicle_type_growth_regions = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='vehicle_type_growth_regions')
vehicle_type_growth = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='vehicle_type_growth')
#%%
regions_passenger = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='regions_passenger')
regions_freight = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='regions_freight')

#join regions to new_sales_shares_sum_0
new_sales_shares_passenger_0 = pd.merge(new_sales_shares_passenger_0, regions_passenger, how='left', on='Economy')
new_sales_shares_freight_0 = pd.merge(new_sales_shares_freight_0, regions_freight, how='left', on='Economy')
#%%
def df_to_nested_dict(df):
    outer_dict = {}
    for i, row in df.iterrows():
        scenario_dict = outer_dict.setdefault(row['Scenario'], {})
        inner_dict = scenario_dict.setdefault(row['Region'], {})
        vehicle_dict = inner_dict.setdefault(row['Vehicle Type'], {})
        if row['Drive'] in vehicle_dict:
            vehicle_dict[row['Drive']].append((row['Share'], row['Date']))
        else:
            vehicle_dict[row['Drive']] = [(row['Share'], row['Date'])]
    return outer_dict

passenger_drive_shares = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='passenger_drive_shares')
freight_drive_shares = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx',sheet_name='freight_drive_shares')

drive_shares_passenger_dict = df_to_nested_dict(passenger_drive_shares)
drive_shares_freight_dict = df_to_nested_dict(freight_drive_shares)

#%%
def create_drive_shares_df(df, drive_shares_dict):
    for scenario, regions in drive_shares_dict.items():
        for region, veh_types in regions.items():
            for veh_type, drives in veh_types.items():
                for drive, shares in drives.items():
                    for share in shares:
                        year = share[1]
                        share_ = share[0]
                        df.loc[(df['Region'] == region) & (df['Vehicle Type'] == veh_type) & (df['Drive'] == drive) & (df['Date'] >= year) & (df['Scenario'] == scenario), 'Drive_share'] = share_
    return df

#using the drive shares we laoded in, create a df with which to set the drive shares
new_sales_shares_passenger_1 = create_drive_shares_df(new_sales_shares_passenger_0, drive_shares_passenger_dict) 
new_sales_shares_freight_1 = create_drive_shares_df(new_sales_shares_freight_0, drive_shares_freight_dict)
################################################################################

#concatenate transport types
new_sales_shares_pre_interp = pd.concat([new_sales_shares_passenger_1, new_sales_shares_freight_1])
################################################################################
#%%
#finally, before we interpolate, if a value is na (missing) in 2017, 2018 or 2019, it is because it has no sales share at all for its vehicle type. we will set the sales share to the average of all otehr economys values for that vehicle type and drive type #this is jsut an error in the orignal data
#get missing data
new_sales_shares_pre_interp_missing = new_sales_shares_pre_interp.loc[(new_sales_shares_pre_interp['Date']>=2017) & (new_sales_shares_pre_interp['Date']<=2019) & (new_sales_shares_pre_interp['Drive_share'].isna())]

#note that this could be come an issue later ^
#drop cols we dont need
new_sales_shares_pre_interp_missing = new_sales_shares_pre_interp_missing.drop(columns=['Drive_share'])

#keep all other data in another df
new_sales_shares_pre_interp_not_missing = new_sales_shares_pre_interp.loc[~((new_sales_shares_pre_interp['Date']>=2017) & (new_sales_shares_pre_interp['Date']<=2019) & (new_sales_shares_pre_interp['Drive_share'].isna()))]

#get avg of not missing data
new_sales_shares_pre_interp_not_missing_avg = new_sales_shares_pre_interp_not_missing.groupby(['Date', 'Vehicle Type', 'Transport Type','Drive', 'Scenario'])['Drive_share'].mean().reset_index()

#join avg of not missing to missing
new_sales_shares_pre_interp_missing = new_sales_shares_pre_interp_missing.merge(new_sales_shares_pre_interp_not_missing_avg, on=['Date', 'Vehicle Type', 'Transport Type','Drive', 'Scenario'], how='left')

#and concat back to not missing to recreate original full set
new_sales_shares_concat = pd.concat([new_sales_shares_pre_interp_missing, new_sales_shares_pre_interp_not_missing])

#reset index. for some reason this needed to happen. dont know why
new_sales_shares_concat = new_sales_shares_concat.reset_index(drop=True)
#%%
################################################################################
#NOW DO INTERPOLATION
#order data by year
new_sales_shares_concat_interp = new_sales_shares_concat.sort_values(by=['Economy', 'Scenario', 'Date', 'Transport Type', 'Vehicle Type', 'Drive']).copy()

#do interpolation using spline adn order = X
X_order = 2#the higher the order the more smoothing but the less detail
new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'])['Drive_share'].apply(lambda group: group.interpolate(method='spline', order=X_order))

#%%
#where any values are negatives just set them to 0
new_sales_shares_concat_interp.loc[new_sales_shares_concat_interp['Drive_share']<0, 'Drive_share'] = 0

#now we just need to normalise by vehicle type
new_sales_shares_concat_interp['D_sum'] = new_sales_shares_concat_interp.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Date'])['Drive_share'].transform('sum')

new_sales_shares_concat_interp['Drive_share'] = new_sales_shares_concat_interp['Drive_share']/new_sales_shares_concat_interp['D_sum']

#%%
#drop uneeded cols
new_sales_shares_interp_by_drive = new_sales_shares_concat_interp.drop(['D_sum'], axis=1)
original_new_sales_shares_by_vehicle = new_sales_shares_sum.drop(['Transport_type_share', 'Drive_share'], axis=1)
#now merge the values onto the oroginal df and times by the vehicle type shares
new_sales_shares_all = new_sales_shares_interp_by_drive.merge(original_new_sales_shares_by_vehicle, on=['Economy', 'Scenario', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'], how='left')

#%%
#times the values to get the final values so that they sum to 1 by transport type
new_sales_shares_all['Transport_type_share'] = new_sales_shares_all['Vehicle_type_share_sum']*new_sales_shares_all['Drive_share']

#%%
#now we wnat to plot the data using plotly. we will plot with facets for each economy, and a different plot for each vehicle type, transport tyep combo
#first we need to create a new column that is the vehicle type and transport type
#we will also plot for comparison between new_sales_shares_sum and new_sales_shares_all so nerge that on now
plotting = False
if plotting:
    new_sales_shares_all_plot = new_sales_shares_all.copy()
    new_sales_shares_all_plot = new_sales_shares_all_plot.merge(new_sales_shares_sum[['Economy', 'Scenario', 'Date', 'Transport Type', 'Vehicle Type', 'Transport_type_share','Drive_share']], on=['Economy', 'Scenario', 'Date', 'Transport Type', 'Vehicle Type'], how='left', suffixes=('', '_8th'))

    import plotly.express as px
    new_sales_shares_all_plot['Vehicle_Transport'] = new_sales_shares_all_plot['Vehicle Type'] + '_' + new_sales_shares_all_plot['Transport Type']

    #extract a df for Value and Drive_share measures:
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot[['Economy', 'Scenario', 'Date', 'Vehicle_Transport', 'Drive', 'Drive_share', 'Drive_share_8th']]
    new_sales_shares_all_plot_value = new_sales_shares_all_plot[['Economy', 'Scenario', 'Date', 'Vehicle_Transport', 'Drive', 'Transport_type_share', 'Transport_type_share_8th']]

    #make them long
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.melt(id_vars=['Economy', 'Scenario', 'Date', 'Vehicle_Transport', 'Drive'], value_vars=['Drive_share', 'Drive_share_8th'], var_name='Measure', value_name='Drive_share')
    new_sales_shares_all_plot_value = new_sales_shares_all_plot_value.melt(id_vars=['Economy', 'Scenario', 'Date', 'Vehicle_Transport', 'Drive'], value_vars=['Transport_type_share', 'Transport_type_share_8th'], var_name='Measure', value_name='Transport_type_share')
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        for Vehicle_Transport in new_sales_shares_all_plot['Vehicle_Transport'].unique():
            plot_data = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Vehicle_Transport']==Vehicle_Transport) & (new_sales_shares_all_plot_drive_shares['Scenario']==scenario)].copy()

            fig = px.line(plot_data, x='Date', y='Drive_share', color='Drive', line_dash = 'Measure', facet_col='Economy',facet_col_wrap=3, title=Vehicle_Transport)
            #write to html in plotting_output\input_exploration\vehicle_sales_shares
            fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/{Vehicle_Transport}_{scenario}_drive_share.html', auto_open=False)

            plot_data = new_sales_shares_all_plot_value.loc[(new_sales_shares_all_plot_value['Vehicle_Transport']==Vehicle_Transport) & (new_sales_shares_all_plot_value['Scenario']==scenario)].copy()

            fig = px.line(plot_data, x='Date', y='Transport_type_share', color='Drive', line_dash = 'Measure', facet_col='Economy',facet_col_wrap=3, title=Vehicle_Transport)
            #write to html in plotting_output\input_exploration\vehicle_sales_shares
            fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/{Vehicle_Transport}_{scenario}Transport_type_share.html', auto_open=False)

#%%

###########################################################################

#now apply vehicle_type_growth. 
# first calcualte teh compound gorwth rate from the xlsx sheet=vehicle_type_growth, (it should be the growth rate . cumprod()) 
# times that by each Transport_type_share to adjust them for the growth rate
#then normalise all to 1 by transport type
vehicle_type_growth_regions = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx', sheet_name='vehicle_type_growth_regions')
vehicle_type_growth = pd.read_excel('input_data/vehicle_sales_share_inputs.xlsx', sheet_name='vehicle_type_growth')
new_sales_shares_all_new= new_sales_shares_all.copy()
#drop regiin col
new_sales_shares_all_new = new_sales_shares_all_new.drop(columns=['Region'])
#use vehicle_type_growth_regions to merge regions to econmy
new_sales_shares_all_new = new_sales_shares_all_new.merge(vehicle_type_growth_regions, on=['Economy'], how='left')
#merge vehicle_type_growth to new_sales_shares_all_new
new_sales_shares_all_new = new_sales_shares_all_new.merge(vehicle_type_growth, on=['Region', 'Scenario', 'Transport Type', 'Vehicle Type'], how='left')
#cumprod the growth rate (Growth) when grouping by Economy, Scenario, Transport Type, Vehicle Type and drive # but first sort by date
new_sales_shares_all_new = new_sales_shares_all_new.sort_values(by=['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Date'])
new_sales_shares_all_new['Compound_growth_rate'] = new_sales_shares_all_new.groupby(['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive'])['Growth'].cumprod()
#apply the growth rate to the Transport_type_share
new_sales_shares_all_new['Transport_type_share_new'] = new_sales_shares_all_new['Transport_type_share'] * new_sales_shares_all_new['Compound_growth_rate']
#normalise the Transport_type_share_new to 1
new_sales_shares_all_new['Transport_type_share_new'] = new_sales_shares_all_new.groupby(['Economy', 'Scenario', 'Transport Type'])['Transport_type_share_new'].transform(lambda x: x/x.sum())

#%%

#do some more plotting. just plot the Transport_type_share_new vs Transport_type_share
plotting=True
if plotting:
    new_sales_shares_all_plot = new_sales_shares_all_new.copy()

    import plotly.express as px

    #extract a df for Transport_type_share measures:
    new_sales_shares_all_plot_transport_type_shares = new_sales_shares_all_plot[['Economy', 'Scenario', 'Date','Transport Type', 'Vehicle Type', 'Drive',  'Transport_type_share', 'Transport_type_share_new']].copy()

    #make them long
    new_sales_shares_all_plot_transport_type_shares = new_sales_shares_all_plot_transport_type_shares.melt(id_vars=['Economy', 'Scenario', 'Date', 'Transport Type','Vehicle Type', 'Drive'], value_vars=['Transport_type_share', 'Transport_type_share_new'], var_name='Measure', value_name='Transport_type_share')

    #join drive and vehicle type
    new_sales_shares_all_plot_transport_type_shares['Vehicle_drive'] = new_sales_shares_all_plot_transport_type_shares['Vehicle Type'] + '_' + new_sales_shares_all_plot_transport_type_shares['Drive']
    for scenario in new_sales_shares_all_plot_transport_type_shares['Scenario'].unique():
        for economy in new_sales_shares_all_plot_transport_type_shares['Economy'].unique():
            plot_data = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Economy']==economy) & (new_sales_shares_all_plot_drive_shares['Scenario']==scenario)].copy()

            fig = px.line(plot_data, x='Date', y='Transport_type_share', color='Vehicle_drive', line_dash = 'Measure', facet_col='Transport Type',facet_col_wrap=1, title='Transport_type_share')
            #write to html in plotting_output\input_exploration\vehicle_sales_shares
            fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/{economy}_{scenario}Transport_type_share.html', auto_open=False)

#%%
#rename Transport_type_share_new to Vehicle^sales_share
new_sales_shares_all_new = new_sales_shares_all_new.rename(columns={'Transport_type_share_new':'Vehicle_sales_share'})
#drop cols
new_sales_shares_all_new = new_sales_shares_all_new.drop(columns=[ 'Drive_share', 'Vehicle_type_share_sum',
       'Transport_type_share', 'Region', 'Growth', 'Compound_growth_rate'])
#drop dupes
new_sales_shares_all_new = new_sales_shares_all_new.drop_duplicates()

###########################################################################
#%%
#save using scenario_id
new_sales_shares_all.to_csv('input_data/calculated/vehicle_stocks_change_share_{}.csv'.format(FILE_DATE_ID), index = False)

#save the variables we used to calculate the data by just saving this file
shutil.copyfile('workflow/create_user_inputs/edit_vehicle_sales_share_data.py', 'input_data/calculated/saved_scripts/edit_vehicle_sales_share_data_{}.py'.format(FILE_DATE_ID))

#%%
#before saving data to user input spreadsheety we will do some formatting:
#add cols for Unit,Medium,Data_available, frequency and Measure
new_sales_shares_all['Unit'] = '%'
new_sales_shares_all['Medium'] = 'road'
new_sales_shares_all['Data_available'] = 'data_available'
new_sales_shares_all['Measure'] = 'Vehicle_sales_share'
new_sales_shares_all['Frequency'] = 'Yearly'
#rename 'Vehicle_sales_share' to 'Value'
new_sales_shares_all = new_sales_shares_all.rename(columns={'Vehicle_sales_share':'Value'})


#%%
#also save the data to the user_input_spreadsheet
with pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx',engine='openpyxl', mode='a',if_sheet_exists = 'replace') as writer: 
       new_sales_shares_all.to_excel(writer, sheet_name='Vehicle_sales_share_new',  index=False)

#%%
REVERT = False
if REVERT:
       #if we want to revert the cahgnes so we use the data we imported to created this data at first in the spreadsheet:
       with pd.ExcelWriter('input_data/user_input_spreadsheet.xlsx',engine='openpyxl', mode='a',if_sheet_exists = 'replace') as writer:
              new_sales_shares.to_excel(writer, sheet_name='Vehicle_sales_share',  index=False)
       
#%%


