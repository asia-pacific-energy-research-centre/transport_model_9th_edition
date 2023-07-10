import numpy as np
import matplotlib.pyplot as plt

# Function to calculate turnover rate based on average age
def calculate_turnover_rate(avg_age, k, x0):
    return 1 / (1 + np.exp(-k * (avg_age - x0)))

# Initial data
ev_mean_age = 1
ev_std_dev = 1
ev_num = 100
ev_new_num = 10

ice_mean_age = 10
ice_std_dev = 10
ice_num = 1000
ice_new_num = 10

# Parameters for the logistic function
k = 0.7
x0 = 12.5

# Lists to store the average ages over time
ev_ages = []
ice_ages = []

# Run the simulation for X years
X = 20
for year in range(X):
    # Calculate turnover rates based on average age
    ev_turnover = calculate_turnover_rate(ev_mean_age, k, x0)
    ice_turnover = calculate_turnover_rate(ice_mean_age, k, x0)

    # Calculate new mean age after turnover
    ev_mean_age = ev_mean_age - ev_std_dev * ev_turnover
    ice_mean_age = ice_mean_age - ice_std_dev * ice_turnover

    # Calculate new mean age after addition of new vehicles
    ev_mean_age = (ev_mean_age * (ev_num - ev_num * ev_turnover) + 0 * ev_new_num) / (ev_num - ev_num * ev_turnover + ev_new_num)
    ice_mean_age = (ice_mean_age * (ice_num - ice_num * ice_turnover) + 0 * ice_new_num) / (ice_num - ice_num * ice_turnover + ice_new_num)

    # Update the number of vehicles
    ev_num = ev_num - ev_num * ev_turnover + ev_new_num
    ice_num = ice_num - ice_num * ice_turnover + ice_new_num

    # Store the average ages
    ev_ages.append(ev_mean_age)
    ice_ages.append(ice_mean_age)

# Plot the average ages over time
plt.plot(range(X), ev_ages, label='EV')
plt.plot(range(X), ice_ages, label='ICE')
plt.xlabel('Year')
plt.ylabel('Average Age')
plt.legend()
plt.show()
