# Arduino RC car with RF transmission

RC car using two Arduinos (transmitter and receiver) communicating with each other through RF transmission to control the car's movement and speed.

## Table of Contents
* [Description](#description)
* [Parts](#parts)
* [Setup](#setup)
* [Code Explanation](#codeexplanation)
* [Technologies](#technologies)
* [Improvements](#improvements)

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

## Technologies

## Improvements
