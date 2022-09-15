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

#laod outputs
model_output = pd.read_csv('output_data/model_output_detailed/{}'.format(model_output_file_name))

#filter for 2017 only
model_output = model_output.loc[model_output['Year'] == 2017]

#filter for road only
model_output = model_output.loc[model_output['Medium'] == 'road']
#%%
#calculate average vehicle efficiency
#travel km
#avg commuting distance / total commuting distance
#?average wfh?
#effect of increasing use of public transport options?
#average freight efficiency? eg. average weigth carried per travel km?, therefore how much energy is used and how much less could be used
#avg eff gain from more EVs

#%%
model_output['avg_vehicle_efficiency'] = model_output['Energy'] / model_output['Travel_km'] / model_output['Stocks']

#remove nans in avg vehicle eff for now but maybe we will want to set them to avgs of other eocnomys later
model_output = model_output.loc[model_output['avg_vehicle_efficiency'].notna()] 
#%%
#work from home module )also useful for buildings integration)

#%%