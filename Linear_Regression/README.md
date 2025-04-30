# Linear Regression on the California Housing Dataset

The goal of this project was to learn how to implement linear regression without using popular libraries such as scikit-learn and then learn how to implement it using 
scikit-learn along with learning how to use matplotlib and seaborn for data visualization and analysis. The California Housing dataset was used because it's a simple
dataset for learning how to implement ML regression algorithms. 

## File Descriptions

- linear_regression_v1.py -> my implementation of linear regression 
- linear_regression_sklearn.py -> linear regression implementation using pipelines
- test.py -> used to test implementing pipelines using examples from the scikit-learn library
- test_tools.py -> this tested the tools.py file functions to make sure they were working as intended
- tools.py -> implemented functions compute_cost, compute_gradient, and gradient_descent that are needed for linear regression
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


### data visualization
### why I chose to use pipelines
### outcomes and how it can be improved
random forest vs linear regression

## Challenges / Problems

## Future 
