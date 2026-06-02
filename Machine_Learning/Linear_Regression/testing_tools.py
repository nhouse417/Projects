# Testing tools functions -------------------------------------------------------------

# x_train_dummy = np.array([[2104, 5, 1, 45], [1416, 3, 2, 40], [852, 2, 1, 35]])
# y_train_dummy = np.array([460, 232, 178])
# w_train_dummy = np.array([ 0.39133535, 18.75376741, -53.36032453, -26.42131618])
# b_train_dummy = 785.1811367994083

# cost = compute_cost(x_train_dummy, y_train_dummy, w_train_dummy, b_train_dummy, lambda_tmp)
# print(cost)

# dj_dw, dj_db = compute_gradient(x_train_dummy, y_train_dummy, w_train_dummy, b_train_dummy, lambda_tmp)
# print(f"This is dj_dw: {dj_dw}")
# print(f"This is dj_db: {dj_db}")

# testing gradient descent
# initial_w = np.zeros_like(w_train_dummy)
# initial_b = 0.
# iterations_dummy = 1000
# alpha_dummy = 5.0e-7
# w_final, b_final, _ = gradient_descent(x_train_dummy, y_train_dummy, initial_w, initial_b, lambda_tmp, alpha_dummy, iterations_dummy)

# Functions work correctly without regularization

# Testing functions with regularization ------------------------------------------------

# compute cost linear regresssion WORKS

# np.random.seed(1)
# X_tmp = np.random.rand(5,6)
# y_tmp = np.array([0,1,0,1,0])
# w_tmp = np.random.rand(X_tmp.shape[1]).reshape(-1,)-0.5
# b_tmp = 0.5
# lambda_tmp = 0.7
# cost_tmp = compute_cost(X_tmp, y_tmp, w_tmp, b_tmp, lambda_tmp)
# print("Regularized cost:", cost_tmp)

# compute gradient linear regression WORKS 

# np.random.seed(1)
# X_tmp = np.random.rand(5,3)
# y_tmp = np.array([0,1,0,1,0])
# w_tmp = np.random.rand(X_tmp.shape[1])
# b_tmp = 0.5
# lambda_tmp = 0.7
# dj_dw_tmp, dj_db_tmp =  compute_gradient(X_tmp, y_tmp, w_tmp, b_tmp, lambda_tmp)

# print(f"dj_db: {dj_db_tmp}", )
# print(f"Regularized dj_dw:\n {dj_dw_tmp.tolist()}", )