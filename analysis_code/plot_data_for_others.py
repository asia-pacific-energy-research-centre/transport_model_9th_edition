#take in detailed output data and print out any useful metrics/statisitcs to summarise the reults of the model. the intention is that the output willbe easy to view through the command line, and that the output will be saved to a file for later viewing.

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
#%%

#load data in
model_output_all = pd.read_csv('output_data/model_output/{}'.format(model_output_file_name))
model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))
change_dataframe_aggregation = pd.read_csv('intermediate_data/road_model/change_dataframe_aggregation.csv')
#%%
#FILTER FOR SCENARIO OF INTEREST
#this should be temporary as the scenario should be passed in as a parameter through config if it is useed elsewhere

model_output_all = model_output_all[model_output_all['Scenario']==SCENARIO_OF_INTEREST]
model_output_detailed = model_output_detailed[model_output_detailed['Scenario']==SCENARIO_OF_INTEREST]
change_dataframe_aggregation = change_dataframe_aggregation[change_dataframe_aggregation['Scenario']==SCENARIO_OF_INTEREST]

#%%

################################################################################################################################################################
#plot sales share of each drive type, in the lv vehicle type, on the same graph as the stocks of each drive type in the lv vehicle type, for each economy, year
#this is to show the relationship between the sales share and the stock share
title='Stocks and sales of each drive vehicle type combination in passenger transport lv vehicles'

#filter for lv vehicles
model_output_detailed_lv = model_output_detailed[model_output_detailed['Vehicle Type']=='lv']
#filter for passenger transport
model_output_detailed_lv_passenger = model_output_detailed_lv[model_output_detailed_lv['Transport Type']=='passenger']

import plotly.graph_objects as go
from plotly.subplots import make_subplots

#create subplots specs list as a set of 3 lists with 7 dictionaries in each that are just {"secondary_y": True} to create 3 rows of 7 subplots each
subplots_specs = [[{"secondary_y": True} for i in range(7)] for j in range(3)] 
subplot_titles = model_output_detailed_lv_passenger['Economy'].unique().tolist()
fig = make_subplots(rows=3, cols=7,
                    specs=subplots_specs,
                    subplot_titles=subplot_titles)

col_number=0
row_number = 1
legend_set = False
drive_list = model_output_detailed_lv_passenger['Drive'].unique().tolist()

for economy in model_output_detailed_lv_passenger['Economy'].unique():
    #filter for economy
    model_output_detailed_lv_passenger_economy = model_output_detailed_lv_passenger[model_output_detailed_lv_passenger['Economy']==economy]

    #set row and column number
    col_number +=1
    if col_number > 7:
        col_number = 1
        row_number += 1
    
    #NOW GO THROUGH EACH DRIVE TYPE AND PLOT THE STOCKS AND SALES OF EACH DRIVE TYPE IN THE LV VEHICLE TYPE
    for drive_type in drive_list:
        #get the index of the current drive
        drive_type_index = drive_list.index(drive_type)
        #GET THE COLOUR WE'LL USE FOR THIS DRIVE TYPE using the index
        color = px.colors.qualitative.Plotly[drive_type_index]
        
        #get the data for this drive type
        model_output_detailed_lv_passenger_economy_drive = model_output_detailed_lv_passenger_economy[model_output_detailed_lv_passenger_economy['Drive']==drive_type]

        if (col_number == 1) & (row_number == 1):#set the legend for the first subplot, and tehrefore all of the subplots

            #create subplot for this economy AND DRIVE
            legend_name = drive_type + '_Stocks'
            fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_drive['Year'], y=model_output_detailed_lv_passenger_economy_drive['Stocks'],  legendgroup=legend_name, name=legend_name, line=dict(color=color, width=2, )), row=row_number, col=col_number, secondary_y=False)

            legend_name = drive_type + '_Vehicle_sales_share'
            fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_drive['Year'], y=model_output_detailed_lv_passenger_economy_drive['Vehicle_sales_share'], legendgroup=legend_name, name=legend_name, line=dict(color=color, dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)
        else:#legend is already set, so just add the traces with showlegend=False
            #create subplot for this economy AND DRIVE
            legend_name = drive_type + '_Stocks'
            fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_drive['Year'], y=model_output_detailed_lv_passenger_economy_drive['Stocks'],  legendgroup=legend_name, name=legend_name,showlegend=False, line=dict(color=color, width=2, )), row=row_number, col=col_number, secondary_y=False)

            legend_name = drive_type + '_Vehicle_sales_share'
            fig.add_trace(go.Scatter(x=model_output_detailed_lv_passenger_economy_drive['Year'], y=model_output_detailed_lv_passenger_economy_drive['Vehicle_sales_share'], legendgroup=legend_name, name=legend_name, showlegend=False, line=dict(color=color, dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)


#%%
################################################################################################################################################################
#plot stocks of each drive vehciel type combination in passenger transport
title='Stocks of each drive vehicle type combination in passenger transport'

model_output_all_passenger = model_output_all[model_output_all['Transport Type']=='passenger']

#plot
fig = px.line(model_output_all_passenger, x="Year", y="Stocks", color="Vehicle Type", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)


################################################################################################################################################################
#%%
#plot energy use for each economy for each year, by drive type.
title = 'Total energy use for each economy for each year, drive type'
model_output_detailed_vtype = model_output_detailed.groupby(['Year','Economy', 'Drive'])['Energy'].sum().reset_index()

#plot
fig = px.line(model_output_detailed_vtype, x="Year", y="Energy", color="Drive", line_dash='Drive', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)

################################################################################################################################################################

#%%
#plot sum of activity and activity growth mean for each year for each economy
title = 'Activity and activity growth'
change_dataframe_aggregation_act = change_dataframe_aggregation.groupby(['Year','Economy'])['Activity'].sum().reset_index()
change_dataframe_aggregation_ag = change_dataframe_aggregation.groupby(['Year','Economy'])['Activity_growth'].mean().reset_index()


#join the dataframes
change_dataframe_aggregation_act_ag = change_dataframe_aggregation_act.merge(change_dataframe_aggregation_ag, on=['Year','Economy'])

import plotly.graph_objects as go
from plotly.subplots import make_subplots

#create subplots specs list as a set of 3 lists with 7 dictionaries in each that are just {"secondary_y": True} to create 3 rows of 7 subplots each
subplots_specs = [[{"secondary_y": True} for i in range(7)] for j in range(3)] 
subplot_titles = change_dataframe_aggregation_act_ag['Economy'].unique().tolist()
fig = make_subplots(rows=3, cols=7,
                    specs=subplots_specs,
                    subplot_titles=subplot_titles)

col_number=0
row_number = 1
legend_set = False

for economy in change_dataframe_aggregation_act_ag['Economy'].unique():
    #filter for economy
    change_dataframe_aggregation_act_ag_e = change_dataframe_aggregation_act_ag[change_dataframe_aggregation_act_ag['Economy']==economy]

    #set row and column number
    col_number +=1
    if col_number > 7:
        col_number = 1
        row_number += 1

    if (col_number == 1) & (row_number == 1):#set the legend for the first subplot, and tehrefore all of the subplots

        #create subplot for this economy
        legend_name = 'Activity'
        fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Year'], y=change_dataframe_aggregation_act_ag_e['Activity'],  legendgroup=legend_name, name=legend_name, line=dict(color='blue', width=2, )), row=row_number, col=col_number, secondary_y=False)

        legend_name = 'Activity_growth'
        fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Year'], y=change_dataframe_aggregation_act_ag_e['Activity_growth'], legendgroup=legend_name, name=legend_name, line=dict(color='red', dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)
    else:#legend is already set, so just add the traces with showlegend=False
        #create subplot for this economy
        legend_name = 'Activity'
        fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Year'], y=change_dataframe_aggregation_act_ag_e['Activity'],  legendgroup=legend_name, name=legend_name,showlegend=False, line=dict(color='blue', width=2, )), row=row_number, col=col_number, secondary_y=False)

        legend_name = 'Activity_growth'
        fig.add_trace(go.Scatter(x=change_dataframe_aggregation_act_ag_e['Year'], y=change_dataframe_aggregation_act_ag_e['Activity_growth'], legendgroup=legend_name, name=legend_name, showlegend=False, line=dict(color='red', dash='dot', width=2)), row=row_number, col=col_number, secondary_y=True)

plotly.offline.plot(fig, filename='./plotting_output/' + title + '.html')
fig.write_image("./plotting_output/static/" + title + '.png', scale=1, width=2000, height=1500)



#%%







# %%
