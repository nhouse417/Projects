"""
This file implements a convolution neural network used for digit recognition on the 
MNIST dataset.
"""

# 3rd party imports
import keras
from keras.datasets import mnist
from keras.layers import Conv2D, Dense, Dropout, Flatten, Input, MaxPooling2D, Rescaling
from keras.models import Sequential
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class DigitClassificationModel:
    """
    This class creates a convolution neural network (CNN) that recognizes digits from the 
    MNIST dataset.
    """

    def __init__(self):
        """
        Initializes the class:
            - loads the dataset and separates into training and test set
            - creates the model for the CNN
        """

        # want to make sure the typing is correct so that I could use numpy functions
        self.x_train: np.ndarray
        self.y_train: np.ndarray
        self.x_test: np.ndarray
        self.y_test: np.ndarray
        (self.x_train, self.y_train) , (self.x_test, self.y_test) = mnist.load_data()

        # change x_train and x_test dimensions to (60000, 28, 28, 1) for the convolution neural network
        self.x_train_reshaped = self.x_train.reshape(60000, 28, 28, 1)
        self.x_test_reshaped = self.x_test.reshape(10000, 28, 28, 1)

        # change y_train and y_test to a binary output vector for better CNN processing
        self.y_train_modified = keras.utils.to_categorical(self.y_train)
        self.y_test_modified = keras.utils.to_categorical(self.y_test)

        # captures the model's loss after running model.fit() function
        self.model_train_history: keras.callbacks.History = None
        self.model_test_history: list = None

        # build the CNN model
        self.network_model = Sequential([
            Input(shape=(28, 28, 1)),
            Rescaling(scale=1./255),
            Conv2D(filters=16, kernel_size=3, activation='relu'),
            MaxPooling2D(),
            Conv2D(filters=32, kernel_size=3, activation='relu'),
            MaxPooling2D(),
            Conv2D(filters=64, kernel_size=3, activation='relu'),
            MaxPooling2D(),
            Flatten(),
            Dense(units=128, activation='relu'),
            Dropout(rate=0.2),
            Dense(units=10, activation='softmax')
        ])


    def visualize_data(self):
        """
        Print out the first 9 samples in a 3x3 grid to see how the digits look.
        """
        
        plt.figure(figsize=(8,8))
        for i in range(25):
            plt.subplot(5, 5, i+1)
            plt.xticks([])
            plt.yticks([])
            plt.imshow(self.x_train[i], cmap='binary')
            plt.xlabel(self.y_train[i])
        plt.show()


    def preprocess_data(self):
        """
        Checks for any missing values and replaces them. Then gets the data ready for the CNN.
        """

        # check for NaN values in x_train, x_test, y_train, y_test
        # there were NONE
        # nan_values = np.isnan(self.y_test)
        # print(sum(nan_values))


    def compile_model(self):
        """
        Compiles the model with loss function, optimizer, and metric
        """

        self.network_model.compile(optimizer='adam',
                                   loss='categorical_crossentropy',
                                   metrics=['accuracy'])


    def train_model(self):
        """
        Train the CNN network.
        """

        self.model_train_history = self.network_model.fit(x=self.x_train_reshaped,
                                                          y=self.y_train_modified,
                                                          validation_split=0.25,
                                                          epochs=10,
                                                          batch_size=64)


    def evaluate_model(self):
        """
        Evaluate the CNN model on the test data.
        """

        self.model_test_history = self.network_model.evaluate(x=self.x_test_reshaped, y=self.y_test_modified)
        evaluation = pd.DataFrame({'Test Loss' : [self.model_test_history[0]*100],
                                   'Test Accuracy' : [self.model_test_history[1]*100]})
        evaluation.to_csv('~/Desktop/coding/ML_Projects/Image_Classification_CNN/Evaluation_Test_Scores.txt',
                          sep='\t', index=False, float_format='%.3f')


    def plot_model_metrics(self):
        """
        Plot the accuracy and loss for every epoch from the training, validation, and test data.
        """

        # plot model_train_history accuracy
        plt.title(label='CNN Model Accuracy', fontweight='bold', fontsize=14)
        plt.plot(self.model_train_history.history['accuracy'], label='Training accuracy')
        plt.plot(self.model_train_history.history['val_accuracy'], label='Validation accuracy')
        plt.xlabel("Epoch Number")
        plt.ylabel('Accuracy')
        plt.legend()
        plt.show()

        # plot model_train_history loss
        plt.title(label='CNN Model Loss', fontweight='bold', fontsize=14)
        plt.plot(self.model_train_history.history['loss'], label='Training loss')
        plt.plot(self.model_train_history.history['val_loss'], label='Validation loss')
        plt.xlabel("Epoch Number")
        plt.ylabel('Loss')
        plt.legend()
        plt.show()


    def implement_gui(self):
        """
        Create a GUI for the user to draw a number and have the network predict what number it is and 
        display the network's accuracy.

        Work in Progress
        """

if __name__ == "__main__":

    model = DigitClassificationModel()
    model.visualize_data()
    model.compile_model()
    model.train_model()
    model.evaluate_model()
    model.plot_model_metrics()
