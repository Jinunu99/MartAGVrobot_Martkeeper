/*
 * ap.c
 *
 *  Created on: Jul 12, 2025
 *      Author: User
 */

#include "ap.h"
#include "tim.h"
#include "usart.h"

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

	HAL_TIM_Base_Start_IT(&htim11);
}

void apMain(void)
{
	while (1)
	{
		if (txFlag == 0)
		{
			txFlag = 1;
			SERIAL_PutData((uint8_t*)"hello Raspberry Pi 4\r\n");
		}
		SERIAL_GetData(rxData);


		HAL_UART_Transmit(&huart2, rxData, strlen(rxData), 100);

		if (i2c1Flag)
		{
			i2c1Flag = 0;
			MPU6050_Parse_DMA(accel, gyro);
//			HMC5883L_Parse_DMA(mag);

		    snprintf(msg, sizeof(msg),
		             "ACC: X=%.2f Y=%.2f Z=%.2f | GYRO: X=%.2f Y=%.2f Z=%.2f | MAG: X=%.2f Y=%.2f Z=%.2f\r\n",
		             accel[0], accel[1], accel[2],
		             gyro[0], gyro[1], gyro[2],
		             mag[0], mag[1], mag[2]);

	    	if (cur_imu == 0)
	    	{
	    		cur_imu = 1;
				i2c1Flag = 1;  // 새로운 데이터 수신 완료 플래그
				MPU6050_ReadAll_DMA_Start();  // 다음 프레임 DMA 재시작

	    	}
	    	else
	    	{
	    		cur_imu = 0;
				i2c1Flag = 1;  // 새로운 데이터 수신 완료 플래그
				HMC5883L_ReadAll_DMA_Start();  // 다음 프레임 DMA 재시작
	    	}

		    HAL_UART_Transmit(&huart2, (uint8_t *)msg, strlen(msg), 100);
		}

		HAL_Delay(100);
	}
}

