#this file will be a kind of planning page for the transport model as a whole. 

#the aim is to create a model that will estimate the input data for the transport model.

#that is, it will estimate activity, stocks and ?efficiency? using a number of different methods.

#these methods can range fro, actual data, to application of qualitative knowledge as weightings, to different policy levers that can be easily turned off and on to generate different scenarios. 
#it is important that this model is always easy to use and interpret so that these things can always be seen as improvements coompared to the researcher estimating the data for each economy themselves

#so for example, activity:
#first calculating the historic data:
#1. actual data should always be used when available.
#2. in the case of no actual data the data can be based off data that another economy has and adjusted to make it suit that economy. eg. 
#use an economys population and gdp compared to the other economy, as well as a weighting according to that econmys 'congestion' vs the other economys, their average elevation of their orads? and etc.?



#this wont work thought because its too comlicatd. just need ability to change things according to the incorporation of different policys and technological changes.

#but we kind of need soem data to help estiamte different economys data according to otehr economys activity.

Perhaps,
historicaL:
multi linear regression to estimate activity based on energy use and other factors for each economy. Can use models that do have activity data to train the multi linear reg, and therefore 
#find the most important variables and such.
-inpts:
energy use
stocks (https://www.oica.net/ - data on many things. esp stocks data for most economys)
urbanisation - urban population
elevation/geography (probably too vague)
gdp per capita
average income in usd
population
?index of road quality/infrastructure?
misc inputs related to transport we already have (perhaps train)
#outputs:
activity


New datasources:
https://www.ev-volumes.com/
chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://theicct.org/wp-content/uploads/2022/06/china-marine-decarbonizing-chinas-coastal-shipping-jun22.pdf v

(https://www.oica.net/ - data on many things. esp stocks data for most economys)