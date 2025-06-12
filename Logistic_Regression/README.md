# Logistic Regression model on Wisconsin Breast Cancer Dataset

The goal of this project is to create a binary classification model to identify if a patient has breast cancer given the data.
This project uses Python libraries such as SciKit-Learn, Pandas, and Seaborn to understand and visualize the dataset which was imported
from scikit-learn using the load_breast_cancer() function.

## Table of Contents

* [Background Information](background-information)
* [Data Visualization](data-visualization)
* [Implementation](implementation)
* [Model Evaluation](model-evaluation)

### Background Information

For this project, I used a Python virtual environment so that I can install packages without messing with my computer's package configurations. Also if there are any package updates in the future, I can easily update the packages used here. The packages and their versions are listed below. 

- Python 3.13
- matplotlib 3.9.4
- numpy 2.0.2
- pandas 2.2.3
- seaborn 0.13.2
- scikit-learn 1.6.1

### Data Visualization

First, I wanted to look at the dataset's class distribution. For this, I created a bar graph that separated the cases labeled 0 (malignant) and 1 (benign). From the [dataset's documentation](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_breast_cancer.html), it shows that 212 cases are malignant and 357 cases are benign. This is shown in the picture below. The implementation for this is in the visualize_data() function.

![Class_Distribution](https://github.com/user-attachments/assets/2056094f-50ff-441b-aafd-2a4f5ea0437d)

Next, I wanted to look at the features that had a strong correlation to the target classes. Since there are 30 features in this dataset, finding the features that are strongly correlated to the target classes is important to see which features have the most effect on the outcome. For this I used the corrwith() function to get each features' correlation value. Then using that I created a correlation matrix to show the top 10 features that have the strongest correlation to the classes (shown below). The implementation for this is in the feature_correlation() function.

![Correlation_Matrix](https://github.com/user-attachments/assets/883a37cf-5d3c-41c6-812b-9ed02eb56c04)


Shown below is how strongly correlated the top 10 features are to the target classes. This was implemented in the evaluate_model() function.
![Top_Features_Correlation_To_Target](https://github.com/user-attachments/assets/732a24e5-5b47-4853-9da6-76787937d81b)


## Implementation

This section is fairly straightforward but is broken down into different functions. The purpose of breaking the implementation into separate functions is for debugging purposes. For example, if something went wrong with training the model, then I go straight to that function instead of having to guess where something went wrong. The sequence of creating the binary classification model is as follows:

1. Preprocess the data using the StandardScaler() (function -> preprocess_data())
2. Train the model using the LogisticRegression() classifier (function -> train_model())
3. Evaluate the model (function -> evaluate_model())
   a. This will be discussed in the next section
4. Cross Validate the model (function -> cross_validate_model())
5. Gather evaluation scores and output to a csv file (function -> evaluation_scores_file())
   a. In the real world I would imagine that someone would like a summary of how the model performed.

## Model Evaluation

This step is important because it shows how my model is performing with the dataset. This is a binary classfication model so the evaluation metrics I chose are accuracy, precision, recall, f1 score, a confusion matrix, roc auc score, roc curve, cross validation score and mean cross validation score. The reasons why I chose these metrics are described in this section.

1. Accuracy calculates the predicted values to the true values. This is useful to see how accurate the model's predictions are compared to the true values of the dataset.
2. Precision measures the model's accuracy of true positive cases meaning how well the model predicted a positive case without getting a false positive.
3. Recall measures the model's ability to correctly identify all true positive cases. It tries to minimize the false negative cases which are actually positives.
4. The f1 score is the harmonic mean between precision and accuracy which gives a better measurement of the model's incorrectly classified cases. This is also useful for imbalanced datasets because it uses both precision and recall to obtain a more balanced score of the model.
5. A confusion matrix is a table that summarizes the model's performance by comparing the predicted values to actual values. It shows if a model is correctly identifying true positive and negative cases (example is shown below).

![Confusion_Matrix](https://github.com/user-attachments/assets/5387faa7-19ec-40cd-93d5-42c00d8022a0)

6. The ROC Curve shows the model's performance at all possible classifcation thresholds. It plots the true positive rate versus the false positive rate at different thresholds. This is important because







