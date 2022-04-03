// include the library code:

#include <LiquidCrystal.h>

// initialize the library by associating any needed LCD interface pin
// with the arduino pin number it is connected to
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// setup for pushbutton
const int pushButton = 6;     // connected to DP7

// led setup
int traffic[3] = {A0, A1, A2};
int pedestrian[2] = {A3, A4};

// time variables
unsigned long t0;
unsigned long t1;
unsigned long t2;  // aux
unsigned long on_time;

// wait time for a request just after traffic light turns green
unsigned int wait_time = 5000;  

void setup() {
  // set up the LCD's number of columns and rows:
  lcd.begin(16, 2);
  
  // Print initial message to pedestrian
  lcd.print("WAIT!");

  // setup for pushbutton
  pinMode(pushButton, INPUT);

  // for LED pins
  for(int i = A0; i < A5; i++){
    pinMode(i, OUTPUT);
  }

  t0 = millis(); // start time

}

void loop() {
  
  // count min time that traffic light will be green for
  t1 = millis();
  if(t1 - t0 < wait_time){
      on_time = t1 - t0;
  }

  // initial state for lights
  digitalWrite(traffic[2], HIGH);
  digitalWrite(pedestrian[0], HIGH);

  // if a request is made
  if(digitalRead(pushButton) == HIGH){
      // wait for traffic light to transition
      delay(8000 - on_time);

      // transitioning traffic light
      digitalWrite(traffic[2], LOW);
      digitalWrite(traffic[1], HIGH); // yellow delays for 2s
      delay(2500);
      digitalWrite(traffic[1], LOW);
      digitalWrite(traffic[0], HIGH);

      // transition pedestrian light
      digitalWrite(pedestrian[0], LOW);
      digitalWrite(pedestrian[1], HIGH);

      // countdown for walking
      lcd.clear();
      lcd.print("WALK!");

      int k = 7;
      while(k > -1){
        lcd.setCursor(0, 1);
        lcd.print(k);
        k--;
        delay(1000);
      }

      // turn signals back to initial state
      digitalWrite(pedestrian[1], LOW);
      digitalWrite(traffic[0], LOW);
      lcd.clear();
      lcd.setCursor(0,0);
      lcd.print("WAIT!");

      t0 = millis();
  }
}
