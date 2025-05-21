#include <AceButton.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ESP32Servo.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

using namespace ace_button;

// ==== WiFi Config ====
const char* ssid = "doantotnghiep";
const char* password = "123456789";
const char* api_url = "http://192.168.137.1:8000/api/gate/event/";
const char* serverIP = "192.168.137.1";  // Địa chỉ IP của server
const int serverPort = 12345;            // Cổng của server
// Mảng trạng thái 6 slot (true: đang nhấn, false: nhả ra)
bool slotState[6] = { false, false, false, false, false, false };

WiFiClient client;
// ==== Nút nhấn ====
#define SwitchPin1 17  // Gate In
#define SwitchPin2 16  // Gate Out
#define SwitchPin3 15
#define SwitchPin4 13
#define SwitchPin5 14
#define SwitchPin6 25
#define SwitchPin7 26
#define SwitchPin8 27

// ==== RFID ====
#define RST_PIN 0
#define SS_1_PIN 4
#define SS_2_PIN 5

MFRC522 rfid1(SS_1_PIN, RST_PIN);
MFRC522 rfid2(SS_2_PIN, RST_PIN);

// ==== Servo ====
#define SERVO_PIN1 21
#define SERVO_PIN2 22
Servo servo1;
Servo servo2;

// ==== Biến RFID ====
String last_uid = "";

// ==== Prototype ====
bool sendGateEvent(String position, String mode, String rfid_id = "");
String readRFID(MFRC522& rfid, const char* label);

// ==== Nút AceButton ====
ButtonConfig config1, config2, config3, config4, config5, config6, config7, config8;
AceButton button1(&config1), button2(&config2), button3(&config3), button4(&config4),
  button5(&config5), button6(&config6), button7(&config7), button8(&config8);
const int slotPins[6] = {
  SwitchPin3,  // Slot 1
  SwitchPin4,  // Slot 2
  SwitchPin5,  // Slot 3
  SwitchPin6,  // Slot 4
  SwitchPin7,  // Slot 5
  SwitchPin8   // Slot 6
};

void setup() {
  Serial.begin(115200);
  SPI.begin();

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    // Serial.print(".");
  }
  Serial.println("\n✅ Da ket noi WiFi!");
  // Kết nối tới TCP server
  if (client.connect(serverIP, serverPort)) {
    Serial.println("✅ Kết nối TCP tới server thành công!");
  } else {
    Serial.println("❌ Kết nối TCP thất bại!");
  }
  rfid1.PCD_Init();
  rfid2.PCD_Init();

  pinMode(SwitchPin1, INPUT_PULLUP);
  pinMode(SwitchPin2, INPUT_PULLUP);
  pinMode(SwitchPin3, INPUT_PULLUP);
  pinMode(SwitchPin4, INPUT_PULLUP);
  pinMode(SwitchPin5, INPUT_PULLUP);
  pinMode(SwitchPin6, INPUT_PULLUP);
  pinMode(SwitchPin7, INPUT_PULLUP);
  pinMode(SwitchPin8, INPUT_PULLUP);

  config1.setEventHandler(buttonGateInHandler);
  config2.setEventHandler(buttonGateOutHandler);
  config3.setEventHandler(buttonSlot1Handler);
  config4.setEventHandler(buttonSlot2Handler);
  config5.setEventHandler(buttonSlot3Handler);
  config6.setEventHandler(buttonSlot4Handler);
  config7.setEventHandler(buttonSlot5Handler);
  config8.setEventHandler(buttonSlot6Handler);

  button1.init(SwitchPin1);
  button2.init(SwitchPin2);
  button3.init(SwitchPin3);
  button4.init(SwitchPin4);
  button5.init(SwitchPin5);
  button6.init(SwitchPin6);
  button7.init(SwitchPin7);
  button8.init(SwitchPin8);

  servo1.attach(SERVO_PIN1);
  servo2.attach(SERVO_PIN2);
  servo1.write(90);
  servo2.write(0);
  Serial.println("code:000000");
}
int check = 0;
void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    Serial.println(command);
  }
  if (client.available()) {
    String command = client.readStringUntil('\n');
    command.trim();
    Serial.println(command);

    if (command == "open_in") {
      servo1.write(0);
      delay(2000);
      servo1.write(90);
    } else if (command == "open_out") {
      servo2.write(90);
      check = 1;
      // ==== Cập nhật trạng thái slot thực tế từ chân nút ====
      for (int i = 0; i < 6; i++) {
        slotState[i] = digitalRead(slotPins[i]) == LOW;  // LOW = nhấn
      }

      // In chuỗi code
      String code = "code:";
      for (int i = 0; i < 6; i++) {
        code += slotState[i] ? "1" : "0";
      }
      Serial.println(code);
    }
  }


  button1.check();
  button2.check();
  button3.check();
  button4.check();
  button5.check();
  button6.check();
  button7.check();
  button8.check();

  String uid1 = readRFID(rfid1, "The 1");
  if (uid1 != "") {
    // Serial.println(">> UID The 1: " + uid1);
    if (sendGateEvent("entry", "rfid", uid1)) {
      servo1.write(0);
    }
  }

  String uid2 = readRFID(rfid2, "The 2");
  if (uid2 != "") {
    // Serial.println(">> UID The 2: " + uid2);
    if (sendGateEvent("exit", "rfid", uid2)) {
      servo2.write(90);
    }
  }
}

// ==== Xử lý nút nhấn ====
void buttonGateInHandler(AceButton* b, uint8_t e, uint8_t s) {
  if (e == AceButton::kEventPressed) {
    delay(1000);
    Serial.println("[IN] Nhan cam bien vao...");
    if (sendGateEvent("entry", "sensor")) {
      servo1.write(0);
    }
  } else if (e == AceButton::kEventReleased) {
    Serial.println("[IN] Nhan.");

    delay(2000);
    servo1.write(90);
  }
}

void buttonGateOutHandler(AceButton* b, uint8_t e, uint8_t s) {
  if (e == AceButton::kEventPressed) {
    // Serial.println("[OUT] Nhan cam bien ra...");
    if (sendGateEvent("exit", "sensor")) {
      servo2.write(90);
      check = 1;
    }
  } else if ((e == AceButton::kEventReleased) && (check == 1)) {
    delay(2000);
    check = 0;
    servo2.write(0);
  }
}

void handleSlotButton(uint8_t slotIndex, uint8_t event) {
  if (event == AceButton::kEventPressed) {
    Serial.printf("Slot %d PRESSED\n", slotIndex + 1);
    slotState[slotIndex] = true;
  } else if (event == AceButton::kEventReleased) {
    Serial.printf("Slot %d RELEASED\n", slotIndex + 1);
    slotState[slotIndex] = false;
  }


  for (int i = 0; i < 6; i++) {
    slotState[i] = digitalRead(slotPins[i]) == LOW;  // LOW = nhấn
  }

  // In chuỗi code
  String code = "code:";
  for (int i = 0; i < 6; i++) {
    code += slotState[i] ? "1" : "0";
  }
  Serial.println(code);
}

void buttonSlot1Handler(AceButton* b, uint8_t e, uint8_t s) {
  handleSlotButton(0, e);
}
void buttonSlot2Handler(AceButton* b, uint8_t e, uint8_t s) {
  handleSlotButton(1, e);
}
void buttonSlot3Handler(AceButton* b, uint8_t e, uint8_t s) {
  handleSlotButton(2, e);
}
void buttonSlot4Handler(AceButton* b, uint8_t e, uint8_t s) {
  handleSlotButton(3, e);
}
void buttonSlot5Handler(AceButton* b, uint8_t e, uint8_t s) {
  handleSlotButton(4, e);
}
void buttonSlot6Handler(AceButton* b, uint8_t e, uint8_t s) {
  handleSlotButton(5, e);
}

// ==== Đọc thẻ RFID ====
String readRFID(MFRC522& rfid, const char* label) {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return "";

  String uidStr = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uidStr += "0";
    uidStr += String(rfid.uid.uidByte[i], HEX);
  }
  uidStr.toUpperCase();

  // Serial.print(label);
  // Serial.print(" UID: ");
  // Serial.println(uidStr);

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  return uidStr;
}
// ==== Gửi API sự kiện cổng ====
bool sendGateEvent(String position, String mode, String rfid_id) {
  if (WiFi.status() != WL_CONNECTED) {
    // Serial.println("⚠ Không có WiFi");
    return false;
  }

  HTTPClient http;
  http.begin(api_url);
  http.addHeader("Content-Type", "application/json");

  String json;
  if (mode == "rfid") {
    json = "{\"mode\":\"rfid\", \"position\":\"" + position + "\", \"rfid_id\":\"" + rfid_id + "\"}";
  } else {
    json = "{\"mode\":\"sensor\", \"position\":\"" + position + "\"}";
  }

  int httpCode = http.POST(json);
  String response = http.getString();

  if (httpCode == 200) {
    // Serial.println("✅ API OK, mở cổng");
    // Serial.println(">> Phản hồi: " + response);

    // === Phân tích JSON trả về ===
    const size_t capacity = 512;
    DynamicJsonDocument doc(capacity);

    DeserializationError error = deserializeJson(doc, response);
    if (error) {
      // Serial.println("❌ Lỗi phân tích JSON!");
      http.end();
      return false;
    }
    String trang_thai = doc["trang_thai"] | "";
    if (trang_thai == "cho_thanh_toan") {
      String file_qr = doc["file_qr"] | "";

      // Xóa ký tự đầu tiên nếu chuỗi không rỗng
      if (file_qr.length() > 0) {
        file_qr = file_qr.substring(1);  // cắt từ ký tự thứ 1 trở đi (bỏ ký tự 0 đầu tiên)
      }

      // Serial.println("🧾 Vui lòng quét mã QR để thanh toán:");
      Serial.println("code:" + file_qr);

      http.end();
      return false;
    }

    http.end();
    return true;
  } else {
    // Serial.println("❌ Lỗi server: " + response);
    http.end();
    return false;
  }
}