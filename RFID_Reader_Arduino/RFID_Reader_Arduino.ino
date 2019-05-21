#include <Wire.h>

#define SLAVE_ADDRESS 0x34

const int totalLength = 16;
char Tag [totalLength];
int bytesread = 0;
char dumbChar;
volatile byte masterByte = 0;
volatile boolean flag = false;
int test [] = {1, 2, 3, 4};
int index = 0;

void setup ()
{
  Serial.begin (9600);
  Serial.setTimeout (120);
  pinMode (2, INPUT_PULLUP);
  pinMode (9, OUTPUT);
  pinMode (A3, OUTPUT);
  digitalWrite (9, LOW);

  Wire.begin (SLAVE_ADDRESS);
  Wire.onReceive (receiveData);
  Wire.onRequest (sendData);
}

void loop ()
{
  masterByte = 0;
  receiveData (1);
  Serial.println(masterByte);
  if (masterByte == 1)
  {
    digitalWrite (9, HIGH);
    while(Serial.available () > 0) {
        char t  = Serial.read();
     }
    delay(125); //Required to give the trinket time to set up, 125 ms at minimum
    if (Serial.available () > 0)
    {
      index = 0;
      Serial.readBytesUntil (3, Tag, totalLength - 1);
      digitalWrite (9, LOW);
    } else {
        Tag[0] = 0;
        index = 0;
        for (int i = 1; i < totalLength; i++) {
          Tag[i] = 255;
        }
    }
  }
  digitalWrite (9, LOW);
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
