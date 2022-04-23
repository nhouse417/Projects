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

1. Run facial_req.py in the RaspberryPi terminal.
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
- 

## Setup

## Technologies
