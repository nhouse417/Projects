# Pedestrian Crossing Project

Simple pedestrian crossing project created with an Arduino, C Programming Language, and a circuit on a breadboard. 

## Table of Contents
* [Description](#description)
* [Parts](#parts)
* [Setup](#setup)
* [Technologies](#technologies)

## Description

I wanted to recreate a pedestrian that wants to cross the street. For this project, the pedestrian that wants to cross the street presses a pushbutton to request to cross the street. The traffic light then changes from green to yellow to red, and there's a pedestrian light that will change from red to green. The LCD screen will change from "WAIT!" to "WALK!" and a countdown will begin for the pedestrian to cross the street. When the countdown is done, the traffic light will change from red to green, and the pedestrian light will change from green to red. Lastly, the LCD screen will cahnge from "WALK!" to "WAIT!". 

## Parts

- 1x Arduino UNO R3
- 1x RBG 16x2 LCD (GWT C1627A by Adafruit)
- 1x 10k potentiometer
- 2x Breadboard
- 2x Green LED
- 2x Red LED
- 1x Yellow LED
- 6x 330ohms resistors
- 1x Pushbutton

## Setup

I have included a schematic in this repo, but the setup will be here as well. 

### Arduino

GND & 5V connected to breadboard

Digital Pins (DP)
- DP 12 -> LCD Pin 4 (Register Select)
- DP 11 -> LCD Pin 6 (Enable)
- DP 6 -> pushbutton
- DP 5 -> LCD Pin 11
- DP 4 -> LCD Pin 12
- DP 3 -> LCD Pin 13
- DP 2 -> LCD Pin 14

Analog Pins
- A0 -> Red Traffic Light LED
- A1 -> Yellow Traffic Light LED
- A2 -> Green Traffic Light LED
- A3 -> Red Pedestrian Light LED
- A4 -> Green Pedestrian Light LED

### LCD Screen 

- Pin 1 -> GND (Vss)
- Pin 2 -> 5V (Vdd)
- Pins 16-18 -> GND 
- Pin 15 -> 5V

### Pushbutton

#### One side

- 1 pin -> 5V
- 1 pin -> GND with resistor before connecting GND

#### On other side

- 1 pin to DP6 on Arduino

## Technologies

Arduino IDE, C Programming Language


