# Facial Recognition Project 

A facial recognition project using a Raspberry Pi 3b+, OpenCV's Haar Cascade Model, Python, Arduino, C Programming Language, Solderless Breadboard,
LCD Screen, LEDs, a webcam, and USB Serial Communication.

## Table of Contents 

* [Description](#description)
* [Parts](#parts)
* [Setup](#setup)
* [Technologies](#technologies)

## Description 

In this project, I wanted to get familiar with how facial recognition is done using Python's OpenCV library. I strengthened my Python skills as this 
project is written in Python except for the Arduino code which was written in C. Also, I learned how a microprocessor (RaspberryPi) and microcontroller
(Arduino) can communicate with each other via a USB serial connection. 

The project flow is as follows:

1. Run facial_req.py in the RaspberryPi terminal by running the command "python3 facial_req.py". 
2. The webcam is started up and a window shows what the camera sees.
3. If there is a face in view of the webcam, the program will determine if the face is in the dataset.
4. If the face is in the dataset, the window will display the person's name (i.e. Noah).
   a. A green LED will turn on.
   b. The LCD screen will display "Face Detection Successful".
5. If the face isn't in the dataset, the window will display "unknown".
   a. A red LED will turn on.
   b. The LCD screen will display "Unknown Face".
6. Once the program is ran, it will stay on until the user presses "q" on the keyboard.

## Parts

- RaspberryPi 3b+ with Raspian OS 32-bit
- Arduino UNO R3
- 1x Green LED
- 1x Red LED
- 1x LCD Screen (Adafruit RBG backlight positive 16x2)
- potentiometer for the LCD screen
- Logitech C270 HD webcam
- Male-to-Male wires
- Female-to-Male wires

## Setup

I have included a schematic of the setup in the project files. 

To use the OpenCV library, you have to install the OpenCV library along with the imutils library. The imutils library is a series
of convenience functions that help OpenCV computing on the RaspberryPi. You can visit this [link](https://pimylifeup.com/raspberry-pi-opencv/)
for a step-by-step guide on installing OpenCV on your pi. 

After installing OpenCV, it's time to train the model for facial recognition. First, create a folder that will hold all of these python files, 
then create a folder called "dataset". This will hold the images for the person that will be recognized by the software. Inside of this dataset
folder, create another folder with the person's name you want to be recognized. In my case, I created a folder named "Noah". After that is done,
open the headshots.py file in Geany (the IDE I used on the RaspberryPi). Now, you want to run that file in the terminal using the command "python3 headshots.py". This will start the webcam and ask you to take pictures of yourself which you can do by pressing the space bar. This will take your
pictures and put them into the dataset folder named after the person you want. After that is done, it's time to train the model which you can do by
running the command "python3 train_model.py". This file will create an encodings file called "encodings.pickle" which holds the criteria needed for 
identifying faces. 

After training the model, you can now run the facial recognition with the command "python3 facial_req.py" in the RaspberryPi terminal. 

## Technologies
