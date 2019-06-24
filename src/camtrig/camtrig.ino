


const int cam1Trig = 4;
const int cam2Trig = 5;







void setup() {
  pinMode(cam1Trig, OUTPUT);
  pinMode(cam2Trig, OUTPUT);
}

void loop() {


  digitalWrite(cam1Trig, LOW);
  digitalWrite(cam2Trig, LOW);
  delay(2);
  digitalWrite(cam1Trig, HIGH);
  digitalWrite(cam2Trig, HIGH);
  delay(2); 
  
}
