
#%%

#set working directory as one folder back so that config works
import os
import re
import pandas as pd
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
import plotly.express as px
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

#%%
#we're oging to take in the data that we have from teh transport datasyetm and see if we can calcualte vehicle efficiency.

FILE_DATE_ID2 = 'DATE20230124'

transport_data_system_folder = '../transport_data_system'
transport_data_system_df_original = pd.read_csv('{}/output_data/{}_interpolated_combined_data.csv'.format(transport_data_system_folder,FILE_DATE_ID2))

INDEX_COLS = ['Date',
 'Economy',
 'Vehicle Type',
 'Medium',
 'Transport Type',
 'Drive',
 'Scope',
 'Frequency']
#%%
analyse = False
if analyse:
    #filter for the same years as are in the model concordances in the transport data system (should just be base year)
    transport_data_system_df = transport_data_system_df_original.copy()
    transport_data_system_df.Measure.unique()
    #we want Efficiency and new_vehicle_efficiency from the transport data system
    transport_data_system_df = transport_data_system_df[transport_data_system_df.Measure.isin(['Efficiency','new_vehicle_efficiency'])]
    #where dataset is nan set it to Final_dataset_selection_method
    transport_data_system_df.loc[transport_data_system_df.Dataset.isna(),'Dataset'] = transport_data_system_df.loc[transport_data_system_df.Dataset.isna(),'Final_dataset_selection_method'] 
    #grab cols we need:
    transport_data_system_df = transport_data_system_df[INDEX_COLS+['Measure','Value']+['Dataset']]
    #pivot the measure col to get an efficiency and new_vehicle_efficiency col
    transport_data_system_df = transport_data_system_df.pivot(index=INDEX_COLS+['Dataset'],columns='Measure',values='Value').reset_index()
#%%

if analyse:
    #lets also load in passengerkm and energy use data from the transport data system
    transport_data_system_df2 = pd.read_csv('{}/output_data/{}_interpolated_combined_data.csv'.format(transport_data_system_folder,FILE_DATE_ID2))
    transport_data_system_df2 = transport_data_system_df2[transport_data_system_df2.Measure.isin(['passenger_km','Energy'])]
    #and we want to calcualte a value for efficiency per km so we will convert passenger km to km by:
    #filtering for only Vehicle Type = lv, lt, and ldv
    transport_data_system_df2 = transport_data_system_df2[transport_data_system_df2['Vehicle Type'].isin(['lv','lt','ldv'])]
    #then where measure = passenger km , divide by occupancy rate = 1.5 and set passenger km to km
    transport_data_system_df2.loc[transport_data_system_df2.Measure == 'passenger_km','Value'] = transport_data_system_df2.loc[transport_data_system_df2.Measure == 'passenger_km','Value']/1.5
    transport_data_system_df2.loc[transport_data_system_df2.Measure == 'passenger_km','Measure'] = 'km'
    #then pivot the measure col to get an energy and km col
    transport_data_system_df2 = transport_data_system_df2.pivot(index=INDEX_COLS,columns='Measure',values='Value').reset_index()
    #and calcualte Efficiency by dividing energy by km
    transport_data_system_df2['Efficiency'] = transport_data_system_df2['Energy']/transport_data_system_df2['km']

    #set dataset to 'Calculated'
    transport_data_system_df2['Dataset'] = 'Calculated'
#%%
if analyse:
    #we will concat with the other eff data so we can plot it altogether.
    eff_data = pd.concat([transport_data_system_df,transport_data_system_df2],sort=False)
    #drop na and 0 values
    eff_data = eff_data.dropna(subset=['Efficiency'])
    eff_data = eff_data[eff_data.Efficiency != 0]   
    #most of the data ranges from xe-10 to xe-8 whjere x is a number between 1 and 9. the higher numbers are making it hard to see the lower numbers. Lets try filter out bad numbers to get a better plot

    #to properly analyse it would be best if kept only the economys where we have data in 'IEA Fuel Economy $ GFEI'
    IEA_economys = transport_data_system_df.loc[transport_data_system_df.Dataset == 'IEA Fuel Economy $ GFEI','Economy'].unique()
    eff_data = eff_data[eff_data.Economy.isin(IEA_economys)]

    #and keep only drive = 'g' 'd' and 'ice'
    eff_data = eff_data[eff_data.Drive.isin(['g','d','ice'])]

    #and make a colwhich joins 'Vehicle Type','Transport Type','Drive'
    eff_data['Vehicle Type'] = eff_data['Vehicle Type'] + ' ' + eff_data['Transport Type'] + ' ' + eff_data['Drive']


#%%
if analyse:
    #now plot y=Efficiency,x=Date and label=Dataset, facet=Economy, hue=Vehicle Type
    plot = px.line(eff_data,x='Date',y='Efficiency',color='Dataset',line_dash='Vehicle Type',facet_col='Economy',facet_col_wrap=3,hover_data=['Vehicle Type','Transport Type','Drive'])
    plot.write_html('plotting_output/testing/efficiency_data.html')
    # print avg eff for each economy for each dataset
    for economy in eff_data.Economy.unique():
        print('\nXXXXX Economy: {} XXXXXXX'.format(economy))
        for dataset in eff_data.Dataset.unique():
            #ignore 'interpolation' dataset
            if dataset == 'interpolation':
                continue
            print('Dataset: {}'.format(dataset))
            print(eff_data[(eff_data.Economy == economy) & (eff_data.Dataset == dataset)].Efficiency.mean())
    #ok great it loks (jsut from a quick look no avg's) like the eff value centres around 3e-9 PJ per km for all data we plotted. If we convert that to litres of gasoline it is 3e-9/3.42e-8 = 0.87 litres per km.which is 8.7 per 100km which is just a bit higher than the average fuel economy of cars and vans in 2021 in the IEA https://www.iea.org/fuels-and-technologies/fuel-economy which is good because it measn we can feel happy using the IEA value, times the occupancy rate of 1.5 to get the eff per passenger km for ldv's!
    #Its also good because it means that the ratio of enegry use to passenger km for ldv g or d drives is correct. 


#%%
analyse =False
if analyse:
    #lets just look at new_vehicle_efficiency quickly
    new_vehicle_efficiency_data = transport_data_system_df_original.copy()
    new_vehicle_efficiency_data = new_vehicle_efficiency_data[new_vehicle_efficiency_data.Measure == 'new_vehicle_efficiency'] 

    #we dont know what the actual unit is for this data. should we bother using it?
    plot = px.line(new_vehicle_efficiency_data,x='Date',y='Value',color='Drive',line_dash='Vehicle Type',facet_col='Economy',facet_col_wrap=3,hover_data=['Vehicle Type','Transport Type','Drive'])
    plot.write_html('plotting_output/testing/new_vehicle_efficiency_data.html')
    # print avg eff for each economy but assume that this is vehicle eff per million passenger km, so we will divide by 1.5 *one million to get eff per passenger km
    print(new_vehicle_efficiency_data.groupby(['Economy','Vehicle Type','Drive'])['Value'].mean()/1.5e6)#nah doesnt seem right aye
    #so we will create a new df with the IEA value for ldv's and then we will use the eff data we have to estimate the eff for the other vehicle types



#%%
#based on the assumption that the ratio of passenger km to energy use is correct we can estimate the eff for the other vehicle types where we dont have data from the iea
#wat well do is filter for passenger km and energy use, filter out data for ldvs that are g or d drives, then pivot the measures, then filter out any rows where we dont have both passenger km and energy use and then calc eff.
#we need to double check this data is correct so we will create a box plot for all values for each vehicle type and drive type and set the color to the economy. we will also add a line for the avg value for each economy for each transport type, vehicle type and drive type

efficiency_other = transport_data_system_df_original.copy()
efficiency_other = efficiency_other[efficiency_other.Measure.isin(['passenger_km','Energy'])]
efficiency_other = efficiency_other[~((efficiency_other['Vehicle Type'] == 'ldv') & (efficiency_other.Drive.isin(['g','d'])))]
#drop vehiuclke type = road
efficiency_other = efficiency_other[efficiency_other['Vehicle Type'] != 'road']
#drop any non road mediums
efficiency_other = efficiency_other[efficiency_other.Medium == 'road']
#keep only Fuel_type.isna() 
efficiency_other = efficiency_other[efficiency_other.Fuel_Type.isna()]

efficiency_other = efficiency_other.pivot(index=['Economy','Dataset','Date','Vehicle Type','Transport Type','Drive'],columns='Measure',values='Value')
efficiency_other = efficiency_other[efficiency_other.passenger_km.notna() & efficiency_other.Energy.notna()]
efficiency_other['efficiency'] = efficiency_other.Energy/efficiency_other.passenger_km
efficiency_other = efficiency_other.reset_index()
analyse = False
#make a col which joins 'Vehicle Type','Transport Type','Drive'
efficiency_other['Vehicle_drive'] = efficiency_other['Vehicle Type']  + ' ' + efficiency_other['Drive']
#remove any outliers
efficiency_other = efficiency_other[efficiency_other.efficiency < efficiency_other.efficiency.quantile(0.9)]
if analyse:
    #plot a violin pllot for each vehicle type.
    for vehicle in efficiency_other['Vehicle Type'].unique():
        plot = px.violin(efficiency_other[efficiency_other['Vehicle Type'] == vehicle],x='Drive',y='efficiency',hover_data=['Economy','Vehicle Type','Drive'],box=True)
        #set title
        plot.update_layout(title_text='Efficiency for {}s'.format(vehicle))
        #show
        plot.show()
        plot.write_html('plotting_output/testing/efficiency_violins/efficiency_other_{}.html'.format(vehicle))
    # #plot box with a facet for each Vehicle_drive
    # plot = px.violin(efficiency_other,y='efficiency',x='Drive',facet_col_wrap=3, hover_data=['Economy'], facet_col='Vehicle Type')#points="all",
    # plot.show()
    # plot.write_html('plotting_output/testing/efficiency_other.html')

#its quite hard to tell but lets just assume its ok. Just for exploration lets print the average eff per drive type on a single violin plot
if analyse:
    plot = px.violin(efficiency_other,y='efficiency',x='Drive',hover_data=['Economy','Vehicle Type','Drive'],box=True)
    plot.update_layout(title_text='Efficiency for all vehicle types')
    plot.show()
    plot.write_html('plotting_output/testing/efficiency_violins/efficiency_other_all.html')

#we're just going to assume that every economy has the same eff for each vehicle type and drive type. so we will just take the average for each vehicle type and drive type and use that for all economies
efficiency_other = efficiency_other.groupby(['Vehicle Type','Drive'])['efficiency'].mean().reset_index()
#%%


################################################################################

#ANALYSIS OVER

################################################################################


#%%
calculate_again = False
if calculate_again:
    #To estiamte the values for the otehr economys we will jsut take the average for available data and use that.
    finalised_new_vehicle_efficiency_ldv_ice = transport_data_system_df_original[(transport_data_system_df_original.Dataset == 'IEA Fuel Economy $ GFEI') & (transport_data_system_df_original['Vehicle Type'] == 'ldv')]
    #keep max Date only for each economy
    finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice[finalised_new_vehicle_efficiency_ldv_ice.Date == finalised_new_vehicle_efficiency_ldv_ice.Date.max()]
    #calc avg eff
    avg_eff = finalised_new_vehicle_efficiency_ldv_ice.Value.mean()

    #create dataframe with all other economys and set eff to avg_eff
    other_economys = transport_data_system_df_original.Economy.unique()
    #get economys not in finalised_new_vehicle_efficiency_ldv_ice
    other_economys = np.setdiff1d(other_economys,finalised_new_vehicle_efficiency_ldv_ice.Economy)
    #for each economy, add a row to finalised_new_vehicle_efficiency_ldv_ice with the avg_eff and all the same other values
    dummy_row = finalised_new_vehicle_efficiency_ldv_ice.iloc[0]
    for economy in other_economys:
        dummy_row.Economy = economy
        dummy_row.Value = avg_eff
        dummy_row.Dataset = 'Estimated'
        finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice.append(dummy_row,ignore_index=True)
    #set Drive = 'g' and Transport Type = 'passenger'
    finalised_new_vehicle_efficiency_ldv_ice['Drive'] = 'g'
    finalised_new_vehicle_efficiency_ldv_ice['Transport Type'] = 'passenger'
    #then copy and set drive = 'd' 
    finalised_new_vehicle_efficiency_ldv_ice_d = finalised_new_vehicle_efficiency_ldv_ice.copy()
    finalised_new_vehicle_efficiency_ldv_ice_d['Drive'] = 'd'
    #append the d drive df to the g drive df
    finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice.append(finalised_new_vehicle_efficiency_ldv_ice_d,ignore_index=True)

    #change values to be in terms of eff per passenger km by timesing by 1.5
    finalised_new_vehicle_efficiency_ldv_ice.Value = finalised_new_vehicle_efficiency_ldv_ice.Value * 1.5

    #change unit to PJ per pkm
    finalised_new_vehicle_efficiency_ldv_ice.Unit = 'PJ per pkm'
    #change measure to New_vehicle_efficiency
    finalised_new_vehicle_efficiency_ldv_ice.Measure = 'New_vehicle_efficiency'

    #sort out dates
    #remove date column
    finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice.drop(columns=['Date'])
    #drop duplicates
    finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice.drop_duplicates()
    #now for every year between this and 10 years ago, stack the dataframe with the date for that year
    #first get the years
    import datetime
    years = np.arange(datetime.datetime.now().year-11,datetime.datetime.now().year-1)
    #convert years to str with 12-31 at end
    years = [str(year)+'-12-31' for year in years]
    finalised_new_vehicle_efficiency_ldv_ice['Date'] = years[0]
    #now stack the dataframe
    for year in years[1:]:
        dummy_df = finalised_new_vehicle_efficiency_ldv_ice.copy()
        dummy_df['Date'] = year
        finalised_new_vehicle_efficiency_ldv_ice = finalised_new_vehicle_efficiency_ldv_ice.append(dummy_df,ignore_index=True)

    #save it so that it can be concatenated to the transport_data_system_df_original
    finalised_new_vehicle_efficiency_ldv_ice.to_csv('input_data/calculated/iea_new_vehicle_efficiency_ldv_ice.csv',index=False)

#%%
#and now create a similar dataframe for the other vehicle types
other_eff_data = transport_data_system_df_original.copy()
#remove duplicates when we subset by economy, vehicle type and drive
other_eff_data = other_eff_data.drop_duplicates(subset=['Economy','Vehicle Type','Drive'])
#set dataset to estimated
other_eff_data.Dataset = 'Estimated'
#set measure to New_vehicle_efficiency
other_eff_data.Measure = 'New_vehicle_efficiency'
#set unit to PJ per pkm
other_eff_data.Unit = 'PJ per pkm'
#fuel type is nan
other_eff_data['Fuel Type'] = np.nan
#scope national
other_eff_data.Scope = 'National'
#transport type is passenger
other_eff_data['Transport Type'] = 'passenger'
#final data selection method is nan
other_eff_data['Final Data Selection Method'] = np.nan
#merge with the efficiency_other df to get the eff values
other_eff_data = other_eff_data.merge(efficiency_other,on=['Vehicle Type','Drive'],how='inner')
#remove vlaue column and rename efficiency to value
other_eff_data = other_eff_data.drop(columns=['Value'])
other_eff_data = other_eff_data.rename(columns={'efficiency':'Value'})
#sort out dates
#remove date column
other_eff_data = other_eff_data.drop(columns=['Date'])
#drop duplicates
other_eff_data = other_eff_data.drop_duplicates()
#now for every year between this and 10 years ago, stack the dataframe with the date for that year
#first get the years
import datetime
years = np.arange(datetime.datetime.now().year-11,datetime.datetime.now().year-1)
#convert years to str with 12-31 at end
years = [str(year)+'-12-31' for year in years]
dummy_df = other_eff_data.copy()
other_eff_data_new = pd.DataFrame()
#now stack the dataframe
for year in years:
    dummy_df['Date'] = year
    other_eff_data_new = pd.concat([other_eff_data_new,dummy_df],ignore_index=True)
#save it so that it can be concatenated to the transport_data_system_df_original
other_eff_data_new.to_csv('input_data/calculated/new_vehicle_efficiency_other_estimates.csv',index=False)
#%%
#we are going to use the efficiency data we do have to try estimate the efficiency of the vehicles that we don't have data for.
#first find what data we do have

#we also have the IEA assumption for average fuel economy of cars and vans in 2021 as 6.7. So for any missing data we will could use this. https://www.iea.org/fuels-and-technologies/fuel-economy

#we dont know trucks tho. can we even estimate this? seems unlikely. perhaps they need to go in the non road model? but then how to deal with freight tonnne km?

#perhaps to do evs we can use the data we have on ice engine eff and then calculate eff per passenger km using occ of 1.5, then calc the


#%%
#we will hvae to fill in values to import into the model so lets copy rows from the transport datasystem df and change the vlaues to the ones we ahve calculated so that we can import and concat the data with the treannsport data system data later

#%%
#we also want to check whether we have the capabilities to run the mdoel for ldvs, 2w, buses and trucks.


#%%
#also how to do turnover rate? 
#we can clauclate it using  some sort of average of the decrease in stocks minus the increase in stocks due to sales. if the value ends up being a bit all over the place we can perhaps set it manually. 
#we will have to calcualte it for each economy individually, check how that ends up and think abo0ut average for different regions or developments