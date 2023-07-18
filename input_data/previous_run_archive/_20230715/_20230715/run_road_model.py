#generally this will all work on the grouping of economy, year, v-type, drive, transport type, and scenario. There is a model simulation excel workbook in the documentation folder to more easily understand the operations here.

#NOTE that there is still the fuel mixing operation that is not in this file of code. 
#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need
import road_model_functions
import logistic_fitting_functions
#%%
def run_road_model(project_to_just_outlook_base_year=False,advance_base_year=False,run_model_before_gompertz=True):
        
    #laod all data
    road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input_wide.csv')

    growth_forecasts = pd.read_csv('intermediate_data/model_inputs/growth_forecasts.csv')
    if project_to_just_outlook_base_year:
        END_YEAR_x = OUTLOOK_BASE_YEAR
        road_model_input = road_model_input[road_model_input['Date'] <= OUTLOOK_BASE_YEAR]
        growth_forecasts = growth_forecasts[growth_forecasts['Date'] <= OUTLOOK_BASE_YEAR]
    else:
        END_YEAR_x = END_YEAR
    if advance_base_year:
        BASE_YEAR_x = OUTLOOK_BASE_YEAR-1
    else:
        BASE_YEAR_x = BASE_YEAR
    main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block, user_inputs_df_dict,low_ram_computer = road_model_functions.prepare_road_model_inputs(BASE_YEAR_x,road_model_input,low_ram_computer=False)
    
    #if you want to analyse what is hapening in th model then set this to true and the model will output a dataframe wioth all the variables that are being calculated.
    ANALYSE_CHANGE_DATAFRAME = True
    #######################################################################
    #RUN PROCESS
    #######################################################################
    # #breakpoint()
    if run_model_before_gompertz:
        #RUN MODEL TO GET RESULTS FOR EACH YEAR
        for year in range(BASE_YEAR_x+1, END_YEAR_x+1):
            main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block = road_model_functions.run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe, low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME, previous_10_year_block, testing=False)

        main_dataframe = road_model_functions.join_and_save_road_model_outputs(main_dataframe, low_ram_computer, low_ram_computer_files_list,ANALYSE_CHANGE_DATAFRAME,change_dataframe_aggregation, gompertz_function_diagnostics_dataframe)

        #save results as pickle for testing purposes
        main_dataframe.to_pickle('./intermediate_data/road_model/main_dataframe.pkl')
    else:
        main_dataframe = pd.read_pickle('./intermediate_data/road_model/main_dataframe.pkl')
        if project_to_just_outlook_base_year:
            main_dataframe = main_dataframe[main_dataframe['Date'] <= OUTLOOK_BASE_YEAR]
    #######################################################################
    #CLEAN DATA FOR NEXT RUN
    #######################################################################
    
    #join on the gompertz gamma and , 'Gdp_per_capita', 'Population' cols from growth_forecasts and gompertz_parameters. THis is because they werent calculated in the model, but are needed as inputs for the next steps
    # main_dataframe = main_dataframe.merge(growth_forecasts[['Economy','Date','Gdp_per_capita', 'Population']].drop_duplicates(), on=['Economy','Date'], how='left')
    main_dataframe = main_dataframe.merge(user_inputs_df_dict['gompertz_parameters'][['Economy','Date', 'Scenario', 'Gompertz_gamma']].drop_duplicates(), on=['Economy','Date','Scenario'], how='left')

    # #breakpoint()
    #PUT RESULTS THROUGH logistic_fitting_function_handler AND FIND NEW PARAMETERS TO AVOID OVERGROWTH OF PASSENGER VEHICLE STOCKS
    #set gompertz gamma to 800 for all economies just to test.
    # main_dataframe['Gompertz_gamma'] = 800
    # #breakpoint()#seems we're getting activity estimates much higher for china than we should be.
    breakpoint()
    ONLY_PASSENGER_VEHICLES = False
    activity_growth_estimates, parameters_estimates = logistic_fitting_functions.logistic_fitting_function_handler(main_dataframe,show_plots=False,matplotlib_bool=False, plotly_bool=True, ONLY_PASSENGER_VEHICLES=ONLY_PASSENGER_VEHICLES,vehicle_gompertz_factors = {'car':1,'lt':1,'suv':1,'bus':5,'2w':0.5, 'lcv':3, 'mt': 3, 'ht': 3})
    #breakpoint()
    #note that activity_growth_estimates will contain new growth rates for only some econmies where their stocks per cpita passed their threshold. For the others, the growth rates will be the same as they were previously.
    #so do a merge and only keep the new growth rates for the economies that have them
    new_growth_forecasts = growth_forecasts.copy()
    similar_cols = [col for col in growth_forecasts.columns if col in activity_growth_estimates.columns]
    index_cols = ['Economy', 'Scenario', 'Date', 'Transport Type']
    new_growth_forecasts = new_growth_forecasts.merge(activity_growth_estimates.drop_duplicates(), on=index_cols, how='left', suffixes=('', '_new'))
    #######################################################################
    CLEAN_UP_GROWTH = False
    if CLEAN_UP_GROWTH:
        new_growth_forecasts = logistic_fitting_functions.average_out_growth_rate_using_cagr(new_growth_forecasts,BASE_YEAR_x, economies_to_avg_growth_over_all_years_in_freight_for = ['19_THA'])
        USE_FREIGHT_GROWTH_FOR_PASSENGER = False
        if USE_FREIGHT_GROWTH_FOR_PASSENGER:
            #also, since we have currently estomated growth to be too high, set passneger transport growth to be the sae as the new freight growth
            new_growth_forecasts_passenger = new_growth_forecasts.loc[new_growth_forecasts['Transport Type']=='freight'].copy()
            new_growth_forecasts_passenger['Transport Type'] = 'passenger'
            new_growth_forecasts =new_growth_forecasts.loc[new_growth_forecasts['Transport Type']!='passenger'].copy()
            new_growth_forecasts = pd.concat([new_growth_forecasts, new_growth_forecasts_passenger])
    #######################################################################
    #now where there is a new growth rate, use that, otherwise use the old one
    new_growth_forecasts['Activity_growth'] = new_growth_forecasts['Activity_growth_new'].fillna(new_growth_forecasts['Activity_growth'])
    #drop the cols with _new suffix
    new_growth_forecasts = new_growth_forecasts[[col for col in new_growth_forecasts.columns if not col.endswith('_new')]]
    
    #now srt growth_forecasts to new_growth_forecasts
    growth_forecasts = new_growth_forecasts.copy()
    
    #save these growth forecasts for use in non road too:
    growth_forecasts.to_pickle('./intermediate_data/road_model/final_road_growth_forecasts.pkl')
    
    #######################################################################
    main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block, user_inputs_df_dict,low_ram_computer = road_model_functions.prepare_road_model_inputs(BASE_YEAR_x, road_model_input,low_ram_computer=False)
    #######################################################################
    #RUN MODEL AGAIN
    ####################################################################### 
    breakpoint()
    
    #run model again with new growth rates for passenger vehicles (so replace growth_forecasts with activity_growth_estimates)
    for year in range(BASE_YEAR_x+1, END_YEAR_x+1):
        main_dataframe,previous_year_main_dataframe, low_ram_computer_files_list, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe,previous_10_year_block = road_model_functions.run_road_model_for_year_y(year, previous_year_main_dataframe, main_dataframe, user_inputs_df_dict, growth_forecasts, change_dataframe_aggregation, gompertz_function_diagnostics_dataframe, low_ram_computer_files_list, low_ram_computer, ANALYSE_CHANGE_DATAFRAME, previous_10_year_block, testing=False)

    
    #######################################################################

    #finalisation processes. save results and create diagnostics plots

    #######################################################################

    #save parameters_estimates as pickle for testing purposes
    parameters_estimates.to_pickle('./intermediate_data/road_model/parameters_estimates.pkl')

    #save as csv for next step
    main_dataframe = road_model_functions.join_and_save_road_model_outputs(main_dataframe, low_ram_computer, low_ram_computer_files_list,ANALYSE_CHANGE_DATAFRAME,change_dataframe_aggregation, gompertz_function_diagnostics_dataframe)

    #save results as pickle for testing purposes
    main_dataframe.to_pickle('./intermediate_data/road_model/main_dataframe_growth_adjusted.pkl')
    
    # #look at lcv growth in thailand
    # main_dataframe.loc[(main_dataframe['Vehicle Type']=='lcv') & (main_dataframe['Economy']=='') & 
    
#%%
run_road_model(project_to_just_outlook_base_year=False,run_model_before_gompertz=True,advance_base_year=True)
#%%



