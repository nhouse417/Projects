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

The **compute_gradient** function was implemented following the algorithm pictured below. The importance of this algorithm is to find the convergence of the w and b
parameters so that the w and b parameters are the best to fit the model. As with the screenshots above, this was taken from the Coursera course.

![gradient_descent_algorithm](https://github.com/user-attachments/assets/aa087b2f-a0b5-4b70-96af-309db6121bc0)




### Linear Regression implemented using sklearn pipelines

### outcomes and how it can be improved
random forest vs linear regression

## Challenges / Problems

## Future 
