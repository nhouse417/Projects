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

## Technologies
