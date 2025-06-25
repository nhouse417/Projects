# Convolutional Neural Network on MNIST dataset of handwritten digits

The goal of this project is to create a deep learning neural network that's able to recognize handwritten digits with accuracy. 

## Table of Contents

* [Background Information](#background-information)
* [Data Visualization](#data-visualization)
* [Implementation](#implementation)
* [Model Evaluation](#model-evaluation)
* [Improvements](#improvements)
* [Resources](#resources)

## Background Information

For this project, I used a Python virtual environment (pyenv) to isolate the installed packages from my computer's configuration. Using a pyenv allows me to update the installed packages if there are any updates to them. The installed packages are listed below:

- Python 3.12.10 (used because tensorflow isn't updated to Python 3.13 as of June 24, 2025)
- Keras 3.10.0
- Matplotlib 3.10.3
- Numpy 2.1.3
- Pandas 2.3.0

## Data Visualization

For this, I created a plot (shown below) showing the first 25 digits of the training set along with their labels.

![Figure_1](https://github.com/user-attachments/assets/8183c1d8-948e-4fb3-9e23-6cfd32cd86d2)

## Implementation

I created a Convolutional Neural Network (CNN) with 11 layers that include:

- 1 Rescaling preprocessing layer
- 1 Flatten layer
- 1 Dropout layer
- 3 Conv2D layers
- 3 MaxPooling2D layers
- 2 Dense layers

A picture of the model summary is shown below.
<img width="762" alt="model_summary" src="https://github.com/user-attachments/assets/a5cd42a5-3398-47bd-a1f2-01f3f56339c3" />


### CNN architecture explained

Next, I'll explain why I picked this architecture starting with the Rescaling layer. 

But before explaining the **Rescaling** layer, there's an **Input** layer before it which reshapes the input data to a 3D array. This is because a CNN is designed to process and analyze spatial relationships within data, specifically images. Because of this the input data is reshaped to (28, 28, 1) -> (row, columns, channels). The images in the dataset are 28x28 pixels and are black and white hence why the 'channels' parameter is '1' (if the images were in RGB, then the channels parameter would be 3). Then the Rescaling layer comes after. This layer is used to scale down the pixel values which range from 0 to 255 to a range of 0 to 1. It's important to scale down these values because computations can get large and might cause overflow.

Next, are the layers that do most of the work in this network which are the **Conv2D** and **MaxPooling2D** layers. This isn't going to be a full breakdown of what these layers do. But to summarize, the Conv2D layer places a kernel of size, in this project I went with a 3x3 kernel size, over the image and it multiplies each pixel of the kernel with the value of the pixel lying beneath it, then you sum those numbers up and place that value in a new convolved image. This is important because it helps the neural network find what pixels are important to the image, and it breaks down the original image into a smaller one. An example is shown below from the book "Why Machines Learn" by Anil Ananthaswamy. 

<img width="926" alt="Screenshot 2025-06-25 at 4 21 49 PM" src="https://github.com/user-attachments/assets/00a4d4f7-b1f9-469a-bd2f-35b9a80912b1" />

After the **Conv2D** layer, the **MaxPooling2d** layer takes the new convolved image then has it's own kernel that takes the maximum value within that kernel and then outputs that value to a new smaller image. An example is shown below. 

<img width="393" alt="MaxPooling2D" src="https://github.com/user-attachments/assets/9ea7be2a-74e1-4c9a-bad3-5803f3ddbc28" />










