/*
 * serial.c
 *
 *  Created on: Jul 12, 2025
 *      Author: User
 */

#include "def.h"
#include "serial.h"

#define DATA_SIZE		64
#define DMA_SIZE		64

volatile uint8_t rxFlag = 0;                // RX 완료 플래그
volatile uint8_t txFlag = 0;                // TX 완료 플래그

static uint8_t rxBuff[DMA_SIZE];
static uint8_t rxData[DATA_SIZE];           // 외부에서 읽어갈 수 있는 RX 데이터 버퍼
static uint8_t rxLength;
static uint8_t txData[DATA_SIZE];           // TX 송신 데이터 버퍼

void SERIAL_Init(void)
{
	HAL_UARTEx_ReceiveToIdle_DMA(&huart1, rxBuff, DMA_SIZE); 	  // DMA + IDLE로 UART 수신 시작
	__HAL_DMA_DISABLE_IT(huart1.hdmarx, DMA_IT_HT);				  // Half-transfer interrupt disable
	__HAL_UART_ENABLE_IT(&huart1, UART_IT_IDLE);				  // IDLE interrupt enable
}

// 외부에서 송신할 데이터를 txData에 복사
void SERIAL_PutData(uint8_t* buff)
{
	memcpy(txData, buff, sizeof(txData));
	txFlag = 1;
}

// 외부에서 rxData 내용을 접근할 수 있도록 buff에 복사
void SERIAL_GetData(uint8_t* buff)
{
	snprintf((char*)buff, DATA_SIZE, "%s\r\n", rxData);
}


void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
    if (huart == &huart1)
    {
        for (uint16_t i = 0; i < Size; i++)
        {
            char c = (char)rxBuff[i];

            if (c != '\n' && rxLength < DATA_SIZE)
            {
            	rxData[rxLength++] = c;
            }
            else if (c == '\n')
            {
            	rxData[rxLength] = '\0';
            	rxLength = 0;
            	rxFlag = 1;
            }
        }
    }
}

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        txFlag = 0;
    }
}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
	if (htim->Instance == TIM11)
	{
		if (txFlag == 1)
		{
//			HAL_UART_Transmit(&huart2, txData, strlen((char*)txData), 100);
			HAL_UART_Transmit_DMA(&huart1, txData, strlen((char*)txData));
		}
	}
}
