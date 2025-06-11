# Logistic Regression model on Wisconsin Breast Cancer Dataset

The goal of this project is to create a binary classification model to identify if a patient has breast cancer given the data.
This project uses Python libraries such as SciKit-Learn, Pandas, and Seaborn to understand and visualize the dataset which was imported
from scikit-learn using the load_breast_cancer() function.

## Table of Contents

* [Background Information](background-information)
* [Data Visualization](data-visualization)
* [Implementation](implementation)

### Background Information

For this project, I used a Python virtual environment so that I can install packages without messing with my computer's package configurations. Also if there are any package updates in the future, I can easily update the packages used here. The packages and their versions are listed below. 

- Python 3.13
- matplotlib 3.9.4
- numpy 2.0.2
- pandas 2.2.3
- seaborn 0.13.2
- scikit-learn 1.6.1

### Data Visualization

First, I wanted to look at the dataset's class distribution. For this, I created a bar graph that separated the cases labeled 0 (malignant) and 1 (benign). From the [dataset's documentation](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_breast_cancer.html), it shows that 212 cases are malignant and 357 cases are benign. This is shown in the picture below. 

![Class_Distribution](https://github.com/user-attachments/assets/2056094f-50ff-441b-aafd-2a4f5ea0437d)

