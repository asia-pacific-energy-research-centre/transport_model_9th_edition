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

DROP_NON_ROAD_TRANSPORT = True
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
####################################
# def dashboard_handler
fig_dict = {}
#fig dict will have the following structure:
#economy > scenario > plots
#so you can iterate through each economy, scenaio and plot the dashboard for the plots ordered as is in the list in the dict.
plots = ['passenger_km_by_drive', 'freight_tonne_km_by_drive',  'activity_growth','energy_use_by_fuel_type',
'drive_share_passenger', 'drive_share_freight']
#so in the end there will be a dashboard for every scenario and economy, with the plots in the order specified in the plots list
for economy in economy_scenario_concordance['Economy'].unique():
    if economy in economies_to_plot_for:
        
        #create economy folder in plotting_output/dashboards too
        if not os.path.exists('plotting_output/dashboards/{}'.format(economy)):
            os.makedirs('plotting_output/dashboards/{}'.format(economy))

        fig_dict[economy] = {}
        for scenario in economy_scenario_concordance['Scenario'].unique():
            fig_dict[economy][scenario] = {}
            for plot in plots:
                fig_dict[economy][scenario][plot] = None
#%%
def create_dashboard(fig_dict):
    #get the plots:
    #create sales share plots
    fig_dict = create_sales_share_plots(fig_dict)
    #create energy use by fuel type plots
    fig_dict = energy_use_by_fuel_type(fig_dict)
    #create freight tonne km by drive plots
    fig_dict = freight_tonne_km_by_drive(fig_dict)
    #create passenger km by drive plots
    fig_dict = passenger_km_by_drive(fig_dict)
    #create activity growth plots
    fig_dict = activity_growth(fig_dict)

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
                    
                    #add the traceas for entire fig_i to the fig. This is because we are suing plotly express which returns a fig with multiple traces, however, plotly subplots only accepts one trace per subplot
                    for trace in fig_dict[economy][scenario][plot][0]['data']:
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
def create_sales_share_plots(fig_dict):
    new_sales_shares_all_plot_drive_shares = pd.read_csv(f'input_data/user_input_spreadsheets/Vehicle_sales_share.csv')
    #sum up all the sales shares for each drive type (so drop vehicle type
    new_sales_shares_all_plot_drive_shares = new_sales_shares_all_plot_drive_shares.drop(columns=['Vehicle Type']).groupby(['Scenario', 'Economy', 'Date', 'Transport Type', 'Drive']).sum().reset_index()
    for scenario in new_sales_shares_all_plot_drive_shares['Scenario'].unique():
        for economy in economies_to_plot_for:
            
            plot_data = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario) & (new_sales_shares_all_plot_drive_shares['Economy']==economy)].copy()

            #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. 
            plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060] else 0, axis=1)
            #drop all drives except phev, bev and fcev
            plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='phev') | (plot_data['Drive']=='fcev')].copy()

            #############
            #now plot
            
            title = f'Average sales shares for passenger vehicles'

            fig = px.bar(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Value', color='Drive', title=title)
            
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['drive_share_passenger'] = [fig,title]
            
            #############
            
            title = f'Average sales shares for freight vehicles'

            fig = px.bar(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Value', color='Drive', title=title)
            
            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['drive_share_freight'] = [fig,title]
            #############
    return fig_dict

def energy_use_by_fuel_type(fig_dict):
    #load in data and recreate plot, as created in all_economy_graphs

    #loop through scenarios and grab the data for each scenario:
    for scenario in economy_scenario_concordance['Scenario'].unique():
        # pkl : plotting_output\all_economy_graphs\_20230614\model_output_with_fuels.pkl
        model_output_with_fuels = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_with_fuels.pkl')
        if DROP_NON_ROAD_TRANSPORT:
            model_output_with_fuels = model_output_with_fuels.loc[model_output_with_fuels['Medium']=='road'].copy()
        #create a new df with only the data we need: 
        energy_use_by_fuel_type = model_output_with_fuels.copy()
        energy_use_by_fuel_type= energy_use_by_fuel_type[['Economy', 'Scenario', 'Date', 'Fuel', 'Energy']].groupby(['Economy', 'Scenario', 'Date', 'Fuel']).sum().reset_index()
        
        #add units (by setting measure to Energy haha)
        energy_use_by_fuel_type['Measure'] = 'Energy'
        #add units
        energy_use_by_fuel_type['Unit'] = energy_use_by_fuel_type['Measure'].map(measure_to_unit_concordance_dict)

        for economy in economies_to_plot_for:
            #filter to economy
            energy_use_by_fuel_type_economy = energy_use_by_fuel_type.loc[energy_use_by_fuel_type['Economy']==economy].copy()
            #sort by date
            # energy_use_by_fuel_type_economy = energy_use_by_fuel_type_economy.sort_values(by='Date')
            #now plot
            fig = px.line(energy_use_by_fuel_type_economy, x='Date', y='Energy', color='Fuel', title='Energy Use by Fuel Type')
            #add units to y col
            title_text = 'Energy Use by Fuel Type ({})'.format(energy_use_by_fuel_type_economy['Unit'].unique()[0])
            # fig.update_yaxes(title_text='Energy ({})'.format(energy_use_by_fuel_type_economy['Unit'].unique()[0]))

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['energy_use_by_fuel_type'] = [fig, title_text]
    return fig_dict

def freight_tonne_km_by_drive(fig_dict):
    # model_output_detailed.pkl
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in economy_scenario_concordance['Scenario'].unique():
        model_output_detailed = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        
        if DROP_NON_ROAD_TRANSPORT:
            model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']=='road'].copy()
        #create a new df with only the data we need:
        freight_tonne_km_by_drive = model_output_detailed.copy()
        freight_tonne_km_by_drive = freight_tonne_km_by_drive[['Economy', 'Scenario', 'Date', 'Drive', 'freight_tonne_km']].groupby(['Economy', 'Scenario', 'Date', 'Drive']).sum().reset_index()

        #add units (by setting measure to Freight_tonne_km haha)
        freight_tonne_km_by_drive['Measure'] = 'Freight_tonne_km'
        #add units
        freight_tonne_km_by_drive['Unit'] = freight_tonne_km_by_drive['Measure'].map(measure_to_unit_concordance_dict)

        for economy in economies_to_plot_for:
            #filter to economy
            freight_tonne_km_by_drive_economy = freight_tonne_km_by_drive.loc[freight_tonne_km_by_drive['Economy']==economy].copy()
            
            #sort by date
            # freight_tonne_km_by_drive_economy = freight_tonne_km_by_drive_economy.sort_values(by='Date')
            #now plot
            fig = px.line(freight_tonne_km_by_drive_economy, x='Date', y='freight_tonne_km', color='Drive')#, title='Freight Tonne Km by Drive Type')
            title_text = 'Freight Tonne Km by Drive Type ({})'.format(freight_tonne_km_by_drive_economy['Unit'].unique()[0])
            #add units to y col
            # fig.update_yaxes(title_text='Freight Tonne Km ({})'.format(freight_tonne_km_by_drive_economy['Unit'].unique()[0]))

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['freight_tonne_km_by_drive'] = [fig, title_text]
    return fig_dict

def passenger_km_by_drive(fig_dict):
    # model_output_detailed.pkl
    
    #loop through scenarios and grab the data for each scenario:
    for scenario in economy_scenario_concordance['Scenario'].unique():
        model_output_detailed = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        
        if DROP_NON_ROAD_TRANSPORT:
            model_output_detailed = model_output_detailed.loc[model_output_detailed['Medium']=='road'].copy()
        #create a new df with only the data we need:
        passenger_km_by_drive = model_output_detailed.copy()
        passenger_km_by_drive = passenger_km_by_drive[['Economy', 'Scenario', 'Date', 'Drive', 'passenger_km']].groupby(['Economy', 'Scenario', 'Date', 'Drive']).sum().reset_index()

        #add units (by setting measure to Freight_tonne_km haha)
        passenger_km_by_drive['Measure'] = 'Passenger_km'
        #add units
        passenger_km_by_drive['Unit'] = passenger_km_by_drive['Measure'].map(measure_to_unit_concordance_dict)

        for economy in economies_to_plot_for:
            #filter to economy
            passenger_km_by_drive_economy = passenger_km_by_drive.loc[passenger_km_by_drive['Economy']==economy].copy()
            
            #sort by date
            # passenger_km_by_drive_economy = passenger_km_by_drive_economy.sort_values(by='Date')
            #now plot
            fig = px.line(passenger_km_by_drive_economy, x='Date', y='passenger_km', color='Drive')#, title='Passenger Km by Drive Type')
            #add units to y col
            title_text = 'Passenger Km by Drive Type ({})'.format(passenger_km_by_drive_economy['Unit'].unique()[0])
            # fig.update_yaxes(title_text='Passenger Km ({})'.format(passenger_km_by_drive_economy['Unit'].unique()[0]))

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['passenger_km_by_drive'] = [fig,title_text]
    return fig_dict


def activity_growth(fig_dict):
    # model_output_detailed.pkl
    breakpoint()
    #loop through scenarios and grab the data for each scenario:
    for scenario in economy_scenario_concordance['Scenario'].unique():
        model_output_detailed = pd.read_pickle(f'plotting_output/all_economy_graphs/{FILE_DATE_ID}/{scenario}/model_output_detailed.pkl')
        #create a new df with only the data we need:
        activity_growth = model_output_detailed.copy()
        activity_growth = activity_growth[['Economy', 'Scenario', 'Date', 'Transport Type', 'Activity_growth']].drop_duplicates()
        #add units (by setting measure to Freight_tonne_km haha)
        activity_growth['Measure'] = 'Activity_growth'
        #add units
        activity_growth['Unit'] = activity_growth['Measure'].map(measure_to_unit_concordance_dict)
        for economy in economies_to_plot_for:
            #filter to economy
            activity_growth_economy = activity_growth.loc[activity_growth['Economy']==economy].copy()

            #now plot
            fig = px.line(activity_growth_economy, x='Date', y='Activity_growth',color='Transport Type')#, title='Activity Growth')
            #add units to y col
            title_text = 'Activity Growth ({})'.format(activity_growth_economy['Unit'].unique()[0])
            fig.update_yaxes(title_text=title_text)#not working for some reason

            #add fig to dictionary for scenario and economy:
            fig_dict[economy][scenario]['activity_growth'] = [fig, title_text]

    return fig_dict



#%%
create_dashboard(fig_dict)
#%%