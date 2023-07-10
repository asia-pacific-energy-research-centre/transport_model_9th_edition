

#set working directory as one folder back so that config works
import os
import re
import shutil
from turtle import title
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive 
# notebook in vscode #or set to notebook
import plotly
import plotly.express as px
pd.options.plotting.backend = "matplotlib"
import plotly.io as pio
pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import sys
sys.path.append("./config/utilities")
import archiving_scripts

###########################################
#PLOTTING:
###########################################


def plot_estimated_data_system_sales_share(sales, INDEX_COLS, SCENARIOS_LIST, YEARS_TO_KEEP_AFTER_BASE_YEAR):
    #plot to check., we will sum all values by everythign except col, then plot
    sales_plot = sales.copy()
    #filter for reference only
    sales_plot = sales_plot.loc[sales_plot['Scenario']=='Reference']
    cols = INDEX_COLS.copy()
    cols.remove('Economy')
    sales_plot = sales_plot.groupby(cols)['Sales Share'].sum().reset_index()
    # plot using plotly
    fig = px.bar(sales_plot, x='Drive', y='Sales Share', color='Drive',facet_col='Vehicle Type', facet_col_wrap=2)
    #WRite to html in plotting_output/input_exploration/
    fig.write_html('plotting_output/input_exploration/Transport_data_system_testing_{}_sales_share.html'.format(FILE_DATE_ID))
    #it doesnt really matter what the values are since we'll be adjusting them as we get more data.

def plot_new_sales_shares(new_sales_shares_all):
        
    #now we wnat to plot the data using plotly. we will plot with facets for each economy, and a different plot for each vehicle type, transport tyep combo
    #first we need to create a new column that is the vehicle type and transport type
    #we will also plot for comparison between new_sales_shares_sum and new_sales_shares_all so nerge that on now
    
    plotting = True
    if plotting:
        import plotly.express as px
        new_sales_shares_all_plot = new_sales_shares_all.copy()
        new_sales_shares_all_plot['Vehicle_Transport'] = new_sales_shares_all_plot['Vehicle Type'] + '_' + new_sales_shares_all_plot['Transport Type']

        for scenario in new_sales_shares_all_plot['Scenario'].unique():
            for Vehicle_Transport in new_sales_shares_all_plot['Vehicle_Transport'].unique():
                plot_data = new_sales_shares_all_plot.loc[(new_sales_shares_all_plot['Vehicle_Transport']==Vehicle_Transport) & (new_sales_shares_all_plot['Scenario']==scenario)].copy()

                fig = px.line(plot_data, x='Date', y='Drive_share', color='Drive', facet_col='Economy',facet_col_wrap=3, title=Vehicle_Transport)
                #write to html in plotting_output\input_exploration\vehicle_sales_shares
                fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/{Vehicle_Transport}_{scenario}_drive_share.html', auto_open=False)

                plot_data = new_sales_shares_all_plot.loc[(new_sales_shares_all_plot['Vehicle_Transport']==Vehicle_Transport) & (new_sales_shares_all_plot['Scenario']==scenario)].copy()
                fig = px.line(plot_data, x='Date', y='Transport_type_share', color='Drive', facet_col='Economy',facet_col_wrap=3, title=Vehicle_Transport)
                #write to html in plotting_output\input_exploration\vehicle_sales_shares
                fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/{Vehicle_Transport}_{scenario}Transport_type_share_pre_vehicle_share_adj.html', auto_open=False)

    #it is also usefu to plot the vehicle sales share by economy now. This is because it is a useful graph for analysis of assumptions. So loop through economys and just plkot the Drive_share by economy, with vehicle type and transport type as facets
    plotting = True
    if plotting:
        for scenario in new_sales_shares_all_plot['Scenario'].unique():
            for economy in new_sales_shares_all_plot['Economy'].unique():
                
                plot_data = new_sales_shares_all_plot.loc[(new_sales_shares_all_plot['Scenario']==scenario) & (new_sales_shares_all_plot['Economy']==economy)].copy()
                title = f'{economy} {scenario} Drive Share by Vehicle Type and Transport Type'
                fig = px.line(plot_data, x='Date', y='Drive_share', color='Drive', facet_col='Vehicle_Transport',facet_col_wrap=3, title=Vehicle_Transport)
                #write to html in plotting_output\input_exploration\vehicle_sales_shares
                fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/by_economy/{economy}_{scenario}_drive_share.html', auto_open=False)

                #also plot the data like the iea does. So plot the data for 2022 and previous, then plot for the follwoign eyars: [2025, 2030, 2035, 2040, 2050, 2060]. Also < also wat??
                plot_data = plot_data.apply(lambda x: x if x['Date'] <= 2022 or x['Date'] in [2025, 2030, 2035, 2040, 2050, 2060] else 0, axis=1)
                #drop all vehicle types except phev and bev
                plot_data = plot_data.loc[(plot_data['Drive']=='bev') | (plot_data['Drive']=='phev') | (plot_data['Drive']=='fcev')].copy()
                title = f'Passenger EV sales share, {economy}, {scenario}'
                #now plot
                fig = px.bar(plot_data[plot_data['Transport Type']=='passenger'], x='Date', y='Drive_share', color='Drive', facet_col='Vehicle Type', title=title, barmode='stack')
                
                fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/by_economy/stacked_passenger_{economy}_{scenario}_drive_share.html', auto_open=False)
                #############
                
                fig = px.bar(plot_data[plot_data['Transport Type']=='freight'], x='Date', y='Drive_share', color='Drive', facet_col='Vehicle Type', title=title, barmode='stack')
                
                fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/by_economy/stacked_freight_{economy}_{scenario}_drive_share.html', auto_open=False)
                # plot_data = new_sales_shares_all_plot_drive_shares.loc[(new_sales_shares_all_plot_drive_shares['Scenario']==scenario) & (new_sales_shares_all_plot_drive_shares['Economy']==economy)].copy()
                
                # title = f'{economy} {scenario} Drive Share by Vehicle Type and Transport Type'
                # fig = px.line(plot_data, x='Date', y='Transport_type_share', color='Drive', line_dash = 'Measure', facet_col='Economy',facet_col_wrap=3, title=Vehicle_Transport)
                # #write to html in plotting_output\input_exploration\vehicle_sales_shares
                # fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/{Vehicle_Transport}_{scenario}Transport_type_share_pre_vehicke_share_adj.html', auto_open=False)
    #save vehicels sales share data for use in plotting our asumtions. we will save it as an excel file to be read in by the plotting assumptions script
    new_sales_shares_all_plot.to_csv(f'output_data/assumptions_outputs/vehicle_sales_shares{FILE_DATE_ID}.csv', index=False)


def plot_new_sales_shares_normalised_by_transport_type(new_sales_shares_all, new_sales_shares_sum,new_sales_shares_all_new):

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
                plot_data = new_sales_shares_all_plot_transport_type_shares.loc[(new_sales_shares_all_plot_transport_type_shares['Economy']==economy) & (new_sales_shares_all_plot_transport_type_shares['Scenario']==scenario)].copy()

                fig = px.line(plot_data, x='Date', y='Transport_type_share', color='Vehicle_drive', line_dash = 'Measure', facet_col='Transport Type',facet_col_wrap=1, title='Transport_type_share')
                #write to html in plotting_output\input_exploration\vehicle_sales_shares
                fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/by_economy/{economy}_{scenario}Transport_type_share.html', auto_open=False)
    print('Plots of new sales shares saved to plotting_output/input_exploration/vehicle_sales_shares/')

def plot_input_sales_shares_before_interpolation(new_sales_shares_pre_interp):
    #new_sales_shares_pre_interp[['Economy', 'Scenario', 'Date', 'Transport Type', 'Vehicle Type', 'Drive','Drive_share']]
    #do some more plotting. just plot the Transport_type_share_new vs Transport_type_share
    breakpoint()
    plotting=True
    if plotting:
        new_sales_shares_all_plot = new_sales_shares_pre_interp.copy()

        import plotly.express as px

        #extract a df for Transport_type_share measures:
        new_sales_shares_all_plot_transport_type_shares = new_sales_shares_all_plot[['Economy', 'Scenario', 'Date', 'Transport Type', 'Vehicle Type', 'Drive','Drive_share']].copy()

        #join drive and vehicle type
        new_sales_shares_all_plot_transport_type_shares['Vehicle_drive'] = new_sales_shares_all_plot_transport_type_shares['Vehicle Type'] + '_' + new_sales_shares_all_plot_transport_type_shares['Drive']
        for scenario in new_sales_shares_all_plot_transport_type_shares['Scenario'].unique():
            for economy in new_sales_shares_all_plot_transport_type_shares['Economy'].unique():
                plot_data = new_sales_shares_all_plot_transport_type_shares.loc[(new_sales_shares_all_plot_transport_type_shares['Economy']==economy) & (new_sales_shares_all_plot_transport_type_shares['Scenario']==scenario)].copy()

                fig = px.line(plot_data, x='Date', y='Drive_share', color='Drive', line_dash = 'Vehicle Type', facet_col='Transport Type',facet_col_wrap=1, title='Drive_share')
                #write to html in plotting_output\input_exploration\vehicle_sales_shares
                fig.write_html(f'plotting_output/input_exploration/vehicle_sales_shares/by_economy/{economy}_{scenario}drive_share_pre_interp.html', auto_open=False)
                
    print('Plots of pre interpolation sales shares saved to plotting_output/input_exploration/vehicle_sales_shares/')

    
    
def plot_supply_side_fuel_mixing(supply_side_fuel_mixing):
    #plot supply side fuel mixing
    # breakpoint()
    supply_side_fuel_mixing_plot = supply_side_fuel_mixing.copy()
    #round the Supply_side_fuel_share column to 2dp
    supply_side_fuel_mixing_plot['Supply_side_fuel_share'] = supply_side_fuel_mixing_plot['Supply_side_fuel_share'].round(2)
    supply_side_fuel_mixing_plot= supply_side_fuel_mixing_plot[['Date', 'Economy','Scenario', 'Fuel','New_fuel' ,'Supply_side_fuel_share']].drop_duplicates()
    for scenario in supply_side_fuel_mixing_plot.Scenario.unique():
        scenario_data = supply_side_fuel_mixing_plot[supply_side_fuel_mixing_plot['Scenario'] == scenario]
        #supply side mixing is just the percent of a fuel type that is mixed into another fuel type, eg. 5% biodiesel mixed into diesel. We can use the concat of Fuel and New fuel cols to show the data:
        scenario_data['Fuel mix'] = scenario_data['Fuel'] + ' mixed with ' + scenario_data['New_fuel']
        #concat
        title = 'Supply side fuel mixing for ' + scenario + ' scenario'
        fig = px.line(scenario_data, x="Date", y="Supply_side_fuel_share", color='Fuel mix', facet_col="Economy", facet_col_wrap=7,  title=title)
        #save to html
        fig.write_html(f"plotting_output/input_exploration/fuel_mixing/{title}.html")

def plot_demand_side_fuel_mixing(demand_side_fuel_mixing):
    #for each cat col in demand_side_fuel_mixing, plot the fuel shares using plotly line graph, with date on x axis, faceted by Economy, and color by Drive and line dash by Fuel
    #do a graph for each scenario
    demand_side_fuel_mixing_plot = demand_side_fuel_mixing.copy()
    demand_side_fuel_mixing_plot['Demand_side_fuel_share'] = demand_side_fuel_mixing_plot['Demand_side_fuel_share'].round(2)
    #drop where Demand_side_fuel_share is 1
    demand_side_fuel_mixing_plot = demand_side_fuel_mixing_plot[demand_side_fuel_mixing_plot['Demand_side_fuel_share'] <= 0.999]
    
    #where medium is not 'road', then set drive to medium
    demand_side_fuel_mixing_plot.loc[demand_side_fuel_mixing_plot['Medium'] != 'road', 'Drive'] = demand_side_fuel_mixing_plot['Medium']
    
    demand_side_fuel_mixing_plot = demand_side_fuel_mixing_plot[['Date', 'Economy','Scenario', 'Fuel','Drive', 'Demand_side_fuel_share']].drop_duplicates()
    
    for scenario in demand_side_fuel_mixing_plot.Scenario.unique():
        scenario_data = demand_side_fuel_mixing_plot[demand_side_fuel_mixing_plot['Scenario'] == scenario]
        title = 'Demand side fuel mixing for ' + scenario + ' scenario'
        #concat drive aND FUEL 
        scenario_data['Drive'] = scenario_data['Drive'] + ' ' + scenario_data['Fuel'] 
        fig = px.line(scenario_data, x="Date", y="Demand_side_fuel_share", color="Drive",facet_col="Economy", facet_col_wrap=7,  title=title)
        #save to html
        fig.write_html(f"plotting_output/input_exploration/fuel_mixing/{title}.html")
        