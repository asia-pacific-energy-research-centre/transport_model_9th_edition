# STILL TO DO
#need to do fuel mixes later
# detailed_fuels_dataframe = energy_base_year.merge(biofuel_blending_ratio, on=['Economy', 'Scenario', 'Drive', 'Transport Type', 'Vehicle Type', 'Year'], how='left')
#is there a better way to to the new stock dist?


#%%
#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
execfile("config/config.py")#usae this to load libraries and set variables. Feel free to edit that file as you need
#%%

#laod clean user input from intermediate file
non_road_efficiency_growth= pd.read_csv('intermediate_data/non_aggregated_input_data/non_road_efficiency_growth.csv')

# road_model_input = pd.read_csv('intermediate_data/model_inputs/road_model_input.csv')
non_road_model_input = pd.read_csv('intermediate_data/model_inputs/non_road_model_input.csv')

activity_growth = pd.read_csv('intermediate_data/model_inputs/activity_growth.csv')
#%%

previous_year_main_dataframe = non_road_model_input.loc[non_road_model_input.Year == BASE_YEAR,:]
#create main dataframe as previous year dataframe, so that currently it only holds the base year's data. This will have each years data added to it at the end of each loop.
main_dataframe = previous_year_main_dataframe.copy()

#%%
#give option to run the process on a low RAM computer. If True then the loop will be split into 10 year blocks, saving each block in a csv, then starting again with an empty main datafrmae for the next 10 years block. If False then the loop will be run on all years without saving intermediate results.
low_ram_computer = True
if low_ram_computer:
    previous_10_year_block = BASE_YEAR
    low_ram_computer_files_list = []
    #remove files from main_dataframe_10_year_blocks for previous runs
    for file in glob.glob(os.path.join('intermediate_data/main_dataframe_10_year_blocks/', '*.csv')):
        os.remove(file)

#if you want to analyse what is hapening in th model then set this to true and lok at the change dataframe.
ANALYSE_CHANGE_DATAFRAME = True
#%%
#START MAIN PROCESS
for year in range(BASE_YEAR+1, END_YEAR+1):
    
    print('Up to year {}. The loop will run until year {}'.format(year, END_YEAR))

    #create change dataframe. This is like a messy notepad where we will adjust the last years values values and perform most calcualtions. 
    change_dataframe = previous_year_main_dataframe.copy()

    #change year in all rows to the next year. For now we will refer to the previous year as the original or base year. And values calculcated for the next year may sometimes be refered to as 'new'.
    change_dataframe.Year = year

    #start cakcualting new values suing the orignal values and adjustments as stated by the user and forecasted by us.

    #generally this will all work on the grouping of economy, year, v-type, drive, transport type, and scenario. The sections will be:
    #
    #TO DO
    #

    #ACTIVITY GROWTH
    #we will apply activity growth to the sum of activity for each transport type. Note that activity growth is assumed to be the same for all vehicle types of the same transport type.
    #join on activity growth
    change_dataframe = change_dataframe.merge(activity_growth, on=['Economy', 'Scenario', 'Year'], how='left')
    #calcualte sum of last years activity by transport type
    activity_transport_type_sum = change_dataframe.copy()[['Economy', 'Scenario', 'Transport Type', 'Year', "Activity"]]
    activity_transport_type_sum = activity_transport_type_sum.groupby(['Economy', 'Scenario', 'Transport Type', 'Year']).sum()
    activity_transport_type_sum.rename(columns={"Activity": "Activity_transport_type_sum"}, inplace=True)
    change_dataframe = change_dataframe.merge(activity_transport_type_sum, on=['Economy', 'Scenario', 'Transport Type', 'Year'], how='left')
    #apply activity growth to activity 
    change_dataframe['Activity'] = (change_dataframe['Activity_growth'] * change_dataframe['Activity']) + change_dataframe['Activity']
    
    #APPLY EFFICIENCY GROWTH TO ORIGINAL EFFICIENCY
    #note that this will then be split into different fuel types when we appply the fuel mix varaible later on.
    change_dataframe = change_dataframe.merge(non_road_efficiency_growth, on=['Economy', 'Scenario', 'Transport Type', 'Drive', 'Medium', 'Vehicle Type', 'Year'], how='left')

    change_dataframe['New_efficiency'] = change_dataframe['Efficiency'] * change_dataframe['Efficiency_growth']

    change_dataframe['Efficiency'] = change_dataframe['New_efficiency']
    
    #CALCUALTE NEW ENERGY CONSUMPTION. 
    #note that this is not split by fuel yet, it is just the total energy consumption for the vehicle/drive type. It is also only for activity per energy unit, not travel km per energy unit.
    change_dataframe['Energy'] = change_dataframe['Activity'] / change_dataframe['Efficiency'] 

    #CREATE STOCKS VALUE
    #if energy use is >0 then stock is 1, else 0
    change_dataframe['Stock'] = np.where(change_dataframe['Energy'] > 0, 1, 0)
    #######################################################################
    #Now start cleaning up the changes dataframe to create the dataframe for the new year.
    addition_to_main_dataframe = change_dataframe.copy() 
    
    addition_to_main_dataframe = addition_to_main_dataframe[['Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Year', 'Drive','Medium',  'Activity', 'Stocks', 'Efficiency', 'Energy']]
    
    #add new year to the main dataframe.
    main_dataframe = pd.concat([main_dataframe, addition_to_main_dataframe])
    previous_year_main_dataframe = addition_to_main_dataframe.copy()
    
    if ANALYSE_CHANGE_DATAFRAME:
        if year == BASE_YEAR+1:
            change_dataframe_aggregation = change_dataframe.copy()
        else:
            change_dataframe_aggregation = pd.concat([change_dataframe, change_dataframe_aggregation])

    #if we have a low ram computer then we will save the dataframe to a csv file at 10 year intervals. this is to save memory. during the proecss we will save a list of the file names that we have saved to, from which to stitch the new dataframe togehter from
    if low_ram_computer == True:
        year_counter = year - BASE_YEAR
        if year_counter % 10 == 0:
            print('The year is at the end of a ten year block, in year {}, saving interemediate results to csv.'.format(year))
            low_ram_file_name = 'intermediate_data/main_dataframe_10_year_blocks/main_dataframe_years_{}_to_{}.csv'.format(previous_10_year_block, year)
            main_dataframe.to_csv(low_ram_file_name, index=False)
            low_ram_computer_files_list.append(low_ram_file_name)

            previous_10_year_block = year
            main_dataframe = pd.DataFrame(columns=main_dataframe.columns)#remove data we just saved from main datafrmae

        elif year == END_YEAR:
            print('The year is at the end of the simulation, saving intermediate results to csv.')
            low_ram_file_name = 'intermediate_data/main_dataframe_10_year_blocks/main_dataframe_years_{}_to_{}.csv'.format(previous_10_year_block, year)
            main_dataframe.to_csv(low_ram_file_name, index=False)
            low_ram_computer_files_list.append(low_ram_file_name)

#%%
#this will be the name of the output file
new_output_file = 'intermediate_data/non_road_model/{}'.format(model_output_file_name)

#now, we will save the main dataframe to a csv file. if the computer is low ram, we will create the file from the already saved 10 year block interval files
if low_ram_computer == True:
    print('The computer is low ram, stitching together the main dataframe from the 10 year block files.')

    #TO CONSIDER, IF WE ARE STILL HAVING MEMORY ISSUES:
    # WE HAVE A CHOICE HERE WHETHER WE WANT TO STITCH ALL THE FILES ONTO A DATAFRAME THEN SAVE TO A CSV, OR ONLY OPEN ONE DATAFRAME AT A TIME, SEQUENTIALLY WRITING THEM TO A CSV WITHOUT OPENING THE CSV USING APPEND OPTION. ONE OTHER ISSUE IS THAT IF WE WILL STILL HAVE ONE GIANT CSV AT THE END, IT WILL CAUSE WHICHEVER COMPUTER LOADS IT TO BE SLOW SO PERHAPS ITS BEST TO SAVE THE DATA IN GROUPS DEPDNING ON THE DATATYPE OR ITS USEFULNESS?

    #FOR NOW LETS JUST WRITE THEM TO A CSV SEQUENTIALLY AS THAT SEEMS TO BE WORKING

    #first check the file we will be writing to doesnt already exist, if so, delete it
    if os.path.exists(new_output_file):
        os.remove(new_output_file)

    for file_i in low_ram_computer_files_list:
        print('Reading file {}'.format(file_i))
        low_ram_dataframe = pd.read_csv(file_i)
        #write to csv
        low_ram_dataframe.to_csv(new_output_file,mode='a', header=not os.path.exists(new_output_file),index=False)
        #remove file 
        os.remove(file_i)
    print('The main dataframe has been written to {}'.format(new_output_file))
else:
    print('The computer is not low ram, saving the main dataframe to a csv.')
    main_dataframe.to_csv(new_output_file, index=False)

if ANALYSE_CHANGE_DATAFRAME:
    #save dataframe
    change_dataframe_aggregation.to_csv('intermediate_data/non_road_model/change_dataframe_aggregation.csv', index=False)

#%%
