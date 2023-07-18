# d:\APERC\PyLMDI\saved_runs\transport_8th_analysis.py
#run the PyLMDI functiosn to produce LMDI graphs of the results. 
#note that the library is in ../PyLMDI

#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'/transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

import plotly
import plotly.express as px
pd.options.plotting.backend = "plotly"#set pandas backend to plotly plotting instead of matplotlib
from plotly.subplots import make_subplots
import plotly.io as pio
import pandas as pd

import sys
sys.path.append("../PyLMDI")
#PyLMDI functions:
import main_function
import plot_output
import data_creation_functions
import LMDI_functions


#%%

def produce_lots_of_LMDI_charts(USE_LIST_OF_CHARTS_TO_PRODUCE = False, PLOTTING = False, USE_LIST_FOR_DATASETS_TO_PRODUCE=False):
    #take in energy and activity data 
    all_data = pd.read_csv('output_data/model_output/{}'.format(model_output_file_name))

    #here write the charts you want to produce.. can use this to make the function run quicker by only producing some of the charts
    if USE_LIST_OF_CHARTS_TO_PRODUCE:
        charts_to_produce = []
        for scenario in all_data.Scenario.unique():
            for transport_type in all_data['Transport Type'].unique():
                for economy in all_data.Economy.unique():
                    charts_to_produce.append(f'{economy}_{scenario}_{transport_type}_road_2_Energy use_Hierarchical')
                    charts_to_produce.append(f'{economy}_{scenario}_{transport_type}__2_Energy use_Hierarchical')
                    
    # #simplify by filtering for road medium only
    # all_data = all_data[all_data['Medium'] == 'road']
    #make drive and vehicle type = medium where it is no road
    temp = all_data.loc[all_data['Medium'] != 'road'].copy()
    temp['Drive'] = temp['Medium']
    temp['Vehicle Type'] = temp['Medium']
    all_data.loc[all_data['Medium'] != 'road'] = temp
    #filter for Date >= OUTLOOK_BASE_YEAR
    all_data = all_data[all_data['Date']>=OUTLOOK_BASE_YEAR]
    #and filter so data is less than GRAPHING_END_YEAR
    all_data = all_data[all_data['Date']<=GRAPHING_END_YEAR]
    #drop Stocks col
    all_data = all_data.drop(columns = ['Stocks'])
    #create an emissions col and fill it with 0's for now
    all_data['Emissions'] = 0

    #drop nans?
    all_data = all_data.dropna()

    #create a 'APEC' economy which is the sum of all and concat it on:
    APEC = all_data.copy()
    #set economy to APEC
    APEC['Economy'] = 'APEC'
    APEC.groupby(['Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Drive', 'Medium']).sum(numeric_only=True).reset_index()

    #concat APEC on
    all_data = pd.concat([all_data, APEC])

    #load data in

    ###########################################################################

    #we will create a script which will loop through the different combinations of data we have and run the LMDI model on them and plot them

    AUTO_OPEN = False

    better_names_dict = {'Drive': 'Engine type'}
    #before going through the data lets rename some structural variables to be more readable
    all_data = all_data.rename(columns=better_names_dict)

    combination_dict_list = []
    #instead of specifiying them manually which is quite repetivitve i am going to create the combinations for wehich we want to run the lmdi method and its graphing functions in a loop by creating a set of different values for each of the variables in the dictionary and then looping through all the combinations of these values to create a permutation of each of the combinations. In some cases there will need to be some extra logic because some values can only go with each other. 
    scenario_list = ['Reference', 'Target']
    transport_type_list = ['passenger', 'freight']
    medium_list = ['everything', 'road']
    structure_variables_list = [['Economy','Vehicle Type', 'Engine type'],['Vehicle Type', 'Engine type'], ['Engine type']]
    emissions_divisia_list = [False]#, True]#no emissions calcualted yet
    hierarchical_list = [False, True]
    economy_list = all_data.Economy.unique()
    for scenario in scenario_list:
        if scenario == 'Reference':
            scenario_text = 'REF'
        elif scenario == 'Target':
            scenario_text = 'TGT'

        for transport_type in transport_type_list:
            if transport_type == 'passenger':
                activity_variable = 'passenger_km'
            elif transport_type == 'freight':
                activity_variable = 'freight_tonne_km'

            for medium in medium_list:
                if medium == 'everything':
                    medium = ''
                for structure_variables in structure_variables_list:
                    residual_variable1 = '{} efficiency'.format(structure_variables[-1])
                    for emissions_divisia in emissions_divisia_list:
                        emissions_string = 'Energy use'
                        if emissions_divisia == True:
                            emissions_string = 'Emissions'
                            
                        for hierarchical in hierarchical_list:
                            hierarchical_string = '' 
                            if hierarchical == True:
                                hierarchical_string = 'Hierarchical'                          
                                if len(structure_variables) == 1:
                                    continue#hierarchical only for more than one structure variable
                            else:
                                if len(structure_variables) > 1:
                                    continue
                                    # print('hierarchical shoudl almost always be used where there is more than one structure variable, so the graphing tools are not built to handle this case since each residual efficiency value wont have the correct labels')
                            for economy in economy_list:
                                extra_identifier = '{}_{}_{}_{}_{}_{}_{}'.format(economy,scenario_text, transport_type, medium, len(structure_variables),emissions_string, hierarchical_string)
                                graph_title = '{} {} {} - Drivers of changes in {} ({}) - {} LMDI'.format(economy, medium, transport_type,emissions_string, scenario_text, hierarchical_string)

                                combination_dict_list.append({'economy':economy,'scenario':scenario, 'transport_type':transport_type, 'medium':medium, 'activity_variable':activity_variable, 'structure_variables_list':structure_variables, 'graph_title':graph_title, 'extra_identifier':extra_identifier, 'emissions_divisia':emissions_divisia, 'hierarchical':hierarchical, 'residual_variable1':residual_variable1})





    #create loop to run through the combinations
    i=0
    for combination_dict in combination_dict_list:
        if combination_dict['scenario'] == 'Target':
            breakpoint()
                
        if USE_LIST_OF_CHARTS_TO_PRODUCE and combination_dict['extra_identifier'] not in charts_to_produce and USE_LIST_FOR_DATASETS_TO_PRODUCE:
            continue
        # if combination_dict['hierarchical'] == False:
        #     #next
        #     continue
        i+=1
        print('\n\nRunning lmdi method for {}th iteration for '.format(i,combination_dict['extra_identifier']))

        #create a dataframe for each combination
        data = all_data.copy()
        #filter data by scenario
        data = data[data['Scenario']==combination_dict['scenario']]
        #filter data by economy
        economy = combination_dict['economy']
        data = data[data['Economy']==combination_dict['economy']]
        #filter data by transport type
        data = data[data['Transport Type']==combination_dict['transport_type']]
        #filter data by medium
        if combination_dict['medium'] == 'road':
            data = data[data['Medium']==combination_dict['medium']]
        else:
            pass

        structure_variables_list = combination_dict['structure_variables_list']
        #sum the data
        data = data.groupby(['Date']+structure_variables_list).sum(numeric_only=True).reset_index()

        #Separate energy and activity data
        energy_data = data[['Date','Energy']+structure_variables_list]
        activity_data = data[['Date', 'Activity']+structure_variables_list]
        emissions_data = data[['Date',  'Emissions']+structure_variables_list]
        #rename activity with variable
        activity_data = activity_data.rename(columns={'Activity':combination_dict['activity_variable']})

        #set variables to input into the LMDI function
        activity_variable = combination_dict['activity_variable']
        structure_variables_list = combination_dict['structure_variables_list']
        graph_title = combination_dict['graph_title']
        extra_identifier = combination_dict['extra_identifier']
        data_title = ''
        energy_variable = 'Energy'
        time_variable = 'Date'
        font_size=25
        y_axis_min_percent_decrease=0.1
        residual_variable1=combination_dict['residual_variable1']
        emissions_divisia = combination_dict['emissions_divisia']
        hierarchical = combination_dict['hierarchical']

        output_data_folder=f'./intermediate_data/LMDI/{economy}/' 
        plotting_output_folder=f'plotting_output/LMDI/{economy}/'
        #check the folders exist:
        if not os.path.exists(output_data_folder):
            os.makedirs(output_data_folder)
        if not os.path.exists(plotting_output_folder):
            os.makedirs(plotting_output_folder)
            
        #run LMDI
        main_function.run_divisia(data_title, extra_identifier, activity_data, energy_data, structure_variables_list, activity_variable, emissions_variable = 'Emissions', energy_variable = energy_variable, emissions_divisia = emissions_divisia, emissions_data=emissions_data, time_variable=time_variable,hierarchical=hierarchical,output_data_folder=output_data_folder)
        
        if USE_LIST_OF_CHARTS_TO_PRODUCE and combination_dict['extra_identifier'] not in charts_to_produce:
            continue
        if PLOTTING:
            #plot LMDI
            plot_output.plot_additive_waterfall(data_title, extra_identifier, structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size, y_axis_min_percent_decrease=y_axis_min_percent_decrease,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical,output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder)

            plot_output.plot_multiplicative_timeseries(data_title, extra_identifier,structure_variables_list=structure_variables_list,activity_variable=activity_variable,energy_variable='Energy', emissions_variable='Emissions',emissions_divisia=emissions_divisia, time_variable='Date', graph_title=graph_title, residual_variable1=residual_variable1, residual_variable2='Emissions intensity', font_size=font_size,AUTO_OPEN=AUTO_OPEN, hierarchical=hierarchical, output_data_folder=output_data_folder, plotting_output_folder=plotting_output_folder)
        

        

            
            
#%%
# produce_lots_of_LMDI_charts(USE_LIST_OF_CHARTS_TO_PRODUCE = True)
#%%