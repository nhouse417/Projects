"""
Linear Regression will be used to predict housing prices in California.
The California Housing Prices dataset from Kaggle is used here.

The dataset is old (census from 1990) but will be used to practice linear and 
logistic regression.

Version 1 is using my implementation of gradient descent with regularization.
Along with z-score normalization to optimize the data. 

For regularization, I use the formula "(lambda / m) * weight" which is 
L2 Regularization or Ridge Regression.

The functions used here are in the tools.py file.

Steps
1. load the csv
2. clean the data
3. use z-score normalization to get values within
   range to run gradient descent
4. run gradient descent to find optimal w and b values
5. make predictions model
6. calculate model accuracy
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import mean_squared_error
from tools import compute_gradient, gradient_descent, zscore_normalization

# load csv into a pandas dataframe
data = pd.read_csv('housing.csv')

# drop rows with missing data
data = data.dropna()

# target values -> 'median_house_value' column
# dropping 'ocean_proximity' as it's a categorical value with no numbers
x_train = data.drop(labels=['median_house_value', 'ocean_proximity'], axis=1)
y_train = data['median_house_value']

# Data Visualization ------------------------------------------------------

# plots for each feature to see it's distribution
data.hist(bins=50, figsize=(12, 8))
plt.show()

# visualize the correlation between features
feature_correlation = data.drop(labels=['ocean_proximity'], axis=1)
plt.figure(figsize=(20, 10))
sns.heatmap(feature_correlation.corr(), annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5)
plt.title("Correlation Heatmap")
plt.show()

# visualize how latitude and longitude correlate to median housing price
data.plot(kind="scatter", x="longitude",y="latitude", c="median_house_value",
          cmap="jet", colorbar=True, legend=True, sharex=False, figsize=(12,8),
          s=data['population']/100, label="population", alpha=0.7,
          title="Median House Value per Area")
plt.show()

# -------------------------------------------------------------------------

# convert to numpy arrays for calculations
x = x_train.to_numpy()
y = y_train.to_numpy()
w = np.random.rand(x.shape[1])
b = 0.0
alpha = 0.1
lambda_tmp = 1.0

# Testing x normalized -----------------------------------------------------

x_normalized = zscore_normalization(x)
dj_dw, dj_db = compute_gradient(x_normalized, y, w, b, lambda_tmp)
iterations = 100
cost_history = []
w, b, cost_history = gradient_descent(x_normalized, y, dj_dw, dj_db, lambda_tmp, alpha, iterations)

# predictions model
m = x.shape[0]
prediction = np.zeros(m,)

for i in range(m):
    prediction[i] = np.dot(x_normalized[i], w) + b

# print 10 predicted samples
for i in range(10):
    print(f"prediction: {prediction[i]:0.2f}, target value: {y[i]}")

# use these to find the accuracy of the model
mse = mean_squared_error(y, prediction)
rmse= np.sqrt(mse)
print(f"The mean squared error: {mse}")
print(f"Root mse: {rmse}")

# Testing x and y normalized datasets --------------------------------------------------

w_norm = np.random.rand(x.shape[1])
b_norm = 0.0

y_normalized = zscore_normalization(y)
dj_dw_norm, dj_db_norm = compute_gradient(x_normalized, y_normalized, w_norm, b_norm, lambda_tmp)
cost_history = []
w_norm, b_norm, cost_history = gradient_descent(x_normalized, y_normalized,
                                                dj_dw_norm, dj_db_norm,
                                                lambda_tmp, alpha, iterations)

# predictions model
m = x.shape[0]
prediction_norm = np.zeros(m,)

for i in range(m):
    prediction_norm[i] = np.dot(x_normalized[i], w_norm) + b_norm

# print 10 predicted samples
for i in range(10):
    print(f"prediction: {prediction_norm[i]:0.2f}, target value: {y_normalized[i]}")

# use these to calculate the accuracy of the model
mse = mean_squared_error(y_normalized, prediction_norm)
rmse= np.sqrt(mse)
print(f"The mean squared error: {mse}")
print(f"Root mse: {rmse}")
