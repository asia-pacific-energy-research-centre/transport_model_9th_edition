
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'/transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
from plotly.subplots import make_subplots
import plotly.io as pio
import pandas as pd

from sklearn.preprocessing import StandardScaler

def remap_vehicle_types(df, value_col='Value', index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive']):

    #also group and sum by the following vehicle type cmbinations:
    vehicle_type_combinations = {'lt':'lpv', 'suv':'lpv', 'car':'lpv', 'ht':'trucks', 'mt':'trucks', 'bus':'bus', '2w':'2w', 'lcv':'lcv', 'all':'non-road', 'air':'non-road', 'rail':'non-road', 'ship':'non-road'}
    
    df['Vehicle Type new'] = df['Vehicle Type'].map(vehicle_type_combinations)
    #drop then rename vehicle type
    df['Vehicle Type'] = df['Vehicle Type new']
    #dxrop the new column
    df.drop(columns=['Vehicle Type new'], inplace=True)
    df = df.groupby(index_cols).sum().reset_index()
    return df
    
def remap_drive_types(df, value_col='Value', index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive']):
    drive_type_combinations = {'ice_g':'ice', 'ice_d':'ice', 'phev_d':'phev', 'phev_g':'phev', 'bev':'bev', 'fcev':'fcev', 'cng':'gas', 'lpg':'gas',  'all':'non-road', 'air':'non-road', 'rail':'non-road', 'ship':'non-road'}
    df["Drive new"] = df['Drive'].map(drive_type_combinations)
    df['Drive'] = df['Drive new']
    df.drop(columns=['Drive new'], inplace=True)
    df = df.groupby(index_cols).sum().reset_index()
    return df
###################################################
def plot_share_of_transport_type(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    # ##breakpoint()
    new_sales_shares_all_plot_drive_shares = pd.read_csv(f'input_data/user_input_spreadsheets/Vehicle_sales_share.csv')

    #and filter so data is less than GRAPHING_END_YEAR
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Date']<=GRAPHING_END_YEAR)].copy()
    #and filter so data is greater than OUTLOOK_BASE_YEAR
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Date']>=OUTLOOK_BASE_YEAR)].copy()

    # #sum up all the sales shares for each drive type
    # new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.groupby(['Scenario', 'Economy', 'Date', 'Vehicle Type','Transport Type', 'Drive']).sum().reset_index()

    new_sales_shares_all_plot_drive_shares = remap_vehicle_types(new_sales_shares_all_plot_drive_shares, value_col='Value', index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'])

    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'

    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        ###
        #grab stocks data to include in the plot. ths can be used to show how stocks increase slowly.
        stocks = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        
        #rename to Value
        stocks = stocks.rename(columns={'Stocks':'Value'})
        
        #and filter so data is less than GRAPHING_END_YEAR  
        stocks = stocks.loc[(stocks['Date']<=GRAPHING_END_YEAR)].copy()
        #and filter so data is greater than OUTLOOK_BASE_YEAR
        stocks = stocks.loc[(stocks['Date']>=OUTLOOK_BASE_YEAR)].copy()
        # #groupby and sum like in sales shares:
        # stocks = stocks[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive','Vehicle Type','Stocks']].groupby(['Scenario', 'Economy', 'Date','Vehicle Type', 'Transport Type', 'Drive']).sum().reset_index()
        
        stocks = remap_vehicle_types(stocks, value_col='Value', index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'])
        
        #now calucalte share of total stocks as a proportion like the sales share
        stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'])['Value'].apply(lambda x: x/x.sum())
        
        #create line_dash column and call it stocks
        stocks['line_dash'] = 'stocks'
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks])
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
                
        for economy in ECONOMIES_TO_PLOT_FOR:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()

            # #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. This helps to keep the plot clean too
            # plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060, 2070, 2080,2090, 2100] else 0, axis=1)
            #drop all drives except phev, bev and fcev
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='phev') | (plot_data['Drive']=='fcev')].copy()

            #concat drive and vehicle type
            plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Vehicle Type']
            
            #sort by date col and line_dash
            plot_data.sort_values(by=['Date'], inplace=True)
            #############
            #now plot
            
            title = f'Sales and stocks shares for passenger vehicles (%)'

            fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['drive_share_passenger'] = [fig,title]
            
            #############
            
            title = f'Sales and stocks shares for freight vehicles (%)'

            fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['drive_share_freight'] = [fig,title]
            #############
    
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    return fig_dict, color_preparation_list


def plot_share_of_vehicle_type_by_transport_type(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    new_sales_shares_all_plot_drive_shares = pd.read_csv(f'input_data/user_input_spreadsheets/Vehicle_sales_share.csv')
    #This data is in terms of transport type, so will need to normalise it to vehicle type by summing up the shares for each vehicle type and dividing individual shares by their sum

    # filter so data is less than GRAPHING_END_YEAR
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Date']<=GRAPHING_END_YEAR)].copy()

    new_sales_shares_all_plot_drive_shares = remap_vehicle_types(new_sales_shares_all_plot_drive_shares, value_col='Value', index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'])
        
    new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares.groupby(['Date','Economy', 'Scenario', 'Transport Type', 'Vehicle Type'])['Value'].transform(lambda x: x/x.sum())
    
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        ###
        #grab stocks data to include in the plot. ths can be used to show how stocks increase slowly.
        stocks = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        
        #rename to Value
        stocks = stocks.rename(columns={'Stocks':'Value'})
        
        #and filter so data is less than GRAPHING_END_YEAR  
        stocks = stocks.loc[(stocks['Date']<=GRAPHING_END_YEAR)].copy()
        
        # #groupby and sum like in sales shares:
        # stocks = stocks[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive','Vehicle Type','Stocks']].groupby(['Scenario', 'Economy', 'Date','Vehicle Type', 'Transport Type', 'Drive']).sum().reset_index()
        
        stocks = remap_vehicle_types(stocks, value_col='Value', index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'])
        
        #now calucalte share of total stocks for each vehicle type as a proportion like the sales share
        stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'])['Value'].apply(lambda x: x/x.sum())
        
        #create line_dash column and call it stocks
        stocks['line_dash'] = 'stocks'
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks])
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
                
        for economy in ECONOMIES_TO_PLOT_FOR:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()

            # #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. This helps to keep the plot clean too
            # plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060, 2070, 2080,2090, 2100] else 0, axis=1)
            #drop all drives except bev and fcev
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev')].copy()

            #concat drive and vehicle type
            plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Vehicle Type']
            
            #sort by date col
            plot_data.sort_values(by=['Date'], inplace=True)
            #############
            #now plot
            
            title = f'Shares for passenger (%)'

            fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
            ###breakpoint()
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['drive_share_passenger'] = [fig,title]
            
            #############
            
            title = f'Shares for freight (%)'

            fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
            
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['drive_share_freight'] = [fig,title]
            #############
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    
    return fig_dict,color_preparation_list
            

def plot_share_of_vehicle_type_by_transport_type_both_on_one_graph(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    #plot share of vehicle type for each economy and scenario
    new_sales_shares_all_plot_drive_shares = pd.read_csv(f'input_data/user_input_spreadsheets/Vehicle_sales_share.csv')
    #This data is in terms of transport type, so will need to normalise it to vehicle type by summing up the shares for each vehicle type and dividing individual shares by their sum

    # filter so data is less than GRAPHING_END_YEAR
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Date']<=GRAPHING_END_YEAR)].copy()

    new_sales_shares_all_plot_drive_shares = remap_vehicle_types(new_sales_shares_all_plot_drive_shares, value_col='Value', index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'])
        
    new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares.groupby(['Date','Economy', 'Scenario', 'Transport Type', 'Vehicle Type'])['Value'].transform(lambda x: x/x.sum())
    
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        ###
        #grab stocks data to include in the plot. ths can be used to show how stocks increase slowly.
        stocks = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        
        #rename to Value
        stocks = stocks.rename(columns={'Stocks':'Value'})
        
        #and filter so data is less than GRAPHING_END_YEAR  
        stocks = stocks.loc[(stocks['Date']<=GRAPHING_END_YEAR)].copy()
        
        # #groupby and sum like in sales shares:
        # stocks = stocks[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive','Vehicle Type','Stocks']].groupby(['Scenario', 'Economy', 'Date','Vehicle Type', 'Transport Type', 'Drive']).sum().reset_index()
        
        stocks = remap_vehicle_types(stocks, value_col='Value', index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'])
        
        #now calucalte share of total stocks for each vehicle type as a proportion like the sales share
        stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'])['Value'].apply(lambda x: x/x.sum())
        
        #create line_dash column and call it stocks
        stocks['line_dash'] = 'stocks'
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks])
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
                
        for economy in ECONOMIES_TO_PLOT_FOR:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()

            # #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. This helps to keep the plot clean too
            # plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060, 2070, 2080,2090, 2100] else 0, axis=1)
            #drop all drives except bev and fcev
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev')].copy()

            #concat drive and vehicle type
            plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Vehicle Type']
            
            #sort by date col
            plot_data.sort_values(by=['Date'], inplace=True)
            #############
            #now plot
            
            title = f'Sales and stock shares (%)'

            fig = px.line(plot_data, x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
            ###breakpoint()
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['drive_share_both'] = [fig,title]
            
            #############
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    
    return fig_dict,color_preparation_list

def share_of_sum_of_vehicle_types_by_transport_type(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    new_sales_shares_all_plot_drive_shares = pd.read_csv(f'input_data/user_input_spreadsheets/Vehicle_sales_share.csv')
    
    #This data is in terms of transport type but obv still shwo drive type, so just dropo vehicle type and we good

    # filter so data is less than GRAPHING_END_YEAR
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Date']<=GRAPHING_END_YEAR)].copy()
    
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive', 'Value']].groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive']).sum().reset_index()
        
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        ###
        #grab stocks data to include in the plot. ths can be used to show how stocks increase slowly.
        stocks = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        
        #rename to Value
        stocks = stocks.rename(columns={'Stocks':'Value'})
        
        #and filter so data is less than GRAPHING_END_YEAR  
        stocks = stocks.loc[(stocks['Date']<=GRAPHING_END_YEAR)].copy()
        
        #groupby and sum like in sales shares:
        stocks = stocks[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive','Stocks']].groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive']).sum().reset_index()
        
        #now calucalte share of total stocks for each transport type as a proportion like the sales share
        stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type'])['Value'].apply(lambda x: x/x.sum())
        
        #create line_dash column and call it stocks
        stocks['line_dash'] = 'stocks'
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks])
        
                
        for economy in ECONOMIES_TO_PLOT_FOR:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()

            # #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. This helps to keep the plot clean too
            # plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060, 2070, 2080,2090, 2100] else 0, axis=1)
            #drop all drives except bev and fcev
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev')].copy()
            
            #sort by date col
            plot_data.sort_values(by=['Date'], inplace=True)
            #############
            #now plot
            
            title = f'Shares for passenger (%)'

            fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
            
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['drive_share_passenger'] = [fig,title]
            
            #############
            
            title = f'Shares for freight (%)'

            fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
            
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['drive_share_freight'] = [fig,title]
            #############

    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    
    return fig_dict, color_preparation_list
###################################################



###################################################
def energy_use_by_fuel_type(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    for scenario in economy_scenario_concordance['Scenario'].unique():
            
        # pkl : plotting_output\all_economy_graphs\_20230614\model_output_with_fuels.pkl
        model_output_with_fuels = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_with_fuels.pkl')
        #and filter so data is less than GRAPHING_END_YEAR\
        model_output_with_fuels = model_output_with_fuels.loc[(model_output_with_fuels['Date']<=GRAPHING_END_YEAR)].copy()
        if DROP_NON_ROAD_TRANSPORT:
            model_output_with_fuels = model_output_with_fuels.loc[model_output_with_fuels['Medium']=='road'].copy()
        
        #create a new df with only the data we need: 
        energy_use_by_fuel_type = model_output_with_fuels.copy()
        energy_use_by_fuel_type= energy_use_by_fuel_type[['Economy', 'Date', 'Fuel', 'Energy']].groupby(['Economy', 'Date', 'Fuel']).sum().reset_index()
        
        #add units (by setting measure to Energy haha)
        energy_use_by_fuel_type['Measure'] = 'Energy'
        #add units
        energy_use_by_fuel_type['Unit'] = energy_use_by_fuel_type['Measure'].map(measure_to_unit_concordance_dict)
        
        for economy in ECONOMIES_TO_PLOT_FOR:
            #filter to economy
            energy_use_by_fuel_type_economy = energy_use_by_fuel_type.loc[energy_use_by_fuel_type['Economy']==economy].copy()
            
            # calculate total 'Energy' for each 'Fuel' 
            total_energy_per_fuel = energy_use_by_fuel_type_economy.groupby('Fuel')['Energy'].sum()

            # Create an ordered category of 'Fuel' labels sorted by total 'Energy'
            energy_use_by_fuel_type_economy['Fuel'] = pd.Categorical(
                energy_use_by_fuel_type_economy['Fuel'],
                categories = total_energy_per_fuel.sort_values(ascending=False).index,
                ordered=True
            )

            # Now sort the DataFrame by the 'Fuel' column:
            energy_use_by_fuel_type_economy.sort_values(by='Fuel', inplace=True)
            
            #now plot
            fig = px.area(energy_use_by_fuel_type_economy, x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
            
            #add units to y col
            title_text = 'Energy by Fuel ({})'.format(energy_use_by_fuel_type_economy['Unit'].unique()[0])
            
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['energy_use_by_fuel_type'] = [fig, title_text]
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_use_by_fuel_type_economy['Fuel'].unique().tolist())
    return fig_dict, color_preparation_list


def create_vehicle_type_stocks_plot(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    #loop through scenarios and grab the data for each scenario:
    for scenario in economy_scenario_concordance['Scenario'].unique():
        
        model_output_detailed = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        #rename Stocks to Value
        model_output_detailed = model_output_detailed.rename(columns={'Stocks':'Value'})
        
        #and filter so data is less than GRAPHING_END_YEAR
        model_output_detailed = model_output_detailed.loc[(model_output_detailed['Date']<=GRAPHING_END_YEAR)].copy()
        
        model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']=='road'].copy()
        
        #create a new df with only the data we need:
        stocks_by_vehicle_type = model_output_detailed.copy()
        stocks_by_vehicle_type = stocks_by_vehicle_type[['Economy', 'Date', 'Vehicle Type', 'Value']].groupby(['Economy', 'Date', 'Vehicle Type']).sum().reset_index()

        #add units (by setting measure to Freight_tonne_km haha)
        stocks_by_vehicle_type['Measure'] = 'Stocks'
        #add units
        stocks_by_vehicle_type['Unit'] = stocks_by_vehicle_type['Measure'].map(measure_to_unit_concordance_dict)

        
        for economy in ECONOMIES_TO_PLOT_FOR:
            #filter to economy
            stocks_by_vehicle_type_economy = stocks_by_vehicle_type.loc[stocks_by_vehicle_type['Economy']==economy].copy()
            
            # #also if stocks of 2w are more than 50% of total stocks then recategorise the vehicle types a bit
            # if stocks_by_vehicle_type_economy.loc[stocks_by_vehicle_type_economy['Vehicle Type']=='2w']['Value'].sum() > 0.5*stocks_by_vehicle_type_economy.loc[stocks_by_vehicle_type_economy['Vehicle Type']!='2w']['Value'].sum():
            # ##breakpoint()
            stocks_by_vehicle_type_economy = remap_vehicle_types(stocks_by_vehicle_type_economy, value_col='Value', index_cols = ['Date', 'Vehicle Type','Unit'])
            
            #sort by date
            # stocks_by_vehicle_type_economy = stocks_by_vehicle_type_economy.sort_values(by='Date')
            #now plot
            fig = px.line(stocks_by_vehicle_type_economy, x='Date', y='Value', color='Vehicle Type', color_discrete_map=colors_dict)
            title_text = 'Vehicle stocks (Millions)'#.format(stocks_by_vehicle_type_economy['Unit'].unique()[0])
            #add units to y col
            # fig.update_yaxes(title_text='Freight Tonne Km ({})'.format(stocks_by_vehicle_type_economy['Unit'].unique()[0]))

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['vehicle_type_stocks'] = [fig, title_text]
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(stocks_by_vehicle_type_economy['Vehicle Type'].unique().tolist())
    return fig_dict, color_preparation_list


def freight_tonne_km_by_drive(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    # model_output_detailed.pkl
    # #breakpoint()
    #loop through scenarios and grab the data for each scenario:
    for scenario in economy_scenario_concordance['Scenario'].unique():
        
        model_output_detailed = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        #and filter so data is less than GRAPHING_END_YEAR
        model_output_detailed = model_output_detailed.loc[(model_output_detailed['Date']<=GRAPHING_END_YEAR)].copy()
        if DROP_NON_ROAD_TRANSPORT:
            model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']=='road'].copy()
        #create a new df with only the data we need:
        freight_tonne_km_by_drive = model_output_detailed.copy()
        freight_tonne_km_by_drive = freight_tonne_km_by_drive[['Economy', 'Date', 'Drive', 'freight_tonne_km']].groupby(['Economy', 'Date', 'Drive']).sum().reset_index()
        
        #simplfiy drive type using remap_drive_types
        freight_tonne_km_by_drive = remap_drive_types(freight_tonne_km_by_drive, value_col='freight_tonne_km', index_cols = ['Economy', 'Date', 'Drive'])
        #add units (by setting measure to Freight_tonne_km haha)
        freight_tonne_km_by_drive['Measure'] = 'Freight_tonne_km'
        #add units
        freight_tonne_km_by_drive['Unit'] = freight_tonne_km_by_drive['Measure'].map(measure_to_unit_concordance_dict)

        for economy in ECONOMIES_TO_PLOT_FOR:
            #filter to economy
            freight_tonne_km_by_drive_economy = freight_tonne_km_by_drive.loc[freight_tonne_km_by_drive['Economy']==economy].copy()
            
            # calculate total 'freight_tonne_km' for each 'Drive' 
            total_freight_per_drive = freight_tonne_km_by_drive_economy.groupby('Drive')['freight_tonne_km'].sum()
            # #drop any 0's
            # total_freight_per_drive = total_freight_per_drive.loc[total_freight_per_drive.freight_tonne_km!=0]
            # Create an ordered category of 'Drive' labels sorted by total 'freight_tonne_km'
            freight_tonne_km_by_drive_economy['Drive'] = pd.Categorical(
                freight_tonne_km_by_drive_economy['Drive'],
                categories = total_freight_per_drive.sort_values(ascending=False).index,
                ordered=True
            )

            # Now you can sort your DataFrame by the 'Drive' column:
            freight_tonne_km_by_drive_economy.sort_values(by='Drive', inplace=True)

            #sort by date
            # freight_tonne_km_by_drive_economy = freight_tonne_km_by_drive_economy.sort_values(by='Date')
            #now plot
            fig = px.area(freight_tonne_km_by_drive_economy, x='Date', y='freight_tonne_km', color='Drive',color_discrete_map=colors_dict)
            title_text = 'Freight Tonne Km (Billions)'#.format(freight_tonne_km_by_drive_economy['Unit'].unique()[0])
            #add units to y col
            # fig.update_yaxes(title_text='Freight Tonne Km ({})'.format(freight_tonne_km_by_drive_economy['Unit'].unique()[0]))

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['freight_tonne_km_by_drive'] = [fig, title_text]
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(freight_tonne_km_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list

def passenger_km_by_drive(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    for scenario in economy_scenario_concordance['Scenario'].unique():
        
        model_output_detailed = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        #and filter so data is less than GRAPHING_END_YEAR
        model_output_detailed = model_output_detailed.loc[(model_output_detailed['Date']<=GRAPHING_END_YEAR)].copy()        
        if DROP_NON_ROAD_TRANSPORT:
            model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']=='road'].copy()
        #create a new df with only the data we need:
        passenger_km_by_drive = model_output_detailed.copy()
        passenger_km_by_drive = passenger_km_by_drive[['Economy', 'Date', 'Drive', 'passenger_km']].groupby(['Economy', 'Date', 'Drive']).sum().reset_index()
        #simplfiy drive type using remap_drive_types
        passenger_km_by_drive = remap_drive_types(passenger_km_by_drive, value_col='passenger_km', index_cols = ['Economy', 'Date', 'Drive'])
        
        #add units (by setting measure to Freight_tonne_km haha)
        passenger_km_by_drive['Measure'] = 'Passenger_km'
        #add units
        passenger_km_by_drive['Unit'] = passenger_km_by_drive['Measure'].map(measure_to_unit_concordance_dict)

        for economy in ECONOMIES_TO_PLOT_FOR:
            #filter to economy
            passenger_km_by_drive_economy = passenger_km_by_drive.loc[passenger_km_by_drive['Economy']==economy].copy()
            
            # calculate total 'passenger_km' for each 'Drive' 
            total_passenger_per_drive = passenger_km_by_drive_economy.groupby('Drive')['passenger_km'].sum()

            # Create an ordered category of 'Drive' labels sorted by total 'passenger_km'
            passenger_km_by_drive_economy['Drive'] = pd.Categorical(
            passenger_km_by_drive_economy['Drive'],
            categories = total_passenger_per_drive.sort_values(ascending=False).index,
            ordered=True
            )

            # Now sort the DataFrame by the 'Drive' column:
            passenger_km_by_drive_economy.sort_values(by='Drive', inplace=True)
            #sort by date

            # passenger_km_by_drive_economy = passenger_km_by_drive_economy.sort_values(by='Date')
            #now plot
            fig = px.area(passenger_km_by_drive_economy, x='Date', y='passenger_km', color='Drive', color_discrete_map=colors_dict)
            #add units to y col
            title_text = 'Passenger Km (Billions)'#.format(passenger_km_by_drive_economy['Unit'].unique()[0])
            # fig.update_yaxes(title_text='Passenger Km ({})'.format(passenger_km_by_drive_economy['Unit'].unique()[0]))

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['passenger_km_by_drive'] = [fig,title_text]
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(passenger_km_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list


def activity_growth(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    ###breakpoint()
    for scenario in economy_scenario_concordance['Scenario'].unique():
        
        model_output_detailed = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        
        #calcualte population growth and gdp growth as a percentage:
        # #first grasb only the data we need for this:
        # model_output_detailed_growth = model_output_detailed[['Economy', 'Date', 'Population', 'Gdp']].copy().drop_duplicates()
        #srot by date
        model_output_detailed = model_output_detailed.sort_values(by='Date')
        model_output_detailed['Population_growth'] = model_output_detailed.groupby(['Economy', 'Transport Type'])['Population'].pct_change()
        model_output_detailed['GDP_growth'] = model_output_detailed.groupby(['Economy', 'Transport Type'])['Gdp'].pct_change()
        
        #minus one from the activity_growth col  and times by 100
        model_output_detailed['Activity_growth'] = (model_output_detailed['Activity_growth']-1)*100
        
        #now drop all cols we dont need for activity growth
        model_output_detailed = model_output_detailed[['Economy', 'Date', 'Transport Type', 'Population_growth', 'GDP_growth', 'Activity_growth']].copy().drop_duplicates()
        
        #and filter so data is less than GRAPHING_END_YEAR
        model_output_detailed = model_output_detailed.loc[(model_output_detailed['Date']<=GRAPHING_END_YEAR)].copy()
        
        #melt so all measures in one col
        activity_growth = pd.melt(model_output_detailed, id_vars=['Economy',  'Date', 'Transport Type'], value_vars=['Population_growth', 'GDP_growth', 'Activity_growth'], var_name='Measure', value_name='Macro_growth')
        
        # #times macro growth by 100 to get percentage
        # activity_growth['Macro_growth'] = activity_growth['Macro_growth']*100
        
        # #add units (by setting measure to Freight_tonne_km haha)
        # activity_growth['Measure'] = 'Macro_growth'
        #add units
        activity_growth['Unit'] = '%'
        for economy in ECONOMIES_TO_PLOT_FOR:
            #filter to economy
            activity_growth_economy = activity_growth.loc[activity_growth['Economy']==economy].copy()

            #now plot
            fig = px.line(activity_growth_economy, x='Date', y='Macro_growth',color='Measure',line_dash='Transport Type', color_discrete_map=colors_dict)
            #add units to y col
            title_text = 'Activity Growth ({})'.format(activity_growth_economy['Unit'].unique()[0])
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['activity_growth'] = [fig, title_text]
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(activity_growth_economy['Measure'].unique().tolist())

    return fig_dict, color_preparation_list

def activity_and_macro_lines(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict, indexed=False):
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    # ##breakpoint()
    ##breakpoint()
    original_model_output_8th = pd.read_csv('input_data/from_8th/reformatted/activity_energy_road_stocks.csv')
    
    #grab only the Activity then sum it by economy, scenario and date
    original_model_output_8th = original_model_output_8th[['Economy', 'Scenario', 'Year', 'Activity']].copy().drop_duplicates()
    original_model_output_8th = original_model_output_8th.groupby(['Economy', 'Scenario', 'Year']).sum().reset_index()
    #rename actovity to Activity_8th
    original_model_output_8th = original_model_output_8th.rename(columns={'Activity':'Activity_8th', 'Year':'Date'})
    for scenario in economy_scenario_concordance['Scenario'].unique():
        
        model_output_detailed = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        #if scenario is Target then look for 'Carbon Neutral' in scenario name
        if scenario == 'Target':
            original_model_output_8th_scenario = original_model_output_8th.loc[original_model_output_8th['Scenario']=='Carbon Neutral'].copy()
        else:
            original_model_output_8th_scenario = original_model_output_8th.loc[original_model_output_8th['Scenario']==scenario].copy()
    
        #drop scenario col
        original_model_output_8th_scenario = original_model_output_8th_scenario.drop(columns=['Scenario'])
        
        #calcualte population, gdp, freight tonne km and passenger km as an index:
        # #first grasb only the data we need for this:
        # model_output_detailed_growth = model_output_detailed[['Economy', 'Scenario', 'Date', 'Population', 'Gdp']].copy().drop_duplicates()
        #srot by date
        # def calc_index(df, col):
        #     df = df.sort_values(by='Date')
        #     df['Value'] = df[col]/df[col].iloc[0]
        #     df['Measure'] = '{}_index'.format(col)
        #     df.drop(columns=[col], inplace=True)
        #     return df

        breakpoint()
        def calc_index(df, col, normalised=True):
            if normalised:
                df = df.sort_values(by='Date')

                # Normalize the data separately for each economy
                df[col] = df.groupby('Economy')[col].transform(lambda x: (x - x.min()) / (x.max() - x.min()))

                # Index the data separately for each economy
                df['Value'] = df.groupby('Economy')[col].transform(lambda x: x / x.iloc[0])

                df['Measure'] = '{}_index'.format(col)
                df.drop(columns=[col], inplace=True)
            else:
                df = df.sort_values(by='Date')

                # Standardize the data separately for each economy
                df[col] = df.groupby('Economy')[col].transform(lambda x: (x - x.mean()) / x.std())

                # Index the data separately for each economy
                df['Value'] = df.groupby('Economy')[col].transform(lambda x: x / x.iloc[0])

                df['Measure'] = '{}_index'.format(col)
                df.drop(columns=[col], inplace=True)

            return df

        def calc_growth(df, col):
            df = df.sort_values(by='Date')

            # Calculate percent growth separately for each economy
            df['Value'] = df.groupby('Economy')[col].transform(lambda x: (x / x.iloc[0] - 1) * 100)

            df['Measure'] = '{}_growth'.format(col)
            df.drop(columns=[col], inplace=True)

            return df
        
        if indexed:
            population = calc_index(model_output_detailed[['Population','Date','Economy']].drop_duplicates(),'Population')
            gdp = calc_index(model_output_detailed[['Gdp','Date','Economy']].drop_duplicates(),'Gdp')
            freight_km = calc_index(model_output_detailed[['freight_tonne_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'freight_tonne_km')
            passenger_km = calc_index(model_output_detailed[['passenger_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'passenger_km')
            original_model_output_8th_scenario = calc_index(original_model_output_8th_scenario,'Activity_8th')

        else:#calc growth
                
            population = calc_growth(model_output_detailed[['Population','Date','Economy']].drop_duplicates(),'Population')
            gdp = calc_growth(model_output_detailed[['Gdp','Date','Economy']].drop_duplicates(),'Gdp')
            freight_km = calc_growth(model_output_detailed[['freight_tonne_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'freight_tonne_km')
            passenger_km = calc_growth(model_output_detailed[['passenger_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'passenger_km')
            original_model_output_8th_scenario = calc_growth(original_model_output_8th_scenario,'Activity_8th')

            
        ##breakpoint()
        #set 'line_dash' to 'solid' in passenger_km and freight_km, then set to 'dash' in original_model_output_8th_scenario and  population and gdp
        passenger_km['line_dash'] = 'final'
        freight_km['line_dash'] = 'final'
        original_model_output_8th_scenario['line_dash'] = 'input'
        population['line_dash'] = 'input'
        gdp['line_dash'] = 'input'

            
        #concat all the data together then melt:
        index_data = pd.concat([population, gdp, freight_km, passenger_km,original_model_output_8th_scenario], axis=0)
                
        if indexed:
            index_data['Unit'] = 'Index'     
        else:                 
            index_data['Unit'] = 'Growth'
            
        #and filter so data is less than GRAPHING_END_YEAR
        index_data = index_data.loc[(index_data['Date']<=GRAPHING_END_YEAR)].copy()
        
        # #melt so all measures in one col
        # index_data = index_data.melt(id_vars=['Economy', 'Date'], value_vars=['Population_index', 'Gdp_index', 'freight_tonne_km_index', 'passenger_km_index', 'Activity_8th'], var_name='Measure', value_name='Index')
        
        for economy in ECONOMIES_TO_PLOT_FOR:
            #filter to economy
            index_data_economy = index_data.loc[index_data['Economy']==economy].copy()

            #now plot
            fig = px.line(index_data_economy, x='Date', y='Value',color='Measure', line_dash='line_dash',color_discrete_map=colors_dict)
            title_text = 'Activity Data ({})'.format(index_data_economy['Unit'].unique()[0])
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['activity_and_macro_lines'] = [fig, title_text]
            
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(index_data_economy['Measure'].unique().tolist())
    
    return fig_dict, color_preparation_list

def plot_supply_side_fuel_mixing(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    #plot supply side fuel mixing
    
    # supply_side_fuel_mixing_plot = pd.read_csv('intermediate_data/model_output_with_fuels/2_supply_side/{}'.format(model_output_file_name))
    
    #save as user input csv
    supply_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\supply_side_fuel_mixing_COMPGEN_base_year_adv.csv')
    
    #and filter so data is less than GRAPHING_END_YEAR
    supply_side_fuel_mixing = supply_side_fuel_mixing.loc[(supply_side_fuel_mixing['Date']<=GRAPHING_END_YEAR)].copy()
    #and so data is greater or equal to OUTLOOK_BASE_YEAR
    supply_side_fuel_mixing = supply_side_fuel_mixing.loc[(supply_side_fuel_mixing['Date']>=OUTLOOK_BASE_YEAR)].copy()
    #round the Supply_side_fuel_share column to 2dp
    supply_side_fuel_mixing['Supply_side_fuel_share'] = supply_side_fuel_mixing['Supply_side_fuel_share'].round(2)
    supply_side_fuel_mixing= supply_side_fuel_mixing[['Date', 'Economy','Scenario', 'Fuel','New_fuel' ,'Supply_side_fuel_share']].drop_duplicates()
    #supply side mixing is just the percent of a fuel type that is mixed into another fuel type, eg. 5% biodiesel mixed into diesel. We can use the concat of Fuel and New fuel cols to show the data:
    supply_side_fuel_mixing['Fuel mix'] = supply_side_fuel_mixing['New_fuel']# supply_side_fuel_mixing_plot['Fuel'] + ' mixed with ' + 
    #actually i changed that because it was too long. should be obivous that it's mixed with the fuel in the Fuel col (eg. biodesel mixed with diesel)
    
    #add units (by setting measure to Freight_tonne_km haha)
    supply_side_fuel_mixing['Measure'] = 'Fuel_mixing'
    #add units
    supply_side_fuel_mixing['Unit'] = '%'
    
    #sort by date
    supply_side_fuel_mixing = supply_side_fuel_mixing.sort_values(by='Date')
    for scenario in economy_scenario_concordance['Scenario'].unique():
        
        supply_side_fuel_mixing_plot_scenario = supply_side_fuel_mixing.loc[supply_side_fuel_mixing['Scenario']==scenario].copy()
        for economy in ECONOMIES_TO_PLOT_FOR:
            #filter to economy
            supply_side_fuel_mixing_plot_economy = supply_side_fuel_mixing_plot_scenario.loc[supply_side_fuel_mixing_plot_scenario['Economy']==economy].copy()

            title = 'Supply side fuel mixing for ' + scenario + ' scenario'
            fig = px.line(supply_side_fuel_mixing_plot_economy, x="Date", y="Supply_side_fuel_share", color='New_fuel',  title=title, color_discrete_map=colors_dict)

            #add units to y col
            title_text = 'Supply side fuel mixing ({})'.format(supply_side_fuel_mixing_plot_economy['Unit'].unique()[0])
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['fuel_mixing'] = [fig, title_text]
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(supply_side_fuel_mixing_plot_economy['New_fuel'].unique().tolist())
    return fig_dict, color_preparation_list

def create_charging_plot(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    #load in data from r'output_data\for_other_modellers\estimated_number_of_chargers.csv' and plot 'sum_of_fast_chargers_needed','sum_of_slow_chargers_needed' as a staked bar chart
    chargers = pd.read_csv(r'output_data\for_other_modellers\estimated_number_of_chargers.csv')
    
    #and filter so data is less than GRAPHING_END_YEAR
    chargers = chargers.loc[(chargers['Date']<=GRAPHING_END_YEAR)].copy()
    #and so data is greater or equal to OUTLOOK_BASE_YEAR
    chargers = chargers.loc[(chargers['Date']>=OUTLOOK_BASE_YEAR)].copy()
    chargers = chargers[['Economy', 'Scenario', 'Date', 'sum_of_fast_chargers_needed','sum_of_slow_chargers_needed']].drop_duplicates()
    for scenario in economy_scenario_concordance['Scenario'].unique():
        
        for economy in ECONOMIES_TO_PLOT_FOR:
            #filter to economy
            chargers_scenario = chargers.loc[chargers['Scenario']==scenario].copy()
            chargers_economy = chargers_scenario.loc[chargers_scenario['Economy']==economy].copy()

            title = 'Expected slow and fast public chargers needed for' + scenario + ' scenario'
            fig = px.bar(chargers_economy, x="Date", y=['sum_of_fast_chargers_needed','sum_of_slow_chargers_needed'], title=title, color_discrete_map=colors_dict)

            #add units to y col
            title_text = 'Public chargers'
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['charging'] = [fig, title_text]
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(['sum_of_fast_chargers_needed','sum_of_slow_chargers_needed'])
    return fig_dict, color_preparation_list

def prodcue_LMDI_mutliplicative_plot(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    for scenario in economy_scenario_concordance.Scenario.unique():
        if scenario == 'Reference':
            scenario_str = 'REF'
        elif scenario == 'Target':
            scenario_str = 'TGT'
        for economy in economy_scenario_concordance.Economy.unique():
            file_identifier = f'{economy}_{scenario_str}_passenger_road_2_Energy use_Hierarchical_hierarchical_multiplicative_output'
            lmdi_data = pd.read_csv(f'./intermediate_data/LMDI/{economy}/{file_identifier}.csv')
            #melt data so we have the different components of the LMDI as rows. eg. for freight the cols are: Date	Change in Energy	Energy intensity effect	freight_tonne_km effect	Engine type effect	Total Energy	Total_freight_tonne_km
            #we want to drop the last two plots, then melt the data so we have the different components of the LMDI as rows. eg. for freight the cols will end up as: Date	Effect. Then we will also create a line dash col and if the Effect is Change in Energy then the line dash will be solid, otherwise it will be dotted
            #drop cols by index, not name so it doesnt matter what thei names are
            lmdi_data_melt = lmdi_data.drop(lmdi_data.columns[[len(lmdi_data.columns)-1, len(lmdi_data.columns)-2]], axis=1)
            lmdi_data_melt = lmdi_data_melt.melt(id_vars=['Date'], var_name='Effect', value_name='Value')
            lmdi_data_melt['line_dash'] = lmdi_data_melt['Effect'].apply(lambda x: 'solid' if x == 'Change in Energy' else 'dash')
                        
            fig = px.line(lmdi_data_melt, x="Date", y='Value',  color='Effect', line_dash='line_dash', 
            color_discrete_map=colors_dict)
            
            title_text = 'Drivers of changes in energy use'
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['lmdi'] = [fig, title_text]

    return fig_dict
            