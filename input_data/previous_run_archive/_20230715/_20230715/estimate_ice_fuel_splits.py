#we will estaimte the amount of each kind of fuel used for each different vehicle type for ice engines. This will be a quick and dirty estimate baed on previously used data so it is not necessarily accurate. It is just a starting point for the user to edit.#this will be concatted onto the bottom of the demand side fuel mix input data (model_concordances_all.to_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv', index=False)) to represent the fuel mix for ICE vehicles.


#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

def estimate_ice_fuel_splits(demand_side_fuel_mixing):
    #take in previous fuel use data

    # 
    # model_output_with_fuels = pd.read_csv("output_data/model_output_with_fuels/archive/model_output_years_2017_to_2050.csv")
    # \input_data\from_8th\reformatted/model_output_years_2017_to_2050_for_cng_inputs.csv
    model_output_with_fuels = pd.read_csv("input_data/from_8th/reformatted/model_output_years_2017_to_2050_for_cng_inputs.csv")
    #repalce Year with Date
    model_output_with_fuels['Date'] = model_output_with_fuels['Year']
    model_output_with_fuels = model_output_with_fuels.drop(columns=['Year'])
    #"config\concordances_and_config_data\8th_fuel_to_9th_fuel.xlsx"
    eighth_to_ninth_fuel_concordances = pd.read_excel("config/concordances_and_config_data/8th_fuel_to_9th_fuel.xlsx", sheet_name='8th_to_9th_fuel_concordances')

    #merge with eighth_to_ninth_fuel_concordances and see if we can replace all Fuels with the 9th fuel value
    model_output_with_fuels = model_output_with_fuels.merge(eighth_to_ninth_fuel_concordances, how='left', left_on='Fuel', right_on='8th_fuel')

    #repalce Fuel with 9th_fuel then drop the other cols
    model_output_with_fuels['Fuel'] = model_output_with_fuels['9th_fuel']
    model_output_with_fuels = model_output_with_fuels.drop(columns=['8th_fuel', '9th_fuel'])

    #replace lt and lv with ldv
    model_output_with_fuels['Vehicle Type'] = model_output_with_fuels['Vehicle Type'].replace(['lt', 'lv'], 'ldv')

    #filter for ice drive types and then drop drive col
    # print(model_output_with_fuels['Drive'].unique())#['bev' 'g' 'cng' 'd' 'lpg' 'phevg' 'phevd' 'fcev' nan]
    model_output_with_fuels = model_output_with_fuels[model_output_with_fuels['Drive'].isin([ 'g', 'd', 'phevg', 'phevd', 'ice', 'phev'])]# 'cng', 'lpg',
    model_output_with_fuels = model_output_with_fuels.drop(columns=['Drive']).drop_duplicates()
    #we're missing data for 2017 for road mediums in here for some reason, so we'll add it back in by copying 2018., since this is a short term function no bigggery
    model_output_with_fuels_2017 = model_output_with_fuels[model_output_with_fuels['Date']==2018]
    model_output_with_fuels_2017['Date'] = 2017
    model_output_with_fuels = pd.concat([model_output_with_fuels, model_output_with_fuels_2017])
    #sum by cols except energy
    cols = model_output_with_fuels.columns.tolist()
    cols.remove('Energy')
    model_output_with_fuels = model_output_with_fuels.groupby(cols).sum().reset_index()

    #pivot fuel use out so we have a col for each fule type
    cols = model_output_with_fuels.columns.tolist()
    cols.remove('Fuel')
    cols.remove('Energy')
    model_output_with_fuels = model_output_with_fuels.pivot(index=cols, columns='Fuel', values='Energy')
    model_output_with_fuels = model_output_with_fuels.reset_index()

    # #drop lpg and natural gas since we expect them to die off #TODO inluce ethese later. they do have a use case still. 
    # model_output_with_fuels = model_output_with_fuels.drop(columns=['7_9_lpg', '8_1_natural_gas'])
    #drop elec since it is not useful here
    model_output_with_fuels = model_output_with_fuels.drop(columns=['17_electricity'])
    #drop bio fuels because they are split out in the supply side mixing:
    model_output_with_fuels = model_output_with_fuels.drop(columns=['16_06_biodiesel','16_05_biogasoline'])
    #set any nas to 0
    model_output_with_fuels = model_output_with_fuels.fillna(0)

    #calcualte proprotion of each fuel type used for each unique vehicle type, transport type, economy, year combination. We will do this by getting every col that isnt 'Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Medium' and claculating its proportuoin of the total energy used for that row. the total energy used for that row is the sum of all the cls that arent 'Date', 'Economy', 'Scenario', 'Transport Type', 'Vehicle Type', 'Medium'
    fuel_cols= [col for col in model_output_with_fuels.columns.tolist() if col not in cols]
    model_output_with_fuels['Total_energy'] = model_output_with_fuels[fuel_cols].sum(axis=1)
    #now divide each fuel col by the total energy col
    for col in fuel_cols:
        model_output_with_fuels[col] = model_output_with_fuels[col].div(model_output_with_fuels['Total_energy'])
    #drop total energy col
    model_output_with_fuels = model_output_with_fuels.drop(columns=['Total_energy'])
    #replace nas with 0
    model_output_with_fuels = model_output_with_fuels.fillna(0)
    #reset index
    # model_output_with_fuels = model_output_with_fuels.reset_index()
    #melt back into long format
    model_output_with_fuels = model_output_with_fuels.melt(id_vars=cols, var_name='Fuel', value_name='Energy_proportion')


    #calcualte the average proportion of the energy proportion when we remove date and scenario col
    #drop date and scenario cols
    model_output_with_fuels = model_output_with_fuels.drop(columns=['Scenario'])#'Date',
    cols = model_output_with_fuels.columns.tolist()
    cols.remove('Energy_proportion')
    model_output_with_fuels = model_output_with_fuels.groupby(cols).mean().reset_index()

    #now we have a df with the proportion of each fuel type used for each unique vehicle type, transport type, economy, year combination. We will do some analysis using boxplots to see if there are any outliers, then calc the averages and so on.
    #use plotly boxplots:
    plot = False
    if plot:
        import plotly.express as px
        #we will create a facet for every transport type vehicle type combination
        #we will have the fuel type on x axis
        #we will have the proportion of energy used on the y axis
        #we will have a different color point for each economy but they will be on the same plot
        model_output_with_fuels_plot = model_output_with_fuels.copy()
        model_output_with_fuels_plot['Vehicle Type'] = model_output_with_fuels_plot['Vehicle Type']+ ' ' + model_output_with_fuels_plot['Transport Type']
        fig = px.box(model_output_with_fuels_plot, x="Fuel", y="Energy_proportion", facet_col="Vehicle Type",facet_col_wrap=2, hover_data=model_output_with_fuels_plot.columns, points="all")
        #save the plot to html
        fig.write_html("plotting_output/input_exploration/ice_fuel_splits/ice_fuel_splits_boxplots.html", auto_open=False)

    #looks okay to me.



    # #save in intermediate_data\model_inputs as a csv
    # model_output_with_fuels.to_csv("intermediate_data\model_inputs\ice_fuel_splits_COMPGEN.csv", index=False)
    #load user input for fuel mixing 
    # demand_side_fuel_mixing = pd.read_csv('intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv')


    #make sure the data is in the right format to concat onto deamnd side fuel mixing
    #demand_side_fuel_mixing cols:
    # Date	Economy	Vehicle Type	Medium	Transport Type	Drive	Scenario	Frequency	Fuel	Demand_side_fuel_share
    #values: 2017	01_AUS	ldv	road	freight	phevg	Carbon Neutral	Yearly	17_electricity	0.5
    #model_output_with_fuels cols:Date	Economy	Transport Type	Vehicle Type	Medium	Fuel	Energy_proportion

    #create new cols to match demand_side_fuel_mixing
    model_output_with_fuels['Frequency'] = 'Yearly'
    model_output_with_fuels['Demand_side_fuel_share'] = model_output_with_fuels['Energy_proportion']
    model_output_with_fuels['Drive'] = 'ice'
    #drop cols that are not in demand_side_fuel_mixing
    model_output_with_fuels = model_output_with_fuels.drop(columns=['Energy_proportion'])

    #for each Scenario in demand_side_fuel_mixing, just copy the model_output_with_fuels df and add the scenario to the scenario col
    #then concat onto demand_side_fuel_mixing
    ice_demand_side_fuel_mixing = pd.DataFrame()
    for scenario in demand_side_fuel_mixing['Scenario'].unique():
        model_output_with_fuels_scenario = model_output_with_fuels.copy()
        model_output_with_fuels_scenario['Scenario'] = scenario
        #concat onto demand_side_fuel_mixing
        ice_demand_side_fuel_mixing = pd.concat([ice_demand_side_fuel_mixing, model_output_with_fuels_scenario], axis=0, ignore_index=True)

    #we may be missing years beyond 2050. so grab the data for 2050 and copy it for the years beyond 2050:
    data_2050 = ice_demand_side_fuel_mixing.copy()
    data_2050 = data_2050[data_2050['Date'] == 2050]
    ice_demand_side_fuel_mixing_beyond_2050 = pd.DataFrame()
    for year in range(2051, END_YEAR+1):
        if year in ice_demand_side_fuel_mixing['Date'].unique():
            continue 
        data_2050['Date'] = year
        ice_demand_side_fuel_mixing_beyond_2050 = pd.concat([ice_demand_side_fuel_mixing_beyond_2050, data_2050], axis=0, ignore_index=True)
    #concat onto ice_demand_side_fuel_mixing
    ice_demand_side_fuel_mixing = pd.concat([ice_demand_side_fuel_mixing, ice_demand_side_fuel_mixing_beyond_2050], axis=0, ignore_index=True)

    # #concat onto ice_demand_side_fuel_mixing
    # demand_side_fuel_mixing = pd.concat([demand_side_fuel_mixing, model_output_with_fuels], axis=0, ignore_index=True)

    return ice_demand_side_fuel_mixing
    #save in intermediate_data\model_inputs as a csv
    # demand_side_fuel_mixing.to_csv("intermediate_data\model_inputs\demand_side_fuel_mixing_COMPGEN.csv", index=False)