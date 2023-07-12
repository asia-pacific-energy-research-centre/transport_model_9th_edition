#we will always have issues with esto energy not matching expected enrgy because of the way we calculate energy from stocks and activity. so create graphs to compare the two. Since ESTO energy is for only a few years that we have model data for, we should compare it suing something different ot a line graph i think.
#%%
#aslo note that esto data is by medium. i think it ha road split into freight and passenger transport types too.
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
import sys
sys.path.append("./workflow")
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'


import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
import plotly.io as pio
import utility_functions
#do a bar chart faceted by  medium and transport type. x axis is year and source. y axis is energy?

#find latest date for our energy data that was cleaned in transpoirt data system:
date_id = utility_functions.get_latest_date_for_data_file('../transport_data_system/intermediate_data/EGEDA/', 'model_input_9th_cleaned')
energy_use_esto = pd.read_csv(f'../transport_data_system/intermediate_data/EGEDA/model_input_9th_cleanedDATE{date_id}.csv')


original_model_output_with_fuels = pd.read_csv('output_data/model_output_with_fuels/{}'.format(model_output_file_name))#cols 	Date	Economy	Scenario	Transport Type	Vehicle Type	Drive	Medium	Fuel	Energy
#grab scenario only = Reference
original_model_output_with_fuels = original_model_output_with_fuels[original_model_output_with_fuels['Scenario'] == 'Reference']

#%%
# cols: ['Economy', 'Fuel_Type', 'Date', 'Value', 'Transport Type', 'Frequency','Unit', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive','Medium']

#TRANSPORT EGEDA
#LETS DO A FULL ANALYSIS OF HOW ENERGY USE IS CORRELATED WITH THE GROWTH RATES LIEK ABOVE, SINCE WE HAVE ENEGRY USE FOR HISTORICAL DATA.
#we will just grab '19 Total' for now
energy_use = energy_use_esto[energy_use_esto['Fuel_Type'] == '19_total']
#%%
#double check that the sum of medium=nan is equal to the sum of all the other mediums
# energy_use[energy_use['Medium'].isna()]['Value'].sum() == energy_use[energy_use['Medium'].notna()]['Value'].sum()#True
#filter for medium = nan
# energy_use = energy_use[energy_use['Medium'].isna()]
#rename where medium = nan to 'Total'
energy_use.loc[energy_use['Medium'].isna(), 'Medium'] = 'Total'
#drop nonneeded cols
energy_use = energy_use.drop(columns=['Fuel_Type', 'Frequency', 'Source', 'Dataset', 'Measure', 'Vehicle Type', 'Drive', 'Transport Type', 'Unit'])
# #pivot so we have a column for each medium
# energy_use = energy_use.pivot(index=['Economy', 'Date'], columns='Medium', values='Value').reset_index()
#while we are analysing medium we shjould also not aggregate into reigons, as certain economys focus on certain mediums more

#reformat date to be in year only
energy_use['Date'] = energy_use['Date'].apply(lambda x: x[:4])
#make into int
energy_use['Date'] = energy_use['Date'].astype(int)
#rename Value to energy
energy_use = energy_use.rename(columns={'Value': 'Energy'})
#%%
#sum original_model_output_with_fuels by Date	Economy	Scenario	Medium
original_model_output_with_fuels = original_model_output_with_fuels.groupby(['Date', 'Economy', 'Medium']).sum().reset_index()

#%%
#extract only similar Dates
original_model_output_with_fuels = original_model_output_with_fuels[original_model_output_with_fuels['Date'].isin(energy_use['Date'].unique())]
energy_use = energy_use[energy_use['Date'].isin(original_model_output_with_fuels['Date'].unique())]
#keep only data after 2015
original_model_output_with_fuels = original_model_output_with_fuels[original_model_output_with_fuels['Date'] >= 2015]
#%%
#conat:
original_model_output_with_fuels['origin'] = 'model'
energy_use['origin'] = 'esto'
#conat them
original_model_output_with_fuels = pd.concat([original_model_output_with_fuels, energy_use])
for economy in original_model_output_with_fuels['Economy'].unique():
    #by economy create a line chart of energy use. make the color the origin, the line dash the origin and facet the medium
    title = f'Line chart of energy use by medium for {economy} - model vs esto'
    fig = px.line(original_model_output_with_fuels[original_model_output_with_fuels['Economy'] == economy], x='Date', y='Energy', color='origin', facet_col='Medium', facet_col_wrap=2, line_dash='origin', title=title, markers=True)
    fig.write_html(f'plotting_output/diagnostics/esto_vs_model_energy_use/{title}.html')
    

#by economy create a line chart of energy use. make the color the origin, the line dash the origin and facet the medium
title = 'Line chart of energy use by medium for each economy - model vs esto'
fig = px.line(original_model_output_with_fuels, x='Date', y='Energy', color='Medium', facet_col='Economy', facet_col_wrap=3, line_dash='origin', title=title, markers=True)
fig.write_html(f'plotting_output/diagnostics/esto_vs_model_energy_use/{title}.html')
#%%