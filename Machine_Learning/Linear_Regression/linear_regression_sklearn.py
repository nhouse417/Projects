"""
Implementing linear regression using the california housing
dataset from sklearn.
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder

# get housing data
housing = pd.read_csv('housing.csv')
housing = housing.dropna()

data = housing.drop(labels=['median_house_value'], axis=1)
target = housing['median_house_value']

# Data Visualization --------------------------------------------------------------

# update correlation heatmap from previous version to include 'ocean_proximity'
le = LabelEncoder()
data_copy = housing.drop(labels=['median_house_value'], axis=1)
data_copy['ocean_proximity'] = le.fit_transform(data_copy['ocean_proximity'])
plt.figure(figsize=(20, 10))
sns.heatmap(data_copy.corr(), annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5)
plt.title("Correlation Heatmap")
plt.show()

# ---------------------------------------------------------------------------------

# clean up data for preprocessing
numerical_features = ['longitude', 'latitude', 'housing_median_age', 'total_rooms',
                      'total_bedrooms', 'population', 'households', 'median_income']
categorical_features = ['ocean_proximity']

# # create two transformers for numerical and categorical data
numerical_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer([
    ('num', numerical_transformer, numerical_features),
    ('cat', categorical_transformer, categorical_features)
])

# split data into test and training sets
x_train, x_test, y_train, y_test = train_test_split(data, target,
                                                    test_size=0.2,
                                                    random_state=42)

# create pipeline to streamline preprocessing and training
pipe = Pipeline([
    ('preprocessor', preprocessor),
    ('regressor', LinearRegression())
])

# score is 0.6488 so rounding up to 0.65
print(f"Accuracy of the model: {pipe.fit(x_train, y_train).score(x_test, y_test)}")
