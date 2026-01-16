/*
 * ESPHome Custom Component for Somfy PoE Motor Control
 *
 * This component implements the Somfy PoE protocol to control blinds/shades
 * from ESPHome. It handles TLS connection, PIN authentication, AES encryption,
 * and motor control commands.
 *
 * Based on reverse-engineered Somfy PoE Motor API v1.2
 */

#pragma once

#include "esphome.h"
#include <WiFiClientSecure.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>
#include "mbedtls/aes.h"
#include "mbedtls/md.h"

namespace esphome {
namespace somfy_poe {

class SomfyPoeMotor : public Component {
 public:
  SomfyPoeMotor(const char* motor_ip, const char* pin_code)
    : motor_ip_(motor_ip),
      pin_code_(pin_code),
      tcp_port_(55056),
      udp_port_(55055),
      message_id_(1),
      is_authenticated_(false),
      current_position_(-1.0f),
      target_id_("") {
  }

  void setup() override {
    ESP_LOGI("somfy_poe", "Setting up Somfy PoE Motor component");

    // Initialize UDP
    udp_.begin(udp_port_);

    // Attempt initial connection
    connect_and_authenticate();
  }

  void loop() override {
    // Check for UDP responses
    check_udp_responses();

    // Reconnect if connection was lost
    if (!is_authenticated_ && millis() - last_connect_attempt_ > 30000) {
      connect_and_authenticate();
    }
  }

  // Motor control methods
  bool move_up() {
    return send_move_command("move.up", -1.0f);
  }

  bool move_down() {
    return send_move_command("move.down", -1.0f);
  }

  bool stop() {
    return send_move_command("move.stop", -1.0f);
  }

  bool move_to_position(float position) {
    // Position: 0 = open, 100 = closed
    if (position < 0.0f) position = 0.0f;
    if (position > 100.0f) position = 100.0f;
    return send_move_command("move.to", position);
  }

  bool wink() {
    // Makes the motor jog briefly for identification
    return send_move_command("move.wink", -1.0f);
  }

  float get_position() {
    request_position_update();
    return current_position_;
  }

  const char* get_status() {
    return current_status_.c_str();
  }

  void reconnect() {
    is_authenticated_ = false;
    connect_and_authenticate();
  }

 private:
  // Connection parameters
  const char* motor_ip_;
  const char* pin_code_;
  uint16_t tcp_port_;
  uint16_t udp_port_;

  // State
  uint32_t message_id_;
  bool is_authenticated_;
  float current_position_;
  String current_status_;
  String target_id_;
  uint8_t aes_key_[16];
  unsigned long last_connect_attempt_;

  // Network clients
  WiFiClientSecure tcp_client_;
  WiFiUDP udp_;

  bool connect_and_authenticate() {
    ESP_LOGI("somfy_poe", "Connecting to motor at %s:%d", motor_ip_, tcp_port_);
    last_connect_attempt_ = millis();

    // Configure TLS - motors use self-signed certificates
    tcp_client_.setInsecure();  // Don't verify motor certificate

    // Connect to motor
    if (!tcp_client_.connect(motor_ip_, tcp_port_)) {
      ESP_LOGE("somfy_poe", "TCP connection failed");
      return false;
    }

    ESP_LOGI("somfy_poe", "TCP connected, authenticating...");

    // Step 1: Authenticate with PIN
    if (!authenticate_with_pin()) {
      tcp_client_.stop();
      return false;
    }

    // Step 2: Get AES encryption key
    if (!get_encryption_key()) {
      tcp_client_.stop();
      return false;
    }

    is_authenticated_ = true;
    ESP_LOGI("somfy_poe", "Successfully authenticated with motor");

    // Request initial position
    request_position_update();

    return true;
  }

  bool authenticate_with_pin() {
    // Create authentication request
    StaticJsonDocument<256> doc;
    doc["id"] = message_id_++;
    doc["method"] = "security.auth";
    JsonObject params = doc.createNestedObject("params");
    params["code"] = pin_code_;

    String request;
    serializeJson(doc, request);

    // Send request
    tcp_client_.print(request);

    // Wait for response
    if (!wait_for_tcp_response()) {
      ESP_LOGE("somfy_poe", "No authentication response");
      return false;
    }

    // Parse response
    String response = tcp_client_.readString();
    StaticJsonDocument<512> response_doc;
    DeserializationError error = deserializeJson(response_doc, response);

    if (error) {
      ESP_LOGE("somfy_poe", "Failed to parse auth response: %s", error.c_str());
      return false;
    }

    if (!response_doc["result"].as<bool>()) {
      ESP_LOGE("somfy_poe", "Authentication failed - check PIN code");
      return false;
    }

    target_id_ = response_doc["targetID"].as<String>();
    ESP_LOGI("somfy_poe", "Authenticated! Target ID: %s", target_id_.c_str());

    return true;
  }

  bool get_encryption_key() {
    // Create key request
    StaticJsonDocument<256> doc;
    doc["id"] = message_id_++;
    doc["method"] = "security.get";

    String request;
    serializeJson(doc, request);

    // Send request
    tcp_client_.print(request);

    // Wait for response
    if (!wait_for_tcp_response()) {
      ESP_LOGE("somfy_poe", "No key exchange response");
      return false;
    }

    // Parse response
    String response = tcp_client_.readString();
    StaticJsonDocument<512> response_doc;
    DeserializationError error = deserializeJson(response_doc, response);

    if (error) {
      ESP_LOGE("somfy_poe", "Failed to parse key response: %s", error.c_str());
      return false;
    }

    if (!response_doc["result"].as<bool>()) {
      ESP_LOGE("somfy_poe", "Key exchange failed");
      return false;
    }

    // Extract AES key from array
    JsonArray key_array = response_doc["key"].as<JsonArray>();
    for (int i = 0; i < 16; i++) {
      aes_key_[i] = key_array[i].as<uint8_t>();
    }

    ESP_LOGI("somfy_poe", "AES key received");
    return true;
  }

  bool wait_for_tcp_response(uint32_t timeout_ms = 5000) {
    unsigned long start = millis();
    while (!tcp_client_.available()) {
      if (millis() - start > timeout_ms) {
        return false;
      }
      delay(10);
    }
    return true;
  }

  bool send_move_command(const char* method, float position) {
    if (!is_authenticated_) {
      ESP_LOGW("somfy_poe", "Not authenticated, cannot send command");
      return false;
    }

    // Create command
    StaticJsonDocument<512> doc;
    doc["id"] = message_id_++;
    doc["method"] = method;

    JsonObject params = doc.createNestedObject("params");
    params["targetID"] = target_id_;
    params["seq"] = 1;

    // Add position parameter if needed
    if (strcmp(method, "move.to") == 0 && position >= 0.0f) {
      params["position"] = position;
    }

    String command;
    serializeJson(doc, command);

    // Encrypt and send via UDP
    return send_encrypted_udp(command);
  }

  bool request_position_update() {
    if (!is_authenticated_) {
      return false;
    }

    // Create position query
    StaticJsonDocument<256> doc;
    doc["id"] = message_id_++;
    doc["method"] = "status.position";

    JsonObject params = doc.createNestedObject("params");
    params["targetID"] = target_id_;

    String query;
    serializeJson(doc, query);

    return send_encrypted_udp(query);
  }

  bool send_encrypted_udp(const String& message) {
    // Generate random IV (16 bytes)
    uint8_t iv[16];
    for (int i = 0; i < 16; i++) {
      iv[i] = random(256);
    }

    // Pad message to multiple of 16 bytes (PKCS7 padding)
    size_t message_len = message.length();
    size_t padded_len = ((message_len / 16) + 1) * 16;
    uint8_t padding = padded_len - message_len;

    uint8_t* padded_message = new uint8_t[padded_len];
    memcpy(padded_message, message.c_str(), message_len);
    for (size_t i = message_len; i < padded_len; i++) {
      padded_message[i] = padding;
    }

    // Encrypt using AES-128-CBC
    uint8_t* encrypted = new uint8_t[padded_len];
    mbedtls_aes_context aes;
    mbedtls_aes_init(&aes);
    mbedtls_aes_setkey_enc(&aes, aes_key_, 128);

    uint8_t iv_copy[16];
    memcpy(iv_copy, iv, 16);
    mbedtls_aes_crypt_cbc(&aes, MBEDTLS_AES_ENCRYPT, padded_len,
                          iv_copy, padded_message, encrypted);
    mbedtls_aes_free(&aes);

    // Send IV + encrypted data via UDP
    udp_.beginPacket(motor_ip_, udp_port_);
    udp_.write(iv, 16);
    udp_.write(encrypted, padded_len);
    bool success = udp_.endPacket();

    // Cleanup
    delete[] padded_message;
    delete[] encrypted;

    return success;
  }

  void check_udp_responses() {
    int packet_size = udp_.parsePacket();
    if (packet_size <= 0) {
      return;
    }

    // Read encrypted response
    uint8_t* buffer = new uint8_t[packet_size];
    udp_.read(buffer, packet_size);

    if (packet_size < 16) {
      ESP_LOGW("somfy_poe", "UDP packet too small");
      delete[] buffer;
      return;
    }

    // Extract IV and encrypted data
    uint8_t iv[16];
    memcpy(iv, buffer, 16);

    size_t encrypted_len = packet_size - 16;
    uint8_t* encrypted = buffer + 16;

    // Decrypt using AES-128-CBC
    uint8_t* decrypted = new uint8_t[encrypted_len];
    mbedtls_aes_context aes;
    mbedtls_aes_init(&aes);
    mbedtls_aes_setkey_dec(&aes, aes_key_, 128);
    mbedtls_aes_crypt_cbc(&aes, MBEDTLS_AES_DECRYPT, encrypted_len,
                          iv, encrypted, decrypted);
    mbedtls_aes_free(&aes);

    // Remove PKCS7 padding
    uint8_t padding = decrypted[encrypted_len - 1];
    size_t message_len = encrypted_len - padding;

    // Convert to string
    String message = "";
    for (size_t i = 0; i < message_len; i++) {
      message += (char)decrypted[i];
    }

    // Parse JSON response
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, message);

    if (!error) {
      process_response(doc);
    } else {
      ESP_LOGW("somfy_poe", "Failed to parse UDP response: %s", error.c_str());
    }

    // Cleanup
    delete[] buffer;
    delete[] decrypted;
  }

  void process_response(JsonDocument& doc) {
    const char* method = doc["method"];

    // Check if this is a position update
    if (doc.containsKey("position")) {
      JsonObject pos = doc["position"];
      current_position_ = pos["value"].as<float>();
      current_status_ = pos["direction"].as<String>();

      ESP_LOGD("somfy_poe", "Position: %.1f%%, Status: %s",
               current_position_, current_status_.c_str());
    }

    // Log result status
    if (doc.containsKey("result")) {
      bool result = doc["result"].as<bool>();
      if (!result) {
        ESP_LOGW("somfy_poe", "Command failed");
      }
    }
  }
};

}  // namespace somfy_poe
}  // namespace esphome
