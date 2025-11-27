# NUCLEO-H755ZI-Q STM32 Firmware Template

This document provides a template for STM32 firmware to run on the NUCLEO-H755ZI-Q board for integration with the AI Tuner application.

## STM32CubeMX Configuration

### Required Peripherals:

1. **USART3** (UART Communication)
   - Mode: Asynchronous
   - Baudrate: 921600
   - Word Length: 8 bits
   - Parity: None
   - Stop Bits: 1
   - DMA: Enable TX and RX DMA channels

2. **SPI1** (SPI Communication - Optional)
   - Mode: Slave
   - Clock: 8MHz
   - Data Size: 8 bits
   - DMA: Enable TX and RX DMA channels

3. **I2C1** (I2C Communication - Optional)
   - Mode: I2C
   - Speed: 400kHz
   - Address: 0x48 (configurable)

4. **ADC1** (Analog Sensor Reading)
   - Resolution: 12-bit
   - Channels: Multiple (configure as needed)
   - DMA: Enable DMA for continuous conversion

5. **CAN1** (CAN Bus - Optional)
   - Mode: CAN FD
   - Bitrate: 1Mbps
   - Loopback: Disabled

6. **FreeRTOS** (Real-Time OS)
   - Enable FreeRTOS
   - Heap: 4 (Dynamic allocation)
   - Tasks: Create sensor reading task

## Firmware Structure

### Main Tasks:

1. **Communication Task** (UART/SPI/I2C)
   - Handles incoming commands from Pi
   - Sends sensor data responses
   - Protocol: JSON over UART/SPI/I2C

2. **Sensor Reading Task**
   - Reads ADC channels
   - Reads I2C sensors
   - Reads CAN messages
   - Updates sensor buffers

3. **Status Task**
   - Monitors CPU usage
   - Monitors memory
   - Reports errors

## Example Firmware Code (C/C++)

### UART Communication Handler

```c
#include "main.h"
#include "usart.h"
#include "cmsis_os.h"
#include "string.h"
#include "stdio.h"

// JSON response buffer
char json_response[512];

// Sensor data structure
typedef struct {
    float temperature;
    float pressure;
    float rpm;
    uint32_t timestamp;
} SensorData_t;

SensorData_t sensor_data = {0};

// UART receive buffer
uint8_t uart_rx_buffer[256];
uint8_t uart_rx_index = 0;

// Parse command and generate response
void process_command(char* cmd) {
    // Simple JSON parser (use cJSON library for production)
    if (strstr(cmd, "\"cmd\":\"ping\"") != NULL) {
        sprintf(json_response, "{\"status\":\"ok\",\"message\":\"pong\"}\n");
    }
    else if (strstr(cmd, "\"cmd\":\"read_sensors\"") != NULL) {
        // Read sensors
        sensor_data.temperature = read_temperature();
        sensor_data.pressure = read_pressure();
        sensor_data.rpm = read_rpm();
        sensor_data.timestamp = HAL_GetTick();
        
        // Format JSON response
        sprintf(json_response,
            "{\"status\":\"ok\",\"data\":{"
            "\"temperature\":%.2f,"
            "\"pressure\":%.2f,"
            "\"rpm\":%.0f"
            "},\"timestamp\":%lu}\n",
            sensor_data.temperature,
            sensor_data.pressure,
            sensor_data.rpm,
            sensor_data.timestamp);
    }
    else if (strstr(cmd, "\"cmd\":\"get_status\"") != NULL) {
        // Get system status
        sprintf(json_response,
            "{\"status\":\"ok\",\"status\":{"
            "\"uptime\":%lu,"
            "\"cpu_m7\":%.1f,"
            "\"cpu_m4\":%.1f,"
            "\"memory_free\":%lu"
            "}}\n",
            HAL_GetTick() / 1000,
            get_cpu_usage_m7(),
            get_cpu_usage_m4(),
            get_free_memory());
    }
    else {
        sprintf(json_response, "{\"status\":\"error\",\"message\":\"unknown command\"}\n");
    }
    
    // Send response
    HAL_UART_Transmit_DMA(&huart3, (uint8_t*)json_response, strlen(json_response));
}

// UART receive callback
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART3) {
        if (uart_rx_buffer[uart_rx_index] == '\n') {
            uart_rx_buffer[uart_rx_index] = '\0';
            process_command((char*)uart_rx_buffer);
            uart_rx_index = 0;
        } else {
            uart_rx_index++;
            if (uart_rx_index >= sizeof(uart_rx_buffer)) {
                uart_rx_index = 0; // Reset on overflow
            }
        }
        // Restart reception
        HAL_UART_Receive_IT(&huart3, &uart_rx_buffer[uart_rx_index], 1);
    }
}

// Sensor reading functions
float read_temperature(void) {
    // Read from ADC or I2C temperature sensor
    // Example: Read from ADC channel
    HAL_ADC_Start(&hadc1);
    HAL_ADC_PollForConversion(&hadc1, 10);
    uint32_t adc_value = HAL_ADC_GetValue(&hadc1);
    
    // Convert to temperature (example calculation)
    float voltage = (adc_value / 4095.0f) * 3.3f;
    float temperature = (voltage - 0.5f) * 100.0f; // Example formula
    
    return temperature;
}

float read_pressure(void) {
    // Read from pressure sensor (I2C or ADC)
    // Example implementation
    return 12.5f; // Placeholder
}

float read_rpm(void) {
    // Read from RPM sensor (frequency measurement or CAN)
    // Example implementation
    return 6500.0f; // Placeholder
}

// FreeRTOS task for sensor reading
void SensorTask(void *argument) {
    for (;;) {
        // Read all sensors periodically
        sensor_data.temperature = read_temperature();
        sensor_data.pressure = read_pressure();
        sensor_data.rpm = read_rpm();
        sensor_data.timestamp = HAL_GetTick();
        
        osDelay(10); // 100Hz update rate
    }
}

// FreeRTOS task for communication
void CommTask(void *argument) {
    // Start UART reception
    HAL_UART_Receive_IT(&huart3, &uart_rx_buffer[0], 1);
    
    for (;;) {
        // Communication handled in interrupt callbacks
        osDelay(100);
    }
}
```

### SPI Communication Handler (Slave Mode)

```c
// SPI receive buffer
uint8_t spi_rx_buffer[256];
uint8_t spi_tx_buffer[256];

// SPI receive callback
void HAL_SPI_RxCpltCallback(SPI_HandleTypeDef *hspi) {
    if (hspi->Instance == SPI1) {
        // Process received command
        process_spi_command(spi_rx_buffer);
        
        // Prepare response
        prepare_spi_response(spi_tx_buffer);
        
        // Send response on next transaction
        HAL_SPI_Transmit_DMA(&hspi1, spi_tx_buffer, sizeof(spi_tx_buffer));
    }
}
```

### I2C Communication Handler

```c
#define I2C_ADDRESS 0x48

// I2C slave receive callback
void HAL_I2C_SlaveRxCpltCallback(I2C_HandleTypeDef *hi2c) {
    if (hi2c->Instance == I2C1) {
        // Process received command
        process_i2c_command();
    }
}

// I2C address match callback
void HAL_I2C_AddrCallback(I2C_HandleTypeDef *hi2c, uint8_t TransferDirection, uint16_t AddrMatchCode) {
    if (hi2c->Instance == I2C1) {
        if (TransferDirection == I2C_DIRECTION_TRANSMIT) {
            // Master wants to read - prepare response
            prepare_i2c_response();
        }
    }
}
```

## Build Instructions

1. **Install STM32CubeMX**
   - Download from STMicroelectronics website
   - Install STM32H7 HAL libraries

2. **Generate Project**
   - Open STM32CubeMX
   - Select STM32H755ZITx
   - Configure peripherals as described above
   - Generate code for STM32CubeIDE or Keil

3. **Add Custom Code**
   - Copy communication handlers to `main.c`
   - Implement sensor reading functions
   - Configure FreeRTOS tasks

4. **Build and Flash**
   - Build project in your IDE
   - Connect NUCLEO board via USB
   - Flash firmware using ST-LINK

## Testing

1. **Connect to Pi**
   - Connect UART pins (PD8/PD9) to Pi GPIO 14/15
   - Power both boards
   - Ensure common ground

2. **Test Communication**
   - Run Python test script:
   ```python
   from interfaces.nucleo_interface import NucleoInterface, NucleoConnectionType
   
   nucleo = NucleoInterface(NucleoConnectionType.UART)
   if nucleo.connect():
       print("Connected!")
       sensors = nucleo.read_sensors()
       print(f"Sensors: {sensors}")
   ```

3. **Verify Data Flow**
   - Check UART communication
   - Verify sensor readings
   - Monitor CPU usage

## Advanced Features

### CAN Bus Integration

```c
// CAN message structure
typedef struct {
    uint32_t id;
    uint8_t data[8];
    uint8_t length;
} CANMessage_t;

// CAN receive callback
void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan) {
    CAN_RxHeaderTypeDef rx_header;
    uint8_t rx_data[8];
    
    HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &rx_header, rx_data);
    
    // Process CAN message
    process_can_message(rx_header.StdId, rx_data, rx_header.DLC);
}
```

### High-Speed ADC Sampling

```c
// ADC DMA configuration for continuous sampling
void start_adc_dma(void) {
    HAL_ADC_Start_DMA(&hadc1, (uint32_t*)adc_buffer, ADC_BUFFER_SIZE);
}

// ADC conversion complete callback
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc) {
    // Process ADC buffer
    process_adc_data(adc_buffer, ADC_BUFFER_SIZE);
}
```

## Resources

- [STM32H755ZI Reference Manual](https://www.st.com/resource/en/reference_manual/rm0433-stm32h7-series-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)
- [STM32CubeH7 HAL Library](https://www.st.com/en/embedded-software/stm32cubeh7.html)
- [FreeRTOS Documentation](https://www.freertos.org/Documentation/RTOS_book.html)
- [cJSON Library](https://github.com/DaveGamble/cJSON) (for JSON parsing)

---

**Note**: This is a template. Customize based on your specific sensor requirements and communication needs.

