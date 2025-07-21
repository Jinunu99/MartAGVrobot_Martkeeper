/*
 * ap.c
 *
 *  Created on: Jul 12, 2025
 *      Author: User
 */

#include "ap.h"
#include "tim.h"
#include "i2c.h"
#include "usart.h"

#include "motor.h"
#include "serial.h"
#include "obstacle.h"

// Serial 변수
extern volatile uint8_t rxFlag;                // RX 완료 플래그
extern volatile uint8_t txFlag;                // TX 완료 플래그
#define RX_SIZE				64
uint8_t cmd[RX_SIZE];

// Motor 관련 변수
#define DEFAULT_SPEED		390
#define HIGH_SPEED			850
#define LOW_SPEED			390

uint16_t distance;

void apInit(void)
{
	SERIAL_Init();
	VL53L0X_Init();

	MOTOR_Init();

	HAL_TIM_Base_Start_IT(&htim11);
}

void apMain(void)
{
	while (1)
	{
		Serial_Task();
		Motor_Task();
		VL53L0X_Task();
	}
}

// === 시리얼 통신 처리 함수 ===
void Serial_Task(void)
{
    // 송신 처리
    if (txFlag == 0) {
        txFlag = 1;
        SERIAL_PutData((uint8_t*)"hello Raspberry Pi 4\r\n");
    }

    // 수신 데이터 받기
    SERIAL_GetData(cmd);

    // 수신 데이터를 USART2로 전송 (디버깅용)
    if (strlen((char*)cmd) > 0) {
//        HAL_UART_Transmit(&huart2, cmd, strlen((char*)cmd), 100);
    }
}

// === 적외선 거리 센서 데이터 처리 함수 ===
uint32_t vl53l0x_last_tick = 0;
const uint32_t vl53l0x_period = 1000;  // 1초 주기 (1000ms)

void VL53L0X_Task(void)
{
	static VL53L0X_State_t state = VL53L0X_STATE_IDLE;
	if (state == VL53L0X_STATE_IDLE)
	{
		if ((HAL_GetTick() - vl53l0x_last_tick) >= vl53l0x_period)
		{
			vl53l0x_last_tick = HAL_GetTick();
			state = VL53L0X_SingleRead();
		}
	}
	else
	{
		state = VL53L0X_SingleRead();
	}
}

// === 모터 제어 명령 처리 함수 ===
void Motor_Task(void)
{
	// 수신된 데이터가 있는지 확인
	if (rxFlag)
	{
		size_t len = strcspn((char*)cmd, "\r\n");
		cmd[len] = '\0';

		// 명령어 파싱 (첫 번째 문자로 방향 결정)
		switch (cmd[0]) {
		    case 'F':
		        MECANUM_Move(MECANUM_FORWARD, DEFAULT_SPEED, DEFAULT_SPEED);
		        break;

		    case 'B':
		        MECANUM_Move(MECANUM_BACKWARD, DEFAULT_SPEED, DEFAULT_SPEED);
		        break;

		    case 'A':
		        MECANUM_Move(MECANUM_LEFT, DEFAULT_SPEED, DEFAULT_SPEED);
		        break;

		    case 'D':
		        MECANUM_Move(MECANUM_RIGHT, DEFAULT_SPEED, DEFAULT_SPEED);
		        break;

		    case 'L':
		        MECANUM_Move(MECANUM_FORWARD_LEFT, DEFAULT_SPEED, DEFAULT_SPEED);
		        break;

		    case 'R':
		        MECANUM_Move(MECANUM_FORWARD_RIGHT, DEFAULT_SPEED, DEFAULT_SPEED);
		        break;

		    case 'Z':
		        MECANUM_Move(MECANUM_BACKWARD_LEFT, DEFAULT_SPEED, DEFAULT_SPEED);
		        break;

		    case 'C':
		        MECANUM_Move(MECANUM_BACKWARD_RIGHT, DEFAULT_SPEED, DEFAULT_SPEED);
		        break;

		    case 'Q':
		        MECANUM_Move(MECANUM_ROTATE_LEFT, DEFAULT_SPEED, DEFAULT_SPEED);
		        break;

		    case 'E':
		        MECANUM_Move(MECANUM_ROTATE_RIGHT, DEFAULT_SPEED, DEFAULT_SPEED);
		        break;

		    case 'S':
		    default:
		        MECANUM_Stop();
		        break;
		}

		// 수신 버퍼 클리어
		memset(cmd, 0, RX_SIZE);
	}
}
