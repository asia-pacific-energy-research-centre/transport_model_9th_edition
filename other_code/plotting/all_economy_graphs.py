#pllot all 21 economys in sepoarate facets in one plkto for easier comparison


#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
#%%

##############FORMATTING#############
#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))
change_dataframe_aggregation = pd.read_csv('intermediate_data/road_model/change_dataframe_aggregation.csv')
model_output_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name))
model_output_8th = pd.read_csv('intermediate_data/activity_energy_road_stocks.csv')
activity_growth = pd.read_csv('intermediate_data/model_inputs/activity_growth.csv')
#%%
#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere

model_output_all = model_output_all[model_output_all['Scenario']==SCENARIO_OF_INTEREST]
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==SCENARIO_OF_INTEREST]
change_dataframe_aggregation = change_dataframe_aggregation[change_dataframe_aggregation['Scenario']==SCENARIO_OF_INTEREST]
model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Scenario']==SCENARIO_OF_INTEREST]
activity_growth = activity_growth[activity_growth['Scenario']==SCENARIO_OF_INTEREST]
#%%
#set nans to '' so that they dont cause issues with the plotly graphs
model_output_all = model_output_all.fillna('')
model_output_detailed = model_output_detailed.fillna('')
model_output_8th = model_output_8th.fillna('')
model_output_with_fuels = model_output_with_fuels.fillna('')

#where medium is not road then set drive and vehicle type to medium, so that we can plot them on the same graph
model_output_all.loc[model_output_all['Medium']!='road', 'Drive'] = model_output_all['Medium']
model_output_all.loc[model_output_all['Medium']!='road', 'Vehicle Type'] = model_output_all['Medium']
model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Drive'] = model_output_detailed['Medium']
model_output_detailed.loc[model_output_detailed['Medium']!='road', 'Vehicle Type'] = model_output_detailed['Medium']
model_output_with_fuels.loc[model_output_with_fuels['Medium']!='road', 'Drive'] = model_output_with_fuels['Medium']
model_output_with_fuels.loc[model_output_with_fuels['Medium']!='road', 'Vehicle Type'] = model_output_with_fuels['Medium']
#%%
stack_ttype = False
if stack_ttype:
    # #stack passenger_km and freight_tonne_km, as well as Occupancy and load. This is so that we can plot them on the same graph but they are labelled differently
    #do the process above for each df
    df_stacked_list = []
    for df in [model_output_all, model_output_detailed, model_output_8th, model_output_with_fuels]:
        passenger =df[df['Transport Type']=='passenger']
        #rename passenger_km to Activity and Occupancy to Occupancy_Load
        passenger = passenger.rename(columns={'passenger_km':'Activity', 'Occupancy':'Occupancy_Load'})
        freight =df[df['Transport Type']=='freight']
        #rename freight_tonne_km to Activity and load to Occupancy_Load
        freight = freight.rename(columns={'freight_tonne_km':'Activity', 'Load':'Occupancy_Load'})
        #combine passenger and freight
        df_stacked = pd.concat([passenger, freight])
        #drop passenger_km and freight_tonne_km and Occupancy and load if the
        try:
            df_stacked = df_stacked.drop(columns=['passenger_km', 'freight_tonne_km', 'Occupancy', 'Load'])
        except:
            try:
                df_stacked = df_stacked.drop(columns=['passenger_km', 'freight_tonne_km'])
            except:
                pass
        df_stacked = df_stacked.fillna('')
        #add to list
        df_stacked_list.append(df_stacked)
    #sep the stacked dfs 
    model_output_all_stacked, model_output_detailed_stacked, model_output_8th_stacked, model_output_with_fuels_stacked = df_stacked_list

##############FORMATTING OVER#############
#%%
#plot data by vehicle type and drive:
#plot energy use by vehicle type and drive:
#plot activity by vehicle type by drive
#plot stocks by vehicle type by drive

#plot energy use by economy by fuel type by drive
#plot energy use by economy by fuel type by vehicle type

#bascially we want to plot every column using economy as the facet then a mix of transport type, drive, vehicle type, medium and fuel as the categories. So we will create a function that does this:
def check_graph_exists(save_folder, title, dont_overwrite_existing_graphs=False):
    #double check we havent already plotted this graph:
    if (os.path.exists(f'./plotting_output/{save_folder}/static/' + title + '.png') | os.path.exists(f'./plotting_output/{save_folder}/' + title + '.html')) & dont_overwrite_existing_graphs:
        return True
    else:
        return False
    
def plot_line(df, y_column, color, line_dash, facet_col_wrap, facet_col, hover_name, hover_data, log_y, log_x, title, independent_y_axis, y_axis_title, x_axis_title, plot_html, plot_png, save_folder, AUTO_OPEN_PLOTLY_GRAPHS=False, width = 2000, height = 800):
    #fucntion for plotting a line graph within plot_line_by_economy
    #this could probably be better as part of a class
    fig = px.line(df, x="Date", y=y_column, color=color,line_dash=line_dash, facet_col_wrap=facet_col_wrap, facet_col =facet_col, hover_name = hover_name, hover_data = hover_data, log_y = log_y, log_x = log_x, title=title)
    if independent_y_axis:
        fig.update_yaxes(matches=None)
        #show y axis on both plots
        fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
    #do y_axis_title and x_axis_title
    fig.update_layout(yaxis_title=y_axis_title, xaxis_title=x_axis_title)
    #save the graph
    if plot_html:
        plotly.offline.plot(fig, filename=f'./plotting_output/{save_folder}' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
    if plot_png:
        fig.write_image(f"./plotting_output/{save_folder}/static/" + title + '.png', scale=1, width=width, height=height)


def plot_line_by_economy(df, color_categories, y_column,title,line_dash_categories=None,  x_column='Date', save_folder='all_economy_graphs', facet_col_wrap=7, facet_col ='Economy', hover_name = None, hover_data = None, log_y = False, log_x = False, y_axis_title = None, x_axis_title = None, width = 2000, height = 800,AUTO_OPEN_PLOTLY_GRAPHS=False, independent_y_axis = True,plot_png=True, plot_html=True, dont_overwrite_existing_graphs=False):
    """This function is intended to make plotting liine graphs of the model data a bit less repetitive. It will take in specifications like the plotly line graphing function (px.line) but will do some formatting before plotting. Can be used to plot data for multiple economies, jsut one or even a mix."""
    check_graph_exists(save_folder, title, dont_overwrite_existing_graphs)

    #copy df so that we dont change the original
    df = df.copy()
    #set color and line dash categories to list even if they are just one category
    if type(color_categories) != list:
        color_categories = [color_categories]
    if type(line_dash_categories) != list and line_dash_categories != None:
        line_dash_categories = [line_dash_categories]
    # convert color and likne dash categorties to one col each seperated by a hyphen
    color = '-'.join(color_categories)
    if line_dash_categories != None:
        line_dash = '-'.join(line_dash_categories)
        #add a column for the line dash
        df[line_dash] = df[line_dash_categories].apply(lambda x: '-'.join(x), axis=1)
    else:
        line_dash = None
    #add a column for the color
    df[color] = df[color_categories].apply(lambda x: '-'.join(x), axis=1)

    #if hover name is none then set it to the color+line_dash
    if hover_name == None:
        if line_dash_categories == None:
            hover_name = color
        else:
            hover_name = color + '-' + line_dash
            #insert hovername into the dataframe as a column
            df[hover_name] = df[color].astype(str) + '-' + df[line_dash].astype(str)

    #if hover data is none then set it to the y column
    if hover_data == None:
        hover_data = [y_column]
    #if y axis title is none then set it to the y column
    if y_axis_title == None:
        y_axis_title = y_column
    #if x axis title is none then set it to the x column
    if x_axis_title == None:
        x_axis_title = x_column
    #plot energy use by drive type
    #title = 'Energy use by drive type'
    #model_output_all_drive = model_output_all.groupby(['Date', 'Drive', 'Economy']).sum().reset_index()
    #if tehre are any '' in the y column then drop them
    df = df[df[y_column] != '']

    #checkl that the folders wqe save to exist
    if not os.path.exists(f'./plotting_output/{save_folder}'):
        os.makedirs(f'./plotting_output/{save_folder}')
    #create static folder too
    if not os.path.exists(f'./plotting_output/{save_folder}/static'):
        os.makedirs(f'./plotting_output/{save_folder}/static')

    #if there are no line dashes then just plot the graph
    if line_dash_categories != None:
        df = df.groupby([x_column, facet_col,color, line_dash])[y_column].sum().reset_index()
    else:
        df = df.groupby([x_column, facet_col,color])[y_column].sum().reset_index()
    
    plot_line(df, y_column, color, line_dash, facet_col_wrap, facet_col, hover_name, hover_data, log_y, log_x, title, independent_y_axis, y_axis_title, x_axis_title, plot_html, plot_png,save_folder, AUTO_OPEN_PLOTLY_GRAPHS, width, height)

#%%
AUTO_OPEN_PLOTLY_GRAPHS = True
#plot energy use by drive type
title = 'Energy use by drive type'
plot_line_by_economy(model_output_all, ['Drive'], 'Energy', title, save_folder='all_economy_graphs', AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS)


##################################################################
###########################plot all data in model_output_all################
##################################################################

#%%
#plot all data in model_output_all:
value_cols = ['freight_tonne_km','passenger_km', 'Energy', 'Stocks',
       'Occupancy','Load', 'Turnover_rate', 'New_vehicle_efficiency',
       'Travel_km', 'Efficiency', 'Travel_km_per_stock', 'Surplus_stocks',
       'Vehicle_sales_share']
#some value cols are not summable because they are factors. so specify them for when we group by economy, then we can calculate the mean of them
non_summable_value_cols = ['Occupancy','Load', 'Turnover_rate', 'New_vehicle_efficiency', 'Efficiency','Travel_km_per_stock','Vehicle_sales_share']
categorical_cols = ['Vehicle Type', 'Medium', 'Transport Type', 'Drive']
#%%
import itertools
AUTO_OPEN_PLOTLY_GRAPHS = False
dataframe_name = 'model_output_detailed'
dont_overwrite_existing_graphs = True
plot_png = True
plot_html = False
#plot each combination of: one of the value cols and then any number of the categorical cols
n_categorical_cols = len(categorical_cols)

#%%
#plot graphs with all economies on one graph
for value_col in value_cols:
    for i in range(1, n_categorical_cols+1):
        for combo in itertools.combinations(categorical_cols, i):
            title = f'{value_col} by {combo}'
            save_folder = f'{dataframe_name}/{value_col}'

            plot_line_by_economy(model_output_detailed, color_categories=list(combo), value_col, title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS, plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs)
            print(f'plotting {value_col} by {combo}')

##################################################################
#%%
dont_overwrite_existing_graphs = True
plot_png = True
plot_html = False
#do it for each unique economy as a singular graph
#first create economy= 'all' which is aplies either an avg or sum to the group of all economies depending on if the col is in non summable cols
model_output_detailed_APEC = model_output_detailed.groupby(categorical_cols+['Date']).agg({col: 'sum' for col in value_cols if col not in non_summable_value_cols else 'mean'}).reset_index()
model_output_detailed_APEC['Economy'] = 'all'
model_output_detailed = pd.concat([model_output_detailed, model_output_detailed_APEC])

#%%
n_categorical_cols = len(categorical_cols)
for economy_x in model_output_detailed['Economy'].unique():
    for value_col in value_cols:
        for i in range(1, n_categorical_cols+1):
            for combo in itertools.combinations(categorical_cols, i):
                title = f'{value_col} by {combo}'
                save_folder = f'{dataframe_name}/{economy_x}/{value_col}'
                                         
                #filter for that ecovnomy only and then plot
                model_output_detailed_econ = model_output_detailed[model_output_detailed['Economy'] == economy_x]
                plot_line_by_economy(model_output_detailed_econ, color_categories=list(combo), value_col, title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs)
                print(f'plotting {value_col} by {combo}')

##################################################################
#%%
#plot regional groupings of economys
#import the region_economy_mappin.xlsx from config/concordances_and_config_data
region_economy_mapping = pd.read_csv('./config/concordances_and_config_data/region_economy_mapping.csv')
#join with model_output_detailed_APEC.
#where there is no region drop the row since we are just plotting singular economies atm
model_output_detailed_regions = model_output_detailed.merge(region_economy_mapping, how='left', left_on='Economy', right_on='Economy')

# model_output_detailed_regions['Region'] = model_output_detailed_regions['Region'].fillna(model_output_detailed_regions['Economy'])
model_output_detailed_regions = model_output_detailed_regions.dropna(subset=['Region'])

model_output_detailed_regions = model_output_detailed_regions.groupby(categorical_cols+['Date',  'Region']).agg({col: 'sum' for col in value_cols if col not in non_summable_value_cols else 'mean'}).reset_index()

#%%
n_categorical_cols = len(categorical_cols)
for economy_x in model_output_detailed_regions['Region'].unique():
    for value_col in value_cols:
        for i in range(1, n_categorical_cols+1):
            for combo in itertools.combinations(categorical_cols, i):
                title = f'{value_col} by {combo}'
                save_folder = f'{dataframe_name}/{economy_x}/{value_col}'

                #filter for that ecovnomy only and then plot
                model_output_detailed_econ = model_output_detailed_regions[model_output_detailed_regions['Region'] == economy_x]
                plot_line_by_economy(model_output_detailed_econ, color_categories=list(combo), value_col, title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html,dont_overwrite_existing_graphs=dont_overwrite_existing_graphs)
                print(f'plotting {value_col} by {combo}')


##################################################################
###########################plot 'Energy' by fuel type############
##################################################################
#%%
#. need to define value cols that are worth plotting
value_cols = ['Energy']
categorical_cols = ['Vehicle Type', 'Medium', 'Transport Type', 'Drive']
dataframe_name = 'model_output_with_fuels'
#we will plot first plot for each economy as then for each region.

#create economy= 'all' which is the sum of all economies:
model_output_with_fuels_plot = model_output_with_fuels.groupby(categorical_cols+['Date','Fuel']).sum().reset_index()
model_output_with_fuels_plot['Economy'] = 'all'
model_output_with_fuels_plot = pd.concat([model_output_with_fuels, model_output_with_fuels_plot])

#plot singular graphs for each economy
n_categorical_cols = len(categorical_cols)
for economy_x in model_output_with_fuels_plot['Economy'].unique():
    for value_col in value_cols:
        for i in range(1, n_categorical_cols+1):
            for combo in itertools.combinations(categorical_cols, i):
                # Add 'Fuel' to the combo
                combo = list(combo) + ['Fuel']
                dataframe_name = 'model_output_with_fuels'
                title = f'{value_col} by {combo}'
                save_folder = f'{dataframe_name}/{economy_x}/{value_col}'
                                         
                #filter for that ecovnomy only and then plot
                model_output_with_fuels_plot_econ = model_output_with_fuels_plot[model_output_with_fuels_plot['Economy'] == economy_x]
                plot_line_by_economy(model_output_with_fuels_plot, color_categories= list(combo), value_col, title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs)
                print(f'plotting {value_col} by {combo}')

##################################################################

#merge with regions
#plot regional groupings of economys
#import the region_economy_mappin.xlsx from config/concordances_and_config_data
region_economy_mapping = pd.read_csv('./config/concordances_and_config_data/region_economy_mapping.csv')
model_output_with_fuels_regions = model_output_with_fuels.merge(region_economy_mapping, how='left', left_on='Economy', right_on='Economy')

#drop nas
model_output_with_fuels_regions = model_output_with_fuels_regions.dropna(subset=['Region'])

model_output_detailed_regions = model_output_detailed_regions.groupby(categorical_cols+['Date',  'Region']).sum().reset_index()

#plot singular graphs for each economy
n_categorical_cols = len(categorical_cols)
for economy_x in model_output_with_fuels_regions['Economy'].unique():
    for value_col in value_cols:
        for i in range(1, n_categorical_cols+1):
            for combo in itertools.combinations(categorical_cols, i):
                # Add 'Fuel' to the combo
                combo = list(combo) + ['Fuel']

                title = f'{value_col} by {combo}'
                save_folder = f'{dataframe_name}/{economy_x}/{value_col}'
                                         
                #filter for that ecovnomy only and then plot
                model_output_with_fuels_regions_region = model_output_with_fuels_regions[model_output_with_fuels_regions['Economy'] == economy_x]
                plot_line_by_economy(model_output_with_fuels_regions_region, color_categories = list(combo), value_col, title, line_dash_categories = 'Fuel', save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs)
                print(f'plotting {value_col} by {combo}')


# %%
##################################################################
#plot graphs with all economies on one graph
for value_col in value_cols:
    for i in range(1, n_categorical_cols+1):
        for combo in itertools.combinations(categorical_cols, i):
            # Add 'Fuel' to the combo
            combo = list(combo) + ['Fuel']
            title = f'{value_col} by {combo}'
            
            save_folder = f'energy_use_by_fuel/all_economies_plot/{value_col}'

            plot_line_by_economy(model_output_with_fuels_plot, color_categories= list(combo), value_col, title, line_dash_categories='Fuel', save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs)
            print(f'plotting {value_col} by {combo}')

#%%
##################################################################
###########################plot 'Energy' by fuel type############
##################################################################

#plot activity growth for the economy to help understand trend:
dataframe_name = 'activity_growth'
#since the activity is just a proportion change each year we will need to start with an index of 1 and then multiply by the activity growth each year to get a line that is more interpretable
#sort in order of date
activity_growth = activity_growth.sort_values(by='Date')
#group by economy and date and do cumprod
activity_growth = activity_growth.groupby(['Economy', 'Date']).cumprod().reset_index()

#for each economy plot a single graph and then plot all on one graph
for economy_x in activity_growth['Economy'].unique():
    value_col = 'Activity'
    title = f'Activity growth for {economy_x}'
    save_folder = f'{dataframe_name}/{economy_x}/{value_col}'
                                
    #filter for that ecovnomy only and then plot
    activity_growth_econ = activity_growth[activity_growth['Economy'] == economy_x]
    plot_line_by_economy(activity_growth_econ, color_categories= list('Economy'), value_col, title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs)
    print(f'plotting {value_col} by {combo}')

#plot all in on egraph

title = f'Activity growth for all economies'
save_folder = f'{dataframe_name}/{value_col}'
value_col = 'Activity'
plot_line_by_economy(activity_growth, color_categories= list('Economy'), value_col, title, save_folder=save_folder, AUTO_OPEN_PLOTLY_GRAPHS=AUTO_OPEN_PLOTLY_GRAPHS,plot_png=plot_png, plot_html=plot_html, dont_overwrite_existing_graphs=dont_overwrite_existing_graphs)
print(f'plotting {value_col} by {combo}')

#%%



















#%%

# AUTO_OPEN_PLOTLY_GRAPHS = True
# #plot energy use by medium and economy
# title = 'Energy use by medium and economy'
# model_output_all_medium = model_output_all.groupby(['Date', 'Medium', 'Economy']).sum().reset_index()

# fig = px.line(model_output_all_medium, x="Date", y="Energy", color='Medium', facet_col='Economy', title='Energy use by medium and economy', facet_col_wrap=7)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)


# # %%
# #plot passenger km by medium and economy
# title = 'Passenger km by medium and economy'
# #filter for transport type = passenger
# model_output_all_medium = model_output_all_medium[model_output_all_medium['Transport Type']=='passenger']
# model_output_all_medium = model_output_all_medium.groupby(['Date', 'Medium', 'Economy']).sum().reset_index()

# fig = px.line(model_output_all_medium, x="Date", y="Activity", color='Medium', facet_col='Economy', title='Passenger km by medium and economy', facet_col_wrap=7)
# #make y axis independent
# fig.update_yaxes(matches=None)
# #show y axis on both plots
# fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)
# #%%
# #plot freight tonne km by medium and economy
# title = 'Freight tonne km by medium and economy'
# #filter for transport type = freight
# model_output_all_medium = model_output_all_medium[model_output_all_medium['Transport Type']=='freight']
# model_output_all_medium = model_output_all_medium.groupby(['Date', 'Medium', 'Economy']).sum().reset_index()
# fig = px.line(model_output_all_medium, x="Date", y="freight_tonne_km", color='Medium', facet_col='Economy', title='freight km by medium and economy', facet_col_wrap=7)
# #make y axis independent
# fig.update_yaxes(matches=None)
# #show y axis on both plots
# fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #%%
# #plot energy use by fuel type
# model_output_with_fuels_plot = model_output_with_fuels.groupby(['Fuel','Date', 'Economy']).sum().reset_index()

# title='Energy use by fuel type'
# #plot using plotly
# fig = px.line(model_output_with_fuels_plot, x="Date", y="Energy", color="Fuel", title=title, facet_col='Economy', facet_col_wrap=7)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #%%

# #plot the total energy use by vehicle type / drive type combination sep by transport type
# #first need to create a new column that combines the vehicle type and drive type
# model_output_detailed['vehicle_type_drive_type'] = model_output_detailed['Vehicle Type'] + ' ' + model_output_detailed['Drive']
# #grab passenger data only
# model_output_detailed_pass = model_output_detailed[model_output_detailed['Transport Type']=='passenger']
# title='Energy use by vehicle type drive type combination, passenger'
# #plot using plotly
# fig = px.line(model_output_detailed_pass, x="Date", y="Energy", color="vehicle_type_drive_type", title=title, facet_col='Economy', facet_col_wrap=7)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #plot the total energy use by vehicle type / drive type combination sep by transport type
# #first need to create a new column that combines the vehicle type and drive type
# model_output_detailed['vehicle_type_drive_type'] = model_output_detailed['Vehicle Type'] + ' ' + model_output_detailed['Drive']
# #grab passenger data only
# model_output_detailed_freight = model_output_detailed[model_output_detailed['Transport Type']=='freight']
# title='Energy use by vehicle type drive type combination, freight'
# #plot using plotly
# fig = px.line(model_output_detailed_freight, x="Date", y="Energy", color="vehicle_type_drive_type", title=title, facet_col='Economy', facet_col_wrap=7)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)
# #%%
# #plot travel km by vehicle type / drive type combination
# title = 'Travel km by vehicle type drive type combination, passenger'
# #grab passenger data only
# model_output_detailed_passenger = model_output_detailed[model_output_detailed['Transport Type']=='passenger']
# #plot using plotly
# fig = px.line(model_output_detailed_passenger, x="Date", y="Travel_km", color="vehicle_type_drive_type", title=title, facet_col='Economy', facet_col_wrap=7)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# title = 'Travel km by vehicle type drive type combination, freight'
# #grab passenger data only
# model_output_detailed_passenger = model_output_detailed[model_output_detailed['Transport Type']=='freight']
# #plot using plotly
# fig = px.line(model_output_detailed_passenger, x="Date", y="Travel_km", color="vehicle_type_drive_type", title=title, facet_col='Economy', facet_col_wrap=7)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)


# #%%
# #plot activity by vehicle type / drive type combination
# title = 'Activity by vehicle type drive type combination, passenger'
# #grab passenger data only
# model_output_detailed_passenger = model_output_detailed[model_output_detailed['Transport Type']=='passenger']

# #plot using plotly
# fig = px.line(model_output_detailed_passenger, x="Date", y="Activity",  color="vehicle_type_drive_type", title=title, facet_col='Economy', facet_col_wrap=7)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# title = 'Activity by vehicle type drive type combination, freight'
# #grab passenger data only
# model_output_detailed_passenger = model_output_detailed[model_output_detailed['Transport Type']=='freight']

# #plot using plotly
# fig = px.line(model_output_detailed_passenger, x="Date", y="Activity",  color="vehicle_type_drive_type", title=title, facet_col='Economy', facet_col_wrap=7)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)
# #%%
# #plot efficiency over time by vehicle type / drive type combination
# title = 'Efficiency by vehicle type drive type combination, passenger'
# #grab passenger data only
# model_output_detailed_passenger = model_output_detailed[model_output_detailed['Transport Type']=='passenger']
# #plot using plotly
# fig = px.line(model_output_detailed, x="Date", y="Efficiency", facet_col='Economy', facet_col_wrap=7, color="vehicle_type_drive_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #plot efficiency over time by vehicle type / drive type combination
# title = 'Efficiency by vehicle type drive type combination, freight'
# #grab passenger data only
# model_output_detailed_passenger = model_output_detailed[model_output_detailed['Transport Type']=='freight']
# #plot using plotly
# fig = px.line(model_output_detailed, x="Date", y="Efficiency", facet_col='Economy', facet_col_wrap=7, color="vehicle_type_drive_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)
# #%%
# #plot stocks over time by vehicle type / drive type combination
# title = 'Stocks by vehicle type drive type combination, passenger'
# #plot using plotly
# fig = px.line(model_output_detailed, x="Date", y="Stocks",facet_col='Economy', facet_col_wrap=7, color="vehicle_type_drive_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #%%
# #plot sales share over time by vehicle type / drive type combination
# title = 'Sales share by vehicle type drive type combination, sep by transport type'
# #plot using plotly
# fig = px.line(model_output_detailed, x="Date", y="Vehicle_sales_share", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_drive_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #%%
# #energy use by vehicle type fuel type combination
# title = 'Energy use by vehicle type fuel type combination, sep by transport type'

# #remove drive type from model_output_with_fuels
# model_output_with_fuels_no_drive = model_output_with_fuels.drop(columns=['Drive'])
# #sum
# model_output_with_fuels_no_drive = model_output_with_fuels_no_drive.groupby(['Economy','Vehicle Type','Transport Type','Fuel','Date']).sum().reset_index()

# #create col for vehicle type and fuel type combination
# model_output_with_fuels_no_drive['vehicle_type_fuel_type'] = model_output_with_fuels_no_drive['Vehicle Type'] + ' ' + model_output_with_fuels_no_drive['Fuel']
# #plot using plotly
# fig = px.line(model_output_with_fuels_no_drive, x="Date", y="Energy", facet_col="Transport Type", facet_col_wrap=2, color="vehicle_type_fuel_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #%%
# #energy use by vehicle type fuel type combination
# title = 'Energy use by Drive fuel type combination, sep by transport type'

# #remove drive type from model_output_with_fuels
# model_output_with_fuels_no_v = model_output_with_fuels.drop(columns=['Vehicle Type'])
# #sum
# model_output_with_fuels_no_v = model_output_with_fuels_no_v.groupby(['Economy','Drive','Transport Type','Fuel','Date']).sum().reset_index()

# #create col for vehicle type and fuel type combination
# model_output_with_fuels_no_v['drive_fuel_type'] = model_output_with_fuels_no_v['Drive'] + ' ' + model_output_with_fuels_no_v['Fuel']
# #plot using plotly
# fig = px.line(model_output_with_fuels_no_v, x="Date", y="Energy", facet_col="Transport Type", facet_col_wrap=2, color="drive_fuel_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #%%
# #energy use by medium, transport type combination
# title = 'Energy use by medium, transport type combination'

# #remove drive type from model_output_with_fuels
# model_output_with_fuels_no_v = model_output_with_fuels.drop(columns=['Vehicle Type', 'Drive'])
# #sum
# model_output_with_fuels_no_v = model_output_with_fuels_no_v.groupby(['Economy','Transport Type','Fuel','Medium','Date']).sum().reset_index()

# #create col for medium and fuel type combination
# model_output_with_fuels_no_v['medium_fuel_type'] = model_output_with_fuels_no_v['Medium'] + ' ' + model_output_with_fuels_no_v['Fuel']
# #plot using plotly
# fig = px.line(model_output_with_fuels_no_v, x="Date", y="Energy", facet_col="Transport Type", facet_col_wrap=2, color="medium_fuel_type", title=title)

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)

# #%%
# #passenger km by medium, transport type combination
# title = 'Activity by medium, transport type combination'

# model_output_detailed_medium_activity = model_output_detailed.groupby(['Economy','Transport Type','Medium','Date']).sum().reset_index()

# #create col for medium and fuel type combination
# model_output_detailed_medium_activity['medium_activity'] = model_output_detailed_medium_activity['Medium'] + ' ' + 'activity'
# #plot using plotly
# fig = px.line(model_output_detailed_medium_activity, x="Date", y="Activity", facet_col="Transport Type", facet_col_wrap=2, color="medium_activity", title=title)
# #make y axis independent
# fig.update_yaxes(matches=None)
# #show y axis on both plots
# fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))

# plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
# fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=800)


# #%%










#%%
# df = model_output_all.copy()
# color_categories = ['Drive']
# line_dash_categories =None
# y_column = 'Energy'
# title = 'Energy use by drive type'
# x_column='Date'
# save_folder='all_economy_graphs'
# facet_col_wrap=7
# facet_col ='Economy'
# hover_name = None
# hover_data = None
# log_y = False
# log_x = False
# y_axis_title = None
# x_axis_title = None
# width = 2000
# height = 800
# AUTO_OPEN_PLOTLY_GRAPHS=True

# #set color and line dash categories to list even if they are just one category
# if type(color_categories) != list:
#     color_categories = [color_categories]
# if type(line_dash_categories) != list and line_dash_categories != None:
#     line_dash_categories = [line_dash_categories]
# # convert color and likne dash categorties to one col each seperated by a hyphen
# color = '-'.join(color_categories)
# if line_dash_categories != None:
#     line_dash = '-'.join(line_dash_categories)
#     #add a column for the line dash
#     df[line_dash] = df[line_dash_categories].apply(lambda x: '-'.join(x), axis=1)
# #add a column for the color
# df[color] = df[color_categories].apply(lambda x: '-'.join(x), axis=1)

# #if hover name is none then set it to the color+line_dash
# if hover_name == None:
#     if line_dash_categories == None:
#         hover_name = color
#     else:
#         hover_name = color + '-' + line_dash
#         #insert hovername into the dataframe as a column
#         df[hover_name] = df[color].astype(str) + '-' + df[line_dash].astype(str)

# #if hover data is none then set it to the y column
# if hover_data == None:
#     hover_data = [y_column]
# #if y axis title is none then set it to the y column
# if y_axis_title == None:
#     y_axis_title = y_column
# #if x axis title is none then set it to the x column
# if x_axis_title == None:
#     x_axis_title = x_column
# #plot energy use by drive type
# #title = 'Energy use by drive type'
# #model_output_all_drive = model_output_all.groupby(['Date', 'Drive', 'Economy']).sum().reset_index()
# if line_dash_categories != None:
#     df = df.groupby([x_column, facet_col,color, line_dash]).sum().reset_index()
#     fig = px.line(df, x="Date", y=y_column, color=color, facet_col_wrap=facet_col_wrap, facet_col =facet_col, hover_name = hover_name, hover_data = hover_data, log_y = log_y, log_x = log_x, title=title)
#     #do y_axis_title and x_axis_title
#     fig.update_layout(yaxis_title=y_axis_title, xaxis_title=x_axis_title)

#     plotly.offline.plot(fig, filename=f'./plotting_output/{save_folder}' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#     fig.write_image(f"./plotting_output/{save_folder}/static/" + title + '.png', scale=1, width=width, height=height)
# else:
#     df = df.groupby([x_column, facet_col,color]).sum().reset_index()
#     fig = px.line(df, x="Date", y=y_column, color=color, facet_col_wrap=facet_col_wrap, facet_col =facet_col, hover_name = hover_name, hover_data = hover_data, log_y = log_y, log_x = log_x, title=title)
#     #do y_axis_title and x_axis_title
#     fig.update_layout(yaxis_title=y_axis_title, xaxis_title=x_axis_title)
#     plotly.offline.plot(fig, filename=f'./plotting_output/{save_folder}' + title + '.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
#     fig.write_image(f"./plotting_output/{save_folder}/static/" + title + '.png', scale=1, width=width, height=height)
