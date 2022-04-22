#include <LiquidCrystal.h>

const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

void setup() {
  lcd.begin(16, 2);
  Serial.begin(9600);
}

void loop() {

  // Read from serial port
  if(Serial.available()){
    String s = Serial.readString();  
      if(s == "success"){
        lcd.clear();
        lcd.print("Face Detection");
        lcd.setCursor(0, 1);
        lcd.print("Successful");  
      }else if(s == "failure"){
        lcd.clear();
        lcd.print("Unknown Face");  
      }
  }
 
}
