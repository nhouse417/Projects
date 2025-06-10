"""
Logistic Regression will be used on Wisconsin breast cancer dataset
from sklearn. 
"""

# third party imports
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_curve,
    roc_auc_score,
    confusion_matrix)
from sklearn.preprocessing import StandardScaler
from sklearn.utils import Bunch


class BreastCancerClassificationModel:
    """
    This class performs logistic regression / binary classification on the breast cancer
    dataset from sklearn. Also it performs an analysis on how well the model.
    """

    def __init__(self, data: Bunch, max_iters: int = 200):
        """
        Initialize the data and target into a pandas dataframe.
        Also split the dataframe into training and testing sets.

        Input:
            data: a Bunch object containing the breast cancer dataset
            max_iters: number of iterations for the class to converge on optimal result
        """

        # create dataframe
        self.data = data
        self.data_df = pd.DataFrame(data=np.c_[data.data, data.target],
                                    columns=list(data.feature_names) + ['target'])

        # split data into test and training set
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            data.data, data.target, test_size=0.25, random_state=1)

        # create scaler and classifier
        self.scaler = StandardScaler()
        self.model = LogisticRegression(random_state=1, max_iter=max_iters, solver='lbfgs')

        # dataframe that'll contain evaluation metrics from this model
        self.evaluation_metrics: pd.DataFrame


    def visualize_data(self) -> None:
        """
        This function will create a bar graph that shows the data distribution.
        """

        sns.set_theme(style="whitegrid", palette="pastel")
        _, ax = plt.subplots(figsize=(8, 6))

        # create a count plot to show the distribution between 0 and 1 targets
        ax = sns.countplot(data=self.data_df, x='target')

        # customize plot
        ax.set_title("Class Distribution", fontsize=14, fontweight="bold")
        ax.set_ylabel(ylabel="Count", fontsize=12, fontweight="bold")
        ax.set_xlabel(xlabel="Class", fontsize=12, fontweight="bold")
        ax.tick_params(axis='both', labelsize=10)

        # add counts above the bars
        for p in ax.patches:
            ax.annotate(text=f"{p.get_height():.0f}",
                        xy=(p.get_x() + p.get_width() / 2., p.get_height()),
                        xytext=(0, 10),
                        ha='center',
                        va='center',
                        fontsize=10,
                        color='black',
                        textcoords='offset points')

        plt.tight_layout()
        plt.show()


    def feature_correlation(self) -> None:
        """
        Finds 10 features that are closely correlated to the target.
        Then creates a correlation matrix to show it.
        """

        # find strongest feature correlations
        feature_correlation = self.data_df.corrwith(self.data_df['target']).abs().sort_values(ascending=False)

        # get only top 10 features
        strongest_features = feature_correlation.iloc[1:11].index.values

        # create the correlation matrix with the top features
        corr_matrix = self.data_df[strongest_features].corr()

        # create correlation matrix plot
        plt.figure(figsize=(12, 8))
        sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5)
        plt.title("Correlation Matrix with 10 strongest features to the target",
                  fontsize=20,
                  fontweight='bold')
        plt.xticks(fontsize=10, rotation=45)
        plt.yticks(fontsize=10)
        plt.show()


    def preprocess_data(self) -> None:
        """
        Fit and transform the training and test sets.

        Don't need to fit and transform the test set because the scaler
        has already found the weights from the training set.
        """
        self.x_train = self.scaler.fit_transform(self.x_train)
        self.x_test = self.scaler.transform(self.x_test)


    def train_model(self) -> None:
        """
        Train the data using the LogisticRegression() model.
        """
        self.model.fit(self.x_train, self.y_train)


    def evaluate_model(self, n: int = 10) -> None:
        """
        This function evaluates the performance of the model using several different metrics such as:
            - accuracy
            - precision and recall
            - f1 score
            - confusion matrix
            - ROC AUC score and curve

        The confusion matrix and roc curve will be shown. The other metrics will be printed
        to the console.

        Note: Model evaluation will be done on the testing data.

        Input:
            n: number of features used to evaluate the model
        """

        # preprocess the data
        self.preprocess_data()

        # train the model
        self.train_model()

        # get y_predictions to use for the evaluation metrics
        y_pred = self.model.predict(self.x_test)

        accuracy: float = accuracy_score(self.y_test, y_pred)
        precision: float = precision_score(self.y_test, y_pred)
        recall: float = recall_score(self.y_test, y_pred)
        f1: float = f1_score(self.y_test, y_pred)

        # get confusion matrix values: true negative, false positive, false negative, true positive
        tn, fp, fn, tp = confusion_matrix(self.y_test, y_pred).ravel()

        # plot confusion matrix
        plt.figure(figsize=(10, 8))
        sns.set_theme(style="ticks")
        sns.heatmap(data=confusion_matrix(y_true=self.y_test, y_pred=y_pred),
                    annot=True,
                    fmt='g',
                    cmap=sns.color_palette(['#F01E2C', '#3BB143']))
        plt.xlabel('Predicted', fontsize=12)
        plt.ylabel('True', fontsize=12)
        plt.title(label='Confusion Matrix', fontsize='16', fontweight='bold')
        plt.tick_params(axis='both', which='both', length=0)
        plt.show()

        # get fpr and tpr from roc curve and get roc_auc_score
        fpr, tpr, _ = roc_curve(y_true=self.y_test, y_score=y_pred)
        roc_auc = roc_auc_score(y_true=self.y_test, y_score=y_pred)

        # plot the roc curve
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='blue', label='ROC Curve (AUC = %0.2f)' % roc_auc)
        plt.plot([0, 1], [0, 1], color='black', linestyle='--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic (ROC) Curve', fontsize=16, fontweight='bold')
        plt.legend(loc='lower right')
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.grid(linestyle='--', alpha=0.8)
        plt.show()

        # plot how strong the top N features correlate to the target
        top_n_features = self.data_df.corrwith(self.data_df['target']).abs().sort_values(ascending=False)[1:n+1]
        bar_colors = ['red' if val < 0 else 'green' for val in top_n_features.values]
        plt.figure(figsize=(10, 8))
        plt.barh(y=top_n_features.index, width=top_n_features.values, color=bar_colors)
        plt.xlabel('Correlation value to Target')
        plt.ylabel('Features')
        plt.title(f"Top {n} Features' Correlation to Target", fontsize=16, fontweight='bold')
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.show()

        # add to evaluation metrics dataframe
        self.evaluation_metrics = pd.DataFrame({
            'Metric' : ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'True Positives', 'True Negatives',
                        'False Positives', 'False Negatives', 'ROC AUC Score'],
            'Value' : [accuracy, precision, recall, f1, float(tp), float(tn), float(fp), float(fn), roc_auc]})


    def cross_validate_model(self) -> None:
        """
        To further evaluate the model, this function performs 5-fold cross validation on it.
        """
        cv_scores = cross_val_score(self.model, self.data.data, self.data.target)
        self.evaluation_metrics.loc[len(self.evaluation_metrics)] = ['Mean Cross-Validation Score', np.mean(cv_scores)]
        # NOTE: I'm not sure how to store this yet
        # print("Cross-validation Scores:", cv_scores)


    def evaluation_scores_file(self):
        """
        This function creates a csv file containing the evaluation metric scores:
            - Accuracy Score
            - Precision Score
            - Recall Score
            - F1 Score
            - Confusion Matrix scores
                - True Positives
                - True Negatives
                - False Positives
                - False Negatives
            - ROC AUC Score
            - Cross Validation Scores
            - Mean Cross Validation Score

        Output:
            CSV file to current directory
        """
        # create a csv for these evaluation metrics
        self.evaluation_metrics.to_csv('~/Desktop/coding/ML_Projects/Logistic_Regression/Evaluation_Metric_Scores.txt',
                                       sep='\t', index=False,
                                       float_format='%.3f')


if __name__ == "__main__":

    cancer_data = load_breast_cancer()
    model = BreastCancerClassificationModel(cancer_data, 3000)

    model.visualize_data()
    model.feature_correlation()
    model.preprocess_data()
    model.train_model()
    model.evaluate_model()
    model.cross_validate_model()
    model.evaluation_scores_file()
