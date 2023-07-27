
###IMPORT GLOBAL VARIABLES FROM config.py
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import sys
sys.path.append("./config")
import config

import pandas as pd 
import numpy as np
import yaml
import datetime
import shutil
import sys
import os 
import re
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import matplotlib
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
####Use this to load libraries and set variables. Feel free to edit that file as you need.

#%%

def remap_vehicle_types(df, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive']):

    #also group and sum by the following vehicle type cmbinations:
    vehicle_type_combinations = {'lt':'lpv', 'suv':'lpv', 'car':'lpv', 'ht':'trucks', 'mt':'trucks', 'bus':'bus', '2w':'2w', 'lcv':'lcv', 'all':'non-road', 'air':'non-road', 'rail':'non-road', 'ship':'non-road'}
    
    df['Vehicle Type new'] = df['Vehicle Type'].map(vehicle_type_combinations)
    #drop then rename vehicle type
    df['Vehicle Type'] = df['Vehicle Type new']
    #dxrop the new column
    df.drop(columns=['Vehicle Type new'], inplace=True)
    df = df.groupby(new_index_cols).sum().reset_index()
    return df
    
def remap_drive_types(df, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'], mapping_type='original', aggregation_type=('sum',), include_non_road=True):
    if mapping_type == 'original':
        if include_non_road:
            drive_type_combinations = {'ice_g':'ice_g', 'ice_d':'ice_d', 'phev_d':'phev_d', 'phev_g':'phev_g', 'bev':'bev', 'fcev':'fcev', 'cng':'cng', 'lpg':'lpg',  'all':'non-road', 'air':'air', 'rail':'rail', 'ship':'ship'}
        else:
            drive_type_combinations = {'ice_g':'ice', 'ice_d':'ice', 'phev_d':'phev', 'phev_g':'phev', 'bev':'bev', 'fcev':'fcev', 'cng':'gas', 'lpg':'gas',  'all':'non-road', 'air':'non-road', 'rail':'non-road', 'ship':'non-road'}
        df["Drive new"] = df['Drive'].map(drive_type_combinations)
        df['Drive'] = df['Drive new']
        df.drop(columns=['Drive new'], inplace=True)
    elif mapping_type == 'simplified':
        if include_non_road:
            drive_type_combinations = {'ice_g':'ice_g', 'ice_d':'ice_d', 'phev_d':'phev_d', 'phev_g':'phev_g', 'bev':'bev', 'fcev':'fcev', 'cng':'cng', 'lpg':'lpg',  'all':'all', 'air':'air', 'rail':'rail', 'ship':'ship'}
        else:
            drive_type_combinations = {'ice_g':'ice', 'ice_d':'ice', 'phev_d':'ev', 'phev_g':'ev', 'bev':'ev', 'fcev':'ev', 'cng':'ice', 'lpg':'ice',  'all':'non-road', 'air':'non-road', 'rail':'non-road', 'ship':'non-road'}
        df["Drive new"] = df['Drive'].map(drive_type_combinations)
        df['Drive'] = df['Drive new']
        df.drop(columns=['Drive new'], inplace=True)
    # if aggregation_type[0] == 'weighted_average':
    #     df_grouped = df.groupby(new_index_cols)
    #     df_weights_sum = df_grouped['Stocks'].transform('sum')
    #     df_weights_sum[df_weights_sum == 0] = 1  # Assign a default value of 1 for zero weights sum
    if aggregation_type[0] == 'weighted_average':
        df['Weighted Value'] = df[value_col] * df[aggregation_type[1]]
        #sum weighted values
        df['Weighted Value sum'] = df.groupby(new_index_cols)['Weighted Value'].transform('sum')
        #sum wieght
        df['Weight sum'] = df.groupby(new_index_cols)[aggregation_type[1]].transform('sum')
        #fill 0 with 1
        df['Weight sum'] = df['Weight sum'].replace(0,1)
        #calculate weighted average
        df[value_col] = df['Weighted Value sum']/df['Weight sum']
        #drop the columns we don't need anymore
        df.drop(columns=['Weighted Value', 'Weighted Value sum', 'Weight sum'], inplace=True)
        

    elif aggregation_type[0]=='sum':
        df = df.groupby(new_index_cols).sum().reset_index()
    return df

def identify_high_2w_economies(stocks_df):
    #remap vehicle types only for econmoys where the 2w vehicle type makes up more than 30% of stocks. This way, tehre wont be too many lines on the plot that arent near 0.#we will spit the data into two dataframes, one with high 2w and one without, then remap the vehicle types for the one with high 2w, then concat them back together
    stocks_sum = stocks_df.groupby(['Economy', 'Vehicle Type'])['Value'].sum().reset_index().copy()
    stocks_sum['Value'] = stocks_sum['Value']/stocks_sum.groupby(['Economy'])['Value'].transform('sum')
    #keep only 2w where Value is greater than 0.3
    stocks_sum = stocks_sum.loc[(stocks_sum['Vehicle Type']=='2w') & (stocks_sum['Value']>=0.3)].copy()
    stocks_sum_economies = stocks_sum['Economy'].unique()
    return stocks_sum_economies

def remap_stocks_and_sales_for_high_2w_economies(stocks, new_sales_shares_all_plot_drive_shares):
    
    stocks_sum_economies = identify_high_2w_economies(stocks)
    #keep those economies in the stocks df
    high_2w_economies_stocks = stocks[stocks['Economy'].isin(stocks_sum_economies)].copy()
    other_economies_stocks = stocks[~stocks['Economy'].isin(stocks_sum_economies)].copy()
    high_2w_economies_sales = new_sales_shares_all_plot_drive_shares[new_sales_shares_all_plot_drive_shares['Economy'].isin(stocks_sum_economies)].copy()
    other_economies_sales = new_sales_shares_all_plot_drive_shares[~new_sales_shares_all_plot_drive_shares['Economy'].isin(stocks_sum_economies)].copy()
    high_2w_economies_stocks = remap_vehicle_types(high_2w_economies_stocks, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'])
    high_2w_economies_sales = remap_vehicle_types(high_2w_economies_sales, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'])
    
    #concat the two dataframes
    stocks = pd.concat([high_2w_economies_stocks, other_economies_stocks])
    new_sales_shares_all_plot_drive_shares = pd.concat([high_2w_economies_sales, other_economies_sales])
    
    return stocks, new_sales_shares_all_plot_drive_shares
    
###################################################
def plot_share_of_transport_type(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares_df,stocks_df,fig_dict, color_preparation_list, colors_dict,share_of_transport_type_type):
    stocks = stocks_df.copy()
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    
    stocks, new_sales_shares_all_plot_drive_shares = remap_stocks_and_sales_for_high_2w_economies(stocks, new_sales_shares_all_plot_drive_shares)
    # #sum up all the sales shares for each drive type
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    #now calucalte share of total stocks as a proportion like the sales share
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'])['Value'].apply(lambda x: x/x.sum())
    #create line_dash column and call it stocks
    stocks['line_dash'] = 'stocks'
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###        
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
                
        for economy in ECONOMY_IDs:
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
            if share_of_transport_type_type == 'passenger':
                title = f'Sales and stocks shares for passenger vehicles (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)

                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['share_of_transport_type_passenger'] = [fig,title]
            
            #############
            elif share_of_transport_type_type == 'freight':
                title = f'Sales and stocks shares for freight vehicles (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)

                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['share_of_transport_type_freight'] = [fig,title]
            elif share_of_transport_type_type == 'all':
                title = f'Sales and stocks shares (%)'
                # sum up, because 2w are used in freight and passenger:
                plot_data = plot_data.groupby(['Scenario', 'Economy', 'Date', 'Drive','line_dash']).sum().reset_index()
                fig = px.line(plot_data, x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)

                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['share_of_transport_type_all'] = [fig,title]
            #############
            else:
                raise ValueError('share_of_transport_type_type must be either passenger or freight')
    
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    return fig_dict, color_preparation_list


def plot_share_of_vehicle_type_by_transport_type(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares_df,stocks_df,fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type):
    #This data is in terms of transport type, so will need to normalise it to vehicle type by summing up the shares for each vehicle type and dividing individual shares by their sum
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    stocks = stocks_df.copy()
    
    stocks, new_sales_shares_all_plot_drive_shares = remap_stocks_and_sales_for_high_2w_economies(stocks, new_sales_shares_all_plot_drive_shares)
    
    new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares.groupby(['Date','Economy', 'Scenario', 'Transport Type', 'Vehicle Type'])['Value'].transform(lambda x: x/x.sum())
    
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'])['Value'].apply(lambda x: x/x.sum())
    stocks['line_dash'] = 'stocks'
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
                
        for economy in ECONOMY_IDs:
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
            if share_of_transport_type_type == 'passenger':
                title = f'Shares for passenger (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                ###
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['share_of_vehicle_type_by_transport_type_passenger'] = [fig,title]
                
                #############
            elif share_of_transport_type_type == 'freight':
                title = f'Shares for freight (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['share_of_vehicle_type_by_transport_type_freight'] = [fig,title]
            elif share_of_transport_type_type == 'all':
                
                title = f'Sales and stock shares (%)'

                fig = px.line(plot_data, x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                ###
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['share_of_vehicle_type_by_transport_type_all'] = [fig,title]
            else:
                raise ValueError('share_of_transport_type_type must be either passenger or freight')
            #############
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    
    return fig_dict,color_preparation_list
            

def plot_share_of_vehicle_type_by_transport_type_both_on_one_graph(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares_df, stocks_df, fig_dict, color_preparation_list, colors_dict):
    #This data is in terms of transport type, so will need to normalise it to vehicle type by summing up the shares for each vehicle type and dividing individual shares by their sum

    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    stocks = stocks_df.copy()
    
    stocks, new_sales_shares_all_plot_drive_shares = remap_stocks_and_sales_for_high_2w_economies(stocks, new_sales_shares_all_plot_drive_shares)
    
    new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares.groupby(['Date','Economy', 'Scenario', 'Transport Type', 'Vehicle Type'])['Value'].transform(lambda x: x/x.sum())
    
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'])['Value'].apply(lambda x: x/x.sum())
    stocks['line_dash'] = 'stocks'
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
            
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
                
        for economy in ECONOMY_IDs:
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
            ###
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['share_of_vehicle_type_by_transport_type_on_one_graph'] = [fig,title]
            
            #############
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    
    return fig_dict,color_preparation_list

def share_of_sum_of_vehicle_types_by_transport_type(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares_df,stocks_df,fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type):
    #i think that maybe stocks % can be higher than sales % here because of turnvoer rates. hard to get it correct right now
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    stocks = stocks_df.copy()
    
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive', 'Value']].groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive']).sum().reset_index()
        
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    
    stocks = stocks[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive','Value']].groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive']).sum().reset_index()
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type'])['Value'].apply(lambda x: x/x.sum())
    stocks['line_dash'] = 'stocks' 
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        stocks_scen = stocks.loc[(stocks['Scenario']==scenario)].copy()
        ###
        
        #then concat the two dataframes
        new_sales_shares_all_plot_drive_shares_scenario = pd.concat([new_sales_shares_all_plot_drive_shares_scenario, stocks_scen])
        
                
        for economy in ECONOMY_IDs:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()

            # #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. This helps to keep the plot clean too
            # plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060, 2070, 2080,2090, 2100] else 0, axis=1)
            #drop all drives except bev and fcev
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='fcev')].copy()
            #sort by date col
            plot_data.sort_values(by=['Date'], inplace=True)
            #############
            #now plot
            if share_of_transport_type_type == 'passenger':
                title = f'Shares for passenger (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['sum_of_vehicle_types_by_transport_type_passenger'] = [fig,title]
                
                #############
            elif share_of_transport_type_type == 'freight':
                title = f'Shares for freight (%)'

                fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['sum_of_vehicle_types_by_transport_type_freight'] = [fig,title]
            elif share_of_transport_type_type == 'all':
                title = 'Share by transport type (%)'
                #concat drive and transport type
                plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Transport Type']
                fig = px.line(plot_data, x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['sum_of_vehicle_types_by_transport_type_all'] = [fig,title]
            else:
                raise ValueError('share_of_transport_type_type must be passenger or freight')
            #############

    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    
    return fig_dict, color_preparation_list
###################################################



###################################################
def energy_use_by_fuel_type(ECONOMY_IDs,model_output_with_fuels,fig_dict,  color_preparation_list, colors_dict,transport_type):
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    model_output_with_fuels_sum= model_output_with_fuels[['Economy', 'Scenario','Date', 'Fuel', 'Transport Type','Energy']].groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel']).sum().reset_index().copy()
    model_output_with_fuels_sum['Measure'] = 'Energy'
    model_output_with_fuels_sum['Unit'] = model_output_with_fuels_sum['Measure'].map(config.measure_to_unit_concordance_dict)
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        energy_use_by_fuel_type_scen = model_output_with_fuels_sum.loc[(model_output_with_fuels_sum['Scenario']==scenario)].copy()
        
        for economy in ECONOMY_IDs:
            #filter to economy
            energy_use_by_fuel_type_economy = energy_use_by_fuel_type_scen.loc[(energy_use_by_fuel_type_scen['Economy']==economy)].copy()
            
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
            if transport_type=='passenger':
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Transport Type']=='passenger'], x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Energy by Fuel {} ({})'.format(transport_type, energy_use_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['energy_use_by_fuel_type_passenger'] = [fig, title_text]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Transport Type']=='freight'], x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Energy by Fuel {} ({})'.format(transport_type, energy_use_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['energy_use_by_fuel_type_freight'] = [fig, title_text]
                
            elif transport_type == 'all':
                #sum across transport types
                energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.groupby(['Economy', 'Date', 'Fuel','Unit']).sum().reset_index()
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy, x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Energy by Fuel ({})'.format(energy_use_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['energy_use_by_fuel_type_all'] = [fig, title_text]
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_use_by_fuel_type_economy['Fuel'].unique().tolist())
    return fig_dict, color_preparation_list


def create_vehicle_type_stocks_plot(ECONOMY_IDs,stocks_df,fig_dict,  color_preparation_list, colors_dict):
    #loop through scenarios and grab the data for each scenario:
    
    #create a new df with only the data we need:
    stocks = stocks_df.copy()
    stocks = stocks[['Economy', 'Date', 'Vehicle Type','Scenario', 'Value']].groupby(['Economy', 'Date','Scenario', 'Vehicle Type']).sum().reset_index()
    stocks['Measure'] = 'Stocks'
    stocks['Unit'] = stocks['Measure'].map(config.measure_to_unit_concordance_dict)
    
    stocks = remap_vehicle_types(stocks, value_col='Value', new_index_cols = ['Date', 'Vehicle Type','Unit','Scenario', 'Economy'])
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        stocks_scenario = stocks.loc[(stocks['Scenario']==scenario)].copy()
        
        for economy in ECONOMY_IDs:
            #filter to economy
            stocks_economy = stocks_scenario.loc[stocks_scenario['Economy']==economy].copy()
            
            # #also if stocks of 2w are more than 50% of total stocks then recategorise the vehicle types a bit
            # if stocks_economy.loc[stocks_economy['Vehicle Type']=='2w']['Value'].sum() > 0.5*stocks_economy.loc[stocks_economy['Vehicle Type']!='2w']['Value'].sum():
            # ##
            
            #sort by date
            # stocks_economy = stocks_economy.sort_values(by='Date')
            #now plot
            fig = px.line(stocks_economy, x='Date', y='Value', color='Vehicle Type', color_discrete_map=colors_dict)
            title_text = 'Vehicle stocks (Millions)'#.format(stocks_economy['Unit'].unique()[0])
            #add units to y col
            # fig.update_yaxes(title_text='Freight Tonne Km ({})'.format(stocks_economy['Unit'].unique()[0]))

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['vehicle_type_stocks'] = [fig, title_text]
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(stocks_economy['Vehicle Type'].unique().tolist())
    return fig_dict, color_preparation_list


def freight_tonne_km_by_drive(ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT,  color_preparation_list, colors_dict):
    
    fkm = model_output_detailed.loc[model_output_detailed['Transport Type']=='freight'].rename(columns={'Activity':'freight_tonne_km'}).copy()
    
    if DROP_NON_ROAD_TRANSPORT:
        fkm = fkm.loc[fkm['Medium']=='road'].copy()
    
    fkm = fkm[['Economy', 'Date', 'Drive','Scenario', 'freight_tonne_km']].groupby(['Economy', 'Date', 'Scenario','Drive']).sum().reset_index()

    #simplfiy drive type using remap_drive_types
    fkm = remap_drive_types(fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'], include_non_road=True)
    
    #add units (by setting measure to Freight_tonne_km haha)
    fkm['Measure'] = 'Freight_tonne_km'
    #add units
    fkm['Unit'] = fkm['Measure'].map(config.measure_to_unit_concordance_dict)
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        freight_tonne_km_by_drive = fkm.loc[(fkm['Scenario']==scenario)].copy()

        for economy in ECONOMY_IDs:
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

def passenger_km_by_drive(ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT,  color_preparation_list, colors_dict, include_non_road=True):
    
    pkm = model_output_detailed.loc[model_output_detailed['Transport Type']=='passenger'].rename(columns={'Activity':'passenger_km'}).copy()
    
    if DROP_NON_ROAD_TRANSPORT:
        pkm = pkm.loc[pkm['Medium']=='road'].copy()
    
    pkm = pkm[['Economy', 'Date', 'Drive','Scenario', 'passenger_km']].groupby(['Economy', 'Date','Scenario', 'Drive']).sum().reset_index()

    #simplfiy drive type using remap_drive_types
    pkm = remap_drive_types(pkm, value_col='passenger_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'], include_non_road=True)
    
    #add units
    pkm['Measure'] = 'Passenger_km'
    pkm['Unit'] = pkm['Measure'].map(config.measure_to_unit_concordance_dict)
    
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        passenger_km_by_drive = pkm.loc[(pkm['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
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


def activity_growth(ECONOMY_IDs,model_output_detailed_df,fig_dict,DROP_NON_ROAD_TRANSPORT,  color_preparation_list, colors_dict):
    
    #calcualte population growth and gdp growth as a percentage:
    # #first grasb only the data we need for this:
    # model_output_detailed_growth = model_output_detailed[['Economy', 'Date', 'Population', 'Gdp']].copy().drop_duplicates()
    #srot by date
    model_output_detailed = model_output_detailed_df.copy()
    model_output_detailed = model_output_detailed.sort_values(by='Date')
    model_output_detailed['Population_growth'] = model_output_detailed.groupby(['Economy','Scenario', 'Transport Type'])['Population'].pct_change()
    model_output_detailed['GDP_growth'] = model_output_detailed.groupby(['Economy','Scenario', 'Transport Type'])['Gdp'].pct_change()
    
    #minus one from the activity_growth col  and times by 100
    model_output_detailed['Activity_growth'] = (model_output_detailed['Activity_growth']-1)*100
    
    #now drop all cols we dont need for activity growth
    model_output_detailed = model_output_detailed[['Economy', 'Date', 'Transport Type','Scenario', 'Population_growth', 'GDP_growth', 'Activity_growth']].copy().drop_duplicates()
    
    #melt so all measures in one col
    activity_growth = pd.melt(model_output_detailed, id_vars=['Economy',  'Date','Scenario', 'Transport Type'], value_vars=['Population_growth', 'GDP_growth', 'Activity_growth'], var_name='Measure', value_name='Macro_growth')
    
    # #times macro growth by 100 to get percentage
    # activity_growth['Macro_growth'] = activity_growth['Macro_growth']*100
    
    # #add units (by setting measure to Freight_tonne_km haha)
    # activity_growth['Measure'] = 'Macro_growth'
    #add units
    activity_growth['Unit'] = '%'
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        activity_growth_scen = activity_growth.loc[(activity_growth['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            activity_growth_economy = activity_growth_scen.loc[activity_growth_scen['Economy']==economy].copy()

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

def activity_and_macro_lines(ECONOMY_IDs,original_model_output_8th_df,model_output_detailed, fig_dict, color_preparation_list, colors_dict, indexed=False):
    original_model_output_8th = original_model_output_8th_df.copy()
    #grab only the Activity then sum it by economy, scenario and date
    original_model_output_8th = original_model_output_8th[['Economy', 'Scenario', 'Date', 'Activity']].copy().drop_duplicates()
    original_model_output_8th = original_model_output_8th.groupby(['Economy', 'Scenario', 'Date']).sum().reset_index()
    #rename actovity to Activity_8th
    original_model_output_8th = original_model_output_8th.rename(columns={'Activity':'Activity_8th'})
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        model_output_detailed_scen = model_output_detailed.loc[(model_output_detailed['Scenario']==scenario)].copy()
        #if scenario is Target then look for 'Carbon Neutral' in scenario name
        if scenario == 'Target':
            original_model_output_8th_scenario = original_model_output_8th.loc[original_model_output_8th['Scenario']=='Carbon Neutral'].copy()
        else:
            original_model_output_8th_scenario = original_model_output_8th.loc[original_model_output_8th['Scenario']==scenario].copy()
    
        #drop scenario col
        original_model_output_8th_scenario = original_model_output_8th_scenario.drop(columns=['Scenario'])
        
        
        freight_km = model_output_detailed_scen.loc[model_output_detailed_scen['Transport Type']=='freight'].rename(columns={'Activity':'freight_tonne_km'}).copy()
        passenger_km = model_output_detailed_scen.loc[model_output_detailed_scen['Transport Type']=='passenger'].rename(columns={'Activity':'passenger_km'}).copy()
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
            population = calc_index(model_output_detailed_scen[['Population','Date','Economy']].drop_duplicates(),'Population')
            gdp = calc_index(model_output_detailed_scen[['Gdp','Date','Economy']].drop_duplicates(),'Gdp')
            freight_km = calc_index(freight_km[['freight_tonne_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'freight_tonne_km')
            passenger_km = calc_index(passenger_km[['passenger_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'passenger_km')
            original_model_output_8th_scenario = calc_index(original_model_output_8th_scenario,'Activity_8th')

        else:#calc growth
                
            population = calc_growth(model_output_detailed_scen[['Population','Date','Economy']].drop_duplicates(),'Population')
            gdp = calc_growth(model_output_detailed_scen[['Gdp','Date','Economy']].drop_duplicates(),'Gdp')
            freight_km = calc_growth(freight_km[['freight_tonne_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'freight_tonne_km')
            passenger_km = calc_growth(passenger_km[['passenger_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'passenger_km')
            original_model_output_8th_scenario = calc_growth(original_model_output_8th_scenario,'Activity_8th')

            
        ##
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
            
        #and filter so data is less than config.GRAPHING_END_YEAR
        index_data = index_data.loc[(index_data['Date']<=config.GRAPHING_END_YEAR)].copy()
        
        # #melt so all measures in one col
        # index_data = index_data.melt(id_vars=['Economy', 'Date'], value_vars=['Population_index', 'Gdp_index', 'freight_tonne_km_index', 'passenger_km_index', 'Activity_8th'], var_name='Measure', value_name='Index')
        
        for economy in ECONOMY_IDs:
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

def plot_supply_side_fuel_mixing(ECONOMY_IDs,supply_side_fuel_mixing_df,fig_dict, color_preparation_list, colors_dict):
    #plot supply side fuel mixing
    supply_side_fuel_mixing = supply_side_fuel_mixing_df.copy()
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
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        supply_side_fuel_mixing_plot_scenario = supply_side_fuel_mixing.loc[supply_side_fuel_mixing['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
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

def create_charging_plot(ECONOMY_IDs,chargers_df,fig_dict, color_preparation_list, colors_dict):
    chargers = chargers_df.copy()
    chargers = chargers[['Economy', 'Scenario', 'Date', 'sum_of_fast_chargers_needed','sum_of_slow_chargers_needed']].drop_duplicates()
    #divide chargers by a million
    chargers['sum_of_fast_chargers_needed'] = chargers['sum_of_fast_chargers_needed']/1000000
    chargers['sum_of_slow_chargers_needed'] = chargers['sum_of_slow_chargers_needed']/1000000
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        chargers_scenario = chargers.loc[chargers['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            chargers_economy = chargers_scenario.loc[chargers_scenario['Economy']==economy].copy()
            
            title = 'Expected slow and fast public chargers needed for' + scenario + ' scenario'
            fig = px.bar(chargers_economy, x="Date", y=['sum_of_fast_chargers_needed','sum_of_slow_chargers_needed'], title=title, color_discrete_map=colors_dict)

            #add units to y col
            title_text = 'Public chargers (millions)'
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['charging'] = [fig, title_text]
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(['sum_of_fast_chargers_needed','sum_of_slow_chargers_needed'])
    return fig_dict, color_preparation_list

def prodcue_LMDI_mutliplicative_plot(ECONOMY_IDs,fig_dict,  colors_dict, transport_type):
    for scenario in config.economy_scenario_concordance.Scenario.unique():
        if scenario == 'Reference':
            scenario_str = 'REF'
        elif scenario == 'Target':
            scenario_str = 'TGT'
        for economy in ECONOMY_IDs:
            file_identifier = f'{economy}_{scenario_str}_{transport_type}__2_Energy use_Hierarchical_hierarchical_multiplicative_output'
            lmdi_data = pd.read_csv(f'./intermediate_data/LMDI/{economy}/{file_identifier}.csv')
            #melt data so we have the different components of the LMDI as rows. eg. for freight the cols are: Date	Change in Energy	Energy intensity effect	freight_tonne_km effect	Engine type effect	Total Energy	Total_freight_tonne_km
            #we want to drop the last two plots, then melt the data so we have the different components of the LMDI as rows. eg. for freight the cols will end up as: Date	Effect. Then we will also create a line dash col and if the Effect is Change in Energy then the line dash will be solid, otherwise it will be dotted
            #drop cols by index, not name so it doesnt matter what thei names are
            lmdi_data_melt = lmdi_data.copy()#drop(lmdi_data.columns[[len(lmdi_data.columns)-1, len(lmdi_data.columns)-2]], axis=1)
            lmdi_data_melt = lmdi_data_melt.melt(id_vars=['Date'], var_name='Effect', value_name='Value')
            lmdi_data_melt['line_dash'] = lmdi_data_melt['Effect'].apply(lambda x: 'solid' if x == 'Percent change in Energy' else 'dash')
                        
            fig = px.line(lmdi_data_melt, x="Date", y='Value',  color='Effect', line_dash='line_dash', 
            color_discrete_map=colors_dict)
            
            title_text = f'Drivers of {transport_type} energy use'
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][f'lmdi_{transport_type}'] = [fig, title_text]

    return fig_dict
    

def plot_average_age_by_simplified_drive_type(ECONOMY_IDs,model_output_detailed_df,fig_dict, color_preparation_list, colors_dict, medium, title):
    model_output_detailed = model_output_detailed_df.copy()
    if medium=='road':
        model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']==medium].copy()
    elif medium=='all':
        pass
    elif medium=='nonroad':
        model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']!='road'].copy()
    else:
        raise ValueError('medium must be road, non_road or all')
    #create a new df with only the data we need:
    avg_age = model_output_detailed.copy()
    # #map drive types:
    # avg_age = avg_age[['Economy', 'Date', 'Drive','Stocks', 'Average_age']].groupby(['Economy', 'Date', 'Drive']).sum(numeric_only=True).reset_index()
    
    #simplfiy drive type using remap_drive_types
    avg_age = remap_drive_types(avg_age, value_col='Average_age', new_index_cols = ['Economy', 'Date','Scenario', 'Transport Type', 'Vehicle Type', 'Drive'], mapping_type='simplified', aggregation_type=('weighted_average', 'Stocks'))
    #drop stocks col
    avg_age.drop(columns=['Stocks'], inplace=True)
    
    #add units (by setting measure to Freight_tonne_km haha)
    avg_age['Measure'] = 'Average_age'
    #add units
    avg_age['Unit'] = 'Age'

    #since average age starts off at  1 or 5 years (depending on if the drive type is a new or old type) we are probably best plotting the average age grouped into these types. So group all ice style engines, and ev/hydrogen/phev engines. then grouping by vehicle type transport type and drive, find the weighted average age of each engine type over time. plot as a line. 
    # model_output_detailed.pkl
    # #
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        avg_age_s = avg_age.loc[(avg_age['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            avg_age_economy = avg_age_s.loc[avg_age_s['Economy']==economy].copy()
            
            #concat drive and vehicle type cols:
            avg_age_economy['Drive'] = avg_age_economy['Vehicle Type']+' '+ avg_age_economy['Drive'] 
            #now plot
            fig = px.line(avg_age_economy, x='Date', y='Average_age', color='Drive',line_dash = 'Transport Type', color_discrete_map=colors_dict)
            title_text = 'Average Age of Vehicles (Years)'#.format(avg_age_economy['Unit'].unique()[0])
            #add units to y col
            # fig.update_yaxes(title_text='Freight Tonne Km ({})'.format(avg_age_economy['Unit'].unique()[0]))

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][title] = [fig, title_text]
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(avg_age_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list



def plot_stocks_per_capita(ECONOMY_IDs,road_model_input, model_output_detailed,fig_dict, color_preparation_list, colors_dict):
    #Plot stocks per capita for each transport type. Also plot the gompertz line for the economy, which is a horizontal line. 

    stocks_per_capita = model_output_detailed.copy()
    stocks_per_capita = stocks_per_capita.loc[stocks_per_capita['Medium']=='road'].copy()
    #map the number of vehicles that each vehicle type represents with regards to vehicles per cpita, using:
    vehicle_gompertz_factors = yaml.load(open('config/parameters.yml'), Loader=yaml.FullLoader)['vehicle_gompertz_factors']
    stocks_per_capita['Stocks'] = stocks_per_capita['Stocks'] * stocks_per_capita['Vehicle Type'].map(vehicle_gompertz_factors)
    #recalcualte stocks per capita after summing up stocks by economy and transport type, scneario anmd date
    #extract population so we can join it after the sum:
    population = stocks_per_capita[['Economy', 'Scenario','Date', 'Population']].drop_duplicates()
    stocks_per_capita = stocks_per_capita.drop(columns=['Population']).groupby(['Economy', 'Date', 'Scenario','Transport Type']).sum(numeric_only=True).reset_index()
    #join population back on:
    stocks_per_capita = stocks_per_capita.merge(population, on=['Economy','Scenario', 'Date'], how='left')
    #calcualte stocks per capita
    stocks_per_capita['Thousand_stocks_per_capita'] = stocks_per_capita['Stocks']/stocks_per_capita['Population']
    #convert to more readable units. We will convert back later if we need to #todo do we need to?
    stocks_per_capita['Stocks_per_thousand_capita'] = stocks_per_capita['Thousand_stocks_per_capita'] * 1000000
    
    gompertz_parameters = road_model_input[['Economy','Date', 'Gompertz_gamma']].drop_duplicates().dropna().copy()
    #and filter so data is less than config.GRAPHING_END_YEAR
    gompertz_parameters = gompertz_parameters.loc[(gompertz_parameters['Date']<=config.GRAPHING_END_YEAR)&(gompertz_parameters['Date']>=config.OUTLOOK_BASE_YEAR)].copy()
    #set transport type to 'maximum_stocks_per_captia'
    gompertz_parameters['Transport Type'] = 'maximum_stocks_per_captia'
    #rename Gompertz_gamma to Stocks_per_thousand_capita
    gompertz_parameters.rename(columns={'Gompertz_gamma':'Stocks_per_thousand_capita'}, inplace=True)
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        stocks_per_capita_s = stocks_per_capita.loc[(stocks_per_capita['Scenario']==scenario)].copy()
        #concat
        stocks_per_capita_s = pd.concat([stocks_per_capita_s, gompertz_parameters], axis=0)
        #add units (by setting measure to Freight_tonne_km haha)
        stocks_per_capita_s['Measure'] = 'Stocks_per_thousand_capita'
        #add units
        stocks_per_capita_s['Unit'] = 'Stocks_per_thousand_capita'
        for economy in ECONOMY_IDs:
            #filter to economy
            stocks_per_capita_economy = stocks_per_capita_s.loc[stocks_per_capita_s['Economy']==economy].copy()

            #now plot
            fig = px.line(stocks_per_capita_economy, x='Date', y='Stocks_per_thousand_capita', color='Transport Type', color_discrete_map=colors_dict)
            title_text = 'Stocks per capita (Thousand)'

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['stocks_per_capita'] = [fig, title_text]
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(stocks_per_capita_economy['Transport Type'].unique().tolist())
    return fig_dict, color_preparation_list


def plot_non_road_energy_use(ECONOMY_IDs,model_output_with_fuels_df,fig_dict,  color_preparation_list, colors_dict,transport_type):
    #we will plot the energy use by fuel type for non road as an area chart.
    model_output_with_fuels = model_output_with_fuels_df.copy()
    model_output_with_fuels = model_output_with_fuels.loc[model_output_with_fuels['Medium']!='road'].copy()
    
    #create a new df with only the data we need: 
    energy_use_by_fuel_type = model_output_with_fuels.copy()
    energy_use_by_fuel_type= energy_use_by_fuel_type[['Economy','Scenario', 'Date', 'Fuel', 'Transport Type','Energy']].groupby(['Economy','Scenario', 'Date','Transport Type', 'Fuel']).sum().reset_index()
    
    #add units (by setting measure to Energy haha)
    energy_use_by_fuel_type['Measure'] = 'Energy'
    #add units
    energy_use_by_fuel_type['Unit'] = energy_use_by_fuel_type['Measure'].map(config.measure_to_unit_concordance_dict)
    
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        energy_use_by_fuel_type_s = energy_use_by_fuel_type.loc[(energy_use_by_fuel_type['Scenario']==scenario)].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            energy_use_by_fuel_type_economy = energy_use_by_fuel_type_s.loc[energy_use_by_fuel_type_s['Economy']==economy].copy()
            
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
            if transport_type=='passenger':
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Transport Type']=='passenger'], x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road energy by Fuel {} ({})'.format(transport_type, energy_use_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_energy_use_by_fuel_type_passenger'] = [fig, title_text]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy.loc[energy_use_by_fuel_type_economy['Transport Type']=='freight'], x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road energy by Fuel {} ({})'.format(transport_type, energy_use_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_energy_use_by_fuel_type_freight'] = [fig, title_text]
                
            elif transport_type == 'all':
                #sum across transport types
                energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.groupby(['Economy', 'Date', 'Fuel','Unit']).sum().reset_index()
                #now plot
                fig = px.area(energy_use_by_fuel_type_economy, x='Date', y='Energy', color='Fuel', title='Energy by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road energy by Fuel ({})'.format(energy_use_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_energy_use_by_fuel_type_all'] = [fig, title_text]
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_use_by_fuel_type_economy['Fuel'].unique().tolist())
    return fig_dict, color_preparation_list

def non_road_activity_by_drive_type(ECONOMY_IDs,model_output_detailed_df,fig_dict, color_preparation_list, colors_dict,transport_type):
    #why arent we getting different drive types.
    #break activity into its ddrive types and plot as an area chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot. in this case, it will have pattern_shape="Transport Type" to distinguish between the two:
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    #since we need detail on non road drive types, we have to pull the data fromm here:
    # 'output_data/model_output/NON_ROAD_DETAILED_{}'.format(config.model_output_file_name)
    model_output_detailed=model_output_detailed_df.copy()
    model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']!='road'].copy()
    
    #create a new df with only the data we need:
    activity_by_drive = model_output_detailed.copy()
    activity_by_drive = activity_by_drive[['Economy', 'Date', 'Drive','Transport Type', 'Scenario','Activity']].groupby(['Economy', 'Date', 'Transport Type','Scenario','Drive']).sum().reset_index()
    
    
    # #simplfiy drive type using remap_drive_types
    # activity_by_drive = remap_drive_types(activity_by_drive, value_col='Activity', new_index_cols = ['Economy', 'Date', 'Transport Type','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    activity_by_drive['Measure'] = 'Activity'
    #add units
    activity_by_drive['Unit'] = 'Activity'
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        #filter for the scenario:
        activity_by_drive_s = activity_by_drive.loc[activity_by_drive['Scenario']==scenario].copy()

        for economy in ECONOMY_IDs:
            #filter to economy
            activity_by_drive_economy = activity_by_drive_s.loc[activity_by_drive_s['Economy']==economy].copy()
            
            # calculate total 'passenger_km' for each 'Drive' 
            total_activity = activity_by_drive_economy.groupby('Drive')['Activity'].sum()

            # Create an ordered category of 'Drive' labels sorted by total 'passenger_km'
            activity_by_drive_economy['Drive'] = pd.Categorical(
            activity_by_drive_economy['Drive'],
            categories = total_activity.sort_values(ascending=False).index,
            ordered=True
            )

            # Now sort the DataFrame by the 'Drive' column:
            activity_by_drive_economy.sort_values(by='Drive', inplace=True)
            #sort by date

            if transport_type=='passenger':
                #now plot
                fig = px.area(activity_by_drive_economy.loc[activity_by_drive_economy['Transport Type']=='passenger'], x='Date', y='Activity', color='Drive', title='Non road passenger activity by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road passenger Km (Billions)'#.format(activity_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_activity_by_drive_passenger'] = [fig, title_text]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.area(activity_by_drive_economy.loc[activity_by_drive_economy['Transport Type']=='freight'], x='Date', y='Activity', color='Drive', title='Non road freight activity by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road freight tonne Km (Billions)'#.format(activity_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_activity_by_drive_freight'] = [fig, title_text]
                
            elif transport_type == 'all':
                #sum across transport types
                fig = px.area(activity_by_drive_economy, x='Date', y='Activity', color='Drive',pattern_shape="Transport Type" , title='Non road activity by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road activity (Freight/Passenger km)'#.format(activity_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_activity_by_drive_all'] = [fig, title_text]
                
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(activity_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list



def non_road_stocks_by_drive_type(ECONOMY_IDs,model_output_detailed_df, fig_dict, color_preparation_list, colors_dict,transport_type):
    #break activity into its ddrive types and plot as an area chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot. in this case, it will have pattern_shape="Transport Type" to distinguish between the two:
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    #since we need detail on non road drive types, we have to pull the data fromm here:

    model_output_detailed=model_output_detailed_df.copy()
    
    model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']!='road'].copy()
    
    #create a new df with only the data we need:
    stocks_by_drive = model_output_detailed.copy()
    stocks_by_drive = stocks_by_drive[['Economy', 'Date', 'Drive','Scenario','Transport Type', 'Stocks']].groupby(['Economy', 'Date', 'Transport Type','Scenario','Drive']).sum().reset_index()
    
    #add units (by setting measure to Freight_tonne_km haha)
    stocks_by_drive['Measure'] = 'Stocks'
    #add units
    stocks_by_drive['Unit'] = 'Stocks'

    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        #filter for the scenario:
        stocks_by_drive_s = stocks_by_drive.loc[stocks_by_drive['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            stocks_by_drive_economy = stocks_by_drive_s.loc[stocks_by_drive_s['Economy']==economy].copy()
            
            # calculate total 'passenger_km' for each 'Drive' 
            total_stocks = stocks_by_drive_economy.groupby('Drive')['Stocks'].sum()

            # Create an ordered category of 'Drive' labels sorted by total 'passenger_km'
            stocks_by_drive_economy['Drive'] = pd.Categorical(
            stocks_by_drive_economy['Drive'],
            categories = total_stocks.sort_values(ascending=False).index,
            ordered=True
            )

            # Now sort the DataFrame by the 'Drive' column:
            stocks_by_drive_economy.sort_values(by='Drive', inplace=True)
            #sort by date

            if transport_type=='passenger':
                #now plot
                fig = px.line(stocks_by_drive_economy.loc[stocks_by_drive_economy['Transport Type']=='passenger'], x='Date', y='Stocks', color='Drive', title='Non road passenger stocks by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road passenger Km (Billions)'#.format(stocks_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_stocks_by_drive_passenger'] = [fig, title_text]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.line(stocks_by_drive_economy.loc[stocks_by_drive_economy['Transport Type']=='freight'], x='Date', y='Stocks', color='Drive', title='Non road freight stocks by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road freight tonne Km (Billions)'#.format(stocks_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_stocks_by_drive_freight'] = [fig, title_text]
                
            elif transport_type == 'all':
                #sum across transport types
                fig = px.line(stocks_by_drive_economy, x='Date', y='Stocks', color='Drive',line_dash="Transport Type" , title='Non road stocks by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Non road stocks (Freight/Passenger km)'#.format(stocks_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['non_road_stocks_by_drive_all'] = [fig, title_text]
                
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(stocks_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list



def turnover_rate_by_drive_type_box(ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict,transport_type):
    #break activity into its ddrive types and plot the variation by medium and treansport type on a box chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot. in this case, it will have pattern_shape="Transport Type" to distinguish between the two:
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    #since we need detail on non road drive types, we have to pull the data fromm here:
    #create a new df with only the data we need:
    turnover_rate_by_drive = model_output_detailed.copy()
    turnover_rate_by_drive = turnover_rate_by_drive[['Economy', 'Date', 'Medium','Drive','Transport Type','Scenario', 'Turnover_rate']].groupby(['Economy', 'Date', 'Medium','Transport Type','Scenario','Drive']).median().reset_index()#median less affected by outliers than mean
    
    #add units (by setting measure to Freight_tonne_km haha)
    turnover_rate_by_drive['Measure'] = 'Turnover_rate'
    #add units
    turnover_rate_by_drive['Unit'] = '%'

    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        #filter for the scenario:
        turnover_rate_by_drive_s = turnover_rate_by_drive.loc[turnover_rate_by_drive['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            turnover_rate_by_drive_economy = turnover_rate_by_drive_s.loc[turnover_rate_by_drive_s['Economy']==economy].copy()
            
            # calculate total 'passenger_km' for each 'Drive' 
            total_turnover_rate = turnover_rate_by_drive_economy.groupby('Drive')['Turnover_rate'].mean()

            # Create an ordered category of 'Drive' labels sorted by total 'passenger_km'
            turnover_rate_by_drive_economy['Drive'] = pd.Categorical(
            turnover_rate_by_drive_economy['Drive'],
            categories = total_turnover_rate.sort_values(ascending=False).index,
            ordered=True
            )

            # Now sort the DataFrame by the 'Drive' column:
            turnover_rate_by_drive_economy.sort_values(by='Drive', inplace=True)
            #sort by date

            if transport_type=='passenger':
                #now plot
                # fig = px.line(turnover_rate_by_drive_economy.loc[turnover_rate_by_drive_economy['Transport Type']=='passenger'], x='Date', y='Turnover_rate', color='Drive', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                fig = px.box(turnover_rate_by_drive_economy.loc[turnover_rate_by_drive_economy['Transport Type']=='passenger'],x='Medium', y='Turnover_rate', color='Drive', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Passenger turnover rate box (based on median)'#.format(turnover_rate_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['box_turnover_rate_by_drive_passenger'] = [fig, title_text]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.box(turnover_rate_by_drive_economy.loc[turnover_rate_by_drive_economy['Transport Type']=='freight'],x='Medium', y='Turnover_rate', color='Drive', title='Freight turnover_rate by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Freight turnover rate box (based on median)'#.format(turnover_rate_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['box_turnover_rate_by_drive_freight'] = [fig, title_text]
                
            elif transport_type == 'all':
                #sum across transport types
                fig = px.box(turnover_rate_by_drive_economy,x='Medium', y='Turnover_rate', color='Drive', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'turnover_rate box (Freight/Passenger km) (based on median)'#.format(turnover_rate_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['box_turnover_rate_by_drive_all'] = [fig, title_text]
                
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(turnover_rate_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list


def turnover_rate_by_drive_type_line(ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict,transport_type):
    #break activity into its ddrive types and plot the variation by medium and treansport type on a box chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot. in this case, it will have pattern_shape="Transport Type" to distinguish between the two:
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    #since we need detail on non road drive types, we have to pull the data fromm here:
    #create a new df with only the data we need:
    turnover_rate_by_drive = model_output_detailed.copy()
    turnover_rate_by_drive = turnover_rate_by_drive[['Economy', 'Date', 'Medium','Drive','Transport Type','Scenario','Vehicle Type', 'Turnover_rate', 'Stocks']].groupby(['Economy', 'Date', 'Medium','Transport Type','Scenario','Vehicle Type','Drive']).agg({'Turnover_rate':'mean', 'Stocks':'sum'}).reset_index()
    
    #simplify the drive types:
    turnover_rate_by_drive = remap_drive_types(turnover_rate_by_drive, value_col='Turnover_rate', new_index_cols = ['Economy', 'Date', 'Medium','Transport Type','Vehicle Type','Scenario','Drive'],mapping_type='simplified', aggregation_type=('weighted_average', 'Stocks'))
        
    #add units (by setting measure to Freight_tonne_km haha)
    turnover_rate_by_drive['Measure'] = 'Turnover_rate'
    #add units
    turnover_rate_by_drive['Unit'] = '%'

    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        #filter for the scenario:
        turnover_rate_by_drive_s = turnover_rate_by_drive.loc[turnover_rate_by_drive['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            turnover_rate_by_drive_economy = turnover_rate_by_drive_s.loc[turnover_rate_by_drive_s['Economy']==economy].copy()
            
            # calculate total 'passenger_km' for each 'Drive' 
            total_turnover_rate = turnover_rate_by_drive_economy.groupby('Drive')['Turnover_rate'].mean()

            # Create an ordered category of 'Drive' labels sorted by total 'passenger_km'
            turnover_rate_by_drive_economy['Drive'] = pd.Categorical(
            turnover_rate_by_drive_economy['Drive'],
            categories = total_turnover_rate.sort_values(ascending=False).index,
            ordered=True
            )

            # Now sort the DataFrame by the 'Drive' column:
            turnover_rate_by_drive_economy.sort_values(by='Drive', inplace=True)
            #sort by date

            if transport_type=='passenger':
                #now plot
                # fig = px.line(turnover_rate_by_drive_economy.loc[turnover_rate_by_drive_economy['Transport Type']=='passenger'], x='Date', y='Turnover_rate', color='Drive', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                fig = px.line(turnover_rate_by_drive_economy.loc[turnover_rate_by_drive_economy['Transport Type']=='passenger'],x='Date', y='Turnover_rate', line_dash = 'Drive', color='Vehicle Type', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Passenger turnover rate (based on mean)'#.format(turnover_rate_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['line_turnover_rate_by_drive_passenger'] = [fig, title_text]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.line(turnover_rate_by_drive_economy.loc[turnover_rate_by_drive_economy['Transport Type']=='freight'],x='Date', y='Turnover_rate', line_dash = 'Drive', color='Vehicle Type', title='Freight turnover_rate by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Freight turnover rate (based on mean)'#.format(turnover_rate_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['line_turnover_rate_by_drive_freight'] = [fig, title_text]
                
            elif transport_type == 'all':
                #sum across transport types
                fig = px.line(turnover_rate_by_drive_economy,x='Date', y='Turnover_rate', line_dash = 'Drive', color='Vehicle Type', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'turnover_rate (Freight/Passenger km) (based on mean)'#.format(turnover_rate_by_drive_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['line_turnover_rate_by_drive_all'] = [fig, title_text]
                
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(turnover_rate_by_drive_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list

