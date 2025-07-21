/*
 * ap.c
 *
 *  Created on: Jul 12, 2025
 *      Author: User
 */

#include "hw.h"
#include "usart.h"
#include "i2c.h"

#include "serial.h"
#include "obstacle.h"

void hwInit(void)
{

}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
	if (htim->Instance == TIM11)
	{
		SERIAL_Print();
	}
}

void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
    if (huart == &huart1)
    {
    	SERIAL_Scanf(Size);
    }
}

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        SERIAL_Flag();
    }
}
