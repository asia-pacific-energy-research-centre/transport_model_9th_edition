#craete an assumptions dashboard in plotly which will display the most important data for the user to see. 
# To simplify things, we will keep this to road data only. Our non road dta is too reliant on intensity from egeda right now, which is probably wrong.
# The most important data will probably be: drive shares by transport type (2 graphs), eneryg use by vehicle type, fuel type (1 line graph), freight tone km by drive, passenger km by drive, activity growth?

#PLEASE NOTE THAT THIS NEEDS TO BE RUN AFTER THE all_economy_graphs.py and create_sales_share_data.py scripts, as that script creates the data that this script uses to create the dashboard
#%%
#%%
#set working directory as one folder back so that config works
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
import assumptions_dashboard_plotting_scripts
DROP_NON_ROAD_TRANSPORT = False
SALES_SHARE_PLOT_TYPE ='share_of_vehicle_type'
#%%
#load in concordances
#import measure to unit concordance
measure_to_unit_concordance = pd.read_csv('config/concordances_and_config_data/measure_to_unit_concordance.csv')
#convert to dict
measure_to_unit_concordance_dict = measure_to_unit_concordance.set_index('Measure')['Magnitude_adjusted_unit'].to_dict()#use this to convert measures to units eg measure_to_unit_concordance_dict[y_column]

#load in measures concodrdance 
model_concordances = pd.read_csv('config/concordances_and_config_data/computer_generated_concordances/{}'.format(model_concordances_file_name))
#extract economy and scenario from df then drop dupes
economy_scenario_concordance = model_concordances[['Economy', 'Scenario']].drop_duplicates().reset_index(drop=True)
#%%
#print every unique name/labels used in the plots and match it to a color. the colors will be themed so that things like electricity and bev's are always the same color
#following done with this chatgpt:https://chat.openai.com/share/d39fec42-e2b2-497a-8826-30a59bd09940
colors_dict = {
    # Electric vehicles and related items (green shades)
    'bev': '#008000',  # green
    'bev 2w': '#006400',  # darkgreen
    'bev lpv': '#32CD32',  # limegreen
    'bev lcv': '#32CD32',  # limegreen
    'bev bus': '#7CFC00',  # lawngreen
    'bev trucks': '#66CDAA',  # mediumaquamarine
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
    'fcev trucks': '#EE82EE',  # violet
    'fcev bus': '#DA70D6',  # orchid
    'fcev lpv': '#9932CC',  # darkorchid
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

    # Other categories
    'Population_index': '#808080',  # grey
    'passenger_km_index': '#FF0000',  # red
    'Gdp_index': '#A9A9A9',  # darkgray
    'Activity_8th_index': '#D3D3D3',  # lightgray
    'freight_tonne_km_index': '#0000FF',  # blue
    '2w': '#FF0000',  # red
    'lpv': '#FF0000',  # red
    'lcv': '#0000FF',  # blue
    'trucks': '#0000FF',  # blue
    'bus': '#FF0000',  # red
    'phev': '#FFFF00',  # yellow
}


plots = ['energy_use_by_fuel_type','passenger_km_by_drive', 'freight_tonne_km_by_drive',  'vehicle_type_stocks',
'drive_share_passenger', 'drive_share_freight', 'activity_indexed','fuel_mixing', 'charging']#activity_growth
####################################


def prepare_fig_dict(plots,ECONOMIES_TO_PLOT_FOR,economy_scenario_concordance):

    #fig dict will have the following structure:
    #economy > scenario > plots
    #so you can iterate through each economy, scenaio and plot the dashboard for the plots ordered as is in the list in the dict.
    #so in the end there will be a dashboard for every scenario and economy, with the plots in the order specified in the plots list
    fig_dict= {}
    for economy in economy_scenario_concordance['Economy'].unique():
        if economy in ECONOMIES_TO_PLOT_FOR:
            
            #create economy folder in plotting_output/dashboards too
            if not os.path.exists('plotting_output/dashboards/{}'.format(economy)):
                os.makedirs('plotting_output/dashboards/{}'.format(economy))

            fig_dict[economy] = {}
            for scenario in economy_scenario_concordance['Scenario'].unique():
                fig_dict[economy][scenario] = {}
                for plot in plots:
                    fig_dict[economy][scenario][plot] = None
    return fig_dict
#%%
def create_dashboard(plots,ECONOMIES_TO_PLOT_FOR, SALES_SHARE_PLOT_TYPE,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, colors_dict):
    
    color_preparation_list = []
    fig_dict = prepare_fig_dict(plots,ECONOMIES_TO_PLOT_FOR,economy_scenario_concordance)
    #get the plots:
    #create sales share plots
    fig_dict, color_preparation_list = create_sales_share_plots(fig_dict, SALES_SHARE_PLOT_TYPE,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    #create energy use by fuel type plots
    fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.energy_use_by_fuel_type(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    #create freight tonne km by drive plots
    fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.freight_tonne_km_by_drive(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    #create passenger km by drive plots
    fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.passenger_km_by_drive(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    #create activity growth plots
    # fig_dict, color_preparation_list = activity_growth(fig_dict)
    
    fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.activity_indexed(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    #insertt fuel mixing plots
    fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_supply_side_fuel_mixing(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    #charging:
    fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.create_charging_plot(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    #vehicle_type_stocks
    fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.create_vehicle_type_stocks_plot(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    
    check_colors_in_color_preparation_list(color_preparation_list, colors_dict)
    #now create the dashboards:
    for economy in fig_dict.keys():
        for scenario in fig_dict[economy].keys():
                rows = int(np.ceil(np.sqrt(len(fig_dict[economy][scenario].keys()))))
                cols = int(np.ceil(len(fig_dict[economy][scenario].keys())/rows))
                
                #extract titles:
                titles= []
                for plot in fig_dict[economy][scenario].keys():
                    titles.append(fig_dict[economy][scenario][plot][1])
                fig  = make_subplots(
                    rows=rows, cols=cols,
                    #specs types will all be xy
                    specs=[[{"type": "xy"} for col in range(cols)] for row in range(rows)],
                    subplot_titles=titles
                
                )
                for i, plot in enumerate(fig_dict[economy][scenario].keys()):
                    row = int(i/cols)+1
                    col = i%cols+1
                    breakpoint()
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
                        if (trace.name in names) else names.add(trace.name))

                fig.update_layout(title_text=f"Dashboard for {economy} {scenario}")
                pio.write_html(fig, 'plotting_output/dashboards/{}/{}_assumptions_dashboard.html'.format(economy, scenario))
    
    return fig_dict

#%%
def create_sales_share_plots(fig_dict, SALES_SHARE_PLOT_TYPE,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict):
    if SALES_SHARE_PLOT_TYPE == 'share_of_transport_type':
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_share_of_transport_type(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    elif SALES_SHARE_PLOT_TYPE == 'share_of_vehicle_type':
        
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.plot_share_of_vehicle_type(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    elif SALES_SHARE_PLOT_TYPE == 'sum_of_vehicle_types_by_transport_type':
        fig_dict, color_preparation_list = assumptions_dashboard_plotting_scripts.share_of_sum_of_vehicle_types_by_transport_type(fig_dict,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance, color_preparation_list, colors_dict)
    return fig_dict,color_preparation_list


def check_colors_in_color_preparation_list(color_preparation_list, colors_dict):
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
    
#%%
create_dashboard(plots,ECONOMIES_TO_PLOT_FOR, SALES_SHARE_PLOT_TYPE,DROP_NON_ROAD_TRANSPORT, measure_to_unit_concordance_dict,economy_scenario_concordance,colors_dict)
#%%