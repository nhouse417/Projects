# Linear Regression on the California Housing Dataset

The goal of this project was to learn how to implement linear regression without using popular libraries such as scikit-learn and then learn how to implement it using 
scikit-learn along with learning how to use matplotlib and seaborn for data visualization and analysis. The California Housing dataset was used because it's a simple
dataset for learning how to implement ML regression algorithms. 

## File Descriptions

- **linear_regression_v1.py** -> my implementation of linear regression 
- **linear_regression_sklearn.py** -> linear regression implementation using pipelines
- **test.py** -> used to test implementing pipelines using examples from the scikit-learn library
- **test_tools.py** -> this tested the tools.py file functions to make sure they were working as intended
- **tools.py** -> implemented functions compute_cost, compute_gradient, and gradient_descent that are needed for linear regression
  - this file is an ongoing file that will be used for my implementation of logistic regression in the future
 
## Implementation

### Background information

If you stumbled upon this project and wanted to recreate it, here's some information on how to do so. I used a python virtual environment so that I can use the latest Python
version and if there were package updates then I could easily update them without messing with my system's configuration. This isn't a tutorial on how to create and use 
python virtual environments so I'll leave that up to you. The packages and versions I used are listed below.

- Python 3.13
- matplotlib 3.10.1
- numpy 2.2.4
- pandas 2.2.3
- scikit_learn 1.6.1
- seaborn 0.13.2

### Preprocessing steps

After loading the data using the pandas read_csv() function, I familiarize myself with the data by printing the first 5 entries of the data using the pandas head() function. 
I then used the isna() function in conjunction with sum() function to see if there were any missing values in the dataset (df.isna().sum(), pictured below).

![image](https://github.com/user-attachments/assets/4050852b-0a78-42f1-a4db-85660f5d0cf3)

After seeing that 207 total bedroom values were missing, I decided to drop those rows of data using the dropna() function. If I wanted to keep those rows of data, I could've used
the fillna() function in conjunction with the mean() function. It would look like df.fillna(value=df['total_bedrooms'].mean(), inplace=True).

After dealing with the missing values, I separate the features from the target into two dataframes. The target dataframe is the 'median_house_value' column because that's what
I'm trying to predict (given all of the features, what would the median house value be?). 

### Data visualization

To further understand the underlying data distribution, I first printed out the histograms of every feature (pictured below) to see each features' distribution. 
It became clear that the features' values have a broad range, and it would be useful to normalize these values to a range so that linear regression can be 
used effectively.

![Figure_1](https://github.com/user-attachments/assets/3eaf2141-49cd-4b6f-83ae-057e7c0bb525)

The next thing I plotted was the correlatin between every feature by printing a correlation matrix (pictured below). To understand this correlation matrix, the
features when matched with itself will have a value of 1 (in the picture, you can see a diagonal of 1s). The values of the matrix range from -1 to 1, and the closer
the value is to 1 means a strong correlation and vice versa when the value is closer to -1. From looking at this matrix, it shows that total_bedrooms, total_rooms, 
households, and population have strong correlation with each other. And the most important is that median income and median house value have a strong correlation
with each other. Their strong correlation means that if median income increases, then median house value would increase as well. 

![Figure_2](https://github.com/user-attachments/assets/a157c3ee-84fd-46d4-a0e3-85961e139889)

The last thing I chose to visualize was the correlation of latitude and longitude and how it affected median house value. In the picture below, it shows a correlation
heat map showing how the median house value increases when houses are nearer to the ocean. Also it shows that a house in a high population density area have more value
than houses that aren't in high population density areas.

![Figure_3](https://github.com/user-attachments/assets/7b58f4cd-194d-4a93-bf2e-181018ab418e)


### Linear Regression (my implementation, linear_regression_v1.py)

The main reason I implemented my own version of linear regression was to learn how it works behind the scenes. Implementing the cost function, the gradient function to get
the best w and b parameters, and then the gradient function solidified my understanding of how the gradient function works and why it's important for linear regression.
In the compute cost_function and compute_gradient function, regularization was implemented to prevent overfitting the data. This helps generalize the model so that it's 
accurate when unseen data is added.

The **cost function** (also known as the mean squared error) I implemented is pictured below. The goal of this function is to minimize the cost or error from the model. By
minimizing this, it leads to more accurate predictions from the model. These screenshots are from the Supervised Machine Learning: Regression and Classification Coursera
course by Andrew Ng. 

![squared_error_function_1](https://github.com/user-attachments/assets/db8d15a2-a9c8-4406-b424-ed8b32046f28)
![squared_error_function_2](https://github.com/user-attachments/assets/a5780e3f-3c0c-470f-83a6-62c37555baf3)

The **compute_gradient** function was implemented to find the best w and b parameters that fit the model. It does this by finding the derivative of the cost function 
with respect to w and b. It uses the formula pictured below.

![derivative_cost_function](https://github.com/user-attachments/assets/1e080fe1-9af4-42c4-9a86-9487ad8b8231)

Then after finding the best w and b parameters that fit the model, those values are inputted to the **gradient_descent** function to fit the model. The algorithm was
implemented following the gradient descent algorithm pictured below.

![gradient_descent_algorithm](https://github.com/user-attachments/assets/aa087b2f-a0b5-4b70-96af-309db6121bc0)

All of these screenshots are from the Coursera course "Supervised Machine Learning: Regression and Classification" by Andrew Ng.

After preprocessing the data, fitting the model, and running linear regression, the model's accuracy was 62% (rounded up to a whole number, real number was 0.6249).
In the screenshot below, the cost is decreasing which is great and the predictions of our model and target values are shown. The mean squared error and root mean squared
error are shown as well. 

![Screenshot 2025-04-15 at 7 47 07 PM](https://github.com/user-attachments/assets/d30ffb74-a8b8-41a1-8cfc-4f9fcd4eb618)


### Linear Regression implemented using sklearn pipelines (**linear_regression_sklearn.py**)

The reason for using sklearn pipelines were to familiarize myself with this popular library and how to use its functions to implement linear regression. I used pipelines
because it provided a streamlined way to preprocess data and then run a machine learning algorithm. Also pipelines provide a way to reuse code easily and ensure that 
there aren't any data leaks when going from preprocessing to fitting the model. 

In this file, I included the "ocean_proximity" column to add more precision to the model's predictions. Since this data is categorical and not numerical, I used the
**OneHotEncoder** class to transform this categorical data into a numerical data array. For the numerical data, I used a pipeline of the **SimpleImputer** and 
**StandardScaler** classes. SimpleImputer replaces any NaN values and I chose the method of 'median' which takes the median value of the column and replaces NaN values
with that median value. StandardScaler performs standardization on the features by removing the mean and scaling to unit variance using the formula **z = (x - u) / s**
which is also known as zscore normalization. In the formula, x is the training data, u (mu) is the mean of each column in an array, and s is the standard deviation of each
column in an array. 

Then I used **ColumnTransformer** to combine the preprocessing steps I did for the numerical data and categorical data. Lastly, I created a pipeline to run linear regression
on the processed data. I then fitted the data and used the **score()** function to find how accurate this model was. In the picture below, the accuracy of this model was 
65% (rounded up from 0.6488) which is a little better than my own implementation of linear regression. I had some runtime warnings that I'll address in the **Problems** section.

![linear_regression_sklearn_output](https://github.com/user-attachments/assets/47f8e7e9-a9a3-47ac-852a-e81bff371ed3)

### Improvements for the future

The most important improvement that can be made is a more accurate model. One estimator that I've tried is the "RandomForestRegressor" which "fits a number of decision tree regressors on various sub-samples of the dataset and uses averaging to improve the predictive accuracy and control over-fitting" (sklearn documentation). Instead of using the "LinearRegression" estimator, I used the RandomForestRegressor and it greatly improved the accuracy of the model. The RandomForestRegressor returned 82% accuracy compared to 65% for the LinearRegression
model used.

I'm going to learn more about the plethora of algorithms for regression models and will try to use different ones in the future. The almost 20% boost of accuracy from LinearRegression to
the RandomForestRegressor has me excited to learn more. 

Another improvement that can be made is creating a class for the tools that I used in my own implementation of linear regression and its functions. Creating a tools class would make it
easier to call those tool functions from other files making it more portable. 

The last improvement I can make is testing both **linear_regression_v1.py** and **linear_regression_sklearn.py** thoroughly by creating unit tests or by adding new data to see if the
model can accurately predict the median house value. 

## Challenges

One of the challenges was implementing the **compute_cost** function, the costs values were too high. This can be seen in the screenshot above in the **Linear Regression (my implementation)** section. The first half of that screenshot shows the cost values decreasing but still too high. That was because I didn't normalize the target values which
caused the cost values too be too high. In the second half of that screenshot, shows the cost values being within a range of -1 to 1 and it being decreased with every 10 iterations.
This taught me that I had to normalize the features and targets to get values that could be understood. 

Another challenge was that I encountered three runtime warnings in **linear_regression_sklearn.py**. The warnings were: (1) divide by zero encountered in matmul (2) overflow encountered
in matmul (3) invalid value encountered in matmul. First, I checked my training and target values datasets to see if there were any NaN values. I discovered that there were some NaN values
in the target dataset that I didn't clean before fitting it to the pipe. I'm still debugging on why I'm getting these warnings, but from my debugging I believe the problem is that when
doing matrix multiplication the result is too big for a float. A reason that I think it's the matrix multiplication because I use the same dataset for my implementation of linear regression and I don't get those warnings. In my implementation, I use the dot product function from numpy, but the LinearRegression estimator uses matmul. 

## Resources

[Scikit Learn Pipelines](https://daily.dev/blog/scikit-learn-pipelines-build-optimize-explain#:~:text=Scikit%2DLearn%20pipelines%20streamline%20machine%20learning%20workflows%20by%20combining%20data,transformations%20across%20training%20and%20testing)

[Linear Regression on California Housing Dataset](https://medium.com/@basumatary18/implementing-linear-regression-on-california-housing-dataset-378e14e421b7)

[Linear Regression on California Housing Dataset](https://github.com/WanQi-K/DataSciencePortfolio/blob/main/California%20Housing%20Linear%20Regression/California_Housing_Linear_Regression_(More_Data).ipynb)

[Sklearn California Housing Dataset](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_california_housing.html)

[Kaggle California Housing Dataset](https://www.kaggle.com/datasets/camnugent/california-housing-prices) - this is where I got **housing.csv** dataset from




