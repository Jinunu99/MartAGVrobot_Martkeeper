/*
 * ap.c
 *
 *  Created on: Jul 12, 2025
 *      Author: User
 */

#include "ap.h"
#include "tim.h"
#include "usart.h"

#include "motor.h"
#include "serial.h"
#include "imu.h"

// Serial 변수
extern volatile uint8_t rxFlag;                // RX 완료 플래그
extern volatile uint8_t txFlag;                // TX 완료 플래그
#define RX_SIZE				64
uint8_t rxData[RX_SIZE];

// IMU Data 변수
char msg[128];
float accel[3], gyro[3], mag[3], temp;
extern volatile uint8_t i2c1Flag;
volatile uint8_t cur_imu = 0;

void apInit(void)
{
	SERIAL_Init();

	MPU6050_Init();
	MPU6050_ReadAll_DMA_Start();

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
    SERIAL_GetData(rxData);

    // 수신 데이터를 USART2로 전송 (디버깅용)
    if (strlen((char*)rxData) > 0) {
        HAL_UART_Transmit(&huart2, rxData, strlen((char*)rxData), 100);
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
        HAL_UART_Transmit(&huart2, (uint8_t *)msg, strlen(msg), 100);
    }
    else
    {
        cur_imu = 0;
        i2c1Flag = 1;
        HMC5883L_ReadAll_DMA_Start();   // HMC5883L 다음 프레임 시작
        HMC5883L_Parse_DMA(mag);
        snprintf(msg, sizeof(msg),
					"MAG: X=%.2f Y=%.2f Z=%.2f\r\n",
					mag[0], mag[1], mag[2]);
        HAL_UART_Transmit(&huart2, (uint8_t *)msg, strlen(msg), 100);
    }
}

// === 모터 제어 명령 처리 함수 ===
void Motor_Task(void)
{
	// 수신된 데이터가 있는지 확인
	if (strlen((char*)rxData) > 0)
	{
		// 명령어 파싱 (첫 번째 문자로 방향 결정)
		switch (rxData[0])
		{
			case 'w': // 전진
				MECANUM_Move(MECANUM_FORWARD, 500);
				SERIAL_PutData((uint8_t*)"Forward\r\n");
				break;

			case 's': // 후진
				MECANUM_Move(MECANUM_BACKWARD, 500);
				SERIAL_PutData((uint8_t*)"Backward\r\n");
				break;

			case 'a': // 좌측 이동
				MECANUM_Move(MECANUM_LEFT, 500);
				SERIAL_PutData((uint8_t*)"Left\r\n");
				break;

			case 'd': // 우측 이동
				MECANUM_Move(MECANUM_RIGHT, 500);
				SERIAL_PutData((uint8_t*)"Right\r\n");
				break;

			case 'q': // 좌회전
				MECANUM_Move(MECANUM_ROTATE_LEFT, 500);
				SERIAL_PutData((uint8_t*)"Rotate Left\r\n");
				break;

			case 'e': // 우회전
				MECANUM_Move(MECANUM_ROTATE_RIGHT, 500);
				SERIAL_PutData((uint8_t*)"Rotate Right\r\n");
				break;

			case 'x': // 정지
				MECANUM_Stop();
				SERIAL_PutData((uint8_t*)"Stop\r\n");
				break;

			default:
				MECANUM_Stop();
				SERIAL_PutData((uint8_t*)"Unknown command\r\n");
				break;
		}

		// 수신 버퍼 클리어
		memset(rxData, 0, RX_SIZE);
	}
}
