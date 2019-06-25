#include <Wire.h>

#define SLAVE_ADDRESS 0x56

const int totalLength = 16;
char Tag [totalLength];
int bytesread = 0;
char dumbChar;
volatile byte masterByte = 0;
volatile boolean flag = false;
int test [] = {1, 2, 3, 4};
int index = 0;
int count = 0;

void setup ()
{
  Serial.begin (9600);
  Serial.setTimeout (120);
  pinMode (2, INPUT_PULLUP);
  pinMode (9, OUTPUT);
  pinMode (A3, OUTPUT);
  digitalWrite (9, HIGH);

  Wire.begin (SLAVE_ADDRESS);
  Wire.onReceive (receiveData);
  Wire.onRequest (sendData);
}

void loop ()
{
  masterByte = 0;
  receiveData (1);
  Serial.println(masterByte);
  if (masterByte == 1){
    delay(20);
    if (Serial.available () > 0){
      index = 0;
      Serial.readBytesUntil (3, Tag, totalLength - 1);
    } else {
      Tag[0] = 0;
      index = 0;
      for (int i = 1; i < totalLength; i++) {
        Tag[i] = 255;
      }
    }
  } else {
    if (count > 500) {
      while(Serial.available () > 0) {
          char t  = Serial.read();
      }
      count = 0;
    } else {
      count++;
      delay(1);
    }
  }
}

void receiveData (int byteCount)
{
  while (Wire.available ())
    masterByte = Wire.read ();
}

void sendData ()
{
  Wire.write (Tag[index]);
  index++;
  index = index % totalLength;
}
