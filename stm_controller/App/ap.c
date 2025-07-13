/*
 * ap.c
 *
 *  Created on: Jul 12, 2025
 *      Author: User
 */

#include "ap.h"
#include "tim.h"
#include "serial.h"

extern volatile uint8_t rxFlag;		// RX 완료 플래그
extern volatile uint8_t txFlag;     // TX 완료 플래그

#define RX_SIZE				64
uint8_t rxData[RX_SIZE];

void apInit(void)
{
	HAL_TIM_Base_Start_IT(&htim11);
	SERIAL_Init();
}

void apMain(void)
{
	while (1)
	{
		if (txFlag == 0)
			SERIAL_PutData((uint8_t*)"hello Raspberry Pi 4\r\n");

		SERIAL_GetData(rxData);
		HAL_UART_Transmit(&huart2, rxData, strlen(rxData), 100);
		HAL_Delay(100);
	}
}
