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
#include "imu.h"
#include "obstacle.h"
#include "vl53l0x.h"

// Serial 변수
extern volatile uint8_t rxFlag;                // RX 완료 플래그
extern volatile uint8_t txFlag;                // TX 완료 플래그
#define RX_SIZE				64
uint8_t cmd[RX_SIZE];

// IMU Data 변수
char msg[128];
float accel[3], gyro[3], mag[3], temp;
extern volatile uint8_t i2c1Flag;
volatile uint8_t cur_imu = 0;

// Motor 관련 변수
#define DEFAULT_SPEED		390
#define HIGH_SPEED			850
#define LOW_SPEED			390

uint16_t distance;

void apInit(void)
{
	SERIAL_Init();

	MPU6050_Init();
//	HMC5883L_Init();
//	QMC5883L_Init();
	MPU6050_ReadAll_DMA_Start();
//	HMC5883L_ReadAll_DMA_Start();
//	QMC5883L_ReadAll_DMA_Start();

	VL53L0X_Init();

	MOTOR_Init();

	HAL_TIM_Base_Start_IT(&htim11);
}

void apMain(void)
{
	while (1)
	{
		Serial_Task();
		ImuSensor_Task();
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

// === IMU 데이터 처리 함수 ===
void ImuSensor_Task(void)
{
    if (cur_imu == 0)
    {
        cur_imu = 1;
        i2c1Flag = 1;
        MPU6050_ReadAll_DMA_Start();    // MPU6050 다음 프레임 시작
        MPU6050_Parse_DMA(accel, gyro);
        snprintf(msg, sizeof(msg),
					"ACC: X=%.2f Y=%.2f Z=%.2f | GYRO: X=%.2f Y=%.2f Z=%.2f\r\n",
					accel[0], accel[1], accel[2],
					gyro[0], gyro[1], gyro[2]);
//        HAL_UART_Transmit(&huart2, (uint8_t *)msg, strlen(msg), 100);
    }
    else
    {
        cur_imu = 0;
        i2c1Flag = 1;
        HMC5883L_ReadAll_DMA_Start();   // HMC5883L 다음 프레임 시작
        HMC5883L_Parse_DMA(mag);
//        QMC5883L_ReadAll_DMA_Start();
//        QMC5883L_Parse_DMA(mag);
        snprintf(msg, sizeof(msg),
					"MAG: X=%.2f Y=%.2f Z=%.2f\r\n",
					mag[0], mag[1], mag[2]);
//        HAL_UART_Transmit(&huart2, (uint8_t *)msg, strlen(msg), 100);
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
