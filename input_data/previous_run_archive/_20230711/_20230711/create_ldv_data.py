#%%
#set working directory as one folder back so that config works
import os
import re
import pandas as pd
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import plotly.express as px
import plotly.subplots as subplots
import plotly.graph_objects as go
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#we're oging to take in the data that we have from teh transport datasyetm and see if we can calcualte vehicle efficiency.

FILE_DATE_ID2 = 'DATE20230126'

transport_data_system_folder = '../transport_data_system'
transport_data_system_df_original = pd.read_csv('{}/output_data/{}_interpolated_combined_data.csv'.format(transport_data_system_folder,FILE_DATE_ID2))

#%%
INDEX_COLS = ['Date',
 'Economy',
 'Medium',
 'Measure',
 'Transport Type',
 'Drive',
 'Scope',
 'Frequency',
 'Fuel_Type',
 'Dataset',
 'Source',
 'Unit']

#%%
#we want to add up the data for lv's and lt's in energy and activity
measures = ['freight_tonne_km','passenger_km','Energy', 'Stocks', 'Sales']
#we should remember to double check if we already have stocks or sales data for ldvs and then compare the results
vtypes = ['lv', 'lt']

ldv_data = transport_data_system_df_original[transport_data_system_df_original['Vehicle Type'].isin(vtypes)]
ldv_data = ldv_data[ldv_data['Measure'].isin(measures)]
#%%
#now pivot so we have lv and lt as columns
ldv_data_wide = ldv_data.pivot(index=INDEX_COLS, columns='Vehicle Type', values='Value')

# #filter for rows where we have data for both lv and lt
# ldv_data_wide = ldv_data_wide[ldv_data_wide['lv'].notna() & ldv_data_wide['lt'].notna()]

#for freight and perhaps some drive types we may have na in lt or na in lv and not the other col. 

#we may have an issue where there are duplicates when we exclude the Unit, Dataset ad lt/lv cols
#lets see
ldv_data_wide_dupes = ldv_data_wide.reset_index()
ldv_data_wide_dupes = ldv_data_wide_dupes[ldv_data_wide_dupes.duplicated(subset=['Date',
 'Economy',
 'Measure',
 'Medium',
 'Transport Type',
 'Drive',
 'Scope',
 'Frequency',
 'Fuel_Type'], keep=False)]
 #DOESNT LOOK LIKE IT!

#TAKE A LOOK at rows where one of lt or lv is na
ldv_data_wide_na = ldv_data_wide.reset_index()
ldv_data_wide_na = ldv_data_wide_na[ldv_data_wide_na['lv'].isna() | ldv_data_wide_na['lt'].isna()]
#there are a couple of instances where this could be an issue but mostly it looks like an oversight in the data. Perhaps we should plot the sum of lv and lt and see if it matches the ldv data we do have
ldv_data_wide = ldv_data_wide.reset_index()
#add so that NA values are 0
ldv_data_wide['ldv'] = ldv_data_wide['lv'].fillna(0) + ldv_data_wide['lt'].fillna(0)

#%%
#for each measure, we will plot a plot for each economy which has the ldv time series colored by drive type. We can also insert actual ldv data if we can:
transport_data_system_ldvs = transport_data_system_df_original[transport_data_system_df_original['Vehicle Type'] == 'ldv']
transport_data_system_ldvs = transport_data_system_ldvs[transport_data_system_ldvs['Measure'].isin(measures)]
#call Value ldv
transport_data_system_ldvs = transport_data_system_ldvs.rename(columns={'Value':'ldv_official'})
#join to ldv_data_wide on the index cols
ldv_data_wide_with_official = ldv_data_wide.merge(transport_data_system_ldvs[INDEX_COLS + ['ldv_official']], on=INDEX_COLS, how='outer')
#%%
#DATA TO SAVE
ldv_data_new = ldv_data_wide.drop(['lv', 'lt'], axis=1)
#make vehicle type ldv
ldv_data_new['Vehicle Type'] = 'ldv'
#make ldv into value
ldv_data_new = ldv_data_new.rename(columns={'ldv':'Value'})
#drop na from vlaue col
ldv_data_new = ldv_data_new[ldv_data_new['Value'].notna()]
#where datasset is na, set Final_dataset_selection_method' = 'interpolation'
ldv_data_new['Final_dataset_selection_method'] = ldv_data_new['Dataset'].fillna('interpolation')
#if dataset is not na, set Final_dataset_selection_method' = 'manual'
ldv_data_new.loc[ldv_data_new['Dataset'].notna(), 'Final_dataset_selection_method'] = 'Manual'

#save for use
ldv_data_new.to_csv('./input_data/calculated/ldv_data.csv', index=False)

#%%
#now plot:\
analyse = False
if analyse:
    for measure in measures:
        for transport_type in ldv_data_wide['Transport Type'].unique():
            #create subplot for 21 economies
            fig = subplots.make_subplots(rows=7, cols=3, subplot_titles=ldv_data_wide['Economy'].unique())
            data = ldv_data_wide[ldv_data_wide['Measure'] == measure]
            data = data[data['Transport Type'] == transport_type]
            if data.shape[0] == 0:
                    continue
            #add traces
            for i, economy in enumerate(ldv_data_wide['Economy'].unique()):
                #get data for this economy
                economy_data = data[data['Economy'] == economy]
                #add trace for each drive type. add a line for ldv_official too but in a dashed line
                for drive in economy_data['Drive'].unique():
                    drive_data = economy_data[economy_data['Drive'] == drive]
                    #check for duplicates if so throw error
                    fig.add_trace(go.Scatter(x=drive_data['Date'], y=drive_data['ldv'], name=drive), row=int(i/3)+1, col=int(i%3)+1)
                    fig.add_trace(go.Scatter(x=drive_data['Date'], y=drive_data['ldv_official'], name=drive + ' official', line=dict(dash='dash')), row=int(i/3)+1, col=int(i%3)+1)
            #update layout
            fig.update_layout(title_text=measure)
            # #save as html
            fig.write_html("plotting_output/testing/ldvs/{}{}_ldv.html".format(measure, transport_type))

#%%
#looking at the graph above it seems that the 8th edition stocks data pre 2017 has been interpolated to be a straight line. Except the ato data which is not broken down by drive type but itys 2017 value is about what youd expect if you summed up the 8th edition data in 2017

#so basically we have some pretty good stocks data from our ato dtaset but its not broken down into drive type. how to solve this?
#well we could get the proprotion of each drive type from the 8th edition data and then multiply that by the ato data to get the breakdown by drive type based on the ato data. Then also where we do know the EV proportion we could replace the evs with that proportion of the ato data, and then scale the rest of the data to match the 8th edition data.
#this can be don efor energy and activity too i guess?













#GENERAL ANALYSIS NOT REALTED TO LDVS
# %%
# Stocks

#passenger km:
#we have not got much new data for this!
#We can do passenger bus for 5 major economies
#road for most
#nothing for 2w or ldv
#rail for most
#air for most!
#ship for 5 majors

#Energy:
#we have only got data for combined trransport type
#can be broken into:
#rail for most (and a few fuel types!)
#road for most

#to do the above we might ass well create a tree diagram using plotly
#%%
%matplotlib inline
#we want to plot a tree diagram which helps to understand exactly wehat we have
#remove the 8th edition data from datasets col
transport_data_system_df_tree = transport_data_system_df_original[transport_data_system_df_original['Dataset'] != '8th edition transport model $ Reference']
#also remove interpolation
transport_data_system_df_tree = transport_data_system_df_tree[transport_data_system_df_tree['Final_dataset_selection_method'] != 'interpolation']
#remove where vehicle type is rail_road
transport_data_system_df_tree = transport_data_system_df_tree[transport_data_system_df_tree['Vehicle Type'] != 'rail_road']
analyse = True
if analyse:
    transport_data_system_df_tree.columns
    import plotly.express as px
    for measure in ['Stocks', 'passenger_km', 'Energy', 'freight_tonne_km']:
        columns_to_plot =['Transport Type', 'Vehicle Type', 'Economy','Drive']
        #filter for measure
        transport_data_system_df_tree_measure = transport_data_system_df_tree[transport_data_system_df_tree['Measure'] == measure]
        # fig = px.treemap(transport_data_system_df_tree, path=columns_to_plot)#, values='Value')
        # #make it bigger
        # fig.update_layout(width=1000, height=1000)
        # #make title
        # fig.update_layout(title_text=measure)
        # #show it in browser rather than in the notebook
        # fig.show()
        # fig.write_html("plotting_output/testing/all_data_tree_{}.html".format(measure))

        #and make one that can fit on my home screen which will be 1.3 times taller and 3 times wider
        fig = px.treemap(transport_data_system_df_tree_measure, path=columns_to_plot)
        #make it bigger
        fig.update_layout(width=2500, height=1300)
        #make title
        fig.update_layout(title_text=measure)
        #show it in browser rather than in the notebook
        fig.write_html("plotting_output/testing/trees/all_data_tree_big_{}.html".format(measure))

#%%
