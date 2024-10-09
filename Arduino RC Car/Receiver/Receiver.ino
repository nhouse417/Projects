#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// radio(ce_pin, csn_pin)
RF24 radio(9, 10);

// the radio reading pipe
const uint64_t pipe = 0xABABABABABAB;

// set up motor pins
const int IN1 = 8;
const int IN2 = 7;
const int IN3 = 3;
const int IN4 = 2;
const int ENA = 6;
const int ENB = 5;

void setup() {
  // setup Serial for printing to the serial monitor
  Serial.begin(9600);
  
  // initialize RF module
  radio.begin();
  radio.openReadingPipe(1, pipe);
  radio.startListening();

  // set motor pins to output
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);

}

void loop() {
  // only do something if there's a payload available from transmitter
  if (radio.available()) {
    // array for sending messages
    int receivedData[2];
    radio.read(receivedData, sizeof(receivedData));

    int x_value = receivedData[0];
    int y_value = receivedData[1];

    int motorSpeed = map(y_value, 0, 1023, -255, 255);
  
    // calculate turning motor speeds based on x-joystick value
    int motorSpeedLeft = motorSpeed + (x_value - 512) / 2;
    int motorSpeedRight = motorSpeed - (x_value - 512) / 2;

    // ensure motor speeds are within valid range
    motorSpeedLeft = constrain(motorSpeedLeft, -255, 255);
    motorSpeedRight = constrain(motorSpeedRight, -255, 255);

    // set motors' direction
    if (motorSpeedLeft > 0) {
      digitalWrite(IN1, LOW);
      digitalWrite(IN2, HIGH);
    } else {
      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);
      motorSpeedLeft = -motorSpeedLeft;  
    }

    if (motorSpeedRight > 0) {
      digitalWrite(IN3, LOW);
      digitalWrite(IN4, HIGH);
    } else {
      digitalWrite(IN3, HIGH);
      digitalWrite(IN4, LOW);
      motorSpeedRight = -motorSpeedRight;
    }

    // set motor speeds
    analogWrite(ENA, motorSpeedLeft);
    analogWrite(ENB, motorSpeedRight);
  }
}
