#include <Arduino.h>

// --- Pin Definitions ---
const int ESTOP_PIN = 2;     // Interrupt pin for safety
const int X_LIMIT_PIN = 5;   // Limit switch for X-axis
const int Y_LIMIT_PIN = 6;   // Limit switch for Y-axis

const int X_STEP_PIN = 3;    // Motor Control Pins
const int X_DIR_PIN = 7;
const int Y_STEP_PIN = 4;
const int Y_DIR_PIN = 8;

// --- System States ---
enum MachineState {
    STATE_BOOT,
    STATE_HOMING,
    STATE_READY,
    STATE_ALARM
};

MachineState currentState = STATE_BOOT;
volatile bool isSystemTripped = false;

// --- Function Declarations ---
void emergencyStopISR();
void executeHoming();

void setup() {
    Serial.begin(115200);

    // Pin Configurations
    pinMode(ESTOP_PIN, INPUT_PULLUP);
    pinMode(X_LIMIT_PIN, INPUT_PULLUP);
    pinMode(Y_LIMIT_PIN, INPUT_PULLUP);

    pinMode(X_STEP_PIN, OUTPUT);
    pinMode(X_DIR_PIN, OUTPUT);
    pinMode(Y_STEP_PIN, OUTPUT);
    pinMode(Y_DIR_PIN, OUTPUT);

    attachInterrupt(digitalPinToInterrupt(ESTOP_PIN), emergencyStopISR, FALLING);
    
    Serial.println("System Booted. Homing required.");
    currentState = STATE_HOMING;
}

void loop() {
    // Universal Safety Check
    if (isSystemTripped) {
        currentState = STATE_ALARM;
    }

    switch (currentState) {
        case STATE_HOMING:
            Serial.println("Starting Homing Cycle...");
            executeHoming();
            break;

        case STATE_READY:
            // Normal operation loop
            Serial.println("Status: READY. Awaiting G-code instructions...");
            delay(2000);
            break;

        case STATE_ALARM:
            // Lockdown loop
            Serial.println("!! CRITICAL ALARM !! Machine Locked. Reset Hardware.");
            delay(1000);
            break;
            
        default:
            break;
    }
}

/**
 * Executes a sequential axis calibration sequence using limit switches
 */
void executeHoming() {
    // 1. Set motor directions to reverse toward the switches
    // (Adjust HIGH/LOW depending on physical motor orientation)
    digitalWrite(X_DIR_PIN, LOW); 
    digitalWrite(Y_DIR_PIN, LOW);

    Serial.println("Homing X-axis...");
    // Keep pulsing X motor until limit switch is pressed (reads LOW because of INPUT_PULLUP)
    while (digitalRead(X_LIMIT_PIN) == HIGH) {
        if (isSystemTripped) return; // Break if E-stop hit
        digitalWrite(X_STEP_PIN, HIGH);
        delayMicroseconds(800); // Pulse delay controls speed
        digitalWrite(X_STEP_PIN, LOW);
        delayMicroseconds(800);
    }
    Serial.println("X-axis Calibrated.");
    delay(200); // Short settle pause

    Serial.println("Homing Y-axis...");
    while (digitalRead(Y_LIMIT_PIN) == HIGH) {
        if (isSystemTripped) return;
        digitalWrite(Y_STEP_PIN, HIGH);
        delayMicroseconds(800);
        digitalWrite(Y_STEP_PIN, LOW);
        delayMicroseconds(800);
    }
    Serial.println("Y-axis Calibrated. Machine Zero Established.");
    
    // Transition system to active state
    currentState = STATE_READY;
}

void emergencyStopISR() {
    isSystemTripped = true;
    digitalWrite(X_STEP_PIN, LOW);
    digitalWrite(Y_STEP_PIN, LOW);
}