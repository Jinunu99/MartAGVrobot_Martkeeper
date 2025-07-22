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
#define DEFAULT_SPEED		100
#define HIGH_SPEED			300
#define LOW_SPEED			290

uint16_t distance;

void apInit(void)
{
	SERIAL_Init();
	VL53L0X_Init();

	Motor_Init();

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
	static uint32_t last = 0;

	// Pi로부터 새 명령이 도착했다면
	if (rxFlag)
	{
		rxFlag = 0;
		SERIAL_GetData((uint8_t*)cmd);
		size_t len = strcspn((char*)cmd, "\r\n");
		cmd[len] = '\0';


		if (HAL_GetTick() - last > 100)  // 100ms 출력 제한
		{
			HAL_UART_Transmit(&huart2, (uint8_t*)cmd, strlen((char*)cmd), 10);
			last = HAL_GetTick();
		}

		// 고급 명령어 처리
		if (strcmp((char*)cmd, "F") == 0)        Set_Direction('F');
		else if (strcmp((char*)cmd, "B") == 0)   Set_Direction('B');
		else if (strcmp((char*)cmd, "L") == 0)   Set_Direction('L');
		else if (strcmp((char*)cmd, "R") == 0)   Set_Direction('R');
//    	    else if (strcmp((char*)cmd, "LF") == 0)  Set_Direction('G');  // 부드러운 좌
//    	    else if (strcmp((char*)cmd, "RF") == 0)  Set_Direction('H');  // 부드러운 우
		else if (strcmp((char*)cmd, "S") == 0)   Set_Direction('S');

		// 복합 명령 처리
		else if (strcmp((char*)cmd, "L90") == 0)
		{
			Set_Direction('F');
			Set_Speed(30);
			HAL_Delay(1800);

			Set_Direction('L');
			Set_Speed(50);
			HAL_Delay(1450);  // 필요시 조정
		}
		else if (strcmp((char*)cmd, "R90") == 0)
		{
			Set_Direction('F');
			Set_Speed(30);
			HAL_Delay(1800);

			Set_Direction('R');
			Set_Speed(50);
			HAL_Delay(1450);
		}
		else if (strcmp((char*)cmd, "R180") == 0)
		{
			Set_Direction('S');
			HAL_Delay(100);
			Set_Direction('R');
			Set_Speed(50);
			HAL_Delay(2900);  // 두 배 회전
			Set_Direction('S');
		}
		else if (strcmp((char*)cmd, "SL") == 0)
		{
			// Step 1: 왼쪽 이동
			Set_Direction('Y');     // 좌측 평행 이동
			Set_Speed(40);          // 적절한 속도 (조정 가능)
			HAL_Delay(1000);        // 약 1초 이동

			// Step 2: 대기
			Set_Direction('S');     // 정지
			HAL_Delay(2000);        // 2초 대기

			// Step 3: 오른쪽 복귀
			Set_Direction('X');     // 우측 평행 이동
			Set_Speed(40);          // 같은 속도
			HAL_Delay(1000);        // 같은 거리 복귀

			// Step 4: 정지 후 라인 복귀 대기
			Set_Direction('S');
		}
		else if (strcmp((char*)cmd, "SR") == 0)
		{
			Set_Direction('X');
			Set_Speed(40);
			HAL_Delay(1000);

			Set_Direction('S');
			HAL_Delay(2000);

			Set_Direction('Y');
			Set_Speed(40);
			HAL_Delay(1000);

			Set_Direction('S');
		}
	}
}
