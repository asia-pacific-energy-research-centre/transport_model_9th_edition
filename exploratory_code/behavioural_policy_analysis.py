#first created to help with producing the OGSS section on behavioural controls and their effect on energy security.
#Topics"
#1. when a car travels at a lower average speed, the wind resistance decreases and therefore the car requires less energy https://www.eea.europa.eu/themes/transport/sl2.jpg/image_preview -  https://www.eea.europa.eu/themes/transport/speed-limits-fuel-consumption-and
    # - In summary, whereas heavy goods vehicles speed limits in motorways are in line with the optimum speed in terms of energy and CO2 reductions per vehicle-km (80–90 km/h), decreasing car passenger speed limits in motorways could lead to substantial benefits.
    # to do this i would need: avg speeds per economy, accurate data on travel km per economy, effect of reduction in speed on efficiency in acutal numbers.
#2. Working from home: By analysing commuter trends and labour market data, we found that if everybody able to work from home worldwide were to do so for just one day a week, it would save around 1% of global oil consumption for road passenger transport per year. https://www.iea.org/commentaries/working-from-home-can-save-energy-and-reduce-emissions-but-how-much
    # -https://www.iea.org/data-and-statistics/charts/average-change-in-energy-demand-and-co2-emissions-from-one-day-of-home-working-for-a-single-household-with-a-car-commute - cool chart
    # - . However, for short commutes by car (less than 6 kilometres in the United States, 3 kilometres in the European Union, and 2 kilometres in China), as well as for those made by public transport, working from home could lead to a small increase in emissions as a result of extra residential energy use.
    # - https://www.iea.org/data-and-statistics/charts/change-in-global-co2-emissions-and-final-energy-consumption-by-fuel-in-the-home-working-scenario
    # - Working from home will normally reduce net energy demand for a household that commutes by car. But for commuters taking public transport, it is likely to increase net energy demand, although regional and seasonal differences are significant. Taking this into account, however, we find that during an average year, the overall energy saved as a result of less commuting is still around four times larger than the increase in residential energy consumption.
#3. car free sundays: - https://blog.gaijinpot.com/tokyos-pedestrians-paradise/
    # - does ginza car free snday have any effect on energy use? i doubt it
#4. incentivise public transport use
    # - cheaper? nz example. There are studies that show that price of transport is not very important to most users, instead it is about convenience and reliability and travel time. https://thespinoff.co.nz/politics/16-05-2022/why-universal-half-price-public-transport-shouldnt-be-made-permanent
    # - other options that have proven value (there are many) https://www.greaterauckland.org.nz/2022/05/12/would-at-rethink-the-eastern-busway/
#5. incentivise micro mobility walkign and biking
    # - bike paths? etc.
    #SKATEBOARDS!
#6. increase occupancy and load factors
    #this we can defs do and show the effects of.
    # rural trips are best to implement car pooling but it is difficult to know the rural split of transport (or at least from what ive seen).
#7. econrouage freight efficiency improvements
#8. incentivise electric vehicles
#9. incentiveise high speed and night trains instead of planes where possible.

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
#compare model output to 8th edition output. If there are any differences, print them
#laod output from 8th edition
model_output = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))
change_dataframe_road = pd.read_csv('intermediate_data/road_model/change_dataframe_aggregation.csv')
change_dataframe_non_road = pd.read_csv('intermediate_data/non_road_model/change_dataframe_aggregation.csv')

#%%
# plot activity growth
a_growth = change_dataframe_road[['Economy', 'Scenario', 'Year', 'Transport Type', 'Activity_growth', 'Activity']].drop_duplicates()


title='Activity growth by year,Scenario, economy,for each transport type'

#plot
fig = px.line(a_growth, x="Year", y="Activity_growth", color="Transport Type", line_dash='Scenario', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles


plotly.offline.plot(fig, filename='./plotting_output/change_dataframe/' + title + '.html')
fig.write_image("./plotting_output/change_dataframe/static/" + title + '.png', scale=1, width=2000, height=800)

################################################################################################################################################################
#%%
#calcualte activity growth from the activity value for each year in case the activity growth isnt being calculated correctly

new_a_growth1 = a_growth[['Economy', 'Scenario', 'Transport Type', 'Year', 'Activity']]
#sum up activity by economy, scenario, transport type
new_a_growth1 = new_a_growth1.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum().reset_index()
#sort values by year
new_a_growth1 = new_a_growth1.sort_values(by=['Economy', 'Scenario', 'Transport Type', 'Year'])

#calc growth rate. set index so that the growth rate is calc only for Value col
new_a_growth2 = new_a_growth1.set_index(['Economy', 'Scenario', 'Transport Type', 'Year']).pct_change().reset_index()

#rename to 'a_growth_recalcualted'
new_a_growth2 = new_a_growth2.rename(columns={'Activity': 'Activity_growth'})

#join back on the absoutle activity growth
new_a_growth = new_a_growth1.merge(new_a_growth2, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')


#before concat we need to sum up activity for each year, economy, scenario, transport type in original df. (but not a_growth, but luckily we can just group by this since it is the same for the categories we need )
a_growth_old = a_growth[['Economy', 'Scenario', 'Transport Type', 'Year', 'Activity_growth', 'Activity']]
a_growth_old = a_growth_old.groupby(['Economy', 'Scenario', 'Transport Type', 'Year', 'Activity_growth']).sum().reset_index()#not 100% it will work

#create label
new_a_growth['dataset'] = 'recalculated'
a_growth_old['dataset'] = 'original'

#concat back into original df
a_growth2 = pd.concat([new_a_growth,a_growth_old])

#join together the transport tyep and scenario cols
a_growth2['TransportType_scenario'] = a_growth2['Transport Type'] + ' ' + a_growth2['Scenario']

#PLOT
title='COMPARISON Activity growth by year,Scenario, economy,for each transport type'

#plot
fig = px.line(a_growth2, x="Year", y="Activity_growth", color="TransportType_scenario", line_dash='dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/change_dataframe/' + title + '.html')
fig.write_image("./plotting_output/change_dataframe/static/" + title + '.png', scale=1, width=2000, height=800)


#PLOT
title='COMPARISON Activity by year,Scenario, economy,for each transport type'

#plot
fig = px.line(a_growth2, x="Year", y="Activity", color="TransportType_scenario", line_dash='dataset', facet_col="Economy", facet_col_wrap=7, title=title)#, #facet_col="Economy",
             #category_orders={"Scenario": ["Reference", "Carbon Neutral"]})
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))#remove 'Economy=X' from titles

plotly.offline.plot(fig, filename='./plotting_output/change_dataframe/' + title + '.html')
fig.write_image("./plotting_output/change_dataframe/static/" + title + '.png', scale=1, width=2000, height=800)
################################################################################################################################################################
#%%

# #take a look at vehicle sales share normalised and see whether it causes activity to grow faster than we intended it to.
# #for simplicity lets jsut look at datafor NZ in scneario = reference.
# change_dataframe_road_nz_ref = change_dataframe_road[(change_dataframe_road['Economy']=='12_NZ') & (change_dataframe_road['Scenario']=='Reference')]

# #filter for only interesting data points
# change_dataframe_road_nz_ref = change_dataframe_road_nz_ref[['Economy', 'Scenario', 'Year', 'Transport Type','Vehicle Type','Drive', 'Activity_growth', 'Activity', 'Original_activity', 'Vehicle_sales_share_normalised', 'New_stock_sales_activity', 'Activity_transport_type_sum', 'Activity_transport_type_growth_abs', 'Vehicle_sales_share_adjusted', 'Vehicle_sales_share_sum' ]]

# #sort by year and transport type
# change_dataframe_road_nz_ref = change_dataframe_road_nz_ref.sort_values(by=['Year', 'Transport Type'])
# #save as csv and look at it
# change_dataframe_road_nz_ref.to_csv('intermediate_data/analysis_single_use/change_dataframe_road_nz_ref.csv', index=False)
# os.startfile(os.path.normpath('intermediate_data/analysis_single_use/change_dataframe_road_nz_ref.csv'))
# %%
