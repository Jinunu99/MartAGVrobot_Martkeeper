/*
 * motor.c
 *
 *  Created on: Jul 14, 2025
 *      Author: User
 */

#include "motor.h"

char current_direction = 'S';

extern TIM_HandleTypeDef htim1;  // TIM1: PA8, PA9
extern TIM_HandleTypeDef htim3;  // TIM3: PA6, PA7

#define DEFAULT_SPEED	100
#define HIGH_SPEED		420 // 350
#define LOW_SPEED		410

// General Wheel 100 500 450


void Motor_Init()
{
    // PWM 시작
    HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1); // M1
    HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_2); // M2
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1); // M3
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_2); // M4

    Set_Speed(0);  // 정지
}

void Set_Speed(int percent)
{
    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;

    uint16_t duty = (1000 * percent) / 100;

    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, duty);  // M1
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, duty);  // M2
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, duty);  // M3
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_2, duty);  // M4
}

void Set_Wheel_Speed(uint16_t m1, uint16_t m2, uint16_t m3, uint16_t m4)
{
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, m1);  // M1
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, m2);  // M2
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, m3);  // M3
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_2, m4);  // M4
}

// ----------------------------- 방향 제어 -----------------------------

void motor_f()
{
    Set_Speed(DEFAULT_SPEED);

    HAL_GPIO_WritePin(M1_IN1_PORT, M1_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M1_IN2_PORT, M1_IN2_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M2_IN1_PORT, M2_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M2_IN2_PORT, M2_IN2_PIN, GPIO_PIN_SET);

    HAL_GPIO_WritePin(M3_IN1_PORT, M3_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M3_IN2_PORT, M3_IN2_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M4_IN1_PORT, M4_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M4_IN2_PORT, M4_IN2_PIN, GPIO_PIN_SET);
}

void motor_b()
{
    Set_Speed(DEFAULT_SPEED);

    HAL_GPIO_WritePin(M1_IN1_PORT, M1_IN1_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M1_IN2_PORT, M1_IN2_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M2_IN1_PORT, M2_IN1_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M2_IN2_PORT, M2_IN2_PIN, GPIO_PIN_RESET);

    HAL_GPIO_WritePin(M3_IN1_PORT, M3_IN1_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M3_IN2_PORT, M3_IN2_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M4_IN1_PORT, M4_IN1_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M4_IN2_PORT, M4_IN2_PIN, GPIO_PIN_RESET);
}

void motor_l()
{
    // 좌측 감속, 우측 강화
    Set_Wheel_Speed(LOW_SPEED, HIGH_SPEED, LOW_SPEED, HIGH_SPEED);  // M2, M3 좌  / M1, M4 우

    HAL_GPIO_WritePin(M1_IN1_PORT, M1_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M1_IN2_PORT, M1_IN2_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M2_IN1_PORT, M2_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M2_IN2_PORT, M2_IN2_PIN, GPIO_PIN_SET);

    HAL_GPIO_WritePin(M3_IN1_PORT, M3_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M3_IN2_PORT, M3_IN2_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M4_IN1_PORT, M4_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M4_IN2_PORT, M4_IN2_PIN, GPIO_PIN_SET);
}

void motor_r()
{
    // 우측 감속, 좌측 강화
    Set_Wheel_Speed(HIGH_SPEED, LOW_SPEED, HIGH_SPEED, LOW_SPEED);

    HAL_GPIO_WritePin(M1_IN1_PORT, M1_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M1_IN2_PORT, M1_IN2_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M2_IN1_PORT, M2_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M2_IN2_PORT, M2_IN2_PIN, GPIO_PIN_SET);

    HAL_GPIO_WritePin(M3_IN1_PORT, M3_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M3_IN2_PORT, M3_IN2_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M4_IN1_PORT, M4_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M4_IN2_PORT, M4_IN2_PIN, GPIO_PIN_SET);
}

//void motor_lf()
//{
//    // 부드러운 좌회전
//    Set_Wheel_Speed(500, 670, 500, 670);
//    motor_f();
//}
//
//void motor_rf()
//{
//    // 부드러운 우회전
//    Set_Wheel_Speed(670, 500, 670, 500);
//    motor_f();
//}

void motor_s()
{
    Set_Speed(0);

    HAL_GPIO_WritePin(M1_IN1_PORT, M1_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M1_IN2_PORT, M1_IN2_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M2_IN1_PORT, M2_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M2_IN2_PORT, M2_IN2_PIN, GPIO_PIN_RESET);

    HAL_GPIO_WritePin(M3_IN1_PORT, M3_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M3_IN2_PORT, M3_IN2_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M4_IN1_PORT, M4_IN1_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M4_IN2_PORT, M4_IN2_PIN, GPIO_PIN_RESET);
}


//		M2          M3
//		[↙]        [↘]
//		┌────────────┐
//		│            │		IN1 : RESET		IN1 : SET
//	앞	│    AGV     │		IN2 : SET		IN2 : RESET
//		│   Robot    │		-> Forward		-> Backward
//		│            │
//		└────────────┘
//		[↖]        [↗]
//		M1          M4

void motor_sl()
{
    // 좌측 평행 이동
    HAL_GPIO_WritePin(M1_IN1_PORT, M1_IN1_PIN, GPIO_PIN_SET);  // M1 CCW
    HAL_GPIO_WritePin(M1_IN2_PORT, M1_IN2_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M2_IN1_PORT, M2_IN1_PIN, GPIO_PIN_RESET);  // M2 CCW
    HAL_GPIO_WritePin(M2_IN2_PORT, M2_IN2_PIN, GPIO_PIN_SET);

    HAL_GPIO_WritePin(M3_IN1_PORT, M3_IN1_PIN, GPIO_PIN_SET);    // M3 CW
    HAL_GPIO_WritePin(M3_IN2_PORT, M3_IN2_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(M4_IN1_PORT, M4_IN1_PIN, GPIO_PIN_RESET);    // M4 CW
    HAL_GPIO_WritePin(M4_IN2_PORT, M4_IN2_PIN, GPIO_PIN_SET);
}

void motor_sr()
{
    // 우측 평행 이동
    HAL_GPIO_WritePin(M1_IN1_PORT, M1_IN1_PIN, GPIO_PIN_RESET);    // M1 CW
    HAL_GPIO_WritePin(M1_IN2_PORT, M1_IN2_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M2_IN1_PORT, M2_IN1_PIN, GPIO_PIN_SET);    // M2 CW
    HAL_GPIO_WritePin(M2_IN2_PORT, M2_IN2_PIN, GPIO_PIN_RESET);

    HAL_GPIO_WritePin(M3_IN1_PORT, M3_IN1_PIN, GPIO_PIN_RESET);  // M3 CCW
    HAL_GPIO_WritePin(M3_IN2_PORT, M3_IN2_PIN, GPIO_PIN_SET);
    HAL_GPIO_WritePin(M4_IN1_PORT, M4_IN1_PIN, GPIO_PIN_SET);  // M4 CCW
    HAL_GPIO_WritePin(M4_IN2_PORT, M4_IN2_PIN, GPIO_PIN_RESET);
}

void Set_Direction(char dir)
{
    current_direction = dir;

    switch (dir)
    {
        case 'F':  motor_f(); break;
        case 'B':  motor_b(); break;
        case 'L':  motor_l(); break;
        case 'R':  motor_r(); break;
//        case 'G':  motor_lf(); break; // 'LF'
//        case 'H':  motor_rf(); break; // 'RF'
        case 'Y':  motor_sl(); break; //SL 좌측이동
        case 'X':  motor_sr(); break; //SR 우측이동
        case 'S': default:    motor_s(); break;
    }
}
