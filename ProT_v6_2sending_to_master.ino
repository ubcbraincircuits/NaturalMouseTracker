#include <Wire.h>

#define SLAVE_ADDRESS 0x33

const int totalLength = 16;
char Tag [totalLength];
int bytesread = 0;
char dumbChar;
volatile byte masterByte = 0;
volatile boolean flag = false;

void setup ()
{
 Serial.begin (9600);
 Serial.setTimeout (120);
 pinMode (2,INPUT_PULLUP);
 pinMode (9,OUTPUT);
 pinMode (A3,OUTPUT);
 digitalWrite (9,LOW);
 
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
   digitalWrite (9,HIGH);
   if (Serial.available ()>0)
   { 
         //if (digitalRead (4) == true)
           //digitalWrite (A3,1);
           
         Serial.readBytesUntil (3,Tag,totalLength-1);
         digitalWrite (9,LOW);
         sendData ();
   }
  }

//digitalWrite (A3,0);  
digitalWrite (9,LOW);
}

void receiveData (int byteCount)
{
 while (Wire.available ())
  masterByte = Wire.read ();
}

void sendData ()
{
 if (digitalRead (4) == true)
     Wire.write ((byte *)Tag,12);
}
