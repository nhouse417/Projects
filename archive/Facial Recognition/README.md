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
open the headshots.py file in Geany (the IDE I used on the RaspberryPi). **NOTE:** In this file, there'll be a variable "name" and you want to put the person's name in this variable. For example, I changed the variable name to Noah because that's the name of the folder in my dataset. Now, you want to run that file in the terminal using the command "python3 headshots.py". This will start the webcam and ask you to take pictures of yourself which you can do by pressing the space bar. This will take your
pictures and put them into the dataset folder named after the person you want. After that is done, it's time to train the model which you can do by
running the command "python3 train_model.py". This file will create an encodings file called "encodings.pickle" which holds the criteria needed for 
identifying faces. 

After training the model, you can now run the facial recognition with the command "python3 facial_req.py" in the RaspberryPi terminal. 

This is a very popular project so I wanted to do more with it than facial recognition. So I added two LEDs, a green LED for successful facial recognition and a red LED for failure. This was simple, I used two GPIO pins which were numbered 4 and 27. This [link](https://www.etechnophiles.com/raspberry-pi-3-b-pinout-with-gpio-functions-schematic-and-specs-in-detail/#raspberry-pi-3b-pinout-with-gpio-function) shows the GPIO layout of the RaspberryPi 3b+. Then I initialized these pins to output which can be seen in the facial_req.py file. Then I used two female-to-male wires and connected them to their respective LEDs.

Also I added an LCD screen so that user can see more output from the program. One problem I had was that since the program would run until the user pressed the "q" key, the window showing what the camera sees would freeze and stop showing what the camera sees. This is why I added the LCD screen so that the user can see if the facial recognition was still working. At first, I tried sending a signal from the Pi to the Arduino but connecting a GPIO pin to an Arduino pin. However this didn't work because before even starting the program the LCD would display "Face Detection Successful". This led me to believe that the Arduino pin was receiving a high signal (using a digital pin) even though the program wasn't running. 

This led me to use USB Serial Communication between the Pi and Arduino. In facial_req.py, I initialized the port by getting the name of the Arduino using the command "ls dev/tty*" while the Arduino was connected to the Pi. The name of my Arduino was "/dev/ttyACM0". After that I setup the port for communication by using the serial.Serial() function which can be seen in facial_req.py file. On the Arduino side, I opened the serial port on the 9600 baud rate which is the same that I used on the Pi. Then I checked if there was data in the Arduino's serial port. The Pi would send either "success" or "failure" and the Arduino would check for either of those two. If it was "success" the LCD screen displayed "Face Detection Successful", if it was "failure" then it would display "Unknown Face". 

## Technologies

Raspberry Pi 3b+ with Raspian OS 32-bit, Python, Geany IDE, Arduino UNO R3, Arduino IDE, USB Serial Communication. 
