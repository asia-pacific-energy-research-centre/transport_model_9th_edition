#calcaulte oil displacement from evs and fcevs. This can be done by recalculating the oil use if fcevs and/or evs werent used. THis will jsut be efficiency * miles driven * number of cars.
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'/transport_model_9th_edition')
from runpy import run_path
FILE_DATE_ID = '_20230610'
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%
import plotly
import plotly.express as px

import plotly.graph_objects as go
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import time
import itertools
AUTO_OPEN_PLOTLY_GRAPHS = True
dont_overwrite_existing_graphs = False
plot_png = False
plot_html = True
subfolder_name = 'all_economy_graphs'
default_save_folder = f'plotting_output/oil_displacement/{FILE_DATE_ID}/'
#CHECK THAT SAVE FOLDER EXISTS, IF NOT CREATE IT
if not os.path.exists(default_save_folder):
    os.makedirs(default_save_folder)
    
#%%

model_output_detailed = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))

#create regions dataset and then concat that on with regions = Economy. so that we can plot regions too.
region_economy_mapping = pd.read_csv('./config/concordances_and_config_data/region_economy_mapping.csv')

#%%
#join with model_output_detailed_APEC.
#where there is no region drop the row since we are just plotting singular economies atm
model_output_detailed_regions = model_output_detailed.merge(region_economy_mapping[['Region', 'Economy']].drop_duplicates(), how='left', left_on='Economy', right_on='Economy')
#%%
# model_output_detailed_regions['Region'] = model_output_detailed_regions['Region'].fillna(model_output_detailed_regions['Economy'])
model_output_detailed_regions = model_output_detailed_regions.dropna(subset=['Region'])
#then sum up stocks, and average out efficiency, occupancy, mileage
model_output_detailed_regions = model_output_detailed_regions.groupby(['Date', 'Region', 'Medium', 'Transport Type', 'Scenario', 'Drive', 'Vehicle Type']).agg({'Stocks': 'sum', 'Efficiency': 'mean', 'Occupancy_or_load': 'mean', 'Mileage': 'mean'}).reset_index()

#set Region to Economy
model_output_detailed_regions['Economy'] = model_output_detailed_regions['Region']
model_output_detailed_regions = model_output_detailed_regions.drop(columns=['Region'])
#now concat this to model_output_detailed but keep only the cols in model_output_detailed_regions
model_output_detailed = pd.concat([model_output_detailed[model_output_detailed_regions.columns], model_output_detailed_regions], ignore_index=True)
#%%
###################
AUTO_OPEN_PLOTLY_GRAPHS = False
#map vtypes to colors and associated opacity
#vtyes: ['all', 'ht', 'ldv', '2w', 'bus']
color_map = {
    'ht': 'rgba(0, 128, 0, 0.2)', # dark green
    'mt': 'rgba(0, 255, 0, 0.2)', # green
    'lcv': 'rgba(144, 238, 144, 0.2)', # light green
    
    'lt': 'rgba(128, 0, 128, 0.2)',   # purple
    'car': 'rgba(0, 0, 255, 0.2)', # blue
    'suv': 'rgba(0, 153, 255, 0.2)', # light blue
    
    '2w': 'rgba(255, 0, 0, 0.2)', # red
    'bus': 'rgba(255, 165, 0, 0.2)'   # orange
}

#so for every econoy and transport type we will do this plot. Also we will do it for fcevs
for economy in model_output_detailed.Economy.unique():
    for t_type in model_output_detailed['Transport Type'].unique():
        for scenario in model_output_detailed.Scenario.unique():
            #to mkae this easier to write we will jsut do the fcev and bev graphs separately rather than iterating over the drive

            plotting_data = model_output_detailed.copy()
            plotting_data = plotting_data[plotting_data['Economy']==economy]
            plotting_data = plotting_data[plotting_data['Transport Type']==t_type]
            plotting_data = plotting_data[plotting_data['Scenario']==scenario]
            #filter for only road
            plotting_data = plotting_data[plotting_data['Medium']=='road']
            #drop those cols
            plotting_data = plotting_data.drop(columns=['Medium', 'Transport Type', 'Scenario', 'Economy'])
            #now do the oil displacement calcualtions
            ##############################################
            #DO SEP PLOT FOR EACH DRIVE TYPE IN BEV AND FCEV
            ##############################################
            breakpoint()
            ice_bev = plotting_data.copy()
            ice = ice_bev[ice_bev['Drive'].isin(['ice_g', 'ice_d'])]
            #grab avg of Efficiency Occupancy_or_load and Mileage and the sum of stocks
            ice = ice.groupby(['Date', 'Vehicle Type']).agg({'Efficiency': 'mean', 'Occupancy_or_load': 'mean', 'Mileage': 'mean', 'Stocks': 'sum'}).reset_index()
            #set Drive to ice
            ice['Drive'] = 'ice'
            #sum or avg ice values
            bev = ice_bev[ice_bev['Drive']=='bev']#later this willprobably need to include phev
            #join
            index_cols = ['Date', 'Vehicle Type']
            ice_bev = pd.merge(ice, bev, on=index_cols, suffixes=('_ice', '_bev'))
            #now we have the data we can calculate oil use.

            # get vehicle types
            v_types = ice_bev['Vehicle Type'].unique()
            #########################WARNING 
            #set efficiency for ice to 0.5 and efficiency for bev to 1. just for testign
            # ice_bev = ice_bev.assign(Efficiency_ice = 0.5)
            # ice_bev = ice_bev.assign(Efficiency_bev = 1)
            #########################WARNING 

            #oil use = efficiency * mileage * stocks
            ice_bev = ice_bev.assign(Oil_displacement = (ice_bev['Mileage_bev'] * ice_bev['Stocks_bev'])/ice_bev['Efficiency_ice'])
            ice_bev = ice_bev.assign(Energy_bev = (ice_bev['Mileage_bev'] * ice_bev['Stocks_bev'])/ice_bev['Efficiency_bev'])
            #note that we are using the mileage of bevs isteadn of ices. THis is probably not necessary to state as an assumption 
            #to make it easy to plot we want to pivot so we have the energy use of each vehicle type as a column for each other index col
            #so firt filter for only energy
            ice_bev = ice_bev[index_cols + ['Oil_displacement', 'Energy_bev']]
            #pivot vehile type so we have suffixes to determin which is which
            index_cols.remove('Vehicle Type')
            ice_bev = ice_bev.pivot(index=index_cols, columns='Vehicle Type', values=['Oil_displacement', 'Energy_bev'])
            #take away
            v_types = ice_bev.columns.get_level_values(1).unique()
            for v_type in v_types:
                ice_bev[('Difference', v_type)] = ice_bev[('Oil_displacement', v_type)] - ice_bev[('Energy_bev', v_type)]
            #calculate total of oiol diaplcement and total of enrgybev
            ice_bev = ice_bev.assign(Total_oil_displacement = ice_bev['Oil_displacement'].sum(axis=1))
            ice_bev = ice_bev.assign(Total_energy_bev = ice_bev['Energy_bev'].sum(axis=1))

            # #if any differences arent positive then tell the user and skip
            # if any(ice_bev['Difference']<0):
            #     print('negative difference for {}'.format((economy, t_type, scenario, 'bev')))
            #     continue

            ############plotting

            fig = go.Figure()
            # first, an empty space
            fig.add_trace(go.Scatter(
                x=ice_bev.index,
                y=ice_bev['Total_energy_bev'],
                mode='lines',
                line_color='rgba(255, 255, 255, 0)',
                name='',
                stackgroup='one'  #this is necessary for the next traces to stack on top of this one
            ))
            # then, for each vehicle type, plot an area chart for the difference
            for v_type in v_types:
                fig.add_trace(go.Scatter(
                    x=ice_bev.index,
                    y=ice_bev[('Difference', v_type)],
                    mode='none', # we don't want lines for individual vehicle types
                    fill='tonexty', # fill to next y value
                    fillcolor=color_map[v_type], 
                    #set opacity to 0.5
                    opacity=0.01,
                    name=f'Oil displacement - {v_type}',
                    stackgroup='one',  #this will stack the areas on top of each other                    
                    hovertemplate=f'{v_type}'+'<br>%{y:.0f}PJ oil displaced'
                ))
            #removed oil displaceemtn line beecause it didnt seem useful
            # # finally, plot the 'Total_oil_displacement' line
            # fig.add_trace(go.Scatter(
            #     x=ice_bev.index,
            #     y=ice_bev['Total_oil_displacement'],
            #     mode='lines',
            #     line_color='Black',
            #     name='Oil displacement'
            # ))
            # finally, plot the 'Total_energy_bev' line
            fig.add_trace(go.Scatter(
                x=ice_bev.index,
                y=ice_bev['Total_energy_bev'],
                mode='lines',
                line_color='Green',
                name='BEV energy use'
            ))
            #add a y axis label
            fig.update_yaxes(title_text='PJ')
            fig.update_layout(title=f'Oil displacement for {t_type} in {economy} in {scenario} (BEV)')
            
            fig.write_html(f'{default_save_folder}/oil_displacement_{t_type}_{economy}_bev_{scenario}.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)


            ####################
            #FCEV:

            
            ice_fcev = plotting_data.copy()
            
            fcev = ice_fcev[ice_fcev['Drive']=='fcev']#later this willprobably need to include phev
            ice = ice_fcev[ice_fcev['Drive'].isin(['ice_g', 'ice_d'])]
            #grab avg of Efficiency Occupancy_or_load and Mileage and the sum of stocks
            ice = ice.groupby(['Date', 'Vehicle Type']).agg({'Efficiency': 'mean', 'Occupancy_or_load': 'mean', 'Mileage': 'mean', 'Stocks': 'sum'}).reset_index()
            #set Drive to ice
            ice['Drive'] = 'ice'
            
            #join
            index_cols = ['Date', 'Vehicle Type']
            ice_fcev = pd.merge(ice, fcev, on=index_cols, suffixes=('_ice', '_fcev'))
            #now we have the data we can calculate oil use.
            
            # get vehicle types
            v_types = ice_fcev['Vehicle Type'].unique()
            #########################WARNING 
            #set efficiency for ice to 0.5 and efficiency for fcev to 1. just for testign
            # ice_fcev = ice_fcev.assign(Efficiency_ice = 0.5)
            # ice_fcev = ice_fcev.assign(Efficiency_fcev = 1)
            #########################WARNING 

            #oil use = efficiency * mileage * stocks
            ice_fcev = ice_fcev.assign(Oil_displacement = (ice_fcev['Mileage_fcev'] * ice_fcev['Stocks_fcev'])/ice_fcev['Efficiency_ice'])
            ice_fcev = ice_fcev.assign(Energy_fcev = (ice_fcev['Mileage_fcev'] * ice_fcev['Stocks_fcev'])/ice_fcev['Efficiency_fcev'])
            #note that we are using the mileage of fcevs isteadn of ices. THis is probably not necessary to state as an assumption 
            #to make it easy to plot we want to pivot so we have the energy use of each vehicle type as a column for each other index col
            #so firt filter for only energy
            ice_fcev = ice_fcev[index_cols + ['Oil_displacement', 'Energy_fcev']]
            #pivot vehile type so we have suffixes to determin which is which
            index_cols.remove('Vehicle Type')
            ice_fcev = ice_fcev.pivot(index=index_cols, columns='Vehicle Type', values=['Oil_displacement', 'Energy_fcev'])
            #take away
            v_types = ice_fcev.columns.get_level_values(1).unique()
            for v_type in v_types:
                ice_fcev[('Difference', v_type)] = ice_fcev[('Oil_displacement', v_type)] - ice_fcev[('Energy_fcev', v_type)]
            #calculate total of oiol diaplcement and total of enrgyfcev
            ice_fcev = ice_fcev.assign(Total_oil_displacement = ice_fcev['Oil_displacement'].sum(axis=1))
            ice_fcev = ice_fcev.assign(Total_energy_fcev = ice_fcev['Energy_fcev'].sum(axis=1))

            #if any differences are positive then tell the user and skip because this is not expected as fcev should be more efficient
            # if any(ice_fcev['Difference']<0):
            #     print('negative difference for {}'.format((economy, t_type, scenario, 'fcev')))
            #     continue

            ############plotting
            

            fig = go.Figure()
            # first, an empty space
            fig.add_trace(go.Scatter(
                x=ice_fcev.index,
                y=ice_fcev['Total_energy_fcev'],
                mode='lines',
                line_color='rgba(255, 255, 255, 0)',
                name='',
                stackgroup='one'  #this is necessary for the next traces to stack on top of this one
            ))
            # then, for each vehicle type, plot an area chart for the difference
            for v_type in v_types:
                fig.add_trace(go.Scatter(
                    x=ice_fcev.index,
                    y=ice_fcev[('Difference', v_type)],
                    mode='none', # we don't want lines for individual vehicle types
                    fill='tonexty', # fill to next y value
                    fillcolor=color_map[v_type], 
                    #set opacity to 0.5
                    opacity=0.2,
                    name=f'Oil displacement - {v_type}',
                    stackgroup='one',  #this will stack the areas on top of each other                    
                    hovertemplate=f'{v_type}'+'<br>%{y:.0f}PJ oil displaced'
                ))
            # # finally, plot the 'Total_oil_displacement' line
            # fig.add_trace(go.Scatter(
            #     x=ice_fcev.index,
            #     y=ice_fcev['Total_oil_displacement'],
            #     mode='lines',
            #     line_color='Black',
            #     name='Oil displacement'
            # ))
            # finally, plot the 'Total_energy_fcev' line
            fig.add_trace(go.Scatter(
                x=ice_fcev.index,
                y=ice_fcev['Total_energy_fcev'],
                mode='lines',
                line_color='Green',
                name='FCEV energy use'
            ))
            #add a y axis label
            fig.update_yaxes(title_text='PJ')
            #give it a title:
            fig.update_layout(title=f'Oil displacement for {t_type} in {economy} in {scenario} (FCEV)')
            fig.write_html(f'{default_save_folder}/oil_displacement_{t_type}_{economy}_fcev_{scenario}.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)
            breakpoint()




#%%











# #%%
# # Assuming you have a dataframe ice_bev with columns 'date', 'quantity1', 'quantity2' and 'category'
# AUTO_OPEN_PLOTLY_GRAPHS =True
# ice_bev = ice_bev.copy()
# #grab datga for only 20_USA, transprot type = passenger, medium = road
# ice_bev = ice_bev[ice_bev['Transport Type']=='passenger']
# ice_bev = ice_bev[ice_bev['Medium']=='road']
# ice_bev = ice_bev[ice_bev['Economy']=='20_USA']
# #scenario = reference
# ice_bev = ice_bev[ice_bev['Scenario']=='Reference']
# #data for 2019 +
# ice_bev = ice_bev[ice_bev['Date']>=2019]

# # Filter data for each category
# v_type = ice_bev['Vehicle Type'].unique()
# fig = go.Figure()

# for v in v_type:
#     ice_bev_plot = ice_bev[ice_bev['Vehicle Type'] == v]

#     fig.add_trace(go.Scatter(
#         x=ice_bev_plot['Date'], 
#         y=ice_bev_plot['Oil_displacement'],
#         fill=None,
#         mode='lines',
#         line_color='blue',
#         name=f'{v} Oil_displacement'
#     ))
    
#     fig.add_trace(go.Scatter(
#         x=ice_bev_plot['Date'], 
#         y=ice_bev_plot['Energy_bev'],
#         fill='tonexty', # fill area between line
#         mode='lines',
#         line_color='red',
#         name=f'{v} Energy'
#     ))

# #plot as html
# fig.write_html(f'{default_save_folder}/oil_displacement.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)


# # %%

# AUTO_OPEN_PLOTLY_GRAPHS=True
# import plotly.graph_objects as go

# # assuming you have a color map for each vehicle type
# # color_map = {'2w': 'blue', 'ldv': 'green', 'bus': 'red'}  # replace with your actual vehicle types and desired colors
# #repalce color map with hex codes
# blue = '#1f77b4'
# green = '#2ca02c'
# red = '#d62728'
# color_map = {'2w': blue, 'ldv': green, 'bus': red}  # replace with your actual vehicle types and desired colors

# # Filter data for each category
# v_type = ice_bev['Vehicle Type'].unique()
# fig = go.Figure()

# # first, plot the 'Oil_displacement' line
# fig.add_trace(go.Scatter(
#     x=ice_bev['Date'],
#     y=ice_bev['Oil_displacement'],
#     line_color='blue',
#     name='Oil_displacement'
# ))

# # then, for each vehicle type, plot an area chart
# for v in v_type:
#     ice_bev_plot = ice_bev[ice_bev['Vehicle Type'] == v]

#     fig.add_trace(go.Scatter(
#         x=ice_bev_plot['Date'], 
#         y=ice_bev_plot['Energy_bev'],
#         fill='tonexty', # fill area between line
#         mode='none',  # we don't want lines for individual vehicle types
#         fillcolor=color_map[v],  # use vehicle type color with 50% opacity
#         name=v,
#         hoverinfo='skip'  # we don't want hover info for individual vehicle types
#     ))

# # finally, plot the 'Energy_ice' line
# fig.add_trace(go.Scatter(
#     x=ice_bev['Date'],
#     y=ice_bev['Energy_bev'],
#     line_color='red',
#     name='Energy_ice'
# ))

# # plot as html
# fig.write_html(f'{default_save_folder}/oil_displacement.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)

# # %%


# import plotly.graph_objects as go


# AUTO_OPEN_PLOTLY_GRAPHS =True
# ice_bev = ice_bev.copy()
# ice_bev = ice_bev.reset_index()
# #grab datga for only 20_USA, transprot type = passenger, medium = road
# ice_bev = ice_bev[ice_bev['Transport Type']=='passenger']
# ice_bev = ice_bev[ice_bev['Medium']=='road']
# ice_bev = ice_bev[ice_bev['Economy']=='20_USA']
# #scenario = reference
# ice_bev = ice_bev[ice_bev['Scenario']=='Reference']
# #data for 2019 +
# ice_bev = ice_bev[ice_bev['Date']>=2019]

# # assuming you have a color map for each vehicle typeblue = '#1f77b4'
# green = '#2ca02c'
# red = '#d62728'
# color_map = {'2w': blue, 'ldv': green, 'bus': red}  # replace with your actual vehicle types and desired colors

# # get vehicle types
# v_types = ['2w', 'bus', 'ldv']

# fig = go.Figure()

# # first, plot the 'Total_oil_displacement' line
# fig.add_trace(go.Scatter(
#     x=ice_bev.index,
#     y=ice_bev['Total_oil_displacement'],
#     mode='lines',
#     line_color='blue',
#     name=''
# ))

# # then, for each vehicle type, plot an area chart for the difference
# for v_type in v_types:
#     fig.add_trace(go.Scatter(
#         x=ice_bev.index,
#         y=ice_bev[('Difference', v_type)],
#         mode='none',  # we don't want lines for individual vehicle types
#         fill='tozeroy',  # fill to zero
#         fillcolor=color_map[v_type],  # use vehicle type color with 50% opacity
#         name=f'Difference {v_type}',
#         stackgroup='one',  # stack area charts
#     ))

# # finally, plot the 'Total_energy_bev' line
# fig.add_trace(go.Scatter(
#     x=ice_bev.index,
#     y=ice_bev['Total_energy_bev'],
#     mode='lines',
#     line_color='red',
#     name='Total Energy BEV'
# ))

# fig.write_html(f'{default_save_folder}/oil_displacement.html', auto_open=AUTO_OPEN_PLOTLY_GRAPHS)

# # %%







# import plotly.graph_objects as go


# AUTO_OPEN_PLOTLY_GRAPHS =True
# ice_bev = ice_bev.copy()
# ice_bev = ice_bev.reset_index()
# #grab datga for only 20_USA, transprot type = passenger, medium = road
# ice_bev = ice_bev[ice_bev['Transport Type']=='passenger']
# ice_bev = ice_bev[ice_bev['Medium']=='road']
# ice_bev = ice_bev[ice_bev['Economy']=='20_USA']
# #scenario = reference
# ice_bev = ice_bev[ice_bev['Scenario']=='Reference']
# #data for 2019 +
# ice_bev = ice_bev[ice_bev['Date']>=2019]

# #make the differences postivie
# ice_bev['Difference'] = ice_bev['Difference'].abs()

# # assuming you have a color map for each vehicle typeblue = '#1f77b4'
# green = '#2ca02c'
# red = '#d62728'
# color_map = {'2w': blue, 'ldv': green, 'bus': red}  # replace with your actual vehicle types and desired colors

# # get vehicle types
# v_types = ['2w', 'bus', 'ldv']

# fig = go.Figure()

# # first, plot the 'Total_oil_displacement' line
# fig.add_trace(go.Scatter(
#     x=ice_bev.index,
#     y=ice_bev['Total_oil_displacement'],
#     mode='lines',
#     line_color='blue',
#     name=''
# ))

# # plot a transparent area chart for 'Total_energy_bev'
# fig.add_trace(go.Scatter(
#     x=ice_bev.index,
#     y=ice_bev['Total_energy_bev'],
#     mode='none',
#     fill='tozeroy',
#     fillcolor='rgba(0,0,0,0)'  # transparent
# ))

# # then, for each vehicle type, plot an area chart for the difference
# for v_type in v_types:
#     fig.add_trace(go.Scatter(
#         x=ice_bev.index,
#         y=ice_bev[('Difference', v_type)],
#         mode='none',  # we don't want lines for individual vehicle types
#         fill='tonexty',  # fill to next y value
#         fillcolor=color_map[v],  # use vehicle type color with 50% opacity
#         name=f'Difference {v_type}'
#     ))

# # finally, plot the 'Total_energy_bev' line
# fig.add_trace(go.Scatter(
#     x=ice_bev.index,
#     y=ice_bev['Total_energy_bev'],
#     mode='lines',
#     line_color='red',
#     name='Total Energy BEV'
# ))

# fig.show()


# #%%










# import plotly.graph_objects as go
# ice_bev = ice_bev.copy()
# ice_bev = ice_bev.reset_index()
# #grab datga for only 20_USA, transprot type = passenger, medium = road
# ice_bev = ice_bev[ice_bev['Transport Type']=='passenger']
# ice_bev = ice_bev[ice_bev['Medium']=='road']
# ice_bev = ice_bev[ice_bev['Economy']=='20_USA']
# #scenario = reference
# ice_bev = ice_bev[ice_bev['Scenario']=='Reference']
# #data for 2019 +
# ice_bev = ice_bev[ice_bev['Date']>=2019]

# #make the differences postivie
# ice_bev['Difference'] = ice_bev['Difference'].abs()

# # assuming you have a color map for each vehicle typeblue = '#1f77b4'
# green = '#2ca02c'
# red = '#d62728'
# color_map = {'2w': blue, 'ldv': green, 'bus': red}  # replace with your actual vehicle types and desired colors

# # get vehicle types
# v_types = ['2w', 'bus', 'ldv']

# fig = go.Figure()

# fig.add_trace(go.Scatter(
#     x=ice_bev.index,
#     y=ice_bev['Total_energy_bev'],
#     fill='tozeroy',
#     fillcolor='rgba(255, 255, 255, 0)',  # completely transparent
#     line=dict(width=0),  # no line
# ))
# # first, plot the 'Total_energy_bev' line
# fig.add_trace(go.Scatter(
#     x=ice_bev.index,
#     y=ice_bev['Total_energy_bev'],
#     mode='lines',
#     line_color='red',
#     name='Total Energy BEV',
#     stackgroup='one'  # this is necessary for the next traces to stack on top of this one
# ))

# # then, for each vehicle type, plot an area chart for the difference
# for v_type in v_types:
#     fig.add_trace(go.Scatter(
#         x=ice_bev.index,
#         y=ice_bev[('Difference', v_type)],
#         mode='none',  # we don't want lines for individual vehicle types
#         fill='tonexty',  # fill to next y value
#         fillcolor=color_map[v_type],  # use vehicle type color with 50% opacity
#         name=f'Difference {v_type}',
#         stackgroup='one'  # this will stack the areas on top of each other
#     ))

# # finally, plot the 'Total_oil_displacement' line
# fig.add_trace(go.Scatter(
#     x=ice_bev.index,
#     y=ice_bev['Total_oil_displacement'],
#     mode='lines',
#     line_color='blue',
#     name=''
# ))

# fig.show()

# # %%



