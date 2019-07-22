#include <CmdParser.hpp>



/*
   When a valid command is received, it will be stored in this struct.
   Only one command is stored at a time (currect command is overwritten when
   new valid command is received and parsed.)
*/
struct CMD {

  uint16_t argc;
  String cmd;
  String* params = NULL;
};
struct CMD* command = new CMD;

// Serial command parser
CmdParser cmdParser;
// This timeout is in ms
uint32_t cmdParserTimeout = 10000;


const int CAMTRIG1 = 8;
const int CAMTRIG2 = 9;
void setup() {

  // Block until serial connection established
  Serial.begin(115200);
  while(!Serial) {
    delay(100);
  }

  pinMode(CAMTRIG1, OUTPUT);
  pinMode(CAMTRIG2, OUTPUT);
  pinMode(13, OUTPUT);

  Serial.write("ARDUINO READY\n");
}


/*
   This function listens on the USB serial port for a newline
   terminated command to arrive. The command is parsed and stored
   in the global struct CMD* <command>. The return code indicates
   one of three conditions:
    0 = New command received and stored in <command>
    1 = Listening timed out
   -1 = Parsing error

   Note: This command times out after <cmdParserTimeout> ms.
*/
int listenForCommandWithTimeout() {

    CmdBuffer<64> myBuffer;
    String cmd;
    uint16_t argc;
    String* params;



    if (myBuffer.readFromSerial(&Serial, cmdParserTimeout))
    {
        if (cmdParser.parseCmd(&myBuffer) != CMDPARSER_ERROR)
        {

            myBuffer.getStringFromBuffer();
            cmd = cmdParser.getCommand();
            argc = cmdParser.getParamCount();

            if(command->params != NULL)
            {
              delete[] command->params;
            }

            params = new String[argc];
            for (size_t i = 0; i < argc; i++)
            {
                params[i] = cmdParser.getCmdParam(i);
            }

            command->argc = argc;
            command->cmd = cmd;
            command->params = params;


            return 0;
        }
        else
        {
            Serial.println("Parser error!");
            return -1;
        }
    }
    else
    {
      return 1;
    }
}



/*
   This function runs the command stored in the global struct CMD* <command>.
   It identifies the command to be run, and ensures the correct number of parameters
   are present. Once this is confirmed, the appropriate command is called.

   Note: Implementing new commands involves adding an "else if" clause
   to this function that calls the new command (which also needs to be implemented).
*/
int runCommand() {

  int rc;

  if(command->cmd == "PULSE")
  {
      if(command->argc != 3)
      {
        sendResponse("Invalid number of parameters!");
        rc = -1;
      }
      else
      {
        rc = pulse(command->params[1].toInt(), command->params[2].toInt());
      }
  }

  return rc;
}


int pulse(int numFramesToAcquire, int triggerFrequency_us) {

  for(int i = 0; i < numFramesToAcquire; i++)
  {
      digitalWrite(CAMTRIG1, HIGH);
      digitalWrite(CAMTRIG2, HIGH);
      delayMicroseconds(triggerFrequency_us/2);
      digitalWrite(CAMTRIG1, LOW);
      digitalWrite(CAMTRIG2, LOW);
      delayMicroseconds(triggerFrequency_us/2);
  }

  return 0;
}


/*
   Wrapper for writing to serial USB port in a way
   python3 will understand.
*/
void sendResponse(String response) {

  response += "\n";
  Serial.write(response.c_str());
}




void loop() {

  // New command received (0), Parse error (-1), Listening timed out (1)
  int rc = listenForCommandWithTimeout();

  switch(rc)
  {
    case 0:
      runCommand();
      break;
    case -1:
      // parse error
      break;
    default:
      break;
  }

}
