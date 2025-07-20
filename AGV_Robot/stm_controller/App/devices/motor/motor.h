/*
 * motor.h
 *
 *  Created on: Jul 14, 2025
 *      Author: User
 */

#ifndef DEVICES_MOTOR_MOTOR_H_
#define DEVICES_MOTOR_MOTOR_H_

#include "def.h"
#include "tim.h"

// 모터 방향 정의
typedef enum {
    MOTOR_STOP = 0,		// 모터 정지
    MOTOR_FORWARD,		// 모터 앞으로
    MOTOR_BACKWARD		// 모터 뒤로
} MotorDir_t;

// 메카넘 휠 이동 방향 정의
typedef enum {
    MECANUM_STOP 	 = 'S',			// 차량 정지
    MECANUM_FORWARD  = 'F',			// 차량 앞으로
    MECANUM_BACKWARD = 'B',			// 차량 뒤로
    MECANUM_LEFT	 = 'A',			// 차량 좌측으로
    MECANUM_RIGHT	 = 'D',			// 차량 우측으로
    MECANUM_FORWARD_LEFT	= 'L',	// 차량 전방 좌회전
    MECANUM_FORWARD_RIGHT	= 'R',	// 차량 전방 우회전
    MECANUM_BACKWARD_LEFT	= 'Z',	// 차량 후방 좌회줜
    MECANUM_BACKWARD_RIGHT	= 'C',	// 차량 후방 우회전
    MECANUM_ROTATE_LEFT		= 'Q',	// 차량 좌측 회전
    MECANUM_ROTATE_RIGHT	= 'E'	// 차량 우측 회전
} MecanumDir_t;

// 모터 핀 정의 구조체
typedef struct {
    GPIO_TypeDef* in1_port;
    uint16_t in1_pin;
    GPIO_TypeDef* in2_port;
    uint16_t in2_pin;
    TIM_HandleTypeDef* htim;
    uint32_t channel;
} MotorPin_t;

void MOTOR_Init(void);
void MOTOR_SetSpeed(uint8_t motor, uint16_t speed, MotorDir_t direction);
void MECANUM_Move(MecanumDir_t direction, uint16_t spd_L, uint16_t spd_R);
void MECANUM_Stop(void);

#endif /* DEVICES_MOTOR_MOTOR_H_ */
