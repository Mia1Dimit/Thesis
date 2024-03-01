#include <ArduinoBLE.h>

#define BUFFER_SIZE 61 // Number of float values per packet
#define TOTAL_SAMPLES 61 // Total number of float values to capture
#define PACKET_SIZE 244 // Size of one packet in bytes
#define NUM_PACKETS (TOTAL_SAMPLES / BUFFER_SIZE) // Total number of packets
#define SAMPLE_RATE 800
#define BAUD_RATE 2000000
#define INPUT_PIN A0

BLEService emgService("19B10000-E8F2-537E-4F6C-D104768A1214");  // Bluetooth® Low Energy LED Service

BLECharacteristic EMG_Filtered_Characteristic("a3b1a544-8794-11ee-b9d1-0242ac120002", BLERead | BLENotify, sizeof(float) * BUFFER_SIZE, true);

float filteredBuffer[TOTAL_SAMPLES];

int bufferIndex = 0;
unsigned long total = 0;
bool capturingData = true; // Flag to control data capture
unsigned long startTime, endTime;


void setup() {
  Serial.begin(BAUD_RATE);
  while (!Serial);

  // begin initialization
  if (!BLE.begin()) {
    Serial.println("starting Bluetooth® Low Energy module failed!");
    while (1);
  }


  Serial.println("BLE module initialized");

  // Print peripheral address
  Serial.print("Peripheral address: ");
  Serial.println(BLE.address());  // Print BLE device address

  // Set advertised local name and service UUID
  BLE.setLocalName("EMG");
  BLE.setAdvertisedService(emgService);

  // Add characteristics to the service
  emgService.addCharacteristic(EMG_Filtered_Characteristic);

  // Add service
  BLE.addService(emgService);

  // For EMG_Filtered_Characteristic
  uint8_t initialFilteredData[sizeof(float) * BUFFER_SIZE] = {0}; // Initialize with zeros or specific default values
  EMG_Filtered_Characteristic.writeValue(initialFilteredData, sizeof(initialFilteredData));

  // Start advertising
  BLE.advertise();

  Serial.println("BLE EMG Peripheral setup completed");
  
}


void loop() {
  // listen for Bluetooth® Low Energy peripherals to connect:
  BLEDevice central = BLE.central();

  // if a central is connected to peripheral:
  if (central) {
    Serial.println("Connected to central: ");
    Serial.println(central.address());
    // Introduce a 0.5-second delay after connection before sending data
    delay(500);
    startTime = millis();

    // while the central is still connected to peripheral:
    while (central.connected()) {
      static unsigned long past = 0;
      unsigned long present = millis();
      unsigned long interval = present - past;
      past = present;

      static long timer = 0;
      timer -= interval;
      
      if (timer < 0) {
        timer += 1000 / SAMPLE_RATE;
        float sensorValue = analogRead(INPUT_PIN);
        float filteredSignal = EMGFilter(sensorValue);
        //filteredBuffer[bufferIndex] = filteredSignal;
        total++;
        //bufferIndex++;

        /*if (bufferIndex >= TOTAL_SAMPLES) {
          bufferIndex = 0; // Reset buffer index
          capturingData = false; // Stop data capture

          // Measure the time taken by sendPackets for filteredBuffer
          startTime = millis();
          sendPackets(filteredBuffer, TOTAL_SAMPLES, EMG_Filtered_Characteristic);
          endTime = millis();
          //Serial.print("Time taken by sendPackets (Filtered): ");
          //Serial.println(endTime - startTime);

          capturingData = true; // Resume data capture for the next set of samples
        }*/
      }
      endTime = millis();
      if(endTime - startTime >= 25000){
        Serial.print("Total values: ");
        Serial.println(total);
        while(1);
      }      
    }
    // when the central disconnects, print it out:
    Serial.print(F("Disconnected from central: "));
    Serial.println(central.address());
    //Serial.print("Total values: ");
    //Serial.println(total);
  }
}

/*void processEMGData() {
  if (capturingData) {
    static unsigned long past = 0;
    unsigned long present = micros();
    unsigned long interval = present - past;
    past = present;

    static long timer = 0;
    timer -= interval;
    
    if (timer < 0) {
      timer += 1000000 / SAMPLE_RATE;
      float sensorValue = analogRead(INPUT_PIN);
      float filteredSignal = EMGFilter(sensorValue);
      //filteredBuffer[bufferIndex] = filteredSignal;
      total++;
      //bufferIndex++;      

      if (bufferIndex >= TOTAL_SAMPLES) {
        bufferIndex = 0; // Reset buffer index
        capturingData = false; // Stop data capture

        // Measure the time taken by sendPackets for filteredBuffer
        startTime = millis();
        sendPackets(filteredBuffer, TOTAL_SAMPLES, EMG_Filtered_Characteristic);
        endTime = millis();
        //Serial.print("Time taken by sendPackets (Filtered): ");
        //Serial.println(endTime - startTime);

        capturingData = true; // Resume data capture for the next set of samples
      }
    }
  }
}*/

/*void sendPackets(float buffer[], int size, BLECharacteristic& characteristic) {
  int packets = size / BUFFER_SIZE;

  // Ensure we only send the total number of packets
  if (packets > NUM_PACKETS) {
    packets = NUM_PACKETS;
  }

  for (int i = 0; i < packets; i++) {
    int start = i * BUFFER_SIZE;
    int end = start + BUFFER_SIZE;

    // Create a buffer to hold the packet data
    uint8_t packetData[PACKET_SIZE];
    memset(packetData, 0, PACKET_SIZE); // Initialize the buffer to 0

    // Copy float values to the packet data buffer as bytes
    int byteOffset = 0;
    for (int j = start; j < end; j++) {
      memcpy(&packetData[byteOffset], &buffer[j], sizeof(float));
      byteOffset += sizeof(float);
    }

    // Send the packet over BLE
    characteristic.writeValue(packetData, PACKET_SIZE);
  }
}*/

// Band-Pass Butterworth IIR digital filter, generated using filter_gen.py.
// Sampling rate: 800 Hz, frequency: [25.0, 380.0] Hz.
// Filter is order 4, implemented as second-order sections (biquads).
// Reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html
float EMGFilter(float input){
  float output = input;
  {
    static float z1, z2; // filter section state
    float x = output - -1.65840715*z1 - 0.69178512*z2;
    output = 0.62836880*x + -1.25673760*z1 + 0.62836880*z2;
    z2 = z1;
    z1 = x;
  }
  {
    static float z1, z2; // filter section state
    float x = output - 1.72298871*z1 - 0.74505076*z2;
    output = 1.00000000*x + 2.00000000*z1 + 1.00000000*z2;
    z2 = z1;
    z1 = x;
  }
  {
    static float z1, z2; // filter section state
    float x = output - -1.82654732*z1 - 0.86249199*z2;
    output = 1.00000000*x + -2.00000000*z1 + 1.00000000*z2;
    z2 = z1;
    z1 = x;
  }
  {
    static float z1, z2; // filter section state
    float x = output - 1.86486416*z1 - 0.88821381*z2;
    output = 1.00000000*x + 2.00000000*z1 + 1.00000000*z2;
    z2 = z1;
    z1 = x;
  }
  return output;
}