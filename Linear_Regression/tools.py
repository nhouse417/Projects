"""
Tools file containing functions for:
- computing cost
- computing gradient descent parameters w and b
- computing gradient descent

TODO:
- logistic regression (could use gradient descent but add name specifier parameter)
- sigmoid function
- plotting stuff?
"""

import copy
import math
import numpy as np
import numpy.typing as npt


def compute_cost(x: npt.NDArray,
                 y: npt.NDArray,
                 w: npt.NDArray,
                 b: float,
                 lambda_: float) -> float:
    """
    This function computes the prediction (f_wb = w * x_i + b) and 
    cost (f_wb(x) - y_i)**2) for that sample. Also computes regularization / overfitting
    to help produce a more accurate value. 

    Returns the total cost over all the samples.
    This will be used to see if the cost decreases over time (which it should w/ correct w and b).

    Inputs:
        x: training data
        y: target values
        w: model parameters
        b: model parameter
        lambda_: controls amount of regularization applied

    Outputs: total cost with regularization over all samples
    """
    m = x.shape[0]
    n = len(w)
    cost = 0.

    # calculate cost over training data
    for i in range(m):
        f_wb_i = np.dot(x[i], w) + b
        cost = cost + (f_wb_i - y[i])**2
    cost = cost / (2 * m)

    # calculate regularization value
    reg_cost = 0.
    for i in range(n):
        reg_cost += (w[i]**2)
    reg_cost = (lambda_ / (2 * m)) * reg_cost

    total_cost = cost + reg_cost
    return total_cost


def compute_gradient(x: npt.NDArray,
                     y: npt.NDArray,
                     w: npt.NDArray,
                     b: float,
                     lambda_: float) -> tuple[npt.NDArray, float]:
    """
    Implements linear regression gradient with regularization.

    Inputs:
        x: training data
        y: target values
        w: model parameters
        b: model parameter
        lambda_: controls amount of regularization applied

    Output: the derivative of w and b (dj_dw and dj_db) over all samples
    """
    m, n = x.shape
    dj_dw = np.zeros((n,))
    dj_db = 0.

    # calculate cost and update dj_dw array
    for i in range(m):
        cost = (np.dot(x[i], w) + b) - y[i]
        for j in range(n):
            dj_dw[j] = dj_dw[j] + cost * x[i, j]
        dj_db += cost

    dj_dw = dj_dw / m
    dj_db = dj_db / m

    # calculate regularization value
    for i in range(n):
        dj_dw[i] = dj_dw[i] + (lambda_ / m) * w[i]

    return dj_dw, dj_db


def gradient_descent(x: npt.NDArray,
                     y: npt.NDArray,
                     w: npt.NDArray,
                     b: float,
                     lambda_: float,
                     alpha: float,
                     num_iters: int) -> tuple[npt.NDArray, float, list]:
    """
    Uses compute_cost function to store cost values for printing.
    Uses compute_gradient function to get best w and b values to
    implement gradient descent.

    Inputs:
        x: training data
        y: target values
        w: model parameters
        b: model parameter
        alpha: learning rate
        num_iters: how many iterations to run gradient descent

    Outputs:
        w: updated values
        b: updated value
        cost_history: list of cost values
    """
    cost_history = []
    w_in = copy.deepcopy(w) # don't want to change the value
    b_in = b

    for i in range(num_iters):

        # compute dj_dw and dj_db
        dj_dw, dj_db = compute_gradient(x, y, w_in, b_in, lambda_)

        # implement gradient descent algorithm
        w_in = w_in - alpha * dj_dw
        b_in = b_in - alpha * dj_db

        # save cost value at every iteration
        if i < 100000:
            cost_history.append(compute_cost(x, y, w_in, b_in, lambda_))

        # print cost value every 100 iterations
        if i % math.ceil(num_iters / 10) == 0:
            print(f"Iteration {i:4d}: Cost {cost_history[-1]:8.2f}")

    return w_in, b_in, cost_history


def zscore_normalization(x: npt.NDArray) -> npt.NDArray:
    """
    Cleans the feature data to be within acceptable ranges so that gradient descent converges faster.

    Input:
        x: training data

    Output:
        x: zscore normalized training data
    """
    # find mean (mu) of each column/feature
    mu = np.mean(x, axis=0)

    # find the standard deviation (sigma) of each column/feature
    sigma = np.std(x, axis=0)

    # calculate normalized x
    x_norm = (x - mu) / sigma

    return x_norm