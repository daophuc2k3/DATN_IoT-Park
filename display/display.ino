#include <WiFi.h>
#include <SPI.h>
#include <GxEPD2_3C.h>
#include <Fonts/FreeMonoBold18pt7b.h>
#include <WiFiClientSecure.h>

// Cấu hình màn hình 4.2" 3 màu
GxEPD2_3C<GxEPD2_420_Z98c, GxEPD2_420_Z98c::HEIGHT> display(
  GxEPD2_420_Z98c(/*CS=*/15, /*DC=*/27, /*RST=*/26, /*BUSY=*/25));

// Cổng mặc định
#define httpPort 8000
#define httpsPort 443

// Bộ đệm và hàm phụ trợ BMP
uint8_t mono_palette_buffer[128];
uint8_t color_palette_buffer[128];
uint16_t rgb_palette_buffer[256];
uint8_t input_buffer[512];

uint16_t read16(WiFiClient& f) {
  uint16_t result;
  ((uint8_t*)&result)[0] = f.read();
  ((uint8_t*)&result)[1] = f.read();
  return result;
}

uint32_t read32(WiFiClient& f) {
  uint32_t result;
  ((uint8_t*)&result)[0] = f.read();
  ((uint8_t*)&result)[1] = f.read();
  ((uint8_t*)&result)[2] = f.read();
  ((uint8_t*)&result)[3] = f.read();
  return result;
}

uint32_t skip(WiFiClient& f, uint32_t length) {
  uint32_t skipped = 0;
  while (length--)
    if (f.read() >= 0) skipped++;
    else break;
  return skipped;
}

uint32_t read8n(WiFiClient& f, uint8_t* buf, uint32_t n) {
  uint32_t i = 0;
  while (i < n && f.available()) buf[i++] = f.read();
  return i;
}

// ⚠️ CHỈ SAU KHI ĐÃ CÓ display và các biến, mới include:
#include "GxEPD2_WiFi_Buffered.h"

// WiFi cấu hình
const char* ssid = "doantotnghiep";
const char* password = "123456789";
char filename[64];  // chứa tên file .bmp

void setup() {
  Serial.begin(115200);
  Serial2.begin(115200, SERIAL_8N1, 16, 17);  // RX=17, TX=16
  Serial.println("✅ UART (TX=16, RX=17) đã khởi tạo");

  SPI.begin(13, -1, 14, 15);  // SPI SCLK, MISO, MOSI, CS

  // Kết nối WiFi
  WiFi.begin(ssid, password);
  Serial.print("Đang kết nối WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nĐã kết nối!");
  Serial.println(WiFi.localIP());

  // Khởi tạo e-paper
  display.init();
  display.setRotation(4);
  display.setFullWindow();
}
void loop() {
  if (Serial.available()) {
    // Đọc chuỗi từ Serial
    size_t len = Serial.readBytesUntil('\n', filename, sizeof(filename) - 1);
    filename[len] = '\0';
    if (filename[len - 1] == '\r') filename[len - 1] = '\0';

    Serial.print("Đã nhận: ");
    Serial.println(filename);

    // Kiểm tra xem có bắt đầu bằng "code:" không
    if (strncmp(filename, "code:", 5) != 0) {
      Serial.println("⚠️ Bỏ qua vì không bắt đầu bằng 'code:'");
      return;
    }

    // Lấy phần nội dung phía sau "code:"
    char* payload = filename + 5;
    while (*payload == ' ') payload++;  // Bỏ khoảng trắng đầu

    // Nếu là file BMP
    if (strstr(payload, ".bmp") != NULL) {
      display.init();
      showBitmapFrom_HTTP_Buffered("192.168.137.1", "/", payload, 50, 0, true);
      display.hibernate();
    }

    // Nếu là chuỗi số: hiển thị bãi giữ xe
    // Nếu là chuỗi số: hiển thị bãi giữ xe
    else {
      // Nếu là chuỗi số 6 ký tự: hiển thị bãi giữ xe dạng nhị phân
      if (strlen(payload) == 6 && strspn(payload, "01") == 6) {
        bool has_car[7] = { false };  // 1-based index

        for (int i = 0; i < 6; i++) {
          if (payload[i] == '1') {
            has_car[i + 1] = true;
          }
        }

        display.init();
        display.setFullWindow();
        display.firstPage();
        do {
          display.fillScreen(GxEPD_WHITE);

          // Kích thước từng ô
          int box_w = 120;
          int box_h = 60;
          int spacing_x = 30;
          int spacing_y = 20;

          int grid_total_width = 2 * box_w + spacing_x;
          int grid_total_height = 3 * box_h + 2 * spacing_y;

          int offset_x = (display.width() - grid_total_width) / 2;
          int offset_y = (display.height() - grid_total_height) / 2;

          for (int i = 1; i <= 6; i++) {
            int col = (i - 1) / 3;
            int row = (i - 1) % 3;

            int x = offset_x + col * (box_w + spacing_x);
            int y = offset_y + row * (box_h + spacing_y);

            display.drawRect(x, y, box_w, box_h, GxEPD_BLACK);
            display.setFont(&FreeMonoBold18pt7b);
            display.setTextColor(GxEPD_BLACK);
            display.setCursor(x + 10, y + 42);
            display.print(i);

            if (has_car[i]) {
              int square_size = 20;
              display.fillRect(x + box_w - square_size - 10, y + 10, square_size, square_size, GxEPD_BLACK);
            }
          }
        } while (display.nextPage());

        display.hibernate();
        Serial.println("✅ Đã hiển thị bãi giữ xe (dạng nhị phân).");
      }
    }
  }
  if (Serial2.available()) {
    // Đọc chuỗi từ Serial
    size_t len = Serial2.readBytesUntil('\n', filename, sizeof(filename) - 1);
    filename[len] = '\0';
    if (filename[len - 1] == '\r') filename[len - 1] = '\0';

    Serial.print("Đã nhận: ");
    Serial.println(filename);

    // Kiểm tra xem có bắt đầu bằng "code:" không
    if (strncmp(filename, "code:", 5) != 0) {
      Serial.println("⚠️ Bỏ qua vì không bắt đầu bằng 'code:'");
      return;
    }

    // Lấy phần nội dung phía sau "code:"
    char* payload = filename + 5;
    while (*payload == ' ') payload++;  // Bỏ khoảng trắng đầu

    // Nếu là file BMP
    if (strstr(payload, ".bmp") != NULL) {
      display.init();
      showBitmapFrom_HTTP_Buffered("192.168.137.1", "/", payload, 50, 0, true);
      display.hibernate();
    }

    // Nếu là chuỗi số: hiển thị bãi giữ xe
    else {
      // Nếu là chuỗi số 6 ký tự: hiển thị bãi giữ xe dạng nhị phân
      if (strlen(payload) == 6 && strspn(payload, "01") == 6) {
        bool has_car[7] = { false };  // 1-based index

        for (int i = 0; i < 6; i++) {
          if (payload[i] == '1') {
            has_car[i + 1] = true;
          }
        }

        display.init();
        display.setFullWindow();
        display.firstPage();
        do {
          display.fillScreen(GxEPD_WHITE);

          // Kích thước từng ô
          int box_w = 120;
          int box_h = 60;
          int spacing_x = 30;
          int spacing_y = 20;

          int grid_total_width = 2 * box_w + spacing_x;
          int grid_total_height = 3 * box_h + 2 * spacing_y;

          int offset_x = (display.width() - grid_total_width) / 2;
          int offset_y = (display.height() - grid_total_height) / 2;

          for (int i = 1; i <= 6; i++) {
            int col = (i - 1) / 3;
            int row = (i - 1) % 3;

            int x = offset_x + col * (box_w + spacing_x);
            int y = offset_y + row * (box_h + spacing_y);

            display.drawRect(x, y, box_w, box_h, GxEPD_BLACK);
            display.setFont(&FreeMonoBold18pt7b);
            display.setTextColor(GxEPD_BLACK);
            display.setCursor(x + 10, y + 42);
            display.print(i);

            if (has_car[i]) {
              int square_size = 20;
              display.fillRect(x + box_w - square_size - 10, y + 10, square_size, square_size, GxEPD_BLACK);
            }
          }
        } while (display.nextPage());

        display.hibernate();
        Serial.println("✅ Đã hiển thị bãi giữ xe (dạng nhị phân).");
      }
    }
  }
}
