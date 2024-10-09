#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// radio(ce_pin, csn_pin)
RF24 radio(9, 10);

// for the radio writing pipe
const uint64_t pipe = 0xABABABABABAB;

// joystick pins
const int joystickX = A1;
const int joystickY = A0;

void setup() {
  // sets up serial monitor for print messages
  Serial.begin(9600);

  // setup pins for input
  pinMode(joystickX, INPUT);
  pinMode(joystickY, INPUT);
  
  // initialize RF module
  radio.begin();
  radio.openWritingPipe(pipe);
}

void loop() {
  // array for sending messages
  int sentData[2];
  
  // read joystick values
  int x_value = analogRead(joystickX);
  int y_value = analogRead(joystickY);

  sentData[0] = x_value;
  sentData[1] = y_value;
  
  // send values to receiver
  radio.write(sentData, sizeof(sentData));

  // in milliseconds; 20ms -> 0.05s
  delay(20);
}
