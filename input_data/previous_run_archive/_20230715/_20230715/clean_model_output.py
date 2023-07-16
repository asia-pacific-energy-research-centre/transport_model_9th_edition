#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%

def process_data(df, is_fuel=False):
    mean_value_cols = ['Activity_growth','Gdp_per_capita', 'Gdp', 'Population', 'Stocks_per_thousand_capita']
    weighted_mean_value_cols = ['Intensity','Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Mileage','Average_age']
    summable_value_cols = ['passenger_km','freight_tonne_km', 'Energy', 'Stocks', 'Travel_km',  'Surplus_stocks','Vehicle_sales_share']

    non_road_df = df[df['Medium'] != 'road'].copy()
    non_road_df['Drive'] = 'all'

    for col in weighted_mean_value_cols:
        if col in non_road_df.columns:
            non_road_df[col] = non_road_df[col].multiply(non_road_df['Activity_growth'], axis='index')

    summable_value_cols_1 = [col for col in non_road_df.columns if col in summable_value_cols]
    mean_value_cols_1 = [col for col in non_road_df.columns if col in mean_value_cols]
    weighted_mean_value_cols_1 = [col for col in non_road_df.columns if col in weighted_mean_value_cols]

    agg_dict = {**{col: 'sum' for col in summable_value_cols_1 + weighted_mean_value_cols_1}, **{col: 'mean' for col in mean_value_cols_1}}

    group_cols = ['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium']
    if is_fuel:
        group_cols.append('Fuel')

    grouped_df = non_road_df.groupby(group_cols).agg(agg_dict).reset_index()

    for col in weighted_mean_value_cols_1:
        grouped_df[col] = grouped_df[col].divide(grouped_df['Activity_growth'], axis='index')

    grouped_df = grouped_df.fillna(0)
    
    return pd.concat([df[df['Medium'] == 'road'], grouped_df])

def clean_non_road_drive_types(model_output_all_with_fuels, model_output_detailed,model_output_non_detailed):
    # breakpoint()
    # Then you can use the function like this:
    new_model_output_all_with_fuels = process_data(model_output_all_with_fuels, is_fuel=True)
    new_model_output_detailed = process_data(model_output_detailed, is_fuel=False)
    new_model_output_non_detailed = process_data(model_output_non_detailed, is_fuel=False)
    
    #jsuty in case we make updates, mcalcaulte Stocks per thousand cpita again:
    new_model_output_detailed['Stocks_per_thousand_capita'] = (new_model_output_detailed['Stocks']/new_model_output_detailed['Population'])* 1000000
    return new_model_output_all_with_fuels,new_model_output_detailed,new_model_output_non_detailed 

def clean_model_output():
    # model_output_file_name = 'model_output_years_2017_to_2050_DATE20220824_1043.csv'
    #take in model ouput and clean ready to use in analysis
    model_output_all_with_fuels = pd.read_csv('intermediate_data/model_output_with_fuels/2_supply_side/{}'.format(model_output_file_name))
    model_output_all = pd.read_csv('intermediate_data/model_output_concatenated/{}'.format(model_output_file_name))
    
    #if frequncy col is in either datafrasme, drop it
    if 'Frequency' in model_output_all.columns:
        model_output_all.drop(columns=['Frequency'], inplace=True)
    if 'Frequency' in model_output_all_with_fuels.columns:
        model_output_all_with_fuels.drop(columns=['Frequency'], inplace=True)
        
    # #remove any rows where the energy use is 0 from the 'with fuels' dataset. This helps because?
    # model_output_all_with_fuels = model_output_all_with_fuels[model_output_all_with_fuels['Energy'] > 0]

    
    #create a detailed and non detailed output from the 'without fuels' dataframes. Then create a model output which is jsut energy use, with the fuels. 
    #detailed output can jsut be the current output, the non_deetailed can just have stocks, energy and activity data
    model_output_detailed = model_output_all.copy()
    model_output_non_detailed = model_output_all.copy()
    model_output_non_detailed = model_output_non_detailed[['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium','Stocks', 'Activity', 'Energy']]

    #now create 'with fuels' output which will only contain energy use. This is to avoid any confusion because the 'with fuels' output contians activity and stocks replicated for each fuel type within a vehicel type / drive combination. 
    model_output_all_with_fuels = model_output_all_with_fuels[['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Fuel',  'Energy']]

    #at sxoem point in the model we get rows full of ans. jsut drop them here for now:
    model_output_detailed = model_output_detailed.dropna(how='all')
    model_output_non_detailed = model_output_non_detailed.dropna(how='all')
    model_output_all_with_fuels = model_output_all_with_fuels.dropna(how='all')
    
    #dsrop where Drive or Vehicle type is 'all' and the mdeium s road
    model_output_detailed = model_output_detailed[~((model_output_detailed['Drive'] == 'all') & (model_output_detailed['Medium'] == 'road'))]
    model_output_non_detailed = model_output_non_detailed[~((model_output_non_detailed['Drive'] == 'all') & (model_output_non_detailed['Medium'] == 'road'))]
    model_output_all_with_fuels = model_output_all_with_fuels[~((model_output_all_with_fuels['Drive'] == 'all') & (model_output_all_with_fuels['Medium'] == 'road'))]
    
    
    #save data without the new drive cols for non road
    model_output_detailed.to_csv('output_data/model_output_detailed/NON_ROAD_DETAILED_{}'.format(model_output_file_name), index=False)

    model_output_non_detailed.to_csv('output_data/model_output/NON_ROAD_DETAILED_{}'.format(model_output_file_name), index=False)

    model_output_all_with_fuels.to_csv('output_data/model_output_with_fuels/NON_ROAD_DETAILED_{}'.format(model_output_file_name), index=False)
   
    breakpoint()
    model_output_all_with_fuels,model_output_detailed,model_output_non_detailed = clean_non_road_drive_types(model_output_all_with_fuels,model_output_detailed,model_output_non_detailed)
   
   
    #save data with the new drive cols for non road:
    
    model_output_detailed.to_csv('output_data/model_output_detailed/{}'.format(model_output_file_name), index=False)

    model_output_non_detailed.to_csv('output_data/model_output/{}'.format(model_output_file_name), index=False)

    model_output_all_with_fuels.to_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name), index=False)
   
   
#%%
# clean_model_output()
#%%


# summable_value_cols = ['passenger_km','freight_tonne_km', 'Energy', 'Stocks', 'Travel_km',  'Surplus_stocks','Vehicle_sales_share']
# #some value cols are not summable because they are factors. so specify them for when we group by economy, then we can calculate the mean of them
# mean_value_cols = ['Gdp_per_capita', 'Gdp', 'Population', 'Stocks_per_thousand_capita']
# weighted_mean_value_cols = [ 'Intensity','Activity_growth','Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Mileage','Average_age']#these cols are divided by activity to get the weighted mean, based on hwo much activity there is for each row. We could have done stocks too, but this is probably better
# #currently the non road drive type is a reference to the fuel that is used. instead, jsut set them to the medium, as we now have th fuel mapped nayway.
# #extract non road data by fitlering for medium != road
# non_road_model_output_all_with_fuels = model_output_all_with_fuels[model_output_all_with_fuels['Medium'] != 'road']
# #set drive to medium then sum or avg depdning on the value in col (note that most of these cols will be na or 0 anyweay since they arent relevant for non road)
# non_road_model_output_all_with_fuels['Drive'] = non_road_model_output_all_with_fuels['Medium'].copy()

# summable_value_cols_1 = [col for col in non_road_model_output_all_with_fuels.columns if col in summable_value_cols]
# non_summable_value_cols_1 = [col for col in non_road_model_output_all_with_fuels.columns if col in non_summable_value_cols]
# agg_dict = {col: 'sum' if col in summable_value_cols_1 else 'mean' for col in summable_value_cols_1 + non_summable_value_cols_1}

# non_road_model_output_all_with_fuels = non_road_model_output_all_with_fuels.groupby(['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Fuel']).agg(agg_dict).reset_index()

# #rejoin to main dataframe
# new_model_output_all_with_fuels = pd.concat([model_output_all_with_fuels[model_output_all_with_fuels['Medium'] == 'road'], non_road_model_output_all_with_fuels])

# summable_value_cols = ['passenger_km','freight_tonne_km', 'Energy', 'Stocks', 'Travel_km',  'Surplus_stocks','Vehicle_sales_share']
# mean_value_cols = ['Gdp_per_capita', 'Gdp', 'Population', 'Stocks_per_thousand_capita']
# weighted_mean_value_cols = [ 'Intensity','Activity_growth','Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Mileage','Average_age']

# non_road_model_output_all_with_fuels = model_output_all_with_fuels[model_output_all_with_fuels['Medium'] != 'road']

# non_road_model_output_all_with_fuels['Drive'] = non_road_model_output_all_with_fuels['Medium'].copy()

# # calculate the product of the values and the weights (activity)
# for col in weighted_mean_value_cols:
#     non_road_model_output_all_with_fuels[col] = non_road_model_output_all_with_fuels[col].multiply(non_road_model_output_all_with_fuels['Activity'], axis='index')

# summable_value_cols_1 = [col for col in non_road_model_output_all_with_fuels.columns if col in summable_value_cols]
# mean_value_cols_1 = [col for col in non_road_model_output_all_with_fuels.columns if col in mean_value_cols]
# weighted_mean_value_cols_1 = [col for col in non_road_model_output_all_with_fuels.columns if col in weighted_mean_value_cols]

# agg_dict = {**{col: 'sum' for col in summable_value_cols_1 + weighted_mean_value_cols_1}, **{col: 'mean' for col in mean_value_cols_1}}

# grouped_df = non_road_model_output_all_with_fuels.groupby(['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Fuel']).agg(agg_dict).reset_index()

# # Calculate the weighted mean for non-summable columns
# for col in weighted_mean_value_cols_1:
#     grouped_df[col] = grouped_df[col].divide(grouped_df['Activity'], axis='index')

# # Handle any NaN values
# grouped_df = grouped_df.fillna(0)

# # Concatenate the road and non-road data
# new_model_output_all_with_fuels = pd.concat([model_output_all_with_fuels[model_output_all_with_fuels['Medium'] == 'road'], grouped_df])

# #############NOW deal with the non fuels dataframesummable_value_cols = ['passenger_km','freight_tonne_km', 'Energy', 'Stocks', 'Travel_km',  'Surplus_stocks','Vehicle_sales_share']
# mean_value_cols = ['Gdp_per_capita', 'Gdp', 'Population', 'Stocks_per_thousand_capita']
# weighted_mean_value_cols = [ 'Intensity','Activity_growth','Occupancy_or_load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Mileage','Average_age']

# non_road_model_output_all = model_output_all[model_output_all['Medium'] != 'road']
# non_road_model_output_all['Drive'] = non_road_model_output_all['Medium'].copy()

# # calculate the product of the values and the weights (activity)
# for col in weighted_mean_value_cols:
#     non_road_model_output_all[col] = non_road_model_output_all[col].multiply(non_road_model_output_all['Activity_growth'], axis='index')

# summable_value_cols_1 = [col for col in non_road_model_output_all.columns if col in summable_value_cols]
# mean_value_cols_1 = [col for col in non_road_model_output_all.columns if col in mean_value_cols]
# weighted_mean_value_cols_1 = [col for col in non_road_model_output_all.columns if col in weighted_mean_value_cols]

# agg_dict = {**{col: 'sum' for col in summable_value_cols_1 + weighted_mean_value_cols_1}, **{col: 'mean' for col in mean_value_cols_1}}

# grouped_df = non_road_model_output_all.groupby(['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium', 'Frequency']).agg(agg_dict).reset_index()

# # Calculate the weighted mean for non-summable columns
# for col in weighted_mean_value_cols_1:
#     grouped_df[col] = grouped_df[col].divide(grouped_df['Activity_growth'], axis='index')

# # Handle any NaN values
# grouped_df = grouped_df.fillna(0)

# # Concatenate the road and non-road data
# new_model_output_all = pd.concat([model_output_all[model_output_all['Medium'] == 'road'], grouped_df])