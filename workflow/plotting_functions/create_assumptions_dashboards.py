#%%
#craete an assumptions dashboard in plotly which will display the most important data for the user to see. 
# To simplify things, we will keep this to road data only. Our non road dta is too reliant on intensity from egeda right now, which is probably wrong.
# The most important data will probably be: drive shares by transport type (2 graphs), eneryg use by vehicle type, fuel type (1 line graph), freight tone km by drive, passenger km by drive, activity growth?

#PLEASE NOTE THAT THIS NEEDS TO BE RUN AFTER THE all_economy_graphs.py and create_sales_share_data.py scripts, as that script creates the data that this script uses to create the dashboard

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

import assumptions_dashboard_plotting_scripts
DROP_NON_ROAD_TRANSPORT = False

#print every unique name/labels used in the plots and match it to a color. the colors will be themed so that things like electricity and bev's are always the same color
#following done with this chatgpt:https://chat.openai.com/share/d39fec42-e2b2-497a-8826-30a59bd09940
colors_dict = {
    # Electric vehicles and related items (green shades)
    'bev': '#008000',  # green
    #passenger types
    'bev 2w': '#006400',  # darkgreen
    'bev lpv': '#228B22',  # forestgreen
    'bev bus': '#7CFC00',  # lawngreen

    #freight types
    'bev lcv': '#3CB371',  # mediumseagreen
    'bev trucks': '#20B2AA',  # lightseagreen
    
    #other:
    '17_electricity': '#008000',  # green
    
    'sum_of_fast_chargers_needed': '#3CB371',  # mediumseagreen
    'sum_of_slow_chargers_needed': '#66CDAA',  # mediumaquamarine

    # Gas vehicles (blue shades)
    'gas': '#0000FF',  # blue
    '07_09_lpg': '#1E90FF',  # dodgerblue
    '08_01_natural_gas': '#00008B',  # darkblue

    # Oil vehicles and related items (red shades)
    'ice': '#FF0000',  # red
    'ice_d': '#B22222',  # firebrick
    'ice_g': '#CD5C5C',  # indianred
    
    '07_01_motor_gasoline': '#B22222',  # firebrick
    '07_07_gas_diesel_oil': '#CD5C5C',  # indianred

    # Fuel cell vehicles and related items (purple shades)
    'fcev': '#800080',  # purple
    #passenger types
    'fcev bus': '#DA70D6',  # orchid
    'fcev lpv': '#9932CC',  # darkorchid
    #fregith types
    'fcev trucks': '#EE82EE',  # violet
    'fcev lcv': '#9400D3',  # darkviolet
    
    '16_x_hydrogen': '#BA55D3',  # mediumorchid

    # Biofuels (orange shades)
    '16_06_biodiesel': '#FFFF00',  # yellow
    '16_05_biogasoline': '#FFAA00',  # darkyellow

    '16_07_bio_jet_kerosene': '#40E0D0',  # turquoise

    # Unique fuel types, non-road vehicles and related items (cyan shades)
    '01_x_coal_thermal': '#00FFFF',  # cyan
    '07_08_fuel_oil': '#20B2AA',  # lightseagreen
    '07_02_aviation_gasoline': '#48D1CC',  # mediumturquoise
    'non-road': '#40E0D0',  # turquoise
    '07_x_jet_fuel': '#00CED1',  # darkturquoise
    '07_x_other_petroleum_products': '#00FFFF',  # cyan 

    # Other categories
    'Population_index': '#808080',  # grey
    'passenger_km_index': '#FF0000',  # red
    'Gdp_index': '#A9A9A9',  # darkgray
    'Activity_8th_index': '#D3D3D3',  # lightgray
    'freight_tonne_km_index': '#0000FF',  # blue
    #passenger types
    '2w': '#FF0000',  # red
    'lpv': '#FFA500',  # orange
    'bus': '#FFFF00',  # yellow

    #freight types
    'lcv': '#0000FF',  # blue
    'trucks': '#000000',  # black
    'phev': '#FFFF00',  # yellow
}

def prepare_fig_dict_and_subfolders(ECONOMY_IDs, plots, ADVANCE_BASE_YEAR):
    """
    Prepares a dictionary of figures and creates subfolders for each economy.

    Args:
        ECONOMY_IDs (list): A list of economy IDs for which the figures are being created.
        plots (list): A list of plot names to include in the figures.
        ADVANCE_BASE_YEAR (int): The base year for the data being displayed in the figures.

    Returns:
        fig_dict (dict): A dictionary of figures, with keys corresponding to the economy IDs.
    """

    #fig dict will have the following structure:
    #economy > scenario > plots
    #so you can iterate through each economy, scenaio and plot the dashboard for the plots ordered as is in the list in the dict.
    #so in the end there will be a dashboard for every scenario and economy, with the plots in the order specified in the plots list
    fig_dict= {}
    for economy in config.economy_scenario_concordance['Economy'].unique():
        if economy in ECONOMY_IDs:
            
            if not ADVANCE_BASE_YEAR and not os.path.exists('plotting_output/dashboards/{}/{}'.format(economy,config.OUTLOOK_BASE_YEAR)):#put plots in a subfolder if we are projecting to the outlook base year
                os.makedirs('plotting_output/dashboards/{}/{}'.format(economy,config.OUTLOOK_BASE_YEAR))
            #create economy folder in plotting_output/dashboards too
            elif ADVANCE_BASE_YEAR and not os.path.exists('plotting_output/dashboards/{}'.format(economy)):
                os.makedirs('plotting_output/dashboards/{}'.format(economy))

            fig_dict[economy] = {}
            for scenario in config.economy_scenario_concordance['Scenario'].unique():
                fig_dict[economy][scenario] = {}
                for plot in plots:
                    fig_dict[economy][scenario][plot] = None
    return fig_dict

def create_dashboard(ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id, hidden_legend_names, ADVANCE_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS):
    """
    Creates an assumptions dashboard for the specified economies and plots.

    Args:
        ECONOMY_IDs (list): A list of economy IDs for which the dashboard is being created.
        plots (list): A list of plot names to include in the dashboard.
        DROP_NON_ROAD_TRANSPORT (bool): Whether to drop non-road transport data from the dashboard.
        colors_dict (dict): A dictionary of colors to use for the dashboard.
        dashboard_name_id (str): The name or ID of the dashboard being created.
        hidden_legend_names (list): A list of legend names to hide in the dashboard.
        ADVANCE_BASE_YEAR (int): The base year for the data being displayed in the dashboard.
        ARCHIVE_PREVIOUS_DASHBOARDS (bool): Whether to archive previous dashboards before saving a new one.

    Returns:
        None
    """
    
    color_preparation_list = []
    fig_dict = prepare_fig_dict_and_subfolders(ECONOMY_IDs, plots,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR)
    
    #get the plots:
    fig_dict, color_preparation_list = plotting_handler(ECONOMY_IDs, plots, fig_dict,  color_preparation_list, colors_dict, DROP_NON_ROAD_TRANSPORT,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR)
            
    check_colors_in_color_preparation_list(color_preparation_list, colors_dict)
    
    #now create the dashboards:
    for economy in fig_dict.keys():
        for scenario in fig_dict[economy].keys():
                rows = int(np.ceil(np.sqrt(len(fig_dict[economy][scenario].keys()))))
                cols = int(np.ceil(len(fig_dict[economy][scenario].keys())/rows))
                
                #extract titles:
                titles= []
                for plot in fig_dict[economy][scenario].keys():
                    try:
                        titles.append(fig_dict[economy][scenario][plot][1])
                    except:
                        raise ValueError(f'No title found for {plot}')
                fig  = make_subplots(
                    rows=rows, cols=cols,
                    #specs types will all be xy
                    specs=[[{"type": "xy"} for col in range(cols)] for row in range(rows)],
                    subplot_titles=titles
                
                )
                for i, plot in enumerate(fig_dict[economy][scenario].keys()):
                    row = int(i/cols)+1
                    col = i%cols+1
                    #add the traceas for entire fig_i to the fig. This is because we are suing plotly express which returns a fig with multiple traces, however, plotly subplots only accepts one trace per subplot
                    for trace in fig_dict[economy][scenario][plot][0]['data']:
                        #we need to change the line_dash in the sales shares data and this is the only way i could find how:
                        fig.add_trace(trace, row=row, col=col) 
                    # fig.update_layout(fig_dict[economy][scenario][plot]['layout'])
                    # fig.add_trace(fig_dict[economy][scenario][plot], row=row, col=col)
                    # fig.update_layout(fig_dict[economy][scenario][plot]['layout'])#dont know why copliot rec'd this. could be sueful
                    #this is a great function to remove duplicate legend items
                
                names = set()
                fig.for_each_trace(
                    lambda trace:
                        trace.update(showlegend=False)
                        if (trace.name in hidden_legend_names or trace.name in names)
                        else names.add(trace.name))

                fig.update_layout(title_text=f"Dashboard for {economy} {scenario} - {dashboard_name_id}")
                if ADVANCE_BASE_YEAR:
                    if ARCHIVE_PREVIOUS_DASHBOARDS:
                        archive_previous_dashboards_before_saving(economy, scenario, dashboard_name_id,config.GRAPHING_END_YEAR)
                    pio.write_html(fig, 'plotting_output/dashboards/{}/{}_{}_dashboard_{}.html'.format(economy, economy, scenario,dashboard_name_id))
                else:
                    if ARCHIVE_PREVIOUS_DASHBOARDS:
                        archive_previous_dashboards_before_saving(economy, scenario,dashboard_name_id, config.OUTLOOK_BASE_YEAR)
                    pio.write_html(fig, 'plotting_output/dashboards/{}/{}/{}_{}_dashboard_{}.html'.format(economy,config.OUTLOOK_BASE_YEAR,economy,  scenario,dashboard_name_id))
    
    return fig_dict


def archive_previous_dashboards_before_saving(economy, scenario, dashboard_name_id, end_year):
    """
    Archives the previous dashboards before saving a new one.

    Args:
        economy (str): The economy for which the dashboard is being created.
        scenario (str): The scenario for which the dashboard is being created.
        dashboard_name_id (str): The name or ID of the dashboard being created.
        end_year (int): The end year of the data being displayed in the dashboard.

    Returns:
        None
    """
    if end_year == config.GRAPHING_END_YEAR:
        #archive previous dashboards:
        if os.path.exists('plotting_output/dashboards/{}/{}_{}_dashboard_{}.html'.format(economy,economy,  scenario,dashboard_name_id)):
            #create dir:
            if not os.path.exists('plotting_output/dashboards/archive/{}/{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy)):
                os.makedirs('plotting_output/dashboards/archive/{}/{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy))
            shutil.move('plotting_output/dashboards/{}/{}_{}_dashboard_{}.html'.format(economy,economy,  scenario,dashboard_name_id), 'plotting_output/dashboards/archive/{}/{}/{}_{}_{}_dashboard_{}.html'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy,config.GRAPHING_END_YEAR, economy, scenario,dashboard_name_id))    
                
    elif end_year == config.OUTLOOK_BASE_YEAR:
        if os.path.exists('plotting_output/dashboards/{}/{}/{}_{}_dashboard_{}.html'.format(economy,config.OUTLOOK_BASE_YEAR,economy,  scenario,dashboard_name_id)):
            #create dir:
            if not os.path.exists('plotting_output/dashboards/archive/{}/{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy)):
                os.makedirs('plotting_output/dashboards/archive/{}/{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy))
            shutil.move('plotting_output/dashboards/{}/{}/{}_{}_dashboard_{}.html'.format(economy,config.OUTLOOK_BASE_YEAR, economy, scenario,dashboard_name_id), 'plotting_output/dashboards/archive/{}/{}/{}_{}_{}_dashboard_{}.html'.format(datetime.datetime.now().strftime("%Y%m%d_%H"), economy,config.OUTLOOK_BASE_YEAR, economy, scenario,dashboard_name_id))
            
            
def load_and_format_input_data(ADVANCE_BASE_YEAR, ECONOMY_IDs):
    """
    Loads and formats the input data for the specified economies.

    Args:
        ADVANCE_BASE_YEAR (int): The base year for the data being displayed in the dashboard.
        ECONOMY_IDs (list): A list of economy IDs for which the input data is being loaded.

    Returns:
        model_output_detailed (pandas.DataFrame): A dataframe containing the detailed model output data for the specified economies.
        measure_to_unit_concordance_dict (dict): A dictionary mapping measure names to unit names.
        economy_scenario_concordance (pandas.DataFrame): A dataframe containing the concordance between economy IDs and scenario names.
    """
    #LAOD IN REQURIED DATA FOR PLOTTING EVERYTHING:
    model_output_detailed = pd.DataFrame()
    model_output_with_fuels = pd.DataFrame()
    chargers = pd.DataFrame()
    supply_side_fuel_mixing = pd.DataFrame()
    road_model_input = pd.DataFrame()
    model_output_detailed_detailed_non_road_drives = pd.DataFrame()
    growth_forecasts = pd.DataFrame() 
    first_road_model_run_data = pd.DataFrame()
    for economy in ECONOMY_IDs:
        model_output_detailed_ = pd.read_csv('output_data/model_output_detailed/{}_{}'.format(economy, config.model_output_file_name))
        model_output_with_fuels_ = pd.read_csv('output_data/model_output_with_fuels/{}_{}'.format(economy, config.model_output_file_name))
        chargers_ = pd.read_csv('output_data/for_other_modellers/{}_estimated_number_of_chargers.csv'.format(economy))
        supply_side_fuel_mixing_ = pd.read_csv('intermediate_data/model_inputs/{}/{}_supply_side_fuel_mixing.csv'.format(config.FILE_DATE_ID, economy))
        road_model_input_ = pd.read_csv('intermediate_data/model_inputs/{}/{}_road_model_input_wide.csv'.format(config.FILE_DATE_ID, economy))
        model_output_detailed_detailed_non_road_drives_ = pd.read_csv('output_data/model_output_detailed/{}_NON_ROAD_DETAILED_{}'.format(economy, config.model_output_file_name))
        growth_forecasts_ = pd.read_csv(f'intermediate_data/model_inputs/{config.FILE_DATE_ID}/{economy}_growth_forecasts_wide.csv')
        first_road_model_run_data_ = pd.read_csv('intermediate_data/road_model/first_run_{}_{}'.format(economy, config.model_output_file_name))
        
        model_output_detailed = pd.concat([model_output_detailed, model_output_detailed_])
        model_output_with_fuels = pd.concat([model_output_with_fuels, model_output_with_fuels_])
        chargers = pd.concat([chargers, chargers_])
        supply_side_fuel_mixing = pd.concat([supply_side_fuel_mixing, supply_side_fuel_mixing_])    
        road_model_input = pd.concat([road_model_input, road_model_input_])
        model_output_detailed_detailed_non_road_drives = pd.concat([model_output_detailed_detailed_non_road_drives, model_output_detailed_detailed_non_road_drives_])
        growth_forecasts = pd.concat([growth_forecasts, growth_forecasts_])
        first_road_model_run_data = pd.concat([first_road_model_run_data, first_road_model_run_data_])
        
    
    original_model_output_8th = pd.read_csv('input_data/from_8th/reformatted/activity_energy_road_stocks.csv').rename(columns={'Year':'Date'})
    new_sales_shares_all_plot_drive_shares = pd.read_csv(f'input_data/user_input_spreadsheets/Vehicle_sales_share.csv')
    gompertz_parameters_df = pd.read_csv('intermediate_data/model_inputs/{}/stocks_per_capita_threshold.csv'.format(config.FILE_DATE_ID))
    emissions_factors = pd.read_csv('config/9th_edition_emissions_factors.csv')
    
    if ADVANCE_BASE_YEAR:
        def filter_between_outlook_BASE_YEAR_and_end_year(df):
            return df.loc[(df['Date']>=config.OUTLOOK_BASE_YEAR) & (df['Date']<=config.GRAPHING_END_YEAR)].copy()
        new_sales_shares_all_plot_drive_shares = filter_between_outlook_BASE_YEAR_and_end_year(new_sales_shares_all_plot_drive_shares)
        model_output_detailed = filter_between_outlook_BASE_YEAR_and_end_year(model_output_detailed)
        model_output_with_fuels = filter_between_outlook_BASE_YEAR_and_end_year(model_output_with_fuels)
        original_model_output_8th = filter_between_outlook_BASE_YEAR_and_end_year(original_model_output_8th)
        chargers = filter_between_outlook_BASE_YEAR_and_end_year(chargers)
        supply_side_fuel_mixing = filter_between_outlook_BASE_YEAR_and_end_year(supply_side_fuel_mixing)
        model_output_detailed_detailed_non_road_drives = filter_between_outlook_BASE_YEAR_and_end_year(model_output_detailed_detailed_non_road_drives)
        gompertz_parameters_df = filter_between_outlook_BASE_YEAR_and_end_year(gompertz_parameters_df)
        growth_forecasts = filter_between_outlook_BASE_YEAR_and_end_year(growth_forecasts)
        first_road_model_run_data = filter_between_outlook_BASE_YEAR_and_end_year(first_road_model_run_data)
        
    else:
        def filter_outlook_BASE_YEAR(df):
            return df.loc[df['Date']<=config.OUTLOOK_BASE_YEAR].copy()
        #filter all data so it is less than or equal to the outlook base year
        new_sales_shares_all_plot_drive_shares = filter_outlook_BASE_YEAR(new_sales_shares_all_plot_drive_shares)
        model_output_detailed = filter_outlook_BASE_YEAR(model_output_detailed)
        model_output_with_fuels = filter_outlook_BASE_YEAR(model_output_with_fuels)
        original_model_output_8th = filter_outlook_BASE_YEAR(original_model_output_8th)
        chargers = filter_outlook_BASE_YEAR(chargers)
        supply_side_fuel_mixing = filter_outlook_BASE_YEAR(supply_side_fuel_mixing)
        model_output_detailed_detailed_non_road_drives = filter_outlook_BASE_YEAR(model_output_detailed_detailed_non_road_drives)
        gompertz_parameters_df = filter_outlook_BASE_YEAR(gompertz_parameters_df)
        growth_forecasts = filter_outlook_BASE_YEAR(growth_forecasts)
        first_road_model_run_data = filter_outlook_BASE_YEAR(first_road_model_run_data)
    
    
    #Format stocks data specifically, since we use it a lot:    
    stocks = model_output_detailed.loc[(model_output_detailed['Medium']=='road')][config.INDEX_COLS_NO_MEASURE+['Stocks']].rename(columns={'Stocks':'Value'}).copy()
    # #filter for ECONOMY_IDs 
    # new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.loc[new_sales_shares_all_plot_drive_shares['Economy'].isin(ECONOMY_IDs)]
    # model_output_detailed = model_output_detailed.loc[model_ostocksutput_detailed['Economy'].isin(ECONOMY_IDs)]
    # model_output_with_fuels = model_output_with_fuels.loc[model_output_with_fuels['Economy'].isin(ECONOMY_IDs)]
    # original_model_output_8th = original_model_output_8th.loc[original_model_output_8th['Economy'].isin(ECONOMY_IDs)]
    # chargers = chargers.loc[chargers['Economy'].isin(ECONOMY_IDs)]
    # supply_side_fuel_mixing = supply_side_fuel_mixing.loc[supply_side_fuel_mixing['Economy'].isin(ECONOMY_IDs)]
    # stocks = stocks.loc[stocks['Economy'].isin(ECONOMY_IDs)] 
    
    return new_sales_shares_all_plot_drive_shares, model_output_detailed, model_output_detailed_detailed_non_road_drives, model_output_with_fuels, original_model_output_8th, chargers, supply_side_fuel_mixing, stocks, road_model_input, gompertz_parameters_df, growth_forecasts, emissions_factors, first_road_model_run_data

def plotting_handler(ECONOMY_IDs, plots, fig_dict, color_preparation_list, colors_dict, DROP_NON_ROAD_TRANSPORT, ADVANCE_BASE_YEAR):
    """
    Handles the creation of plots for the specified economies and plots.

    Args:
        ECONOMY_IDs (list): A list of economy IDs for which the plots are being created.
        plots (list): A list of plot names to include in the figures.
        fig_dict (dict): A dictionary of figures, with keys corresponding to the economy IDs.
        color_preparation_list (list): A list of colors to use for the plots.
        colors_dict (dict): A dictionary of colors to use for the dashboard.
        DROP_NON_ROAD_TRANSPORT (bool): Whether to drop non-road transport data from the plots.
        ADVANCE_BASE_YEAR (int): The base year for the data being displayed in the plots.

    Returns:
        None
    """
    
    new_sales_shares_all_plot_drive_shares, model_output_detailed, model_output_detailed_detailed_non_road_drives, model_output_with_fuels, original_model_output_8th, chargers, supply_side_fuel_mixing, stocks,road_model_input, gompertz_parameters_df, growth_forecasts, emissions_factors, first_road_model_run_data = load_and_format_input_data(ADVANCE_BASE_YEAR,ECONOMY_IDs)
    # Share of Transport Type
    share_transport_types = ['passenger', 'freight', 'all']
    for transport_type in share_transport_types:
        if f'share_of_transport_type_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_share_of_transport_type(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares,stocks,fig_dict, color_preparation_list, colors_dict,share_of_transport_type_type=transport_type)

    # Share of Vehicle Type by Transport Type
    share_vehicle_types = ['passenger', 'freight', 'all']
    for share_of_transport_type_type in share_vehicle_types:
        if f'share_of_vehicle_type_by_transport_type_{share_of_transport_type_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_share_of_vehicle_type_by_transport_type(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares,stocks,fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type)

    # Sum of Vehicle Types by Transport Type
    sum_vehicle_types = ['passenger', 'freight', 'all']
    for share_of_transport_type_type in sum_vehicle_types:
        if f'sum_of_vehicle_types_by_transport_type_{share_of_transport_type_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.share_of_sum_of_vehicle_types_by_transport_type(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares,stocks,fig_dict, color_preparation_list, colors_dict, share_of_transport_type_type)

    # Energy Use by Fuel Type
    energy_transport_types = [p.split('_')[-1] for p in plots if 'energy_use_by_fuel_type' in p]
    for transport_type in energy_transport_types:
        if f'energy_use_by_fuel_type_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.energy_use_by_fuel_type(ECONOMY_IDs,model_output_with_fuels,fig_dict,color_preparation_list, colors_dict,transport_type)
            
    #Non road energy Use by Fuel Type
    energy_transport_types = [p.split('_')[-1] for p in plots if 'non_road_energy_use_by_fuel_type' in p]
    for transport_type in energy_transport_types:
        if f'non_road_energy_use_by_fuel_type_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_non_road_energy_use(ECONOMY_IDs,model_output_with_fuels,fig_dict, color_preparation_list, colors_dict,transport_type)

    non_road_activity_types = [p.split('_')[-1] for p in plots if 'non_road_activity_by_drive' in p]
    for transport_type in non_road_activity_types:
        if f'non_road_activity_by_drive_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.non_road_activity_by_drive_type(ECONOMY_IDs,model_output_detailed_detailed_non_road_drives,fig_dict,color_preparation_list, colors_dict,transport_type)
        
    non_road_stocks_types = [p.split('_')[-1] for p in plots if 'non_road_stocks_by_drive' in p]
    for transport_type in non_road_stocks_types:
        if f'non_road_stocks_by_drive_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.non_road_stocks_by_drive_type(ECONOMY_IDs,model_output_detailed_detailed_non_road_drives, fig_dict,color_preparation_list, colors_dict,transport_type)
    
    # Emissions by Fuel Type
    emissions_transport_types = [p.split('_')[-1] for p in plots if 'emissions_by_fuel_type' in p]
    for transport_type in emissions_transport_types:
        if f'emissions_by_fuel_type_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.emissions_by_fuel_type(ECONOMY_IDs, emissions_factors, model_output_with_fuels, fig_dict, color_preparation_list, colors_dict,transport_type)    
    
    # turnover_rate_by_drive_type(fig_dict,DROP_NON_ROAD_TRANSPORT,  color_preparation_list, colors_dict,transport_type)
    turnover_rate_types = [p.split('_')[-1] for p in plots if 'turnover_rate_by_drive' in p]
    for transport_type in turnover_rate_types:
        if f'box_turnover_rate_by_drive_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.turnover_rate_by_drive_type_box(ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict,transport_type) 
                  
    
    turnover_rate_types = [p.split('_')[-1] for p in plots if 'turnover_rate_by_vtype' in p]
    for transport_type in turnover_rate_types:
        if f'line_turnover_rate_by_vtype_{transport_type}' in plots:
            fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.turnover_rate_by_vehicle_type_line(ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict,transport_type)       
        
    avg_age_types = [p for p in plots if 'avg_age' in p]
    for title in avg_age_types:
        #could be avg_age_nonroad, avg_age_road, avg_age_all
        medium = title.split('_')[-1]
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_average_age_by_simplified_drive_type(ECONOMY_IDs,model_output_detailed,fig_dict, color_preparation_list, colors_dict, medium, title)
        
    if 'freight_tonne_km_by_drive' in plots:
        #create freight tonne km by drive plots
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.freight_tonne_km_by_drive(ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT,color_preparation_list, colors_dict)
    if 'passenger_km_by_drive' in plots:
        #create passenger km by drive plots
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.passenger_km_by_drive(ECONOMY_IDs,model_output_detailed,fig_dict,DROP_NON_ROAD_TRANSPORT, color_preparation_list, colors_dict)
    if 'activity_and_macro_lines' in plots:
        #create activity growth plots
        # fig_dict, color_preparation_list = activity_growth(fig_dict)
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.activity_and_macro_lines(ECONOMY_IDs,original_model_output_8th,model_output_detailed, growth_forecasts, fig_dict, color_preparation_list, colors_dict, indexed=False)
    if 'fuel_mixing' in plots:
        #insertt fuel mixing plots
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_supply_side_fuel_mixing(ECONOMY_IDs,supply_side_fuel_mixing,fig_dict, color_preparation_list, colors_dict)
    if 'charging' in plots:
        #charging:
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.create_charging_plot(ECONOMY_IDs,chargers,fig_dict, color_preparation_list, colors_dict)
    if 'vehicle_type_stocks' in plots:
        #vehicle_type_stocks
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.create_vehicle_type_stocks_plot(ECONOMY_IDs,stocks,fig_dict, color_preparation_list, colors_dict)
    if 'lmdi_passenger' in plots:
        #LMDI
        fig_dict = assumptions_dashboard_plotting_scripts.prodcue_LMDI_mutliplicative_plot(ECONOMY_IDs,fig_dict,  colors_dict, transport_type = 'passenger')
    if 'lmdi_freight' in plots:
        #LMDI
        fig_dict = assumptions_dashboard_plotting_scripts.prodcue_LMDI_mutliplicative_plot(ECONOMY_IDs,fig_dict,  colors_dict, transport_type = 'freight')
    if 'stocks_per_capita' in plots:
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_stocks_per_capita(ECONOMY_IDs,gompertz_parameters_df,model_output_detailed, first_road_model_run_data, fig_dict, color_preparation_list, colors_dict)
    if 'non_road_share_of_transport_type' in plots:
        fig_dict,color_preparation_list = assumptions_dashboard_plotting_scripts.plot_share_of_transport_type_non_road(ECONOMY_IDs,new_sales_shares_all_plot_drive_shares,fig_dict, color_preparation_list, colors_dict)
        
    return fig_dict, color_preparation_list

def check_colors_in_color_preparation_list(color_preparation_list, colors_dict):
    """
    Checks that all colors in the color preparation list are present in the colors dictionary.

    Args:
        color_preparation_list (list): A list of colors to use for the plots.
        colors_dict (dict): A dictionary of colors to use for the dashboard.

    Raises:
        ValueError: If any color in the color preparation list is not present in the colors dictionary.

    Returns:
        None
    """
    #filter out duplicates and then check what values are not in the colors_dict (which is what we set the colors in the charts with). If colors are missing then just add them manually.
    flattened_list = [item for sublist in color_preparation_list for item in sublist]
    color_preparation_list = list(set(flattened_list))
    missing_colors = []
    for color in color_preparation_list:
        if color not in colors_dict.keys():
            missing_colors.append(color)
    if len(missing_colors)>0:
        print(f'The following colors are missing from the colors_dict: \n {missing_colors}')
    #save them to a csv so we can add them to the colors_dict later too
    pd.DataFrame(missing_colors).to_csv('plotting_output/dashboards/missing_colors.csv')
    

def dashboard_creation_handler(ADVANCE_BASE_YEAR, ECONOMY_ID=None, ARCHIVE_PREVIOUS_DASHBOARDS=True):
    """
    Handles the creation of assumptions dashboards for the specified economies.

    Args:
        ADVANCE_BASE_YEAR (int): The base year for the data being displayed in the dashboards.
        ECONOMY_ID (str or None): The ID of the economy for which the dashboard is being created. If None, dashboards are created for all economies.
        ARCHIVE_PREVIOUS_DASHBOARDS (bool): Whether to archive previous dashboards before saving a new one.

    Returns:
        None
    """
    
    if ECONOMY_ID == None:
        #fill with all economys
        ECONOMY_IDs = config.economy_scenario_concordance['Economy'].unique().tolist()
    else:
        ECONOMY_IDs = [ECONOMY_ID]
    #PLOT OPTIONS: 
    # share_of_transport_type_passenger
    # share_of_transport_type_freight
    # share_of_transport_type_all
    # share_of_vehicle_type_by_transport_type_passenger
    # share_of_vehicle_type_by_transport_type_freight
    # share_of_vehicle_type_by_transport_type_all
    # sum_of_vehicle_types_by_transport_type_passenger
    # sum_of_vehicle_types_by_transport_type_freight
    # sum_of_vehicle_types_by_transport_type_all
    # energy_use_by_fuel_type
    # freight_tonne_km_by_drive
    # passenger_km_by_drive
    # activity_and_macro_lines
    # fuel_mixing
    # charging
    # vehicle_type_stocks
    # lmdi
    # avg_age
    # stocks_per_capita
    # non_road_activity_by_drive_{transport_type}
    # non_road_energy_use_by_fuel_type_{transport_type}
    # non_road_stocks_by_drive_{transport_type}
    # box_turnover_rate_by_drive_{transport_type}
    # avg_age_nonroad, avg_age_road, avg_age_all
    # line_turnover_rate_by_vtype_all
    # line_turnover_rate_by_vtype_freight
    # line_turnover_rate_by_vtype_passenger
    # emissions_by_fuel_type_{transport_type}
    #####################################'
    hidden_legend_names =  ['bev lcv, stocks', 'bev trucks, stocks', 'fcev trucks, stocks', 'bev 2w, stocks', 'bev bus, stocks', 'fcev bus, stocks', 'bev lpv, stocks', 'fcev lpv, stocks', 'fcev lcv, stocks']
    
    plots = ['stocks_per_capita', 'avg_age_all']


    create_dashboard(ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'development',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
    
    #THAILAND DASHBOARD:
    plots = ['energy_use_by_fuel_type_all','energy_use_by_fuel_type_freight','energy_use_by_fuel_type_passenger','fuel_mixing', 'freight_tonne_km_by_drive','passenger_km_by_drive',  'activity_and_macro_lines', 'non_road_activity_by_drive_freight', 'non_road_activity_by_drive_passenger','vehicle_type_stocks', 'share_of_vehicle_type_by_transport_type_all','sum_of_vehicle_types_by_transport_type_all']#, 'charging'#activity_growth# 'charging',
    create_dashboard(ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'detailed',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
    

    #create a presentation dashboard:

    plots = ['energy_use_by_fuel_type_all','passenger_km_by_drive', 'freight_tonne_km_by_drive', 'share_of_transport_type_passenger']#activity_growth

    create_dashboard(ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'presentation',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)


    #create a development dashboard:

    plots = ['energy_use_by_fuel_type_all','energy_use_by_fuel_type_freight','energy_use_by_fuel_type_passenger','fuel_mixing', 'freight_tonne_km_by_drive','passenger_km_by_drive',  'activity_and_macro_lines', 'vehicle_type_stocks', 'share_of_vehicle_type_by_transport_type_all','sum_of_vehicle_types_by_transport_type_all','share_of_transport_type_all',  'lmdi_freight', 'lmdi_passenger','stocks_per_capita', 'box_turnover_rate_by_drive_all','emissions_by_fuel_type_all']#, 'charging']#activity_growth# 'charging',

    create_dashboard(ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'development',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)


    #checkout turnover rate and average age related data:
    plots = ['avg_age_road','avg_age_nonroad','box_turnover_rate_by_drive_all','line_turnover_rate_by_vtype_all' ]#, 'charging']#activity_growth# 'charging',
    create_dashboard(ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'turnover_rate',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
    
    
    
    #Create assumptions/major inputs dashboard to go along side a results dashboard:
    plots = ['energy_use_by_fuel_type_all','activity_and_macro_lines','stocks_per_capita','share_of_vehicle_type_by_transport_type_all','sum_of_vehicle_types_by_transport_type_all','non_road_share_of_transport_type', 'fuel_mixing','avg_age_road','line_turnover_rate_by_vtype_all']#, 'charging']#activity_growth# 'charging',
    create_dashboard(ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'assumptions',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
    
    
    #Create a results dashboard:
    plots = ['energy_use_by_fuel_type_all','emissions_by_fuel_type_all',  'vehicle_type_stocks','non_road_energy_use_by_fuel_type_all','passenger_km_by_drive', 'freight_tonne_km_by_drive','charging', 'lmdi_freight', 'lmdi_passenger']#, 'charging']#activity_growth# 'charging',
    create_dashboard(ECONOMY_IDs, plots, DROP_NON_ROAD_TRANSPORT, colors_dict, dashboard_name_id = 'results',hidden_legend_names = hidden_legend_names,ADVANCE_BASE_YEAR=ADVANCE_BASE_YEAR, ARCHIVE_PREVIOUS_DASHBOARDS=ARCHIVE_PREVIOUS_DASHBOARDS)
    
     

#%%
# dashboard_creation_handler(True,'19_THA', ARCHIVE_PREVIOUS_DASHBOARDS=True)
#%%