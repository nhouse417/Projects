"""
Testing pipeline usage to see if I still get runtime warnings.
This example is taken from the pipeline documentation on sklearn.
"""

from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

X, y = make_classification(random_state=0)
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)
pipe = Pipeline([('scaler', StandardScaler()), ('svc', SVC())])

# The pipeline can be used as any other estimator
# and avoids leaking the test set into the train set
print(pipe.fit(X_train, y_train).score(X_test, y_test))

# An estimator's parameter can be set using '__' syntax
pipe.set_params(svc__C=10).fit(X_train, y_train).score(X_test, y_test)

# -------------------------------------------------------------------------
# Testing the california housing dataset
# from sklearn.datasets import fetch_california_housing
# from sklearn.linear_model import LinearRegression
# from sklearn.model_selection import train_test_split

# x, y = fetch_california_housing(return_X_y=True)
# x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.4, random_state=0)

# model = LinearRegression().fit(x_train, y_train)
# print(model.score(x_train, y_train))
# print(model.score(x_test, y_test))
