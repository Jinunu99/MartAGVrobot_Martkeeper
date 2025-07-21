/*
 * obstacle.c
 *
 *  Created on: Jul 21, 2025
 *      Author: USER
 */


#include "obstacle.h"
#include "vl53l0x.h"

#include "i2c.h"
#include "usart.h"

#define I2C_BUS		&hi2c2

static VL53L0X_State_t vl53l0x_state = VL53L0X_STATE_IDLE;
static uint32_t vl53l0x_start_time = 0;
extern uint8_t g_stopVariable;

static uint16_t g_distance = 0;
static statInfo_t_VL53L0X g_distanceStat;

static char uart_buffer[64];

void VL53L0X_Init(void)
{
    initVL53L0X(1, I2C_BUS);

    setSignalRateLimit(200);
    setVcselPulsePeriod(VcselPeriodPreRange, 10);
    setVcselPulsePeriod(VcselPeriodFinalRange, 14);
    setMeasurementTimingBudget(300 * 1000UL);

    vl53l0x_state = VL53L0X_STATE_IDLE;
}

VL53L0X_State_t VL53L0X_SingleRead(void)
{
    switch (vl53l0x_state)
    {
        case VL53L0X_STATE_IDLE:
            writeReg(0x80, 0x01);
            writeReg(0xFF, 0x01);
            writeReg(0x00, 0x00);
            writeReg(0x91, g_stopVariable);
            writeReg(0x00, 0x01);
            writeReg(0xFF, 0x00);
            writeReg(0x80, 0x00);
            writeReg(SYSRANGE_START, 0x01);

            vl53l0x_start_time = HAL_GetTick();
            vl53l0x_state = VL53L0X_STATE_WAITING;
            break;

        case VL53L0X_STATE_WAITING:
            if (!(readReg(SYSRANGE_START) & 0x01))
            {
                vl53l0x_state = VL53L0X_STATE_READ;
            }
            else if (HAL_GetTick() - vl53l0x_start_time > 100)
            {
                HAL_UART_Transmit(&huart2, (uint8_t *)"VL53L0X Timeout\r\n", 18, 100);
                vl53l0x_state = VL53L0X_STATE_IDLE;
            }
            break;

        case VL53L0X_STATE_READ:
        {
            uint8_t msb, lsb;
            msb = readReg(RESULT_RANGE_STATUS + 10);
            lsb = readReg(RESULT_RANGE_STATUS + 11);
            uint16_t dist = (msb << 8) | lsb;

            snprintf(uart_buffer, sizeof(uart_buffer), "Distance = %d mm\r\n", dist);
            HAL_UART_Transmit(&huart2, (uint8_t *)uart_buffer, strlen(uart_buffer), 100);

            writeReg(SYSTEM_INTERRUPT_CLEAR, 0x01);
            vl53l0x_state = VL53L0X_STATE_IDLE;
            break;
        }

        default:
            vl53l0x_state = VL53L0X_STATE_IDLE;
            break;
    }
    return vl53l0x_state;
}

uint16_t VL53L0X_GetDistance(void)
{
    return g_distance;
}
