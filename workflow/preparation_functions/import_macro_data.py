#%%
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config
####Use this to load libraries and set variables. Feel free to edit that file as you need.
#%%
def import_macro_data():
    #grab the file D:\APERC\transport_model_9th_edition\input_data\macro\APEC_Gdp_population.csv
    #from 
    # Modelling/Data/Gdp/Gdp projections 9th/Gdp_estimates/Gdp_estimates_12May2023/data
    macro = pd.read_csv('./input_data/macro/APEC_GDP_data.csv')
    #filter so  variable is in ['real_Gdp', 'population','Gdp_per_capita']
    macro = macro[macro['variable'].isin(['real_GDP', 'population','GDP_per_capita'])]
    #drop units col
    macro = macro.drop(columns=['units'])

    #import coeffficients prodcuied in create_growth_parameters:
    # 'input_data/growth_coefficients_by_region.csv'
    growth_coeff = pd.read_csv('input_data/growth_coefficients_by_region.csv')
    #drop Region	alpha	r2	Model
    growth_coeff = growth_coeff.drop(columns=['Region', 'alpha', 'r2', 'Model'])
    growth_coeff.rename(columns={'Economy':'economy'}, inplace=True)
    #pull in activity_growth 
    activity_growth_8th = pd.read_csv('input_data/from_8th/reformatted/activity_growth_8th.csv')

    #pivot so each measure in the vairable column is its own column.
    macro = macro.pivot_table(index=['economy_code', 'economy', 'year'], columns='variable', values='value').reset_index()
    # macro.columns#Index(['economy_code', 'economy', 'date', 'real_Gdp', 'Gdp_per_capita', 'population'], dtype='object', name='variable')
    
    #make lowercase
    activity_growth_8th.columns = activity_growth_8th.columns.str.lower()
    #drop scenario and remove duplicvates
    activity_growth_8th = activity_growth_8th.drop(columns=['scenario']).drop_duplicates()
    #rename activity_growth to activity_growth_8th
    activity_growth_8th = activity_growth_8th.rename(columns={'activity_growth':'activity_growth_8th'})
    #soret by date
    activity_growth_8th = activity_growth_8th.sort_values(by=['economy', 'date'])
    #calcualte the growth rates compounded over time for use in diagnostics:
    activity_growth_8th['activity_growth_8th_index'] = activity_growth_8th.groupby('economy')['activity_growth_8th'].apply(lambda x: (1 + x).cumprod())

    #cahnge real_Gdp to Gdp for brevity (we dont use the actual values anyway(just growth rates)) and some other stuff:
    macro = macro.drop(columns=['economy'])
    macro = macro.rename(columns={'real_GDP':'Gdp', 'GDP_per_capita': 'Gdp_per_capita','population':'Population', 'economy_code':'economy', 'year':'date'})

    
    #times population and gdp by 1000 to get it in actual numbers
    macro['Population'] = macro['Population'] * 1000
    macro['Gdp'] = macro['Gdp'] * 1000000

    #calcualate gdp_times_capita
    macro['Gdp_times_capita'] = macro['Gdp'] * macro['Population']

    #calcaulte grwoth rates for all when you group by economy (make sure that date is sorted from low to high)
    macro1 = macro.copy()
    macro1 = macro1.sort_values(by=['economy', 'date'])
    macro1['Gdp_growth'] = macro1.groupby('economy')['Gdp'].pct_change()
    macro1['Population_growth'] = macro1.groupby('economy')['Population'].pct_change()
    macro1['Gdp_per_capita_growth'] = macro1.groupby('economy')['Gdp_per_capita'].pct_change()
    macro1['Gdp_times_capita_growth'] = macro1.groupby('economy')['Gdp_times_capita'].pct_change()
    
    #identify what variables will be timesd by coefficients anbd check we have them, by chekcing the var nabmes that end with _coeff:
    coeff_vars = [col for col in growth_coeff.columns if col.endswith('_coeff')]
    #drop coeff from the cols in coeff_vars
    vars = [col.replace('_coeff', '') for col in coeff_vars]
    if not set(vars).issubset(set(macro1.columns)):
        missing_cols = [col for col in vars if col not in macro1.columns]
        raise ValueError('The following variables are not in macro1: {}'.format(missing_cols))
    #combine it with above data using a merge
    macro1 = pd.merge(macro1, growth_coeff, on=['economy'], how='left')
    #filter any rows with nas
    macro1 = macro1.dropna()

    #calcuilate energy growth rate using the coefficents in the growth_coeff file:
    macro1['energy_growth_est'] = macro1['const']
    for col in vars:
        macro1['energy_growth_est'] = macro1['energy_growth_est'] + macro1[col] * macro1[col+'_coeff']
    #since we currently have no idea about intensity, we will assume that energy growth is the same as activity growth
    macro1['Activity_growth'] = macro1['energy_growth_est']
    #ADD ONE
    macro1['Activity_growth'] = macro1['Activity_growth'] + 1
    #also add one to activity_growth_8th.activity_growth_8th
    activity_growth_8th['activity_growth_8th'] = activity_growth_8th['activity_growth_8th'] + 1
    
    #join activity_growth_8th on for diagnostics so they are from same date
    macro1 = pd.merge(macro1, activity_growth_8th, on=['economy', 'date'], how='left')

    
    #make all cols start with caps 
    macro1.columns = [col.capitalize() for col in macro1.columns]
    #make tall and then attach units:
    macro1 = macro1.melt(id_vars=['Economy', 'Date'], value_vars=['Gdp_per_capita', 'Population', 'Gdp',
    'Gdp_times_capita', 'Gdp_growth', 'Population_growth',
    'Gdp_per_capita_growth', 'Gdp_times_capita_growth', 'Const',
    'Energy_growth_est', 'Activity_growth', 'Activity_growth_8th',
    'Activity_growth_8th_index']+coeff_vars, var_name='Measure', value_name='Value')

    
    #split into 'Transport Type' by creating one df for each transport type in 'passenger' and 'freight'
    macro1_passenger = macro1.copy()
    macro1_passenger['Transport Type'] = 'passenger'
    macro1_freight = macro1.copy()
    macro1_freight['Transport Type'] = 'freight'
    #concat
    macro1 = pd.concat([macro1_passenger, macro1_freight])

    
    #split macro into the required scenarios. perhaps later, if the macro differs by scenario we will do this somehwere ese:
    new_macro = pd.DataFrame()
    for scenario in config.SCENARIOS_LIST:
        s_macro = macro1.copy()
        s_macro['Scenario'] = scenario
        new_macro = pd.concat([new_macro, s_macro])
    macro1 = new_macro.copy()
    
    config.measure_to_unit_concordance = pd.read_csv('config/concordances_and_config_data/config.measure_to_unit_concordance.csv')
    macro1 = pd.merge(macro1, config.measure_to_unit_concordance[['Unit', 'Measure']], on=['Measure'], how='left')

    
    #save to intermediate_data/model_inputs/regression_based_growth_estimates.csv
    macro1.to_csv('intermediate_data/model_inputs/regression_based_growth_estimates.csv', index=False)

    
#%%
# import_macro_data()
#%%
























# #####
# #convert the 'Carbon Neutral_activity_growth' and 'Reference_activity_growth' to be in terms of actual numbers rather than growth rates (i.e. inverse of growth rate)
# macro1['Carbon Neutral_activity'] = (1 + macro1['Carbon Neutral_activity_growth']).cumprod()
# macro1['Reference_activity'] = (1 + macro1['Reference_activity_growth']).cumprod()
# #index it to be in terms of the other indexes 
# macro1['Carbon Neutral_activity_growth_index'] = macro1.groupby('economy')['Carbon Neutral_activity'].apply(lambda x: x/x.iloc[0])
# macro1['Reference_activity_growth_index'] = macro1.groupby('economy')['Reference_activity'].apply(lambda x: x/x.iloc[0])
# #calcaulte an index of all values so we can plot them on the same graph
# macro1['Gdp_index'] = macro1.groupby('economy')['Gdp'].apply(lambda x: x/x.iloc[0])
# macro1['Population_index'] = macro1.groupby('economy')['Population'].apply(lambda x: x/x.iloc[0])
# macro1['Gdp_per_capita_index'] = macro1.groupby('economy')['Gdp_per_capita'].apply(lambda x: x/x.iloc[0])
# #####
# #try it differently by using the smae method as (1 + df['Carbon Neutral_activity_growth']).cumprod() for all the variables
# macro1_indexed_pct_growth = macro1.copy()
# macro1_indexed_pct_growth['Gdp_index'] = (1 + macro1_indexed_pct_growth['Gdp_growth']).cumprod()
# macro1_indexed_pct_growth['Population_index'] = (1 + macro1_indexed_pct_growth['Population_growth']).cumprod()
# macro1_indexed_pct_growth['Gdp_per_capita_index'] = (1 + macro1_indexed_pct_growth['Gdp_per_capita_growth']).cumprod()
# macro1_indexed_pct_growth['Carbon Neutral_activity_growth_index'] = (1 + macro1_indexed_pct_growth['Carbon Neutral_activity_growth']).cumprod()
# macro1_indexed_pct_growth['Reference_activity_growth_index'] = (1 + macro1_indexed_pct_growth['Reference_activity_growth']).cumprod()
# #####
# 
# plot_this = False
# if plot_this:
#     #plot these as line graphs using plotly
#     #first melt
#     macro1_melt = macro1.melt(id_vars=['economy', 'date'], value_vars=['Gdp_index', 'Population_index', 'Gdp_per_capita_index', 'Carbon Neutral_activity_growth_index', 'Reference_activity_growth_index'], var_name='variable', value_name='value')
#     #then plot
#     import plotly.express as px
#     fig = px.line(macro1_melt, x='date', y='value', color='variable', facet_col='economy', facet_col_wrap=3)
#     #name y axis as an indexed
#     fig.update_yaxes(title_text='Index (base date = {}'.format(macro1['date'].min()))
#     #save to plotting_output\input_analysis
#     fig.write_html('plotting_output/input_analysis/macro_data_growth_indexes2.html')

#     macro1_melt = macro1_indexed_pct_growth.melt(id_vars=['economy', 'date'], value_vars=['Gdp_index', 'Population_index', 'Gdp_per_capita_index', 'Carbon Neutral_activity_growth_index', 'Reference_activity_growth_index'], var_name='variable', value_name='value')
#     #then plot
#     import plotly.express as px
#     fig = px.line(macro1_melt, x='date', y='value', color='variable', facet_col='economy', facet_col_wrap=3)
#     #name y axis as an indexed
#     fig.update_yaxes(title_text='Index (base date = {}'.format(macro1['date'].min()))
#     #save to plotting_output\input_analysis
#     fig.write_html('plotting_output/input_analysis/macro_data_growth_indexes1.html')


# #if it is not similar then we should try and estiamte an average multiplicative diffeence. We could use this to times by growth in gdp per capita to find the activity growth rate. 

# # if similar then great, we can use the gdp per capita growth rate to calcualte activity growth by timesing it by activity.
# # %%
# ######################################

# #try somethihng different: we will take in the og data and then test the effect of different ggrowth rates vs the actual growth rates hugh used.
# #also to help, we will split the data into similar regions in terms of growth and geography:

# #first, split data into regions using D:\APERC\transport_model_9th_edition\config\concordances_and_config_data\region_economy_mapping.csv and the columns Economy Region_growth_analysis



# #so take in the activity data and calcualte the growth rates for each economy
# 
# #data
# #take in activity data from 8th edition up to 2050 (activity_from_OSEMOSYS-hughslast.csv)
# activity = pd.read_csv('input_data/from_8th/reformatted/activity_from_OSEMOSYS-hughslast.csv')

# region_economy_mapping = pd.read_csv('config/concordances_and_config_data/region_economy_mapping.csv')
# #make cols lower case
# region_economy_mapping.columns = [col.lower() for col in region_economy_mapping.columns]
# #drop Region col
# region_economy_mapping.drop('region', axis=1, inplace=True)

# #keep reference only since the growth rates are the same
# activity = activity[activity['Scenario'] == 'Reference']
# 
# #define index cols
# config.INDEX_COLS = ['Economy','Date']

# #remove unnecessary cols and remove duplicates (all cols that arent config.INDEX_COLS or Value)
# activity.drop([col for col in activity.columns if col not in config.INDEX_COLS + ['Activity']], axis=1, inplace=True)
# activity.drop_duplicates(inplace=True)

# #sum up Value col by index cols
# activity_growth = activity.groupby(config.INDEX_COLS).sum().reset_index()

# #sort by year and everything else in ascending order
# activity_growth = activity_growth.sort_values(by=config.INDEX_COLS)

# #make cols lower case
# activity_growth.columns = [col.lower() for col in activity_growth.columns]
# 
# #join activity_growth with macro data
# macro2 = macro.copy()
# macro2 = macro2.merge(activity_growth, how='inner', on=['economy', 'date'])

# #merge the regions on and sum by region
# macro2 = macro2.merge(region_economy_mapping, how='left', on='economy')
# #drop nonneeded cols
# macro2.drop(['economy'], axis=1, inplace=True)
# macro2 = macro2.groupby(['region_growth_analysis', 'date']).sum().reset_index()
# #change actvitiy to be called 8th_activity
# macro2.rename(columns={'activity': '8th_activity'}, inplace=True)
# #calcaulte grwoth rates for all (except activity) when you group by region_growth_analysis (make sure that date is sorted form low to high)
# macro2 = macro2.sort_values(by=['region_growth_analysis', 'date'])
# macro2['Gdp_growth'] = macro2.groupby('region_growth_analysis')['Gdp'].pct_change()
# macro2['Population_growth'] = macro2.groupby('region_growth_analysis')['Population'].pct_change()
# macro2['Gdp_per_capita_growth'] = macro2.groupby('region_growth_analysis')['Gdp_per_capita'].pct_change()

# #the base year to 1 as the growth rate is not defined for the base year (in the code its actually using the row above for 2050 currently)
# macro2.loc[macro2['date'] == config.BASE_YEAR, ['Gdp_growth', 'Population_growth', 'Gdp_per_capita_growth']] = 0

# # Calculate cumulative product of growth rates+1
# #add 1 to the growth rates
# macro2['Gdp_growth2'] = macro2['Gdp_growth'] + 1
# macro2['Population_growth2'] = macro2['Population_growth'] + 1   
# macro2['Gdp_per_capita_growth2'] = macro2['Gdp_per_capita_growth'] + 1

# macro2['Gdp_index'] = macro2.groupby('region_growth_analysis')['Gdp_growth2'].cumprod()
# macro2['Population_index'] = macro2.groupby('region_growth_analysis')['Population_growth2'].cumprod()
# macro2['Gdp_per_capita_index'] = macro2.groupby('region_growth_analysis')['Gdp_per_capita_growth2'].cumprod()

# #calcuale activity using the growth rates
# #grab the 8th activity in first year (and keep region_growth_analysis)
# first_year_activity = macro2.loc[macro2['date'] == config.BASE_YEAR, ['region_growth_analysis', '8th_activity']]
# #call the col 8th_activity_first_year
# first_year_activity = first_year_activity.rename(columns={'8th_activity': '8th_activity_first_year'})
# #now join it on
# macro2 = macro2.merge(first_year_activity, how='left', on='region_growth_analysis')
# #now calcualte the activity for each growth rate
# macro2['Gdp_activity'] = macro2['Gdp_index'] * macro2['8th_activity_first_year']
# macro2['Population_activity'] = macro2['Population_index'] * macro2['8th_activity_first_year']
# macro2['Gdp_per_capita_activity'] = macro2['Gdp_per_capita_index'] * macro2['8th_activity_first_year']

# #melt so the cols Gdp_activity, Population_activity, Gdp_per_capita_activity and 8th_activity are all in one col called activity with a col called variable that says which one it is
# #first filter for useful cols
# macro2_melt = macro2[['region_growth_analysis', 'date', 'Gdp_activity', 'Population_activity', 'Gdp_per_capita_activity', '8th_activity']]

# macro2_melt = macro2.melt(id_vars=['region_growth_analysis', 'date'], value_vars=['Gdp_activity', 'Population_activity', 'Gdp_per_capita_activity', '8th_activity'], var_name='variable', value_name='activity')

# 
# #drop china and North America because they are too big and mess up the graph
# macro2_melt = macro2_melt[macro2_melt['region_growth_analysis'] != 'China']
# macro2_melt = macro2_melt[macro2_melt['region_growth_analysis'] != 'North America']
# #where variable is 8th acitivty, make 'line_dash' = '8th_activity' and everything else make it 'line_dash' = 'variable'
# macro2_melt['line_dash'] = macro2_melt['variable'].apply(lambda x: '8th_activity' if x == '8th_activity' else 'variable')
# plot_this = False
# if plot_this:
#     #plot these as line graphs using plotly
#     #then plot
#     #make the lines for everythign except 8th activity be dashed and slihtly transparent. Make sure the 8th activity is solid and not transparent
#     import plotly.express as px
#     fig = px.line(macro2_melt, x='date', y='activity', color='variable', line_dash='line_dash', color_discrete_sequence=px.colors.qualitative.Plotly, facet_col='region_growth_analysis', facet_col_wrap=3)
#     #name y axis as activity
#     fig.update_yaxes(title_text='Activity')
#     #save to plotting_output\input_analysis
#     fig.write_html('plotting_output/input_analysis/macro_data_growth_analysis_no_china.html')

# #for now save a dummy growth rate so we can continue with the model (this will be replaced with the real growth rates later)
# #we can gernally assume that gdp per capita is the best to use, and then the S curves for stocks will serve as a way of decreasing growth if stocks are too high.
# #it seems likely that passenger transport is slightly weighted towards population growth, and freight transport is slightly weighted towards Gdp growth so we can slightly adjust the values for these and recalcultate gdp per capita using this. 

# # freight_transport_population_parameter = 0.9
# # passenger_transport_population_parameter = 1.1
# # freight_transport_gdp_parameter = 1.1
# # passenger_transport_gdp_parameter = 0.9

# # new_macro = macro.copy()
# # new_macro['freight_Gdp_per_capita'] = (new_macro['Gdp'] * freight_transport_gdp_parameter) / (new_macro['Population'] * freight_transport_population_parameter)

# #join together passenger and frieght growth rates

# #save the new macro data






# ##################################################################################################











# # %%
# #try taking in energy use for transport from these ecoinomys balance tables. We have this data form the ESTO team:
# #\transport_data_system\intermediate_data\EGEDA\EGEDA_transport_outputDATE20230215.csv
# #load it in
# energy_use = pd.read_csv('D:/APERC/transport_data_system/intermediate_data/EGEDA/EGEDA_transport_outputDATE20230215.csv')

# #take in egeda_industry_output from same place as egeda_transport
# egeda_industry_output = pd.read_csv('D:/APERC/transport_data_system/intermediate_data/EGEDA/egeda_industry_outputDATE20230522.csv')
# #now do the same cleaning process

# #cols: ['Economy', 'Fuel_Type', 'Date', 'Value', 'Transport Type', 'Frequency','Unit', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive','Medium'],
# #get unique vlaues for each col
# # energy_use['Economy'].unique()
# # energy_use['Fuel_Type'].unique()
# #array(['1.2 Other bituminous coal', '7.01 Motor gasoline',
# #    '7.02 Aviation gasoline', '7.05 Kerosene type jet fuel',
# #    '7.07 Gas/diesel oil', '7.08 Fuel oil', '7.09 LPG',
# #    '17 Electricity', '19 Total', '21 Modern renewables',
# #    '7.04 Gasoline type jet fuel', '8.1 Natural gas', '7.06 Kerosene',
# #    '1.3 Sub-bituminous coal', '2.1 Coke oven coke',
# #    '7.12 White spirit SBP', '7.14 Bitumen', '1.1 Coking coal',
# #    '1.4 Anthracite', '1.5 Lignite', '6.1 Crude oil', '3 Peat',
# #    '2.3 Coke oven gas', '8.3 Gas works gas', '16.5 Biogasoline',
# #    '20 Total Renewables', '2.8 BKB/PB', '16.6 Biodiesel',
# #    '7.13 Lubricants', '6.2 Natural gas liquids',
# #    '7.17 Other products'], dtype=object)
# # energy_use['Date'].min()#'1980-12-31'
# # energy_use['Date'].max()#'2020-12-31'
# # energy_use['Medium'].unique()#array([nan, 'rail', 'road', 'air', 'ship', 'pipeline', 'nonspecified'],
# #   dtype=object)


# #TRANSPORT EGEDA
# #LETS DO A FULL ANALYSIS OF HOW ENERGY USE IS CORRELATED WITH THE GROWTH RATES LIEK ABOVE, SINCE WE HAVE ENEGRY USE FOR HISTORICAL DATA.
# #we will just grab '19 Total' for now
# energy_use = energy_use[energy_use['Fuel_Type'] == '19 Total']
# #double check that the sum of medium=nan is equal to the sum of all the other mediums
# # energy_use[energy_use['Medium'].isna()]['Value'].sum() == energy_use[energy_use['Medium'].notna()]['Value'].sum()#True
# #filter for medium = nan
# # energy_use = energy_use[energy_use['Medium'].isna()]
# #rename where medium = nan to 'Total'
# energy_use.loc[energy_use['Medium'].isna(), 'Medium'] = 'Total'
# #drop nonneeded cols
# energy_use = energy_use.drop(columns=['Fuel_Type', 'Frequency', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive'])
# #pivot so we have a column for each medium
# energy_use = energy_use.pivot(index=['Economy', 'Date'], columns='Medium', values='Value').reset_index()
# #while we are analysing medium we shjould also not aggregate into reigons, as certain economys focus on certain mediums more

# #INDUSTRY EGEDA
# #we will just grab '19 Total' for now
# egeda_industry_output = egeda_industry_output[egeda_industry_output['Fuel_Type'] == '19 Total']
# #drop nonneeded cols
# egeda_industry_output = egeda_industry_output.drop(columns=['Fuel_Type'])
# #call value industry_energy_use
# egeda_industry_output = egeda_industry_output.rename(columns={'Value': 'Industry'})

# #JOIN TRANSPORT AND INDUSTRY EGEDA
# #join together
# energy_use = energy_use.merge(egeda_industry_output, left_on=['Economy', 'Date'], right_on=['Economy', 'Date'], how='inner')

# #while we are analysing medium we shjould also not aggregate into reigons, as certain economys focus on certain mediums more
# #make all cols lowercase
# energy_use.columns = energy_use.columns.str.lower()
# #reformat date to be in year only
# energy_use['date'] = energy_use['date'].apply(lambda x: x[:4])
# #make into int
# energy_use['date'] = energy_use['date'].astype(int)
# 
# ##########################################
# 
# #do same for macro
# new_macro=macro.copy()
# new_macro.columns = new_macro.columns.str.lower()

# #join together
# energy_macro = energy_use.merge(new_macro, left_on=['economy', 'date'], right_on=['economy', 'date'], how='inner')

# #calculaqte a test value that is Gdp * Population. this might be better than gdp/population
# energy_macro['gdp_times_capita'] = energy_macro['gdp'] * energy_macro['population']
# 
# # Make sure data is sorted by year
# energy_macro = energy_macro.sort_values('date')

# # Calculate growth rates for each column except date and economy
# for col in energy_macro.columns:
#     if col not in ['date', 'economy']:
        
#         energy_macro[col + ' Growth Rate'] = energy_macro.groupby('economy')[col].pct_change()
#         #growth rates arent veryt interesting to look at, instead calcualte df['Cumulative Growth'] = (1 + df['Growth Rate']).cumprod() - 1
#         #thing is though, these will be made difficult to analyse by nas
#         energy_macro[col + ' Cumulative Growth'] = (1 + energy_macro[col + ' Growth Rate'])
#         energy_macro[col + ' Cumulative Growth'] = energy_macro.groupby('economy')[col + ' Cumulative Growth'].cumprod(skipna=True)

# 
# # Remove the first year (since it has no growth rate)
# energy_macro = energy_macro[energy_macro['date'] != energy_macro['date'].min()]

# #redo above plot but plot by region so we have bigger graphs.
# #import  reigonal mappigns from 'D:\APERC\transport_model_9th_edition\config\concordances_and_config_data\region_economy_mapping.csv'
# region_mappings = pd.read_csv('D:/APERC/transport_model_9th_edition/config/concordances_and_config_data/region_economy_mapping.csv')
# # region_mappings 	Economy	Region	Region_growth_analysis
# #so join on region
# energy_macro_r_old = energy_macro.merge(region_mappings, left_on='economy', right_on='Economy', how='inner')
# #we want to remove any cols with nan if they are based on medium, then remove any rows with nan if they are based on macro. BUT we want to do this by economy
# mediums = ['total', 'air','rail', 'road', 'ship', 'pipeline', 'nonspecified', 'industry']
# macros = ['gdp', 'population', 'gdp_per_capita','gdp_times_capita']
# #new df
# energy_macro_r = pd.DataFrame()
# #first remove cols with nan
# for economy in energy_macro_r_old.Economy.unique():
#     #grab just the economy
#     energy_macro_e = energy_macro_r_old[energy_macro_r_old['Economy'] == economy]
#     for col in energy_macro_e.columns:
#         for medium in mediums:
#             if medium == 'total':
#                 continue
#             if medium in col:
#                 if energy_macro_e[col].isna().sum() > 0:
#                     print('Dropping ' + col + ' because there are ' + str(energy_macro_e[col].isna().sum()) + ' missing values')
#                     energy_macro_e = energy_macro_e.drop(columns=[col])
#                 break
#         for macro in macros:
#             if macro in col:
#                 if energy_macro_e[col].isna().sum() > 0:
#                     print('Dropping rows for ' + col + ' because there are ' + str(energy_macro_e[col].isna().sum()) + ' missing values')
#                     energy_macro_e = energy_macro_e.dropna(subset=[col])
#                 break
#     #now add to new df
#     energy_macro_r = pd.concat([energy_macro_r, energy_macro_e], ignore_index=True)


# #then iterate through regions
# plot_this = False
# plot_all_mediums=False
# if plot_this:
#     for region in region_mappings.Region_growth_analysis.unique():
        
#         energy_macro_melt = energy_macro_r[energy_macro_r['Region_growth_analysis'] == region]
#         #drop Region, Economy and Region_growth_analysis cpls
#         energy_macro_melt = energy_macro_melt.drop(columns=['Region', 'Economy', 'Region_growth_analysis'])
#         #melt all, but keep date and economy
#         energy_macro_melt = energy_macro_melt.melt(id_vars=['economy', 'date'])
#         if not plot_all_mediums:
#             #drop all mediums except total and road
#             medium_values_to_remove = [value for value in energy_macro_melt['variable'].unique() if any(x in value for x in mediums) and not any(x in value for x in ['total', 'road', 'industry'])]
#             energy_macro_melt = energy_macro_melt[~energy_macro_melt['variable'].isin(medium_values_to_remove)]
#         #filter so variable only contains vlauyes with Growth Rate in it
#         energy_macro_melt = energy_macro_melt[energy_macro_melt['variable'].str.contains('Cumulative Growth')]
#         #create col to inidciate if it is a medium or macro
#         medium_values = [value for value in energy_macro_melt['variable'].unique() if any(x in value for x in mediums)]
#         energy_macro_melt['type'] = energy_macro_melt['variable'].apply(lambda x: 'medium' if x in medium_values else 'macro')

#         title = 'Energy Use Cumulative growth vs Macro Cumulative growth for ' + region
#         #plot with type as the dash
#         fig = px.line(energy_macro_melt, x='date', y='value', color='variable', facet_col='economy', line_dash='type', facet_col_wrap=3, title=title)

#         #save to html
#         fig.write_html('plotting_output/input_analysis/regions/energy_use_cumulative_growth_vs_macro_growth_cumulative' + region + '.html')

#         # #and plot correlation df
#         # title = 'Correlation Between Energy Use Cumulative growth and Cumulative growth Rate for ' + region
#         # fig2 = px.scatter(correlation_df_r[correlation_df_r['Region_growth_analysis'] == region], x='Medium', y='Macro', color='Correlation', facet_col='Economy', facet_col_wrap=3, title=title)

#         # #save to html
#         # fig2.write_html('plotting_output/input_analysis/regions/correlation_between_energy_use_cumulative_growth_rate_and_macro_growth_cumulative_' + region + '.html')
        

# 


# #################################################
# #################################################


# from scipy.stats import pearsonr

# # Calculate correlation between each medium and each macro variable
# #we will do it by economy as well
# mediums = ['total', 'air','rail', 'road', 'ship', 'nonspecified', 'pipeline', 'industry']
# macros = ['gdp', 'population', 'gdp_per_capita','gdp_times_capita']
# correlation_df = pd.DataFrame(columns=['Medium', 'Macro', 'Correlation', 'P-Value', 'Economy'])
# for medium in mediums:
#     for macro in macros:
#         for economy in energy_macro['economy'].unique():
#             #if there are nas in either of the columns, then the correlation will be nan, so as long as there are not more than 10 missing vlaues we will calculate the correlation
#             #ACTUALLY WE WILL JUST DROP ANY COLS WITH NA, BECAUSE THEY MAKE IT TOO DIFFICULT TO ANALYSE
#             #that is, unless the na is in a macro variable, in which case we drop the rows with na (because the na's will be at the start of the df, rtahter than in the middle)
#             economy_df = energy_macro[energy_macro['economy'] == economy]
#             if economy_df[medium + ' Growth Rate'].isna().sum() > 0 and (medium != 'total'):
#                 print('Not enough data for ' + economy + ' for ' + medium + ' and ' + macro + 'because there are ' + str(economy_df[medium + ' Growth Rate'].isna().sum()) + ' missing values in ' + medium)
#             elif economy_df[macro + ' Growth Rate'].isna().sum() > 0:
#                 print('Not enough data for ' + economy + ' for ' + medium + ' and ' + macro + 'because there are ' + str(economy_df[macro + ' Growth Rate'].isna().sum()) + ' missing values in ' + macro)
#             else:
#                 #drop infs 
#                 economy_df = economy_df.replace([np.inf, -np.inf], np.nan)
#                 #drop rows wiuth na
#                 economy_df = economy_df.dropna(subset=[medium + ' Growth Rate', macro + ' Growth Rate'])
#                 correlation, _ = pearsonr(economy_df[medium + ' Growth Rate'], economy_df[macro + ' Growth Rate'])
#                 #roudn to 2 dp
#                 correlation = round(correlation, 2)
#                 _ = round(_, 2)
#                 print('The correlation between ' + medium + ' and ' + macro + ' for ' + economy + ' is ' + str(correlation))
#                 #add as a row to df using pd.concat
#                 new_row = pd.DataFrame([[medium, macro, correlation, _, economy]], columns=['Medium', 'Macro', 'Correlation', 'P-Value', 'Economy'])
#                 correlation_df = pd.concat([correlation_df, new_row], ignore_index=True)
# 
# #do the same as above but for Cumulative Growth to see if it is more correlated

# # Calculate correlation between each medium and each macro variable
# #we will do it by economy as well
# mediums = ['total', 'air','rail', 'road', 'ship', 'nonspecified', 'pipeline','industry']
# macros = ['gdp', 'population', 'gdp_per_capita','gdp_times_capita']
# correlation_df_cumulative = pd.DataFrame(columns=['Medium', 'Macro', 'Correlation', 'P-Value', 'Economy'])
# for medium in mediums:
#     for macro in macros:
#         for economy in energy_macro['economy'].unique():
#             #if there are nas in either of the columns, then the correlation will be nan, so as long as there are not more than 10 missing vlaues we will calculate the correlation
#             economy_df = energy_macro[energy_macro['economy'] == economy]
#             if (economy_df[medium + ' Cumulative Growth'].isna().sum() >  0) and (medium != 'total'):
#                 print('Not enough data for ' + economy + ' for ' + medium + ' and ' + macro + 'because there are ' + str(economy_df[medium + ' Cumulative Growth'].isna().sum()) + ' missing values in ' + medium)
#             elif economy_df[macro + ' Cumulative Growth'].isna().sum() > 0:
#                 print('Not enough data for ' + economy + ' for ' + medium + ' and ' + macro + 'because there are ' + str(economy_df[macro + ' Cumulative Growth'].isna().sum()) + ' missing values in ' + macro)
#             else:
#                 #drop infs 
#                 economy_df = economy_df.replace([np.inf, -np.inf], np.nan)
#                 #drop rows wiuth na
#                 economy_df = economy_df.dropna(subset=[medium + ' Cumulative Growth', macro + ' Cumulative Growth'])
#                 correlation, _ = pearsonr(economy_df[medium + ' Cumulative Growth'], economy_df[macro + ' Cumulative Growth'])
#                 #roudn to 2 dp
#                 correlation = round(correlation, 2)
#                 _ = round(_, 2)
#                 print('The correlation between ' + medium + ' and ' + macro + ' for ' + economy + ' is ' + str(correlation))
#                 #add as a row to df using pd.concat
#                 new_row = pd.DataFrame([[medium, macro, correlation, _, economy]], columns=['Medium', 'Macro', 'Correlation', 'P-Value', 'Economy'])
#                 correlation_df_cumulative = pd.concat([correlation_df_cumulative, new_row], ignore_index=True)


# correlation_df_r = correlation_df.merge(region_mappings, left_on='Economy', right_on='Economy', how='inner')
# # %%
# plot_this = False
# if plot_this:
#     #attempt heatmap from chatgpt:
#     import plotly.express as px

#     # Assume your DataFrame is named correlation_df
#     economies = correlation_df['Economy'].unique()

#     for economy in economies:
#         # Create a pivot table for each economy
#         pivot_table = correlation_df[correlation_df['Economy'] == economy].pivot('Macro', 'Medium', 'Correlation')

#         # Create a heatmap for each pivot table
#         fig = px.imshow(pivot_table,
#                         labels=dict(x="Medium", y="Macro", color="Correlation"),
#                         title='Correlation Heatmap for ' + economy)
#         #save to html   
#         fig.write_html('plotting_output/input_analysis/economies/correlation_heatmap_' + economy + '.html')
# # %%
# plot_this = False
# if plot_this:
#     #attempt heatmap from chatgpt:
#     import plotly.express as px

#     # Assume your DataFrame is named correlation_df
#     economies = correlation_df_cumulative['Economy'].unique()

#     for economy in economies:
#         # Create a pivot table for each economy
#         pivot_table = correlation_df_cumulative[correlation_df_cumulative['Economy'] == economy].pivot('Macro', 'Medium', 'Correlation')

#         # Create a heatmap for each pivot table
#         fig = px.imshow(pivot_table,
#                         labels=dict(x="Medium", y="Macro", color="Correlation"),
#                         title='Correlation Heatmap for ' + economy)
#         #save to html   
#         fig.write_html('plotting_output/input_analysis/economies/correlation_heatmap_' + economy + '.html')
# 
# # energy_macro.columns
# # Index(['economy', 'date', 'total', 'air', 'nonspecified', 'pipeline', 'rail',
# #    'road', 'ship', 'industry', 'gdp_per_capita', 'population', 'gdp',
# #    'gdp_times_capita', 'total Growth Rate', 'total Cumulative Growth',
# #    'air Growth Rate', 'air Cumulative Growth', 'nonspecified Growth Rate',
# #    'nonspecified Cumulative Growth', 'pipeline Growth Rate',
# #    'pipeline Cumulative Growth', 'rail Growth Rate',
# #    'rail Cumulative Growth', 'road Growth Rate', 'road Cumulative Growth',
# #    'ship Growth Rate', 'ship Cumulative Growth', 'industry Growth Rate',
# #    'industry Cumulative Growth', 'gdp_per_capita Growth Rate',
# #    'gdp_per_capita Cumulative Growth', 'population Growth Rate',
# #    'population Cumulative Growth', 'gdp Growth Rate',
# #    'gdp Cumulative Growth', 'gdp_times_capita Growth Rate',
# #    'gdp_times_capita Cumulative Growth'],

# #OKAY. BASICALLY IT SEEMS THAT THE CORRELATION IS PRETTY CLEAR, OF COURSE. BUT THERE ARE SOME DIFFERENCES WHICH DONT SEEM TO BE BASED ON WHETHER AN ECONOMY IS DEVELOPING OR NOT: THE CORRELATION  BETWEEN Gdp/ENERGY VS Gdp_PER_CAPITA/ENERGY IS DIFFERENT FOR DIFFERENT ECONOMIES. FOR EXAMPLE, NZ IS MORE CORRELATED WITH Gdp, BUT AUS IS MORE CORRELATED WITH Gdp_PER_CAPITA. ITS NOT CLEAR WHAT IS CAUSING THE DIFFERENCE. HAVE LOOKED AT THINGS LIKE: EFFECT OF POPULATION GROWTH RATE ON Gdp PER CPITA. 
# #COULD BE BECAUSE OF RELATIVE EFFICIENCY LEVELS COMING FROM THE INDUSTRY MIX. LIKE MAYBE HTERE IS A CORRELATION BETWEEN ENERGY USE IN INDUSTRY AND ENERGY USE IN TRANSPORT?
# #PERHAPS ITS ENOUGH JUST TO TAKE IT AS IT IS AND SLIGHTLY CHANGE THE WEIGHTING OF THE MACRO VARIABLES DEPENDING ON THE ECONOMY? 

# #do regression analysis using Population and gdp as independent vars:
# # !pip install statsmodels
# import statsmodels.api as sm

# #create new df with less cols
# df = energy_macro[['economy', 'date', 'total','road', 'gdp', 'population', 'gdp_per_capita', 'gdp_times_capita']]
# #rename total to energy_total
# df = df.rename(columns={'total': 'energy_total'})
# #rename road to energy_road
# df = df.rename(columns={'road': 'energy_road'})

# #drop rows with na
# df = df.dropna()

# # Assume you have a DataFrame df with 'independent_variable1', 'independent_variable2' and 'dependent_variable'
# X = df[['population', 'gdp']]
# y = df['energy_total']

# # Add a constant (intercept term) to the independent variables
# X = sm.add_constant(X)

# # Fit the model
# model = sm.OLS(y, X)
# results = model.fit()

# # Print out the statistics
# print(results.summary())
# 
# #plot
# import plotly.graph_objects as go

# # Creating the 3D scatter plot
# fig = go.Figure(data=[go.Scatter3d(
#     x=df['gdp'],
#     y=df['population'],
#     z=df['energy_total'],
#     mode='markers',
#     marker=dict(
#         size=4,
#         color='blue',
#         opacity=0.8
#     )
# )])

# # Creating the plane of best fit
# x_pred = np.linspace(df['gdp'].min(), df['gdp'].max(), 10)
# y_pred = np.linspace(df['population'].min(), df['population'].max(), 10)
# xx_pred, yy_pred = np.meshgrid(x_pred, y_pred)
# model_viz = np.array([xx_pred.flatten(), yy_pred.flatten()]).T
# model_viz = sm.add_constant(model_viz)
# predicted = results.predict(exog=model_viz)
# zz_pred = predicted.reshape(xx_pred.shape)

# # Adding the plane of best fit to the figure
# fig.add_trace(go.Surface(x=x_pred, y=y_pred, z=zz_pred, name='Predicted Plane'))

# # Set labels
# fig.update_layout(scene = dict(
#                     xaxis_title='gdp',
#                     yaxis_title='population',
#                     zaxis_title='energy_total'),
#                     width=700,
#                     margin=dict(r=20, b=10, l=10, t=10))

# #save to html
# fig.write_html("plotting_output/input_analysis/energy_vs_macro_regression.html")
# 
# #                             OLS Regression Results                            
# # ==============================================================================
# # Dep. Variable:           energy_total   R-squared:                       0.873
# # Model:                            OLS   Adj. R-squared:                  0.873
# # Method:                 Least Squares   F-statistic:                     2779.
# # Date:                Tue, 23 May 2023   Prob (F-statistic):               0.00
# # Time:                        17:10:19   Log-Likelihood:                -7212.8
# # No. Observations:                 809   AIC:                         1.443e+04
# # Df Residuals:                     806   BIC:                         1.445e+04
# # Df Model:                           2                                         
# # Covariance Type:            nonrobust                                         
# # ==============================================================================
# #                  coef    std err          t      P>|t|      [0.025      0.975]
# # ------------------------------------------------------------------------------
# # const         18.5482     72.484      0.256      0.798    -123.731     160.827
# # population    -0.0045      0.000    -15.689      0.000      -0.005      -0.004
# # gdp            0.0014   2.05e-05     69.410      0.000       0.001       0.001
# # ==============================================================================
# # Omnibus:                      185.592   Durbin-Watson:                   1.824
# # Prob(Omnibus):                  0.000   Jarque-Bera (JB):             6628.334
# # Skew:                           0.141   Prob(JB):                         0.00
# # Kurtosis:                      17.020   Cond. No.                     4.76e+06
# # ==============================================================================

# # Notes:
# # [1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
# # [2] The condition number is large, 4.76e+06. This might indicate that there are
# # strong multicollinearity or other numerical problems.
# # AIC:  14431.618096345892
# # BIC:  14445.705493097068

# 
# #i think we actually want to try find the relation between 'growth' in energy and growth in gdp/population. So we need to do a regression on the growth rates.
# df_growth = energy_macro[['economy', 'date', 'total Growth Rate','road Growth Rate', 'gdp Growth Rate', 'population Growth Rate', 'gdp_per_capita Growth Rate', 'gdp_times_capita Growth Rate']]
# #rename total to energy_total
# df_growth = df_growth.rename(columns={'total Growth Rate': 'energy_total_growth'})
# #rename road to energy_road
# df_growth = df_growth.rename(columns={'road Growth Rate': 'energy_road_growth'})
# #rename gdp to energy_gdp
# df_growth = df_growth.rename(columns={'gdp Growth Rate': 'gdp_growth'})
# #rename population to energy_population
# df_growth = df_growth.rename(columns={'population Growth Rate': 'population_growth'})
# #rename gdp_per_capita to energy_gdp_per_capita
# df_growth = df_growth.rename(columns={'gdp_per_capita Growth Rate': 'gdp_per_capita_growth'})
# #rename gdp_times_capita to energy_gdp_times_capita
# df_growth = df_growth.rename(columns={'gdp_times_capita Growth Rate': 'gdp_times_capita_growth'})

# #drop rows with na
# df_growth = df_growth.dropna()

# # Assume you have a DataFrame df with 'independent_variable1', 'independent_variable2' and 'dependent_variable'
# X = df_growth[['gdp_growth', 'population_growth']]
# y = df_growth['energy_total_growth']

# # Add a constant (intercept term) to the independent variables
# X = sm.add_constant(X)

# # Fit the model
# model = sm.OLS(y, X)
# results = model.fit()

# # Print out the statistics
# print(results.summary())

# 
# #plot
# import plotly.graph_objects as go

# # Creating the 3D scatter plot
# fig = go.Figure(data=[go.Scatter3d(
#     x=df_growth['gdp_growth'],
#     y=df_growth['population_growth'],
#     z=df_growth['energy_total_growth'],
#     mode='markers',
#     marker=dict(
#         size=4,
#         color='blue',
#         opacity=0.8
#     )
# )])

# # Creating the plane of best fit
# x_pred = np.linspace(df_growth['gdp_growth'].min(), df_growth['gdp_growth'].max(), 10)
# y_pred = np.linspace(df_growth['population_growth'].min(), df_growth['population_growth'].max(), 10)
# xx_pred, yy_pred = np.meshgrid(x_pred, y_pred)
# model_viz = np.array([xx_pred.flatten(), yy_pred.flatten()]).T
# model_viz = sm.add_constant(model_viz)
# predicted = results.predict(exog=model_viz)
# zz_pred = predicted.reshape(xx_pred.shape)
# # Adding the plane of best fit to the figure
# fig.add_trace(go.Surface(x=x_pred, y=y_pred, z=zz_pred, name='Predicted Plane'))

# # Set labels
# fig.update_layout(scene = dict(
#                     xaxis_title='Gdp Growth',
#                     yaxis_title='Population Growth',
#                     zaxis_title='Energy Growth'),
#                     width=700,
#                     margin=dict(r=20, b=10, l=10, t=10))

# #save to html
# fig.write_html("plotting_output/input_analysis/energy_growth_vs_macro_regression.html")

# # %%
# #lets try a polynomial regression, just for fun
# #i expect it is not a great idea because i cannot think of any reason why the relation would be polynomial) (probably results in overfitting)
# from sklearn.preprocessing import PolynomialFeatures

# # Assume you have a DataFrame df with 'independent_variable1', 'independent_variable2' and 'dependent_variable'
# X = df_growth[['gdp_growth', 'population_growth']]
# y = df_growth['energy_total_growth']

# # Transform your features into a higher degree
# poly = PolynomialFeatures(degree=2)
# X_poly = poly.fit_transform(X)

# # Fit the model
# model = sm.OLS(y, X_poly)
# results = model.fit()

# # Print out the statistics
# print(results.summary())
# 
# # Create the prediction plane
# x_pred = np.linspace(df_growth['gdp_growth'].min(), df_growth['gdp_growth'].max(), 10)
# y_pred = np.linspace(df_growth['population_growth'].min(), df_growth['population_growth'].max(), 10)
# xx_pred, yy_pred = np.meshgrid(x_pred, y_pred)
# model_viz = np.array([xx_pred.flatten(), yy_pred.flatten()]).T
# model_viz_poly = poly.transform(model_viz)
# predicted = results.predict(exog=model_viz_poly)
# zz_pred = predicted.reshape(xx_pred.shape)

# # Creating the 3D scatter plot
# fig = go.Figure(data=[go.Scatter3d(
#     x=df_growth['gdp_growth'],
#     y=df_growth['population_growth'],
#     z=df_growth['energy_total_growth'],
#     mode='markers',
#     marker=dict(
#         size=4,
#         color='blue',
#         opacity=0.8
#     )
# )])

# # Adding the plane of best fit to the figure
# fig.add_trace(go.Surface(x=x_pred, y=y_pred, z=zz_pred, name='Predicted Plane'))

# # Set labels
# fig.update_layout(scene = dict(
#                     xaxis_title='Gdp Growth',
#                     yaxis_title='Population Growth',
#                     zaxis_title='Energy Growth'),
#                     width=700,
#                     margin=dict(r=20, b=10, l=10, t=10))

# #save to html
# fig.write_html("plotting_output/input_analysis/polynomial_energy_growth_vs_macro_regression.html")

# # %%
# #it is actually not bad because the higher pop growth indicates a lower development level and in turn a lower energy growth because of lower gdp per capita... hmm

# #lets take a lok at regression analysis for gdp_per_cpita
# 
# #i think we actually want to try find the relation between 'growth' in energy and growth in gdp/population. So we need to do a regression on the growth rates.
# df_growth = energy_macro[['economy', 'date', 'total Growth Rate','road Growth Rate', 'gdp_per_capita Growth Rate']]
# #rename total to energy_total
# df_growth = df_growth.rename(columns={'total Growth Rate': 'energy_total_growth'})
# #rename road to energy_road
# df_growth = df_growth.rename(columns={'road Growth Rate': 'energy_road_growth'})
# #rename gdp_per_capita to gdp_per_capita
# df_growth = df_growth.rename(columns={'gdp_per_capita Growth Rate': 'gdp_per_capita_growth'})

# #drop rows with na
# df_growth = df_growth.dropna()

# # Assume you have a DataFrame df with 'independent_variable1', 'independent_variable2' and 'dependent_variable'
# X = df_growth['gdp_per_capita_growth']
# y = df_growth['energy_total_growth']

# # Add a constant (intercept term) to the independent variables
# X = sm.add_constant(X)

# # Fit the model
# model = sm.OLS(y, X)
# results = model.fit()

# # Print out the statistics
# print(results.summary())

# 
# #i want to create a functionised version of the regression analysis done above so i dont have to repeat it for each variable
# from sklearn.linear_model import LinearRegression
# def regression_analysis(df, x, y):
#     #drop rows with na
#     df = df.dropna()

#     # Assume you have a DataFrame df with 'independent_variable1', 'independent_variable2' and 'dependent_variable'
#     X = df[x]
#     Y = df[y]

#     # Add a constant (intercept term) to the independent variables
#     X = sm.add_constant(X)

#     # Fit the model
#     model = sm.OLS(Y, X)
#     results = model.fit()

#     # Print out the statistics
#     #print out the names of the variables
#     print('Regression analysis for {} and {}'.format(x,y))
#     print(results.summary())
#     return results

# def plot_regression_results(results, df, x, y,plot_name,add_one=True):
#     #if x is list, then it is a multiple regression
#     if isinstance(x, list):
#         if len(x) > 2:
#             regression_type = 'multiple_plus'#we will plot each variabl;e against the dependent variable on a different facet
#         else:
#             regression_type = 'multiple'
#     else:
#         regression_type = 'simple'
    
#     # Create the prediction plane/line
#     if regression_type == 'multiple':
#         x_pred = np.linspace(df[x[0]].min(), df[x[0]].max(), 10)
#         y_pred = np.linspace(df[x[1]].min(), df[x[1]].max(), 10)
#         xx_pred, yy_pred = np.meshgrid(x_pred, y_pred)
#         model_viz = np.array([xx_pred.flatten(), yy_pred.flatten()]).T
#         model_viz = sm.add_constant(model_viz)
#         predicted = results.predict(exog=model_viz)
#         zz_pred = predicted.reshape(xx_pred.shape)
#     elif regression_type == 'simple':
#         x_pred = np.linspace(df[x].min(), df[x].max(), 10)
#         model_viz = sm.add_constant(x_pred)
#         predicted = results.predict(exog=model_viz)
#         y_pred = predicted.reshape(x_pred.shape)
#     else:
#         multiple_plus_df = pd.DataFrame()
#         for x_var in x:
#             #put the variable into dataframe with cols: independent_var_name, independent_var_value, dependent_var_value

#             new_df_values = pd.DataFrame()
#             new_df_values['independent_var_value'] = df[x_var]
#             new_df_values['dependent_var_value'] = df[y]
#             new_df_values['independent_var_name'] = x_var

#             multiple_plus_df = pd.concat([multiple_plus_df,new_df_values])
                


#     # Creating the scatter plot
#     if regression_type == 'multiple':
#         fig = go.Figure(data=[go.Scatter3d(
#             x=df[x[0]],
#             y=df[x[1]],
#             z=df[y],
#             mode='markers',
#             marker=dict(
#                 size=4,
#                 color='blue',
#                 opacity=0.8
#             )
#         )])
#     elif regression_type == 'simple':
#         fig = go.Figure(data=[go.Scatter(
#             x=df[x],
#             y=df[y],
#             mode='markers',
#             marker=dict(
#                 size=4,
#                 color='blue',
#                 opacity=0.8
#             )
#         )])
#     elif regression_type == 'multiple_plus':
#         #plot using express
#         # if there are negative x vlaues then dont use log scale
#         if multiple_plus_df['independent_var_value'].min() < 0:
#             if add_one:
#                 multiple_plus_df['independent_var_value'] = multiple_plus_df['independent_var_value'] + 1
#                 multiple_plus_df['dependent_var_value'] = multiple_plus_df['dependent_var_value'] + 1
#                 fig = px.scatter(multiple_plus_df, x="independent_var_value", y="dependent_var_value", facet_col="independent_var_name", trendline="ols", log_x=True)
#                 fig.update_layout(title_text=plot_name)
#             else:
#                 fig = px.scatter(multiple_plus_df, x="independent_var_value", y="dependent_var_value", facet_col="independent_var_name", trendline="ols")
#                 fig.update_layout(title_text=plot_name)
#         else:
#             fig = px.scatter(multiple_plus_df, x="independent_var_value", y="dependent_var_value", facet_col="independent_var_name", trendline="ols", log_x=True)
#             fig.update_layout(title_text=plot_name)

#         #save the plot
#         fig.write_html('plotting_output/input_analysis/macro_regression/{}.html'.format(plot_name))
#         return

#     # Adding the plane of best fit to the figure
#     if regression_type == 'multiple':
#         fig.add_trace(go.Surface(x=x_pred, y=y_pred, z=zz_pred, name='Predicted Plane'))
#     elif regression_type == 'simple':
#         fig.add_trace(go.Scatter(x=x_pred, y=y_pred, name='Predicted Line'))

#     # Set labels
#     if regression_type == 'multiple':
#         fig.update_layout(scene = dict(
#                             xaxis_title=x[0],
#                             yaxis_title=x[1],
#                             zaxis_title=y),
#                             width=700,
#                             margin=dict(r=20, b=10, l=10, t=10))
#     elif regression_type == 'simple':
#         fig.update_layout(xaxis_title=x,
#                             yaxis_title=y,
#                             width=700,
#                             margin=dict(r=20, b=10, l=10, t=10))
        
#     #save the plot
#     fig.write_html('plotting_output/input_analysis/macro_regression/{}.html'.format(plot_name))
    


# # %%
# #i think we actually want to try find the relation between 'growth' in energy and growth in gdp/population. So we need to do a regression on the growth rates.
# df = energy_macro[['economy', 'date', 'total Growth Rate','road Growth Rate', 'gdp Growth Rate', 'population Growth Rate', 'gdp_per_capita Growth Rate', 'gdp_times_capita Growth Rate', 'total','road', 'gdp', 'population', 'gdp_per_capita', 'gdp_times_capita']]
# df.rename(columns={'total': 'energy_total', 'road': 'energy_road', 'gdp Growth Rate': 'gdp_growth', 'population Growth Rate': 'population_growth', 'gdp_per_capita Growth Rate': 'gdp_per_capita_growth', 'gdp_times_capita Growth Rate': 'gdp_times_capita_growth', 'total Growth Rate': 'energy_total_growth', 'road Growth Rate': 'energy_road_growth'}, inplace=True)
# 
# #do it for the following:
# #energy_road_growth vs gdp_per_capita_growth, gdp_times_capita_growth, gdp_growth, population_growth
# #energy_total_growth vs gdp_per_capita_growth, gdp_times_capita_growth, gdp_growth, population_growth
# #and then do it without growth rates:
# #energy_road vs gdp_per_capita, gdp_times_capita, gdp, population
# #energy_total vs gdp_per_capita, gdp_times_capita, gdp, population
# plot_this = False
# if plot_this:
#     independent_variables = ['gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth', 'population_growth']
#     dependent_variable = 'energy_road_growth'

#     plot_regression_results(regression_analysis(df, independent_variables, dependent_variable), df, independent_variables, dependent_variable, 'regression_macro_growth_vs_energy_road_growth')

#     independent_variables = ['gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth', 'population_growth']
#     dependent_variable = 'energy_total_growth'

#     plot_regression_results(regression_analysis(df, independent_variables, dependent_variable), df, independent_variables, dependent_variable, 'regression_macro_growth_vs_energy_total_growth')

#     independent_variables = ['gdp_per_capita', 'gdp_times_capita', 'gdp', 'population']
#     dependent_variable = 'energy_road'

#     plot_regression_results(regression_analysis(df, independent_variables, dependent_variable), df, independent_variables, dependent_variable, 'regression_macro_vs_energy_road')

#     independent_variables = ['gdp_per_capita', 'gdp_times_capita', 'gdp', 'population']
#     dependent_variable = 'energy_total'

#     plot_regression_results(regression_analysis(df, independent_variables, dependent_variable), df, independent_variables, dependent_variable, 'regression_macro_vs_energy_total')
# 
# #ok it works. Now lets do it by economy (ignore energy road)
# #filter for only 07_INA
# df = df[df['economy'] == '07_INA']
# for economy in df.economy.unique():
#     economy_df = df[df['economy'] == economy]
#     independent_variables = ['gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth', 'population_growth']
#     dependent_variable = 'energy_total_growth'

#     plot_regression_results(regression_analysis(economy_df, independent_variables, dependent_variable), economy_df, independent_variables, dependent_variable, '{}_regression_macro_growth_vs_energy_total_growth'.format(economy))
    
#     independent_variables = ['gdp_per_capita', 'gdp_times_capita', 'gdp', 'population']
#     dependent_variable = 'energy_total'

#     plot_regression_results(regression_analysis(economy_df, independent_variables, dependent_variable), economy_df, independent_variables, dependent_variable, '{}_regression_macro_vs_energy_total'.format(economy))

#     independent_variables = ['gdp_per_capita_growth', 'gdp_times_capita_growth', 'gdp_growth']
#     dependent_variable = 'energy_total_growth'

#     plot_regression_results(regression_analysis(economy_df, independent_variables, dependent_variable), economy_df, independent_variables, dependent_variable, '{}_regression_macro_growth_vs_energy_total_growth_no_pop'.format(economy))

# # %%
# #i think we need to douible check population growth as its having negative ciorrelation inn medcs. might be best to leave out 





# # independent_variables = ['gdp_per_capita', 'gdp_times_capita', 'gdp', 'population']
# # dependent_variable = 'energy_total'
# # results = regression_analysis(economy_df, independent_variables, dependent_variable)
# # df =economy_df
# # x=independent_variables 
# # y=dependent_variable
# # plot_name ='{}_regression_macro_vs_energy_total'.format('07_INA')
# # # plot_regression_results(, economy_df, independent_variables, dependent_variable, '{}_regression_macro_vs_energy_total'.format(economy))



# # 

# # #if x is list, then it is a multiple regression
# # if isinstance(x, list):
# #     if len(x) > 2:
# #         regression_type = 'multiple_plus'#we will plot each variabl;e against the dependent variable on a different facet
# #     else:
# #         regression_type = 'multiple'
# # else:
# #     regression_type = 'simple'

# # # Create the prediction plane/line
# # if regression_type == 'multiple':
# #     x_pred = np.linspace(df[x[0]].min(), df[x[0]].max(), 10)
# #     y_pred = np.linspace(df[x[1]].min(), df[x[1]].max(), 10)
# #     xx_pred, yy_pred = np.meshgrid(x_pred, y_pred)
# #     model_viz = np.array([xx_pred.flatten(), yy_pred.flatten()]).T
# #     model_viz = sm.add_constant(model_viz)
# #     predicted = results.predict(exog=model_viz)
# #     zz_pred = predicted.reshape(xx_pred.shape)
# # elif regression_type == 'simple':
# #     x_pred = np.linspace(df[x].min(), df[x].max(), 10)
# #     model_viz = sm.add_constant(x_pred)
# #     predicted = results.predict(exog=model_viz)
# #     y_pred = predicted.reshape(x_pred.shape)
# # else:
# #     multiple_plus_df = pd.DataFrame()
# #     for x_var in x:
# #         #put the variable into dataframe with cols: independent_var_name, independent_var_value, dependent_var_value

# #         new_df_values = pd.DataFrame()
# #         new_df_values['independent_var_value'] = df[x_var]
# #         new_df_values['dependent_var_value'] = df[y]
# #         new_df_values['independent_var_name'] = x_var

# #         multiple_plus_df = pd.concat([multiple_plus_df,new_df_values])
        

# # 
# # # Creating the scatter plot
# # if regression_type == 'multiple':
# #     fig = go.Figure(data=[go.Scatter3d(
# #         x=df[x[0]],
# #         y=df[x[1]],
# #         z=df[y],
# #         mode='markers',
# #         marker=dict(
# #             size=4,
# #             color='blue',
# #             opacity=0.8
# #         )
# #     )])
# # elif regression_type == 'simple':
# #     fig = go.Figure(data=[go.Scatter(
# #         x=df[x],
# #         y=df[y],
# #         mode='markers',
# #         marker=dict(
# #             size=4,
# #             color='blue',
# #             opacity=0.8
# #         )
# #     )])
# # elif regression_type == 'multiple_plus':
# #     #plot using express
# #     # if there are negative x vlaues then dont use log scale
# #     if multiple_plus_df['independent_var_value'].min() < 0:
# #         fig = px.scatter(multiple_plus_df, x="independent_var_value", y="dependent_var_value", facet_col="independent_var_name", trendline="ols")
# #         fig.update_layout(title_text=plot_name)
# #     else:
# #         fig = px.scatter(multiple_plus_df, x="independent_var_value", y="dependent_var_value", facet_col="independent_var_name", trendline="ols", log_x=True)
# #         fig.update_layout(title_text=plot_name)

# #     #save the plot
# #     fig.write_html('plotting_output/input_analysis/macro_regression/{}.html'.format(plot_name))
# #     return

# # # Adding the plane of best fit to the figure
# # if regression_type == 'multiple':
# #     fig.add_trace(go.Surface(x=x_pred, y=y_pred, z=zz_pred, name='Predicted Plane'))
# # elif regression_type == 'simple':
# #     fig.add_trace(go.Scatter(x=x_pred, y=y_pred, name='Predicted Line'))

# # # Set labels
# # if regression_type == 'multiple':
# #     fig.update_layout(scene = dict(
# #                         xaxis_title=x[0],
# #                         yaxis_title=x[1],
# #                         zaxis_title=y),
# #                         width=700,
# #                         margin=dict(r=20, b=10, l=10, t=10))
# # elif regression_type == 'simple':
# #     fig.update_layout(xaxis_title=x,
# #                         yaxis_title=y,
# #                         width=700,
# #                         margin=dict(r=20, b=10, l=10, t=10))
    
# # #save the plot
# # fig.write_html('plotting_output/input_analysis/macro_regression/{}.html'.format(plot_name))

# # # %%
