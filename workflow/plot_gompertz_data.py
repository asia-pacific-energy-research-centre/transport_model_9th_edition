#set working directory as one folder back so that config works
import os
import re
os.chdir(re.split('transport_model_9th_edition', os.getcwd())[0]+'\\transport_model_9th_edition')
from runpy import run_path
exec(open("config/config.py").read())#usae this to load libraries and set variables. Feel free to edit that file as you need

# pio.renderers.default = "browser"#allow plotting of graphs in the interactive notebook in vscode #or set to notebook
import matplotlib.pyplot as plt
plt.rcParams['figure.facecolor'] = 'w'
def plot_gompertz_data(gompertz_function_diagnostics_dataframe):



    save_html=True
    save_fig=False

    ################################################################################################################################################################

    #plot data from the gompertz_function_diagnostics_dataframe. this contians the columns: 'Economy','Scenario', 'Drive', 'Vehicle Type', 'Transport Type', 'Date', 'Stocks_per_thousand_capita', 'Expected_Gdp_per_capita', 'Gdp_per_capita','Expected_stocks_per_thousand_capita_derivative', 'Activity_growth_adjusted', 'Activity_growth_est','Mileage_growth_adjusted', 'Mielage_growth', 'Mileage', 'Expected_stocks_per_thousand_capita', 
    # Note that the below vars have been temproarily or permanently dropped
    # 'Expected_Gdp_per_capita', 
    # 'Expected_stocks_per_thousand_capita_2', 'Expected_stocks_per_thousand_capita_derivative_2'
    #we will plot these all, but provide the option to plot only the most important ones
    #first we will plot:
    #scatter of the stocks per capita (y) and Gdp_per_capita (x) for each economy and each year
    #overlay of a line showing the stocks per capita (y) and Expected_Gdp_per_capita (x) for each economy and scenario and each year. It might eb that this line is too messy though.

    #we will do this using plotly
    import plotly.express as px
    import plotly.graph_objects as go

    #filter for only the Reference scenario 
    gompertz_function_diagnostics_dataframe = gompertz_function_diagnostics_dataframe[gompertz_function_diagnostics_dataframe['Scenario'] == 'Reference']
    ################################
    #plot stocks per capita (y) and Gdp_per_capita (x) for each economy and each year,. The economy will be in facets. 
    title = 'Stocks per capita (y) and Gdp_per_capita (x) for each economy and each year'
    #to plot the expected gdp per cpita, we will melt the gdp per cpitas to be in one col, and the measure name in another col so we can colr by measure name
    gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy','Date', 'Vehicle Type','Stocks_per_thousand_capita', 'Gdp_per_capita']].drop_duplicates()#,'Expected_Gdp_per_capita'

    ################################
    #plot gdp per capita vs expected gdp per capita
    if 'Expected_Gdp_per_capita' in gompertz_function_diagnostics_dataframe.columns:
        title = 'Gdp per capita vs expected gdp per capita'
        gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date','Vehicle Type', 'Expected_Gdp_per_capita', 'Gdp_per_capita']].drop_duplicates()
        #melt
        gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy', 'Date','Vehicle Type'], value_vars=['Expected_Gdp_per_capita', 'Gdp_per_capita'], var_name='Measure', value_name='Value')
        #cnocatenate the measure name to the vehicle type
        gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Vehicle Type'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Measure']

        fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Value", facet_col="Economy", color='Measure',facet_col_wrap=7, title=title)
        # #add the derivative
        # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_derivative_2'], mode='lines', line=dict(color='grey', dash='dash'), name='Expected_stocks_per_thousand_capita_derivative_2')
        #save html
        if save_html:
            fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
        #save fig
        if save_fig:
            fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))

    ################################
    #plot Expected_stocks_per_thousand_capita vs Stocks_per_thousand_capita for each economy and scenario and each year. We will use grey lighter colors for the expected values
    if 'Expected_stocks_per_thousand_capita' in gompertz_function_diagnostics_dataframe.columns:
        title = 'Expected_stocks_per_thousand_capita vs Stocks_per_thousand_capita for each economy and scenario and each year'
        gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy','Date', 'Vehicle Type','Transport Type','Stocks_per_thousand_capita', 'Expected_stocks_per_thousand_capita']].drop_duplicates()
        #melt
        gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy','Date','Vehicle Type','Transport Type'], value_vars=['Expected_stocks_per_thousand_capita','Stocks_per_thousand_capita'], var_name='Measure', value_name='Value')
        #concat measure with vehicle type and transport type
        gompertz_function_diagnostics_dataframe_plot['Dash'] = gompertz_function_diagnostics_dataframe_plot['Measure'].apply(lambda x: 'Expected' if x == 'Expected_stocks_per_thousand_capita' else 'Actual')

        gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Measure'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Vehicle Type'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Transport Type']

        #now plot 
        fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Value", facet_col="Economy", facet_col_wrap=7, color="Measure", title=title, line_dash='Dash')
        #save the plot
        fig.write_html(f"./plotting_output/diagnostics/html/{title}.html", auto_open=AUTO_OPEN_PLOTLY_GRAPHS)

    ################################

    gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy','Date','Vehicle Type','Stocks_per_thousand_capita'], value_vars=['Gdp_per_capita'], var_name='Measure', value_name='Gdp_per_capita')#,'Expected_Gdp_per_capita'
    #concat the  'Vehicle Type', and Measure
    gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Vehicle Type'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Measure']
    fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Gdp_per_capita", y="Stocks_per_thousand_capita", facet_col="Economy", facet_col_wrap=7, color="Measure", title=title)
    #save html
    if save_html:
        fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
    #save fig
    if save_fig:
        fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))



    ################################
    #also plot stocks per capita (y) and Gdp_per_capita (x)  vs Expected_Gdp_per_capita (y) and Expected_stocks_per_thousand_capita (x) for each economy and scenario and each year. We will use grey lighter colors for the expected values
    if 'Expected_Gdp_per_capita' in gompertz_function_diagnostics_dataframe.columns:
        title = 'Stocks per capita (y) and Gdp_per_capita (x)  vs Expected_stocks_per_thousand_capita (x) for each economy and scenario and each year'#Expected_Gdp_per_capita (y) and 
        #to plot the expected gdp per cpita, we will melt the gdp per cpitas to be in one col, and the measure name in another col so we can colr by measure name
        gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy','Date', 'Vehicle Type','Transport Type','Stocks_per_thousand_capita', 'Gdp_per_capita']].drop_duplicates()
        #Create a column called 'Measure' which = 'Actual' for the actual values, and 'Expected' for the expected values
        gompertz_function_diagnostics_dataframe_plot['Measure'] = 'Actual'
        #add in the expected values
        gompertz_function_diagnostics_dataframe_plot2 = gompertz_function_diagnostics_dataframe[['Economy','Date', 'Vehicle Type','Transport Type', 'Expected_stocks_per_thousand_capita','Gdp_per_capita']].drop_duplicates()#, 'Expected_Gdp_per_capita' swapped for 'Gdp_per_capita'
        #rename the columns so they are the same as the actual values
        gompertz_function_diagnostics_dataframe_plot2 = gompertz_function_diagnostics_dataframe_plot2.rename(columns={'Expected_stocks_per_thousand_capita':'Stocks_per_thousand_capita'})
        gompertz_function_diagnostics_dataframe_plot2['Measure'] = 'Expected'
        gompertz_function_diagnostics_dataframe_plot = pd.concat([gompertz_function_diagnostics_dataframe_plot, gompertz_function_diagnostics_dataframe_plot2])
        #concat measure with vehicle type and transport type
        gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Measure'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Vehicle Type'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Transport Type']
        #now plot 
        fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Gdp_per_capita", y="Stocks_per_thousand_capita", facet_col="Economy", facet_col_wrap=7, color="Measure", title=title, color_discrete_map={'Actual':'black', 'Expected':'grey'})
        #save the plot
        fig.write_html(f"./plotting_output/diagnostics/html/{title}.html", auto_open=AUTO_OPEN_PLOTLY_GRAPHS)

    ################################
    #then we will plot Expected_stocks_per_thousand_capita_derivative over time for each economy . also add in a dashed, lighter line which shows the Expected_stocks_per_thousand_capita_derivative_2 so we can see if that is a better fit
    title = 'Expected_stocks_per_thousand_capita_derivative over time for each economy'
    gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date','Vehicle Type', 'Expected_stocks_per_thousand_capita_derivative']].drop_duplicates()

    fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Expected_stocks_per_thousand_capita_derivative", facet_col="Economy", color='Vehicle Type',facet_col_wrap=7, title=title)
    # #add the derivative
    # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_derivative_2'], mode='lines', line=dict(color='grey', dash='dash'), name='Expected_stocks_per_thousand_capita_derivative_2')
    #save html
    if save_html:
        fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
    #save fig
    if save_fig:
        fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))
    ################################
    #then we will plot Expected_stocks_per_thousand_capita_second_derivative over time for each economy . also add in a dashed, lighter line which shows the Expected_stocks_per_thousand_capita_derivative_2 so we can see if that is a better fit
    title = 'Expected_stocks_per_thousand_capita_growth over time for each economy'
    gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date','Vehicle Type','Expected_stocks_per_thousand_capita_growth']].drop_duplicates()

    fig = px.scatter(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Expected_stocks_per_thousand_capita_growth", facet_col="Economy", color='Vehicle Type',facet_col_wrap=7, title=title)
    # #add the derivative
    # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_derivative_2'], mode='lines', line=dict(color='grey', dash='dash'), name='Expected_stocks_per_thousand_capita_derivative_2')
    #save html
    if save_html:
        fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
    #save fig
    if save_fig:
        fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))



    ################################
    from scipy import stats
    #plot stocks per cpita with gamma line too
    title = 'Stocks per capita over time with Gompertz_gamma for each economy'
    gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date', 'Vehicle Type','Stocks_per_thousand_capita', 'Gompertz_gamma']].drop_duplicates()
    # #melt so values are in one column
    gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy', 'Date', 'Vehicle Type'], value_vars=['Stocks_per_thousand_capita', 'Gompertz_gamma'], value_name='Value', var_name='Measure').dropna()
    #concat measure with vehicle type 
    gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Measure'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Vehicle Type']
    fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Value", facet_col="Economy",color='Measure', facet_col_wrap=7, title=title)
    #save html
    if save_html:
        fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
    #save fig
    if save_fig:
        fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))

    # 
    # ################################
    # #plot  derivative 

    # title = 'Stocks per capita derivative over time for each economy'
    # gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date','Vehicle Type', 'Expected_stocks_per_thousand_capita_derivative']].drop_duplicates()
    # fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Expected_stocks_per_thousand_capita_derivative", facet_col="Economy", color='Vehicle Type',facet_col_wrap=7, title=title)
    # #save html
    # if save_html:
    #     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
    # #save fig
    # if save_fig:
    #     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))



    # title = 'Stocks per capita 2nd derivative over time for each economy'
    # gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date','Vehicle Type', 'Expected_stocks_per_thousand_capita_second_derivative']].drop_duplicates()
    # fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Expected_stocks_per_thousand_capita_second_derivative", facet_col="Economy", color='Vehicle Type',facet_col_wrap=7, title=title)
    # #save html
    # if save_html:
    #     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
    # #save fig
    # if save_fig:
    #     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))




    # ################################
    # #plot the same stocks per cpita on one y axis and its derivative on the other, but also plot the expected stocks per capita derivative 2 and the Expected_stocks_per_thousand_capita_2 on the same plot using grey lighter colors and dashed lines
    # title = 'Stocks per capita vs its derivative over time for each economy with derivative 2 and stocks per capita 2 for comparison'
    # gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date', 'Stocks_per_thousand_capita', 'Expected_stocks_per_thousand_capita_derivative']].drop_duplicates()
    # fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Stocks_per_thousand_capita", facet_col="Economy", facet_col_wrap=7, title=title)
    # #add the derivative
    # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_derivative'], mode='lines', name='Expected_stocks_per_thousand_capita_derivative')
    # #add the derivative 2
    # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_derivative_2'], mode='lines', line=dict(color='grey', dash='dash'), name='Expected_stocks_per_thousand_capita_derivative_2')
    # #add the stocks per capita 2
    # fig.add_scatter(x=gompertz_function_diagnostics_dataframe_plot['Date'], y=gompertz_function_diagnostics_dataframe_plot['Expected_stocks_per_thousand_capita_2'], mode='lines', line=dict(color='grey', dash='dash'), name='Expected_stocks_per_thousand_capita_2')
    # #save html
    # if save_html:
    #     fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
    # #save fig
    # if save_fig:
    #     fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))



    ################################
    #PLOT activity growth vs activity growth adjusted
    title = 'Activity growth vs activity growth adjusted over time for each economy'
    gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date', 'Activity_growth_est','Transport Type', 'Activity_growth_adjusted']].drop_duplicates()
    #melt
    gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy','Transport Type','Date'], value_vars=['Activity_growth_est','Activity_growth_adjusted'], var_name='Measure', value_name='Activity_growth_est')
    #concat Measure and 'Transport Type'
    gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Measure'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Transport Type']
    fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Activity_growth_est", facet_col="Economy", facet_col_wrap=7, color='Measure', title=title)
    #save html
    if save_html:
        fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
    #save fig
    if save_fig:
        fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))


    ################################
    #and lastly plot mileage growth vs mileage growth adjusted (not plotting actual mileage because it is different for each vehicle type and drive type, but the growth is the same for all vehicle type and drive types)
    title = 'Mileage over time for each economy'
    gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date', 'Mileage', 'Vehicle Type']].drop_duplicates()
    fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Mileage", facet_col="Economy", facet_col_wrap=7, color='Vehicle Type', title=title)
    #save html
    if save_html:
        fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
    #save fig
    if save_fig:
        fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))

    #and lastly plot mileage growth vs mileage growth adjusted (not plotting actual mileage because it is different for each vehicle type and drive type, but the growth is the same for all vehicle type and drive types)
    title = 'Mileage growth vs mileage growth adjusted over time for each economy'
    gompertz_function_diagnostics_dataframe_plot = gompertz_function_diagnostics_dataframe[['Economy', 'Date', 'Mileage_growth_adjusted', 'Mileage_growth', 'Vehicle Type']].drop_duplicates()
    #melt
    gompertz_function_diagnostics_dataframe_plot = pd.melt(gompertz_function_diagnostics_dataframe_plot, id_vars=['Economy','Date', 'Vehicle Type'], value_vars=['Mileage_growth_adjusted', 'Mileage_growth'], var_name='Measure', value_name='Mileage_growth')
    #concat Measure and 'Vehicle Type'
    gompertz_function_diagnostics_dataframe_plot['Measure'] = gompertz_function_diagnostics_dataframe_plot['Measure'] + ' ' + gompertz_function_diagnostics_dataframe_plot['Vehicle Type']
    fig = px.line(gompertz_function_diagnostics_dataframe_plot, x="Date", y="Mileage_growth", facet_col="Economy", facet_col_wrap=7, color='Measure', title=title)
    #save html
    if save_html:
        fig.write_html('./plotting_output/diagnostics/html/{}.html'.format(title))
    #save fig
    if save_fig:
        fig.write_image('./plotting_output/diagnostics/png/{}.png'.format(title))
