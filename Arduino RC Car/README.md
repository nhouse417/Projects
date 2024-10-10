# Arduino RC car with RF transmission

RC car using two Arduinos (transmitter and receiver) communicating with each other through RF transmission to control the car's movement and speed.

## Table of Contents
* [Description](#description)
* [Parts](#parts)
* [Setup](#setup)
* [Code Explanation](#codeexplanation)
* [Technologies](#technologies)
* [Improvements](#improvements)
* [Resources](#resources)

## Description

Remote controlled car using two Arduinos. One for the transmitter which is the controller that uses an analog joystick to move the car. Also the transmitter can change the speed at which the car moves in any direction. Another Arduino is used as the receiver which receives the analog inputs from the joystick and translates that information to move the car. Both use RF transmitters for communication.

## Parts

- 2x Arduino Uno R3
- 1x L298N DC Motor Driver Module
- 2x nRF24L01 Wireless RF Module
- 1x Analog Joystick Module or Arduino PS2 Joystick
- 1x 2WD Smart Robot Chassis Kit from Amazon
- 2x 9V battery holder
- 2x 9V batteries (I used Duracell 9V 580mAh batteries)
- 1x Arduino power supply for transmitter (9VDC 1A Arduino compatible power supply)
- Male-to-Male jumper wires
- Female-to-Male jumper wires

## Setup

Schematics will be included in this repository, but it'll be explained here as well.

### RC Car

#### 9V battery for Arduino
- Positive terminal -> Arduino Vin
- GND -> Arduino GND

#### 9V battery for L298n module
- Positive terminal -> 12V input
- GND -> L298n GND

#### Arduino 
- GND -> GND of L298n module
- GND -> GND of nRF24L01 module
- 3.3V -> VCC of nRF24L01 module
- Pin 9 -> CE pin of nRF24L01 module
- Pin 10 -> CSN pin of nRF24L01 module
- Pin 11 -> MOSI pin of nRF24L01 module
- Pin 12 -> MISO pin of nRF24L01 module
- Pin 13 -> SCK pin of nRF24L01 module
- Pin 8 -> IN1 of L298n module
- Pin 7 -> IN2 of L298n module
- Pin 3 -> IN3 of L298n module
- Pin 2 -> IN4 of L298n module
- Pin 6 -> ENA of L298n module
- Pin 5 -> ENB of L298n module

#### Motor
- red and black wires were included in the RC chassis kit
- Right side motor (red) -> OUT1 of L298n module
- Right side motor (black) -> OUT2 of L298n module
- Left side motor (red) -> OUT3 of L298n module
- Left side motor (black) -> OUT4 of L298n module

### Transmitter w/ second Arduino
This Arduino is powered by a 9VDC 1A power supply.

#### nRF24L01 module
- VCC -> 3.3V 
- GND -> GND 
- CE -> Pin 9
- CSN -> Pin 10
- MOSI -> Pin 11
- MISO -> Pin 12
- SCK -> Pin 13

#### Analog joystick
- GND -> GND
- 5V -> 5V
- VRx -> A1
- VRy -> A0

## Code Explanation

It's important that when you're connecting the nRF transmitters, that the pipe/address that they're listening to have the same value. In the transmitter and receiver code, the pipe has the same value.

### Transmitter
  The code is fairly straightforward, but make sure that when you instantiate the radio class to assign the CSN pin to pin 10 on the Arduino. This is because for the RF communication to work, CSN must be connected to the CSN pin of the Arduino. You could assign it to a different pin but you would still need to activate pin 10 by making it an "OUTPUT". The rest of the code is populating the "sentData" array with the inputs from the analog joystick and sending that array over RF. An improvement would be creating a struct that contains data members for the analog joystick values and sending that struct over RF.

### Receiver
  To start with the assigning of pins, I assigned ENA and ENB from the L298n module to pins 6 and 5 because those two pins generate a PWM frequency of 980Hz. This allows the vehicle to respond quickly to inputs from the analog joystick. Also when I had these pins assigned to non-PWM Arduino pins, the motor never got the instructions and there would be a constant buzzing sound.
  Next in the loop, I always want to check if the radio is available (if RF is available) to see if communication is available. After obtaining the transmitter's values, I map the y-value (0-1023) from -255 to 255 to determine the speed and which direction the car should move. For the equation that calculates the motor speed left and right, I got that from the youtube video I used for this project. But this equation is used so that both motors dont spin at the same speed resulting in easier control of the car. The youtube video will be linked in the resources section. Then I want to constrain the left and right motor speed values to be within the range the motor can take. Lastly, this part "motorSpeedLeft = -motorSpeedLeft" and "motorSpeedRight = -motorSpeedRight" is used for backwards movement of the car.

## Technologies

## Improvements
