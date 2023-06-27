#generally this will all work on the grouping of economy, year, v-type, drive, transport type, and scenario. There is a model simulation excel workbook in the documentation folder to more easily understand the operations here.

#NOTE that there is still the fuel mixing operation that is not in this file of code. 
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
import numpy as np
from scipy.optimize import newton
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
import functions
#%%
def run_road_model():
    #laod all data
    road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input_wide.csv')

    growth_forecasts = pd.read_csv('intermediate_data/model_inputs/growth_forecasts.csv')
    
    main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block, user_inputs_df_dict,low_ram_computer = functions.prepare_road_model_inputs(road_model_input,low_ram_computer=False)
    
    #if you want to analyse what is hapening in th model then set this to true and the model will output a dataframe wioth all the variables that are being calculated.
    ANALYSE_CHANGE_DATAFRAME = True
    #######################################################################
    #RUN PROCESS
    #######################################################################
    run_this = True#set to false if you want to skip this step and just load the results from pickle.
    # breakpoint()
    if run_this:
        #RUN MODEL TO GET RESULTS FOR EACH YEAR
        for year in range(BASE_YEAR+1, END_YEAR+1):
            main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block = functions.run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe, low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME, previous_10_year_block, testing=False)

        main_dataframe = functions.join_and_save_road_model_outputs(main_dataframe, low_ram_computer, low_ram_computer_files_list,ANALYSE_CHANGE_DATAFRAME,change_dataframe_aggregation, gompertz_function_diagnostics_dataframe)

        #save results as pickle for testing purposes
        main_dataframe.to_pickle('./intermediate_data/road_model/main_dataframe.pkl')
    else:
        main_dataframe = pd.read_pickle('./intermediate_data/road_model/main_dataframe.pkl')
    
    #######################################################################
    #CLEAN DATA FOR NEXT RUN
    #######################################################################
    
    #join on the gompertz gamma and , 'Gdp_per_capita', 'Population' cols from growth_forecasts and gompertz_parameters. THis is because they werent calculated in the model, but are needed as inputs for the next steps
    # main_dataframe = main_dataframe.merge(growth_forecasts[['Economy','Date','Gdp_per_capita', 'Population']].drop_duplicates(), on=['Economy','Date'], how='left')
    main_dataframe = main_dataframe.merge(user_inputs_df_dict['gompertz_parameters'][['Economy','Date', 'Scenario', 'Gompertz_gamma']].drop_duplicates(), on=['Economy','Date','Scenario'], how='left')

    
    #PUT RESULTS THROUGH logistic_fitting_function_handler AND FIND NEW PARAMETERS TO AVOID OVERGROWTH OF PASSENGER VEHICLE STOCKS
    #set gompertz gamma to 800 for all economies just to test.
    # main_dataframe['Gompertz_gamma'] = 800
    # breakpoint()#seems we're getting activity estimates much higher for china than we should be.
    activity_growth_estimates, parameters_estimates = logistic_fitting_functions.logistic_fitting_function_handler(main_dataframe,show_plots=False,matplotlib_bool=False, plotly_bool=True)
    breakpoint()
    #set transport type to passenger for all rows
    activity_growth_estimates['Transport Type'] = 'passenger'
    #note that activity_growth_estimates will contain new growth rates for only some econmies where their stocks per cpita passed their threshold. For the others, the growth rates will be the same as they were previously.
    #so do a merge and only keep the new growth rates for the economies that have them
    new_growth_forecasts = growth_forecasts.copy()
    similar_cols = [col for col in growth_forecasts.columns if col in activity_growth_estimates.columns]
    index_cols = ['Economy', 'Scenario', 'Date', 'Transport Type']
    new_growth_forecasts = new_growth_forecasts.merge(activity_growth_estimates.drop_duplicates(), on=index_cols, how='left', suffixes=('', '_new'))
    #now where there is a new growth rate, use that, otherwise use the old one
    new_growth_forecasts['Activity_growth'] = new_growth_forecasts['Activity_growth_new'].fillna(new_growth_forecasts['Activity_growth'])
    #drop the cols with _new suffix
    new_growth_forecasts = new_growth_forecasts[[col for col in new_growth_forecasts.columns if not col.endswith('_new')]]
    
    #now srt growth_forecasts to new_growth_forecasts
    growth_forecasts = new_growth_forecasts.copy()
    
    main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block, user_inputs_df_dict,low_ram_computer = functions.prepare_road_model_inputs(road_model_input,low_ram_computer=False)
    #######################################################################
    #RUN MODEL AGAIN
    ####################################################################### 
    # breakpoint()
    #run model again with new growth rates for passenger vehicles (so replace growth_forecasts with activity_growth_estimates)
    for year in range(BASE_YEAR+1, END_YEAR+1):
        main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block = functions.run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe, low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME, previous_10_year_block, testing=False)

    
    #######################################################################

    #finalisation processes. save results and create diagnostics plots

    #######################################################################

    #save parameters_estimates as pickle for testing purposes
    parameters_estimates.to_pickle('./intermediate_data/road_model/parameters_estimates.pkl')

    #save as csv for next step
    main_dataframe = functions.join_and_save_road_model_outputs(main_dataframe, low_ram_computer, low_ram_computer_files_list,ANALYSE_CHANGE_DATAFRAME,change_dataframe_aggregation, gompertz_function_diagnostics_dataframe)

    #save results as pickle for testing purposes
    main_dataframe.to_pickle('./intermediate_data/road_model/main_dataframe_growth_adjusted.pkl')
    
#%%
run_road_model()
#%%



# #######################################################################
# #######################################################################
# plot_this=True
# if plot_this:
#     main_dataframe_new = main_dataframe.copy()
#     # main_dataframe_new = main_dataframe.merge(growth_forecasts[['Economy','Date','Activity_growth']].drop_duplicates(), on=['Economy','Date'], how='left')
#     a = main_dataframe_new[['Activity','Activity_growth','Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive',
#         'Scenario']]
#     #grab vehicle type = ldv, transport type = passenger, drive = bev, scenario = Target
#     a = a[(a['Vehicle Type'] == 'ldv') & (a['Transport Type'] == 'passenger')  & (a['Scenario'] == 'Target')  & (a['Economy'] == '20_USA')]#& (a['Date'] < 2100)#& (a['Drive'] == 'bev')

#     #plot the sum of activity of 20_USA  for transport ype = passenger, with the activity growth on the right axis. 
#     import plotly.express as px
#     fig = px.line(a, x="Date", y="Activity", color='Drive', title='Activity of 20_USA for transport type = passenger')
#     #and include the activity growth on the right axis
#     fig.add_scatter(x=a['Date'].drop_duplicates(), y=a['Activity_growth'].drop_duplicates(), mode='lines', name='Activity growth', yaxis='y2')
#     fig.update_layout(yaxis=dict(title='Activity'), yaxis2=dict(title='Activity growth', overlaying='y', side='right'))
#     #write to html
#     fig.write_html("20_USA_activity.html", auto_open=True)


#     #and also plot stocks per capita for 20_USA
#     # main_dataframe_new = main_dataframe.merge(growth_forecasts[['Economy','Date','Activity_growth','Population']].drop_duplicates(), on=['Economy','Date'], how='left')
#     main_dataframe_new = main_dataframe.copy()
#     #calcualte stocks per capita
#     main_dataframe_new['Thousand_stocks_per_capita'] = main_dataframe_new['Stocks']/main_dataframe_new['Population']
#     #convert to more readable units. We will convert back later if we need to #todo do we need to?
#     main_dataframe_new['Stocks_per_thousand_capita'] = main_dataframe_new['Thousand_stocks_per_capita'] * 1000000

#     main_dataframe_new['Gompertz_gamma'] = 800

#     a = main_dataframe_new[['Stocks_per_thousand_capita','Activity_growth','Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive',
#         'Scenario', 'Gompertz_gamma']]
#     #grab vehicle type = ldv, transport type = passenger, drive = bev, scenario = Target
#     a = a[(a['Vehicle Type'] == 'ldv') & (a['Transport Type'] == 'passenger')  & (a['Scenario'] == 'Target') & (a['Economy'] == '20_USA')]# & (a['Date'] < 2100)]#& (a['Drive'] == 'ice')

#     #plot stocks per cpiat  and then activity growth on right axis
#     fig = px.line(a, x="Date", y="Stocks_per_thousand_capita", color='Drive', title='Stocks per capita of 20_USA for transport type = passenger')
#     #and include the activity growth on the right axis
#     fig.add_scatter(x=a['Date'].drop_duplicates(), y=a['Activity_growth'].drop_duplicates(), mode='lines', name='Activity growth', yaxis='y2')
#     fig.update_layout(yaxis=dict(title='Stocks per capita'), yaxis2=dict(title='Activity growth', overlaying='y', side='right'))
#     #write to html
#     fig.write_html("20_USA_stocks_per_capita.html", auto_open=True)








# plot_this=False
# if plot_this:
#     main_dataframe_new = main_dataframe.copy()
#     # main_dataframe_new = main_dataframe.merge(growth_forecasts[['Economy','Date','Activity_growth']].drop_duplicates(), on=['Economy','Date'], how='left')
#     a = main_dataframe_new[['Activity','Activity_growth','Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive',
#         'Scenario']]
#     #grab vehicle type = ldv, transport type = passenger, drive = bev, scenario = Target
#     a = a[(a['Vehicle Type'] == 'ldv') & (a['Transport Type'] == 'passenger')  & (a['Scenario'] == 'Target')  & (a['Economy'] == '20_USA')]#& (a['Date'] < 2100)#& (a['Drive'] == 'bev')

#     #plot the sum of activity of 20_USA  for transport ype = passenger, with the activity growth on the right axis. 
#     import plotly.express as px
#     fig = px.line(a, x="Date", y="Activity", color='Drive', title='Activity of 20_USA for transport type = passenger')
#     #and include the activity growth on the right axis
#     fig.add_scatter(x=a['Date'].drop_duplicates(), y=a['Activity_growth'].drop_duplicates(), mode='lines', name='Activity growth', yaxis='y2')
#     fig.update_layout(yaxis=dict(title='Activity'), yaxis2=dict(title='Activity growth', overlaying='y', side='right'))
#     #write to html
#     fig.write_html("20_USA_activity.html", auto_open=True)

#     #and also plot stocks per capita for 20_USA
#     main_dataframe_new = main_dataframe.copy()#merge(growth_forecasts[['Economy','Date','Activity_growth','Population']].drop_duplicates(), on=['Economy','Date'], how='left')

#     #calcualte stocks per capita
#     main_dataframe_new['Thousand_stocks_per_capita'] = main_dataframe_new['Stocks']/main_dataframe_new['Population']
#     #convert to more readable units. We will convert back later if we need to #todo do we need to?
#     main_dataframe_new['Stocks_per_thousand_capita'] = main_dataframe_new['Thousand_stocks_per_capita'] * 1000000

#     main_dataframe_new['Gompertz_gamma'] = 800

#     a = main_dataframe_new[['Stocks_per_thousand_capita','Activity_growth','Date', 'Economy', 'Vehicle Type', 'Medium', 'Transport Type', 'Drive',
#         'Scenario', 'Gompertz_gamma']]
#     #grab vehicle type = ldv, transport type = passenger, drive = bev, scenario = Target
#     a = a[(a['Vehicle Type'] == 'ldv') & (a['Transport Type'] == 'passenger')  & (a['Scenario'] == 'Target') & (a['Economy'] == '20_USA')]# & (a['Date'] < 2100)]#& (a['Drive'] == 'ice')

#     #plot stocks per cpiat  and then activity growth on right axis
#     fig = px.line(a, x="Date", y="Stocks_per_thousand_capita", color='Drive', title='Stocks per capita of 20_USA for transport type = passenger')
#     #and include the activity growth on the right axis
#     fig.add_scatter(x=a['Date'].drop_duplicates(), y=a['Activity_growth'].drop_duplicates(), mode='lines', name='Activity growth', yaxis='y2')
#     fig.update_layout(yaxis=dict(title='Stocks per capita'), yaxis2=dict(title='Activity growth', overlaying='y', side='right'))
#     #write to html
#     fig.write_html("20_USA_stocks_per_capita.html", auto_open=True)


