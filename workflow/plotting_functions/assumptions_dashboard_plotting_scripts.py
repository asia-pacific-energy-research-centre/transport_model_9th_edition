
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

def remap_vehicle_types(df, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified', include_non_road=True, aggregation_type=('sum',)):
    if vehicle_type_mapping_set == 'original':
        vehicle_type_combinations = {
            'lt': 'lt', 'suv': 'suv', 'car': 'car', 'ht': 'ht', 'mt': 'mt', 'bus': 'bus', '2w': '2w', 'lcv': 'lcv'}
    elif vehicle_type_mapping_set == 'simplified':
        #also group and sum by the following vehicle type cmbinations:
        vehicle_type_combinations = {'lt':'lpv', 'suv':'lpv', 'car':'lpv', 'ht':'trucks', 'mt':'trucks', 'bus':'bus', '2w':'2w', 'lcv':'lcv'}
    elif vehicle_type_mapping_set == 'similar_trajectories':
        vehicle_type_combinations = {'lt':'lpv', 'suv':'lpv', 'car':'lpv', 'ht':'trucks', 'mt':'trucks', 'bus':'bus_2w', '2w':'bus_2w', 'lcv':'lcv'}
    elif vehicle_type_mapping_set == 'similar_trajectories_lpv_detailed':
        vehicle_type_combinations = {'lt':'lt', 'suv':'suv', 'car':'car', 'ht':'trucks', 'mt':'trucks', 'bus':'bus_2w', '2w':'bus_2w', 'lcv':'lcv'}
    if include_non_road:
        vehicle_type_combinations['rail'] = 'rail'
        vehicle_type_combinations['ship'] = 'ship'
        vehicle_type_combinations['air'] = 'air'
        vehicle_type_combinations['all'] = 'non-road'
    else:
        vehicle_type_combinations['rail'] = 'non-road'
        vehicle_type_combinations['ship'] = 'non-road'
        vehicle_type_combinations['air'] = 'non-road'
        vehicle_type_combinations['all'] = 'non-road'    
    
    df['Vehicle Type new'] = df['Vehicle Type'].map(vehicle_type_combinations)
    #drop then rename vehicle type
    df['Vehicle Type'] = df['Vehicle Type new']
    #dxrop the new column
    df.drop(columns=['Vehicle Type new'], inplace=True)
    
    if aggregation_type[0] == 'weighted_average':
        df['Weighted Value'] = df[value_col] * df[aggregation_type[1]]
        #create copy of aggregation_type[1] spo we can set it to 1 if it is 0
        df[aggregation_type[1] + ' copy'] = df[aggregation_type[1]]
        #sum weighted values and weights so we can calculate weighted average:
        df = df.groupby(new_index_cols).sum().reset_index()
        #fill 0 with 1
        df[aggregation_type[1] + ' copy'] = df[aggregation_type[1] + ' copy'].replace(0,1)
        #calculate weighted average
        df[value_col] = df['Weighted Value']/df[aggregation_type[1] + ' copy']
        #drop the columns we don't need anymore
        df.drop(columns=['Weighted Value', aggregation_type[1] + ' copy'], inplace=True)
        
    elif aggregation_type[0]=='sum':
        df = df.groupby(new_index_cols, group_keys=False).sum(numeric_only=True).reset_index()
        
    return df
    
def remap_drive_types(df, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'], drive_type_mapping_set='original', aggregation_type=('sum',), include_non_road=True):
    if drive_type_mapping_set == 'original':
        drive_type_combinations = {'ice_g':'ice_g', 'ice_d':'ice_d', 'phev_d':'phev_d', 'phev_g':'phev_g', 'bev':'bev', 'fcev':'fcev', 'cng':'cng', 'lpg':'lpg'}
    elif drive_type_mapping_set == 'simplified':
        drive_type_combinations = {'ice_g':'ice', 'ice_d':'ice', 'phev_d':'phev', 'phev_g':'phev', 'bev':'bev', 'fcev':'fcev', 'cng':'gas', 'lpg':'gas'}
        
    if include_non_road:
        drive_type_combinations['rail'] = 'rail'
        drive_type_combinations['ship'] = 'ship'
        drive_type_combinations['air'] = 'air'
        drive_type_combinations['all'] = 'non-road'
    else:
        drive_type_combinations['rail'] = 'non-road'
        drive_type_combinations['ship'] = 'non-road'
        drive_type_combinations['air'] = 'non-road'
        drive_type_combinations['all'] = 'non-road'
            
    df["Drive new"] = df['Drive'].map(drive_type_combinations)
    df['Drive'] = df['Drive new']
    df.drop(columns=['Drive new'], inplace=True)
    
    if aggregation_type[0] == 'weighted_average':
        df['Weighted Value'] = df[value_col] * df[aggregation_type[1]]
        #create copy of aggregation_type[1] spo we can set it to 1 if it is 0
        df[aggregation_type[1] + ' copy'] = df[aggregation_type[1]]
        #sum weighted values and weights so we can calculate weighted average:
        df = df.groupby(new_index_cols).sum().reset_index()
        #fill 0 with 1
        df[aggregation_type[1] + ' copy'] = df[aggregation_type[1] + ' copy'].replace(0,1)
        #calculate weighted average
        df[value_col] = df['Weighted Value']/df[aggregation_type[1] + ' copy']
        #drop the columns we don't need anymore
        df.drop(columns=['Weighted Value', aggregation_type[1] + ' copy'], inplace=True)
        
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

def remap_stocks_and_sales_based_on_economy(stocks, new_sales_shares_all_plot_drive_shares):
    """ based on patterns we will make teh graphs a bit different by economy."""
    stocks_sum_economies = identify_high_2w_economies(stocks)
    #keep those economies in the stocks df
    high_2w_economies_stocks = stocks[stocks['Economy'].isin(stocks_sum_economies)].copy()
    other_economies_stocks = stocks[~stocks['Economy'].isin(stocks_sum_economies)].copy()
    high_2w_economies_sales = new_sales_shares_all_plot_drive_shares[new_sales_shares_all_plot_drive_shares['Economy'].isin(stocks_sum_economies)].copy()
    other_economies_sales = new_sales_shares_all_plot_drive_shares[~new_sales_shares_all_plot_drive_shares['Economy'].isin(stocks_sum_economies)].copy()    
    
    high_2w_economies_stocks = remap_vehicle_types(high_2w_economies_stocks, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
    high_2w_economies_sales = remap_vehicle_types(high_2w_economies_sales, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
    
    #then do remappign for the otehres:
    other_economies_stocks = remap_vehicle_types(other_economies_stocks, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
    other_economies_sales = remap_vehicle_types(other_economies_sales, value_col='Value', new_index_cols = ['Scenario', 'Economy', 'Date', 'Transport Type', 'Vehicle Type', 'Drive'],vehicle_type_mapping_set='simplified')
    
    
    #concat the two dataframes
    stocks = pd.concat([high_2w_economies_stocks, other_economies_stocks])
    new_sales_shares_all_plot_drive_shares = pd.concat([high_2w_economies_sales, other_economies_sales])
    
    return stocks, new_sales_shares_all_plot_drive_shares
    
###################################################
def plot_share_of_transport_type(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares_df,stocks_df,fig_dict, color_preparation_list, colors_dict,share_of_transport_type_type):
    stocks = stocks_df.copy()
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    
    stocks, new_sales_shares_all_plot_drive_shares = remap_stocks_and_sales_based_on_economy(stocks, new_sales_shares_all_plot_drive_shares)
    # #sum up all the sales shares for each drive type
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    #now calucalte share of total stocks as a proportion like the sales share
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'], group_keys=False)['Value'].apply(lambda x: x/x.sum(numeric_only=True))
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


###################################################
def plot_share_of_transport_type_non_road(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares_df,fig_dict, color_preparation_list, colors_dict):
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df[new_sales_shares_all_plot_drive_shares_df['Medium']!='road'].copy()
    
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        new_sales_shares_all_plot_drive_shares_scenario = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario)]
        ###        
        
        #times shares by 100
        new_sales_shares_all_plot_drive_shares_scenario['Value'] = new_sales_shares_all_plot_drive_shares_scenario['Value']*100
                
        for economy in ECONOMY_IDs:
            plot_data =  new_sales_shares_all_plot_drive_shares_scenario.loc[(new_sales_shares_all_plot_drive_shares_scenario['Economy']==economy)].copy()

            # #concat drive and vehicle type
            # plot_data['Drive'] = plot_data['Drive'] + ' ' + plot_data['Vehicle Type']
            #sort by date col and line_dash
            plot_data.sort_values(by=['Date'], inplace=True)
            # #############
            # #now plot
            # if share_of_transport_type_type == 'passenger':
            #     title = f'Sales and stocks shares for passenger vehicles (%)'

            #     fig = px.line(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)

            #     #add fig to dictionary for scenario and economy:
            #     fig_dict[economy][scenario]['share_of_transport_type_passenger'] = [fig,title]
            
            # #############
            # elif share_of_transport_type_type == 'freight':
            #     title = f'Sales and stocks shares for freight vehicles (%)'

            #     fig = px.line(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title, line_dash='line_dash', color_discrete_map=colors_dict)

            #     #add fig to dictionary for scenario and economy:
            #     fig_dict[economy][scenario]['share_of_transport_type_freight'] = [fig,title]
            # elif share_of_transport_type_type == 'all':
            title = f'Share of new activity for non road (%)'
            # sum up, because 2w are used in freight and passenger:
            plot_data = plot_data.groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive']).sum(numeric_only=True).reset_index()
            fig = px.line(plot_data, x='Date', y='Value', color='Drive', title=title, line_dash='Transport Type', color_discrete_map=colors_dict)

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['non_road_share_of_transport_type'] = [fig,title]
            # #############
            # else:
            #     raise ValueError('share_of_transport_type_type must be either passenger or freight')
    
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(plot_data['Drive'].unique().tolist())
    return fig_dict, color_preparation_list


def plot_share_of_vehicle_type_by_transport_type(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares_df,stocks_df,fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type):
    #This data is in terms of transport type, so will need to normalise it to vehicle type by summing up the shares for each vehicle type and dividing individual shares by their sum
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares_df.copy()
    stocks = stocks_df.copy()
    
    stocks, new_sales_shares_all_plot_drive_shares = remap_stocks_and_sales_based_on_economy(stocks, new_sales_shares_all_plot_drive_shares)
    
    new_sales_shares_all_plot_drive_shares['Value'] = new_sales_shares_all_plot_drive_shares.groupby(['Date','Economy', 'Scenario', 'Transport Type', 'Vehicle Type'], group_keys=False)['Value'].transform(lambda x: x/x.sum())
    
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type','Vehicle Type'], group_keys=False)['Value'].apply(lambda x: x/x.sum(numeric_only=True))
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
    
    stocks, new_sales_shares_all_plot_drive_shares = remap_stocks_and_sales_based_on_economy(stocks, new_sales_shares_all_plot_drive_shares)
    
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
    
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive', 'Value']].groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive'], group_keys=False).sum().reset_index()
        
    new_sales_shares_all_plot_drive_shares['line_dash'] = 'sales'
    
    stocks = stocks[['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive','Value']].groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive'], group_keys=False).sum().reset_index()
    stocks['Value'] = stocks.groupby(['Scenario', 'Economy', 'Date', 'Transport Type'], group_keys=False)['Value'].apply(lambda x: x/x.sum(numeric_only=True))
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
def energy_use_by_fuel_type(ECONOMY_IDs,energy_output_for_outlook_data_system_tall,fig_dict,  color_preparation_list, colors_dict,transport_type):
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    energy_use_by_fuel_type= energy_output_for_outlook_data_system_tall[['Economy', 'Scenario','Date', 'Fuel', 'Transport Type','Energy']].groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel']).sum().reset_index().copy()
    energy_use_by_fuel_type['Measure'] = 'Energy'
    energy_use_by_fuel_type['Unit'] = energy_use_by_fuel_type['Measure'].map(config.measure_to_unit_concordance_dict)
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        energy_use_by_fuel_type_scen = energy_use_by_fuel_type.loc[(energy_use_by_fuel_type['Scenario']==scenario)].copy()
        
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
                energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.groupby(['Economy', 'Date', 'Fuel','Unit']).sum(numeric_only =True).reset_index()
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
    
    stocks = remap_vehicle_types(stocks, value_col='Value', new_index_cols = ['Date', 'Vehicle Type','Unit','Scenario', 'Economy'], vehicle_type_mapping_set='simplified')
    
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
    else:
        fkm.loc[fkm['Medium'] != 'road', 'Drive'] = fkm.loc[fkm['Medium'] != 'road', 'Medium']
        
    fkm = fkm[['Economy', 'Date', 'Drive','Scenario', 'freight_tonne_km']].groupby(['Economy', 'Date', 'Scenario','Drive']).sum().reset_index()

    #simplfiy drive type using remap_drive_types
    fkm = remap_drive_types(fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
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

def passenger_km_by_drive(ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT,  color_preparation_list, colors_dict):
    
    pkm = model_output_detailed.loc[model_output_detailed['Transport Type']=='passenger'].rename(columns={'Activity':'passenger_km'}).copy()
    
    if DROP_NON_ROAD_TRANSPORT:
        pkm = pkm.loc[pkm['Medium']=='road'].copy()
    else:
        pkm.loc[pkm['Medium'] != 'road', 'Drive'] = pkm.loc[pkm['Medium'] != 'road', 'Medium']
    
    pkm = pkm[['Economy', 'Date', 'Drive','Scenario', 'passenger_km']].groupby(['Economy', 'Date','Scenario', 'Drive']).sum().reset_index()

    #simplfiy drive type using remap_drive_types
    pkm = remap_drive_types(pkm, value_col='passenger_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
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

def activity_and_macro_lines(ECONOMY_IDs,original_model_output_8th_df,model_output_detailed,growth_forecasts, fig_dict, color_preparation_list, colors_dict, indexed=False):
    original_model_output_8th = original_model_output_8th_df.copy()
    #grab only the Activity then sum it by economy, scenario and date
    original_model_output_8th = original_model_output_8th[['Economy', 'Scenario', 'Date', 'Activity']].copy().drop_duplicates()
    original_model_output_8th = original_model_output_8th.groupby(['Economy', 'Scenario', 'Date']).sum().reset_index()
    #rename actovity to Activity_8th
    original_model_output_8th = original_model_output_8th.rename(columns={'Activity':'Activity_8th'})
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        model_output_detailed_scen = model_output_detailed.loc[(model_output_detailed['Scenario']==scenario)].copy()
        growth_forecasts_scen = growth_forecasts.loc[(growth_forecasts['Scenario']==scenario)].copy()
        ###
        #if scenario is Target then look for 'Carbon Neutral' in scenario name
        if scenario == 'Target':
            original_model_output_8th_scenario = original_model_output_8th.loc[original_model_output_8th['Scenario']=='Carbon Neutral'].copy()
        else:
            original_model_output_8th_scenario = original_model_output_8th.loc[original_model_output_8th['Scenario']==scenario].copy()
    
        #drop scenario col
        original_model_output_8th_scenario = original_model_output_8th_scenario.drop(columns=['Scenario'])
        
        ###
        original_growth_forecasts = growth_forecasts_scen[['Activity_growth','Date','Economy', 'Transport Type']].copy()
        #calcualte cumulative growth so it can be compared to activity when it is converted to indexed or growth:
        original_growth_forecasts['Activity_growth'] = original_growth_forecasts.groupby(['Economy', 'Transport Type'])['Activity_growth'].cumprod()
        #split into freight and passenger, if the values are differen then we will plot them sepeartely, if not just plot one:
        original_growth_forecasts = original_growth_forecasts.pivot(index=['Economy', 'Date'], columns='Transport Type', values='Activity_growth').reset_index()
        if original_growth_forecasts['freight'].equals(original_growth_forecasts['passenger']):
            PLOT_ORIGINAL_FORECASTS_BY_TTYPE = False
            original_growth_forecasts = original_growth_forecasts[['Economy', 'Date', 'freight']].copy().rename(columns={'freight':'Original_activity'})
        else:
            PLOT_ORIGINAL_FORECASTS_BY_TTYPE = True
            original_growth_forecasts_p = original_growth_forecasts[['Economy', 'Date', 'passenger']].copy().rename(columns={'passenger':'Original_activity_passenger'})
            original_growth_forecasts_f = original_growth_forecasts[['Economy', 'Date', 'freight']].copy().rename(columns={'freight':'Original_activity_freight'})
        ###
        
        
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
            if PLOT_ORIGINAL_FORECASTS_BY_TTYPE:
                original_growth_forecasts_p = calc_index(original_growth_forecasts_p,'Original_activity_passenger')
                original_growth_forecasts_f = calc_index(original_growth_forecasts_f,'Original_activity_passenger')
            else:
                original_growth_forecasts = calc_index(original_growth_forecasts,'Original_activity')
                

        else:#calc growth
                
            population = calc_growth(model_output_detailed_scen[['Population','Date','Economy']].drop_duplicates(),'Population')
            gdp = calc_growth(model_output_detailed_scen[['Gdp','Date','Economy']].drop_duplicates(),'Gdp')
            freight_km = calc_growth(freight_km[['freight_tonne_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'freight_tonne_km')
            passenger_km = calc_growth(passenger_km[['passenger_km','Date','Economy']].drop_duplicates().dropna().groupby(['Economy','Date']).sum().reset_index(),'passenger_km')
            original_model_output_8th_scenario = calc_growth(original_model_output_8th_scenario,'Activity_8th')
            if PLOT_ORIGINAL_FORECASTS_BY_TTYPE:
                original_growth_forecasts_p = calc_growth(original_growth_forecasts_p,'Original_activity_passenger')
                original_growth_forecasts_f = calc_growth(original_growth_forecasts_f,'Original_activity_freight')
            else:
                original_growth_forecasts = calc_growth(original_growth_forecasts,'Original_activity')

            
        ##
        #set 'line_dash' to 'solid' in passenger_km and freight_km, then set to 'dash' in original_model_output_8th_scenario and  population and gdp
        passenger_km['line_dash'] = 'final'
        freight_km['line_dash'] = 'final'
        original_model_output_8th_scenario['line_dash'] = 'input'
        population['line_dash'] = 'input'
        gdp['line_dash'] = 'input'
        if PLOT_ORIGINAL_FORECASTS_BY_TTYPE:
            original_growth_forecasts_p['line_dash'] = 'input'
            original_growth_forecasts_f['line_dash'] = 'input'
            
            #concat all the data together then melt:
            index_data = pd.concat([population, gdp, freight_km, passenger_km,original_model_output_8th_scenario, original_growth_forecasts_p, original_growth_forecasts_f], axis=0)
        else:
            original_growth_forecasts['line_dash'] = 'input'
            
            #concat all the data together then melt:
            index_data = pd.concat([population, gdp, freight_km, passenger_km,original_model_output_8th_scenario, original_growth_forecasts], axis=0)
                
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
    #average out the supply side fuel mixing by economy, scenario and new fuel, so that we have the average share of each fuel type that is mixed into another fuel type (note that this isnt weighted by the amount of fuel mixed in, just the share of the fuel that is mixed in... its a safe asumption given that every new fuel should be mixed in with similar shares
    supply_side_fuel_mixing= supply_side_fuel_mixing[['Date', 'Economy','Scenario', 'New_fuel' ,'Supply_side_fuel_share']].groupby(['Date', 'Economy','Scenario', 'New_fuel']).mean().reset_index()
    #round the Supply_side_fuel_share column to 2dp
    supply_side_fuel_mixing['Supply_side_fuel_share'] = supply_side_fuel_mixing['Supply_side_fuel_share'].round(2)
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
    avg_age = remap_drive_types(avg_age, value_col='Average_age', new_index_cols = ['Economy', 'Date','Scenario', 'Transport Type', 'Drive'], drive_type_mapping_set='simplified', aggregation_type=('weighted_average', 'Stocks'))# 'Vehicle Type',
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
            # avg_age_economy['Drive'] = avg_age_economy['Vehicle Type']+' '+ avg_age_economy['Drive'] 
            #now plot
            fig = px.line(avg_age_economy, x='Date', y='Average_age', color='Drive',line_dash = 'Transport Type', color_discrete_map=colors_dict)
            title_text = f'Average Age of {medium} vehicles by drive'

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario][title] = [fig, title_text]
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(avg_age_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list



def plot_stocks_per_capita(ECONOMY_IDs,gompertz_parameters_df, model_output_detailed, first_road_model_run_data, fig_dict, color_preparation_list, colors_dict):
    
    #Plot stocks per capita for each transport type. Also plot the gompertz line for the economy, which is a horizontal line. 
    first_model_run_stocks_per_capita = first_road_model_run_data[['Economy', 'Date', 'Stocks','Scenario', 'Vehicle Type', 'Transport Type', 'Population']].copy().drop_duplicates()
    #set 'model' to 'first_model_run' so we can distinguish it from the other model runs
    first_model_run_stocks_per_capita['Model'] = 'Original'
    
    stocks_per_capita = model_output_detailed[['Economy', 'Date','Medium', 'Scenario','Stocks', 'Vehicle Type', 'Transport Type','Population']].copy()
    stocks_per_capita = stocks_per_capita.loc[stocks_per_capita['Medium']=='road'].copy()
    #set 'model' to 'Adjusted' so we can distinguish it from the other model runs
    stocks_per_capita['Model'] = 'Adjusted'
    
    #now concat the two dfs:
    stocks_per_capita = pd.concat([stocks_per_capita, first_model_run_stocks_per_capita], axis=0)
    
    #extract the vehicles_per_stock_parameters:
    vehicles_per_stock_parameters = pd.read_excel('input_data/parameters.xlsx', sheet_name='gompertz_vehicles_per_stock')
    #convert from regiosn to economies:
    vehicles_per_stock_regions = pd.read_excel('input_data/parameters.xlsx', sheet_name='vehicles_per_stock_regions')
    #join on region
    vehicles_per_stock_parameters = vehicles_per_stock_parameters.merge(vehicles_per_stock_regions, on='Region', how='left')
    #dro regions
    vehicles_per_stock_parameters.drop(columns=['Region'], inplace=True)
    
    #Convert some stocks to gompertz adjusted stocks by multiplying them by the vehicle_gompertz_factors. This is because you can expect some economies to have more or less of that vehicle type than others. These are very general estiamtes, and could be refined later.
    new_stocks = stocks_per_capita.merge(vehicles_per_stock_parameters, on=['Vehicle Type', 'Economy'], how='left')
    new_stocks['Stocks'] = new_stocks['Stocks'] * new_stocks['gompertz_vehicles_per_stock']
    
    #recalcualte stocks per capita after summing up stocks by economy and transport type, scneario anmd date
    #extract population so we can join it after the sum:
    population = stocks_per_capita[['Economy', 'Scenario','Date', 'Population','Model']].drop_duplicates()
    stocks_per_capita = stocks_per_capita.drop(columns=['Population']).groupby(['Economy', 'Date', 'Scenario','Transport Type','Model']).sum(numeric_only=True).reset_index()
    #join population back on:
    stocks_per_capita = stocks_per_capita.merge(population, on=['Economy','Scenario', 'Date','Model'], how='left')
    #calcualte stocks per capita
    stocks_per_capita['Thousand_stocks_per_capita'] = stocks_per_capita['Stocks']/stocks_per_capita['Population']
    #convert to more readable units. We will convert back later if we need to #todo do we need to?
    stocks_per_capita['Stocks_per_thousand_capita'] = stocks_per_capita['Thousand_stocks_per_capita'] * 1000000
    
    gompertz_parameters = gompertz_parameters_df[['Economy','Date', 'Gompertz_gamma']].drop_duplicates().dropna().copy()
    #and filter so data is less than config.GRAPHING_END_YEAR
    gompertz_parameters = gompertz_parameters.loc[(gompertz_parameters['Date']<=config.GRAPHING_END_YEAR)&(gompertz_parameters['Date']>=config.OUTLOOK_BASE_YEAR)].copy()
    #set transport type to 'maximum_stocks_per_captia'
    gompertz_parameters['Transport Type'] = 'stocks_per_capita_threshold'
    gompertz_parameters['Model'] = 'Adjusted'
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
            fig = px.line(stocks_per_capita_economy, x='Date', y='Stocks_per_thousand_capita', color='Transport Type', line_dash='Model', color_discrete_map=colors_dict)
            title_text = 'Stocks per capita (Thousand)'

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['stocks_per_capita'] = [fig, title_text]
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(stocks_per_capita_economy['Transport Type'].unique().tolist())
    return fig_dict, color_preparation_list


def plot_non_road_energy_use(ECONOMY_IDs,energy_output_for_outlook_data_system_tall, fig_dict,  color_preparation_list, colors_dict,transport_type):
    
    #we will plot the energy use by fuel type for non road as an area chart.
    model_output_with_fuels = energy_output_for_outlook_data_system_tall.copy()
    #extract Medium != road
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
                energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.groupby(['Economy', 'Date', 'Fuel','Unit']).sum(numeric_only = True).reset_index()
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


def turnover_rate_by_vehicle_type_line(ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict,transport_type):
    #break activity into its _vehicle types and plot the variation by medium and treansport type on a line chart. will do a plot for each transport type or a plot where passneger km and freight km are in same plot. in this case, it will have pattern_shape="Transport Type" to distinguish between the two:
    # model_output_detailed.pkl
    #loop through scenarios and grab the data for each scenario:
    #since we need detail on non road drive types, we have to pull the data fromm here:
    #create a new df with only the data we need:
    turnover_rate_by_vtype = model_output_detailed.copy()
    #drop non road since its turnover rate is non informative:
    turnover_rate_by_vtype = turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Medium']=='road'].copy()
    turnover_rate_by_vtype = turnover_rate_by_vtype[['Economy', 'Date', 'Medium','Transport Type','Scenario','Vehicle Type', 'Turnover_rate', 'Stocks']].groupby(['Economy', 'Date', 'Medium','Transport Type','Scenario','Vehicle Type']).agg({'Turnover_rate':'mean', 'Stocks':'sum'}).reset_index()#,'Drive'
    # #simplify the drive types:
    # turnover_rate_by_vtype = remap_drive_types(turnover_rate_by_vtype, value_col='Turnover_rate', new_index_cols = ['Economy', 'Date', 'Medium','Transport Type','Vehicle Type','Scenario','Drive'],drive_type_mapping_set='simplified', aggregation_type=('weighted_average', 'Stocks'))
    #and simplify the vehicle types:
    turnover_rate_by_vtype = remap_vehicle_types(turnover_rate_by_vtype, value_col='Turnover_rate', new_index_cols = ['Economy', 'Date', 'Medium','Transport Type','Vehicle Type','Scenario'],vehicle_type_mapping_set='simplified', aggregation_type=('weighted_average', 'Stocks'))#,'Drive'
    #add units (by setting measure to Freight_tonne_km haha)
    turnover_rate_by_vtype['Measure'] = 'Turnover_rate'
    #add units
    turnover_rate_by_vtype['Unit'] = '%'

    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        #filter for the scenario:
        turnover_rate_by_vtype_s = turnover_rate_by_vtype.loc[turnover_rate_by_vtype['Scenario']==scenario].copy()
        for economy in ECONOMY_IDs:
            #filter to economy
            turnover_rate_by_vtype_economy = turnover_rate_by_vtype_s.loc[turnover_rate_by_vtype_s['Economy']==economy].copy()
            #TEMP:
            #CHECK FOR DUPICATES WHEN YOU INGORE THE VLAUE OCLUMN:
            cols = turnover_rate_by_vtype_economy.columns.tolist()
            cols = cols.remove('Turnover_rate')
            dupes = turnover_rate_by_vtype_economy[turnover_rate_by_vtype_economy.duplicated(subset=cols, keep=False)]
            if len(dupes)>0:
                breakpoint()
            # Now sort the DataFrame by the 'Date' column:
            turnover_rate_by_vtype_economy.sort_values(by='Date', inplace=True)
            #sort by date

            if transport_type=='passenger':
                #now plot
                # fig = px.line(turnover_rate_by_vtype_economy.loc[turnover_rate_by_vtype_economy['Transport Type']=='passenger'], x='Date', y='Turnover_rate', color='Drive', title='Passenger turnover_rate by drive', color_discrete_map=colors_dict)
                fig = px.line(turnover_rate_by_vtype_economy.loc[turnover_rate_by_vtype_economy['Transport Type']=='passenger'],x='Date', y='Turnover_rate', line_dash = 'Medium', color='Vehicle Type', title='Passenger turnover_rate by vehicle type', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Passenger turnover rate (based on mean)'#.format(turnover_rate_by_vtype_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['line_turnover_rate_by_vtype_passenger'] = [fig, title_text]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.line(turnover_rate_by_vtype_economy.loc[turnover_rate_by_vtype_economy['Transport Type']=='freight'],x='Date', y='Turnover_rate', line_dash = 'Medium', color='Vehicle Type', title='Freight turnover_rate by vehicle type', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Freight turnover rate (based on mean)'#.format(turnover_rate_by_vtype_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['line_turnover_rate_by_vtype_freight'] = [fig, title_text]
                
            elif transport_type == 'all':
                #get mean again because there are some vehicle types used for bnoth ttypes:
                turnover_rate_by_vtype_economy = turnover_rate_by_vtype_economy.groupby(['Economy', 'Date','Medium', 'Vehicle Type','Unit']).mean().reset_index().copy()
                #sum across transport types
                fig = px.line(turnover_rate_by_vtype_economy,x='Date', y='Turnover_rate', line_dash = 'Medium', color='Vehicle Type', title='Passenger turnover_rate by vehicle type', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'turnover_rate (Freight/Passenger km) (based on mean)'#.format(turnover_rate_by_vtype_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['line_turnover_rate_by_vtype_all'] = [fig, title_text]
                
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(turnover_rate_by_vtype_economy['Vehicle Type'].unique().tolist())
    return fig_dict, color_preparation_list

def emissions_by_fuel_type(ECONOMY_IDs, emissions_factors,model_output_with_fuels, fig_dict, color_preparation_list, colors_dict,transport_type):
    #load in data and recreate plot, as created in all_economy_graphs
    #loop through scenarios and grab the data for each scenario:
    model_output_with_fuels_sum= model_output_with_fuels[['Economy', 'Scenario','Date', 'Fuel', 'Transport Type','Energy']].groupby(['Economy', 'Scenario','Date','Transport Type', 'Fuel']).sum().reset_index().copy()
    
    #join on the emissions factors (has the cols fuel_code,	Emissions factor (MT/PJ))
    model_output_with_fuels_sum = model_output_with_fuels_sum.merge(emissions_factors, how='left', left_on='Fuel', right_on='fuel_code')
    #identify where there are no emissions factors:
    missing_emissions_factors = model_output_with_fuels_sum.loc[model_output_with_fuels_sum['Emissions factor (MT/PJ)'].isna()].copy()
    if len(missing_emissions_factors)>0:
        breakpoint()
        raise ValueError(f'missing emissions factors, {missing_emissions_factors.Fuel.unique()}')
    
    #calculate emissions:
    model_output_with_fuels_sum['Emissions'] = model_output_with_fuels_sum['Energy'] * model_output_with_fuels_sum['Emissions factor (MT/PJ)']

    model_output_with_fuels_sum['Measure'] = 'Emissions'
    model_output_with_fuels_sum['Unit'] = 'Mt CO2'
    
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        emissions_by_fuel_type_scen = model_output_with_fuels_sum.loc[(model_output_with_fuels_sum['Scenario']==scenario)].copy()
        
        for economy in ECONOMY_IDs:
            #filter to economy
            emissions_by_fuel_type_economy = emissions_by_fuel_type_scen.loc[(emissions_by_fuel_type_scen['Economy']==economy)].copy()
            
            # calculate total 'Emissions' for each 'Fuel' 
            total_emissions_per_fuel = emissions_by_fuel_type_economy.groupby('Fuel')['Emissions'].sum()

            # Create an ordered category of 'Fuel' labels sorted by total 'Emissions'
            emissions_by_fuel_type_economy['Fuel'] = pd.Categorical(
                emissions_by_fuel_type_economy['Fuel'],
                categories = total_emissions_per_fuel.sort_values(ascending=False).index,
                ordered=True
            )

            # Now sort the DataFrame by the 'Fuel' column:
            emissions_by_fuel_type_economy.sort_values(by='Fuel', inplace=True)
            if transport_type=='passenger':
                #now plot
                fig = px.area(emissions_by_fuel_type_economy.loc[emissions_by_fuel_type_economy['Transport Type']=='passenger'], x='Date', y='Emissions', color='Fuel', title='Emissions by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Emissions by Fuel {} ({})'.format(transport_type, emissions_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['emissions_by_fuel_type_passenger'] = [fig, title_text]
                
            elif transport_type == 'freight':
                #now plot
                fig = px.area(emissions_by_fuel_type_economy.loc[emissions_by_fuel_type_economy['Transport Type']=='freight'], x='Date', y='Emissions', color='Fuel', title='Emissions by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Emissions by Fuel {} ({})'.format(transport_type, emissions_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['emissions_by_fuel_type_freight'] = [fig, title_text]
                
            elif transport_type == 'all':
                #sum across transport types
                emissions_by_fuel_type_economy = emissions_by_fuel_type_economy.groupby(['Economy', 'Date', 'Fuel','Unit'], group_keys=False).sum().reset_index()
                #now plot
                fig = px.area(emissions_by_fuel_type_economy, x='Date', y='Emissions', color='Fuel', title='Emissions by Fuel', color_discrete_map=colors_dict)
                
                #add units to y col
                title_text = 'Emissions by Fuel ({})'.format(emissions_by_fuel_type_economy['Unit'].unique()[0])
                
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['emissions_by_fuel_type_all'] = [fig, title_text]
            else:
                raise ValueError('transport_type must be passenger, all or freight')
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(emissions_by_fuel_type_economy['Fuel'].unique().tolist())
    return fig_dict, color_preparation_list


def plot_comparison_of_energy_by_dataset(ECONOMY_IDs,energy_output_for_outlook_data_system_df, energy_use_esto, energy_8th, fig_dict, color_preparation_list, colors_dict):
            
    model_output_with_fuels = energy_output_for_outlook_data_system_df.copy()
    energy_use_esto_df = energy_use_esto.copy()
    energy_8th_df = energy_8th.copy()#.drop(columns=['Stocks', 'Activity'])
    
    #create col in both which refers to where they came from:
    energy_use_esto_df['Dataset'] = 'ESTO'
    model_output_with_fuels['Dataset'] = '9th_model'
    energy_8th_df['Dataset'] = '8th_model'
    
    #create a new df with only the data we need: 
    energy_use_by_fuel_type = pd.concat([model_output_with_fuels, energy_use_esto_df,energy_8th_df])
    
    # #because of the way we mapped drive to fuel in the data prep phase, where medium is not road then set drive to medium. This will decrease some of the granularity of the data, but it will allow us to compare the data across the models more easily (plus there are too many lines anyway!)
    # energy_use_by_fuel_type.loc[energy_use_by_fuel_type['Medium']!='road', 'Fuel'] = energy_use_by_fuel_type.loc[energy_use_by_fuel_type['Medium']!='road', 'Medium']

    
    energy_use_by_fuel_type = energy_use_by_fuel_type[['Economy','Scenario', 'Date', 'Fuel', 'Energy','Dataset']].groupby(['Economy','Scenario', 'Date','Dataset', 'Fuel']).sum().reset_index()
    
    #create a total fuel for each dataset. this will jsut be the sum of energy for each dataset, by year, scenario and economy:
    energy_use_by_fuel_type_totals = energy_use_by_fuel_type[['Economy','Scenario', 'Date','Dataset', 'Energy']].groupby(['Economy','Scenario', 'Date','Dataset']).sum(numeric_only=True).reset_index().copy()
    #set Fuel to total:
    energy_use_by_fuel_type_totals['Fuel'] = 'Total'
    #cocnat the total onto the main df:
    energy_use_by_fuel_type = pd.concat([energy_use_by_fuel_type, energy_use_by_fuel_type_totals])
    
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
            
            #now plot
            fig = px.line(energy_use_by_fuel_type_economy, x='Date', y='Energy', color='Fuel',line_dash='Dataset', title='Compared Energy by Fuel', color_discrete_map=colors_dict)
            
            #add units to y col
            title_text = 'Compared energy by Fuel (8th_simplified, 9th and ESTO)'#.format(energy_use_by_fuel_type_economy['Unit'].unique()[0])
            
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['compare_energy'] = [fig, title_text]
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_use_by_fuel_type_economy['Fuel'].unique().tolist())
    
    return fig_dict, color_preparation_list

def plot_energy_efficiency_growth(ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict):

    #to help with checking that the data is realistic, plot growth in energy efficiency here:
    
    energy_eff = model_output_detailed.copy()
    if DROP_NON_ROAD_TRANSPORT:
        energy_eff = energy_eff.loc[energy_eff['Medium']=='road']
    else:
        #set vehicle type to medium so we can plot strip plot by vehicle type: 
        energy_eff.loc[energy_eff['Medium'] != 'road', 'Vehicle Type'] = energy_eff.loc[energy_eff['Medium'] != 'road', 'Medium']
        
    #calc mean and, importantly, remove date, scenario
    energy_eff = energy_eff[['Date', 'Economy', 'Vehicle Type', 'Drive', 'Scenario','Efficiency']].groupby(['Date','Economy', 'Vehicle Type','Scenario', 'Drive']).mean().reset_index()

    # #simplfiy drive type using remap_drive_types
    # fkm = remap_drive_types(fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    energy_eff['Measure'] = 'Efficiency growth'
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        energy_eff_by_scen = energy_eff.loc[(energy_eff['Scenario']==scenario)].copy()
        
        #calcaulte growth by calculating the % change in efficiency from the previous year:
        
        #sort by date:
        energy_eff_by_scen = energy_eff_by_scen.sort_values(by='Date')
        #calc % change:
        energy_eff_by_scen['Efficiency_growth'] = energy_eff_by_scen.groupby(['Economy', 'Vehicle Type', 'Drive']).Efficiency.pct_change()
        
        

        for economy in ECONOMY_IDs:
            #filter to economy
            energy_eff_by_scen_by_economy = energy_eff_by_scen.loc[energy_eff_by_scen['Economy']==economy].copy()

            #sort by date
            # freight_tonne_km_by_drive_economy = freight_tonne_km_by_drive_economy.sort_values(by='Date')
            #now plot
            title='Energy efficiency growth by vehicle type'
            fig = px.line(energy_eff_by_scen_by_economy, x='Date', y='Efficiency_growth', color='Drive',line_dash='Vehicle Type', title=title, color_discrete_map=colors_dict)
            
            if DROP_NON_ROAD_TRANSPORT:
                #add fig to dictionary for scenario and economy:
                fig_dict[economy][scenario]['energy_efficiency_growth_road'] = [fig, title]
            else:
                fig_dict[economy][scenario]['energy_efficiency_growth_all'] = [fig, title]
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_eff_by_scen_by_economy['Drive'].unique().tolist())
    
    return fig_dict, color_preparation_list

def plot_energy_efficiency(ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict):
    #to help with checking that the data is realistic, plot energy efficiency here:
    
    energy_eff = model_output_detailed.copy()
    if DROP_NON_ROAD_TRANSPORT:
        energy_eff = energy_eff.loc[energy_eff['Medium']=='road']
    else:
        #set vehicle type to medium so we can plot strip plot by vehicle type: 
        energy_eff.loc[energy_eff['Medium'] != 'road', 'Vehicle Type'] = energy_eff.loc[energy_eff['Medium'] != 'road', 'Medium']
        
    #calc mean and, importantly, remove date, scenario
    energy_eff = energy_eff[['Economy', 'Vehicle Type', 'Drive', 'Scenario','Efficiency']].groupby(['Economy', 'Vehicle Type','Scenario', 'Drive']).mean().reset_index()

    # #simplfiy drive type using remap_drive_types
    # fkm = remap_drive_types(fkm, value_col='freight_tonne_km', new_index_cols = ['Economy', 'Date', 'Scenario','Drive'])
    
    #add units (by setting measure to Freight_tonne_km haha)
    energy_eff['Measure'] = 'Efficiency'
    #add units
    energy_eff['Unit'] = energy_eff['Measure'].map(config.measure_to_unit_concordance_dict)
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in config.economy_scenario_concordance['Scenario'].unique():
        
        energy_eff_by_scen = energy_eff.loc[(energy_eff['Scenario']==scenario)].copy()

        for economy in ECONOMY_IDs:
            #filter to economy
            energy_eff_by_scen_by_economy = energy_eff_by_scen.loc[energy_eff_by_scen['Economy']==economy].copy()

            #sort by date
            # freight_tonne_km_by_drive_economy = freight_tonne_km_by_drive_economy.sort_values(by='Date')
            #now plot
            title='Energy efficiency by vehicle type'
            fig = px.strip(energy_eff_by_scen_by_economy, x='Vehicle Type', y='Efficiency', color='Drive', title=title, color_discrete_map=colors_dict)
            #add fig to dictionary for scenario and economy:
            if DROP_NON_ROAD_TRANSPORT:
                fig_dict[economy][scenario]['energy_efficiency_road'] = [fig, title]
            else:
                fig_dict[economy][scenario]['energy_efficiency_all'] = [fig, title]
            
    #put labels for the color parameter in color_preparation_list so we can match them against suitable colors:
    color_preparation_list.append(energy_eff_by_scen_by_economy['Drive'].unique().tolist())
    return fig_dict, color_preparation_list