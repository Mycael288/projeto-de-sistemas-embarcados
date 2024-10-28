// Inclusão de bibliotecas
#include <UnicViewAD.h>
#include <SoftwareSerial.h>

const byte rxPin = 3;
const byte txPin = 2;
int buttonValidCount = 0;
int buttonInvalidCount = 0;
SoftwareSerial mySerial(rxPin, txPin);
LCM Lcm(mySerial);

LcmVar buttonValid(0);
LcmVar buttonInvalid(1);  // Cria uma variável para o buttonInvalid

enum State {
  WAITING,
  PROCESSING_A,
  PROCESSING_B,
  RESET
};

State currentState = WAITING;

void setup() {
  Lcm.begin();
  mySerial.begin(115200);
  Serial.begin(9600);

  buttonValid.write(0);
  buttonInvalid.write(0);
}

void loop() {
  if (Serial.available() > 0) {
    char input = Serial.read();

    switch (input) {
      case 'A':
        currentState = PROCESSING_A;
        break;
      case 'B':
        currentState = PROCESSING_B;
        break;
      case 'C':
        currentState = RESET;
        break;
      default:
        currentState = WAITING;
        break;
    }
  }

  switch (currentState) {
    case PROCESSING_A:
      buttonValidCount++;
      buttonValid.write(buttonValidCount);  // Atualiza o valor no display para buttonValid
      currentState = WAITING;
      break;

    case PROCESSING_B:
      buttonInvalidCount++;
      buttonInvalid.write(buttonInvalidCount);  // Atualiza o valor no display para buttonInvalid
      currentState = WAITING;
      break;

    case RESET:
      buttonValidCount = 0;
      buttonInvalidCount = 0;
      buttonValid.write(buttonValidCount);  // Zera o valor no display para buttonValid
      buttonInvalid.write(buttonInvalidCount);  // Zera o valor no display para buttonInvalid
      currentState = WAITING;
      break;

    case WAITING:
    default:
      // Não faz nada, apenas aguarda por entrada
      break;
  }
}
