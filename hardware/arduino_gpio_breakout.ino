/*
 * Arduino GPIO Breakout Firmware
 * 
 * This firmware allows an Arduino to act as a GPIO breakout board
 * for the TelemetryIQ system. It accepts commands via serial and
 * controls GPIO pins accordingly.
 * 
 * Commands:
 *   CONFIG:pin:mode:pull:active_low - Configure a pin
 *   READ:pin - Read digital pin value
 *   WRITE:pin:value - Write digital pin value (0 or 1)
 *   READ_ANALOG:pin - Read analog pin value (0-1023)
 *   PWM:pin:value - Set PWM value (0-255)
 *   STATUS - Get status of all configured pins
 * 
 * Example:
 *   CONFIG:2:input:up:0
 *   READ:2
 *   WRITE:3:1
 *   READ_ANALOG:A0
 *   PWM:9:128
 */

#define MAX_PINS 20
#define SERIAL_BAUD 115200

// Pin configuration structure
struct PinConfig {
  int pin;
  char mode;  // 'i' = input, 'o' = output, 'p' = pwm
  bool pullup;
  bool active_low;
  bool configured;
};

PinConfig pins[MAX_PINS];
int pin_count = 0;

void setup() {
  Serial.begin(SERIAL_BAUD);
  
  // Initialize pin array
  for (int i = 0; i < MAX_PINS; i++) {
    pins[i].configured = false;
  }
  
  // Wait for serial connection
  while (!Serial) {
    delay(10);
  }
  
  Serial.println("OK:Arduino GPIO Breakout Ready");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      processCommand(command);
    }
  }
  
  // Periodic status update (optional)
  // Could send pin states periodically
}

void processCommand(String cmd) {
  if (cmd.startsWith("CONFIG:")) {
    // CONFIG:pin:mode:pull:active_low
    int pin = getValue(cmd, 1).toInt();
    String mode_str = getValue(cmd, 2);
    String pull_str = getValue(cmd, 3);
    int active_low = getValue(cmd, 4).toInt();
    
    char mode = mode_str.charAt(0);
    bool pullup = (pull_str == "up");
    bool active_low_bool = (active_low == 1);
    
    configurePin(pin, mode, pullup, active_low_bool);
    Serial.println("OK:CONFIG");
    
  } else if (cmd.startsWith("READ:")) {
    // READ:pin
    int pin = getValue(cmd, 1).toInt();
    int value = readPin(pin);
    
    if (value >= 0) {
      Serial.print("VALUE:");
      Serial.println(value);
    } else {
      Serial.println("ERROR:Pin not configured");
    }
    
  } else if (cmd.startsWith("WRITE:")) {
    // WRITE:pin:value
    int pin = getValue(cmd, 1).toInt();
    int value = getValue(cmd, 2).toInt();
    
    if (writePin(pin, value)) {
      Serial.println("OK:WRITE");
    } else {
      Serial.println("ERROR:Pin not configured or not output");
    }
    
  } else if (cmd.startsWith("READ_ANALOG:")) {
    // READ_ANALOG:pin
    String pin_str = getValue(cmd, 1);
    int pin;
    
    if (pin_str.startsWith("A")) {
      // Analog pin (A0, A1, etc.)
      pin = pin_str.substring(1).toInt();
      int value = analogRead(pin);
      Serial.print("VALUE:");
      Serial.println(value);
    } else {
      Serial.println("ERROR:Invalid analog pin");
    }
    
  } else if (cmd.startsWith("PWM:")) {
    // PWM:pin:value
    int pin = getValue(cmd, 1).toInt();
    int value = getValue(cmd, 2).toInt();
    value = constrain(value, 0, 255);
    
    analogWrite(pin, value);
    Serial.println("OK:PWM");
    
  } else if (cmd == "STATUS") {
    // STATUS - Return status of all configured pins
    Serial.print("STATUS:");
    for (int i = 0; i < pin_count; i++) {
      if (pins[i].configured) {
        Serial.print(pins[i].pin);
        Serial.print(":");
        Serial.print(pins[i].mode);
        Serial.print(":");
        Serial.print(readPin(pins[i].pin));
        if (i < pin_count - 1) Serial.print(",");
      }
    }
    Serial.println();
    
  } else {
    Serial.println("ERROR:Unknown command");
  }
}

void configurePin(int pin, char mode, bool pullup, bool active_low) {
  // Find or create pin config
  int index = findPinIndex(pin);
  if (index < 0) {
    if (pin_count < MAX_PINS) {
      index = pin_count++;
    } else {
      return;  // No space
    }
  }
  
  pins[index].pin = pin;
  pins[index].mode = mode;
  pins[index].pullup = pullup;
  pins[index].active_low = active_low;
  pins[index].configured = true;
  
  // Configure hardware
  if (mode == 'i') {
    // Input mode
    if (pullup) {
      pinMode(pin, INPUT_PULLUP);
    } else {
      pinMode(pin, INPUT);
    }
  } else if (mode == 'o') {
    // Output mode
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);
  } else if (mode == 'p') {
    // PWM mode
    pinMode(pin, OUTPUT);
    analogWrite(pin, 0);
  }
}

int readPin(int pin) {
  int index = findPinIndex(pin);
  if (index < 0 || !pins[index].configured) {
    return -1;
  }
  
  if (pins[index].mode == 'i') {
    int value = digitalRead(pin);
    if (pins[index].active_low) {
      return (value == LOW) ? 1 : 0;
    } else {
      return (value == HIGH) ? 1 : 0;
    }
  }
  
  return -1;
}

bool writePin(int pin, int value) {
  int index = findPinIndex(pin);
  if (index < 0 || !pins[index].configured) {
    return false;
  }
  
  if (pins[index].mode == 'o') {
    if (pins[index].active_low) {
      digitalWrite(pin, (value == 1) ? LOW : HIGH);
    } else {
      digitalWrite(pin, (value == 1) ? HIGH : LOW);
    }
    return true;
  }
  
  return false;
}

int findPinIndex(int pin) {
  for (int i = 0; i < pin_count; i++) {
    if (pins[i].pin == pin) {
      return i;
    }
  }
  return -1;
}

String getValue(String data, int index) {
  int found = 0;
  int strIndex[] = {0, -1};
  int maxIndex = data.length() - 1;
  
  for (int i = 0; i <= maxIndex && found <= index; i++) {
    if (data.charAt(i) == ':' || i == maxIndex) {
      found++;
      strIndex[0] = strIndex[1] + 1;
      strIndex[1] = (i == maxIndex) ? i + 1 : i;
    }
  }
  
  return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}
















