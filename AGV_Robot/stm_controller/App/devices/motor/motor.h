/*
 * motor.h
 *
 *  Created on: Jul 14, 2025
 *      Author: User
 */

#ifndef DEVICES_MOTOR_MOTOR_H_
#define DEVICES_MOTOR_MOTOR_H_

#include "def.h"
#include "gpio.h"

// 모터 방향 제어 핀 정의
#define M1_IN1_PORT  GPIOC
#define M1_IN1_PIN   GPIO_PIN_0
#define M1_IN2_PORT  GPIOC
#define M1_IN2_PIN   GPIO_PIN_1

#define M2_IN1_PORT  GPIOC
#define M2_IN1_PIN   GPIO_PIN_3
#define M2_IN2_PORT  GPIOC
#define M2_IN2_PIN   GPIO_PIN_2

#define M3_IN1_PORT  GPIOB
#define M3_IN1_PIN   GPIO_PIN_1
#define M3_IN2_PORT  GPIOB
#define M3_IN2_PIN   GPIO_PIN_15

#define M4_IN1_PORT  GPIOB
#define M4_IN1_PIN   GPIO_PIN_13
#define M4_IN2_PORT  GPIOB
#define M4_IN2_PIN   GPIO_PIN_14

void Motor_Init(void);

void Set_Direction(char dir);
void Set_Speed(int percent);
void Set_Wheel_Speed(uint16_t m1, uint16_t m2, uint16_t m3, uint16_t m4);


void motor_f();
void motor_b();
void motor_l();
void motor_r();
void motor_s();
void motor_rf();
void motor_lf();

#endif /* DEVICES_MOTOR_MOTOR_H_ */
