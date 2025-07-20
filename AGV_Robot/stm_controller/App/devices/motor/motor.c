/*
 * motor.c
 *
 *  Created on: Jul 14, 2025
 *      Author: User
 */

#include "motor.h"

// 4개 모터 핀 설정
static const MotorPin_t motorPins[4] = {
    // 모터 1 (앞 왼쪽)
    {GPIOC, GPIO_PIN_0,  GPIOC, GPIO_PIN_1,  &htim1, TIM_CHANNEL_1},
    // 모터 2 (앞 오른쪽)
    {GPIOC, GPIO_PIN_3,  GPIOC, GPIO_PIN_2,  &htim1, TIM_CHANNEL_2},
    // 모터 3 (뒤 왼쪽)
    {GPIOB, GPIO_PIN_1,  GPIOB, GPIO_PIN_15, &htim3, TIM_CHANNEL_1},
    // 모터 4 (뒤 오른쪽)
    {GPIOB, GPIO_PIN_13, GPIOB, GPIO_PIN_14, &htim3, TIM_CHANNEL_2}
};

void MOTOR_Init(void)
{
    // PWM 타이머 시작
    HAL_TIM_PWM_Start(motorPins[0].htim, motorPins[0].channel); // TIM1_CH1
    HAL_TIM_PWM_Start(motorPins[1].htim, motorPins[1].channel); // TIM1_CH2
    HAL_TIM_PWM_Start(motorPins[2].htim, motorPins[2].channel); // TIM3_CH1
    HAL_TIM_PWM_Start(motorPins[3].htim, motorPins[3].channel); // TIM3_CH2

    // Frequency 변경 : Hz = 100,000,000
//	__HAL_TIM_SET_AUTORELOAD(&htim1, 2000-1);
//	__HAL_TIM_SET_AUTORELOAD(&htim3, 2000-1);

    // 모든 모터 정지
    MECANUM_Stop();
}

// 개별 모터 제어 함수
void MOTOR_SetSpeed(uint8_t motor, uint16_t speed, MotorDir_t direction)
{
    if (motor >= 4) return; // 모터 번호 검사

    const MotorPin_t* pin = &motorPins[motor];

    // PWM 속도 설정 (0~1000 범위 가정)
    __HAL_TIM_SET_COMPARE(pin->htim, pin->channel, speed);

    // 방향 제어
    switch (direction) {
        case MOTOR_FORWARD:
            HAL_GPIO_WritePin(pin->in1_port, pin->in1_pin, GPIO_PIN_SET);
            HAL_GPIO_WritePin(pin->in2_port, pin->in2_pin, GPIO_PIN_RESET);
            break;

        case MOTOR_BACKWARD:
            HAL_GPIO_WritePin(pin->in1_port, pin->in1_pin, GPIO_PIN_RESET);
            HAL_GPIO_WritePin(pin->in2_port, pin->in2_pin, GPIO_PIN_SET);
            break;

        case MOTOR_STOP:
        default:
            HAL_GPIO_WritePin(pin->in1_port, pin->in1_pin, GPIO_PIN_RESET);
            HAL_GPIO_WritePin(pin->in2_port, pin->in2_pin, GPIO_PIN_RESET);
            break;
    }
}

void MECANUM_Move(MecanumDir_t direction, uint16_t spd_L, uint16_t spd_R)
{
    /*
     * 메카넘 휠 배치:
     * 모터1(FL) --- 모터2(FR)
     *    |             |
     * 모터3(BL) --- 모터4(BR)
     */

    switch (direction) {
        case MECANUM_FORWARD:
            // 모든 바퀴 전진
            MOTOR_SetSpeed(0, spd_L, MOTOR_FORWARD);  // FL
            MOTOR_SetSpeed(1, spd_R, MOTOR_FORWARD);  // FR
            MOTOR_SetSpeed(2, spd_L, MOTOR_FORWARD);  // BL
            MOTOR_SetSpeed(3, spd_R, MOTOR_FORWARD);  // BR
            break;

        case MECANUM_BACKWARD:
            // 모든 바퀴 후진
            MOTOR_SetSpeed(0, spd_L, MOTOR_BACKWARD); // FL
            MOTOR_SetSpeed(1, spd_R, MOTOR_BACKWARD); // FR
            MOTOR_SetSpeed(2, spd_L, MOTOR_BACKWARD); // BL
            MOTOR_SetSpeed(3, spd_R, MOTOR_BACKWARD); // BR
            break;

        case MECANUM_FORWARD_LEFT:

        case MECANUM_FORWARD_RIGHT:
            // 전진 + 우측 이동
            MOTOR_SetSpeed(0, spd_L, MOTOR_FORWARD);  // FL
            MOTOR_SetSpeed(1, spd_R, MOTOR_FORWARD);  // FR
            MOTOR_SetSpeed(2, spd_L, MOTOR_FORWARD);  // BL
            MOTOR_SetSpeed(3, spd_R, MOTOR_FORWARD);  // BR
            break;

        case MECANUM_LEFT:
            // 좌측 이동 (대각선 바퀴 조합)
            MOTOR_SetSpeed(0, spd_L, MOTOR_BACKWARD); // FL
            MOTOR_SetSpeed(1, spd_R, MOTOR_FORWARD);  // FR
            MOTOR_SetSpeed(2, spd_L, MOTOR_FORWARD);  // BL
            MOTOR_SetSpeed(3, spd_R, MOTOR_BACKWARD); // BR
            break;

        case MECANUM_RIGHT:
            // 우측 이동 (대각선 바퀴 조합)
            MOTOR_SetSpeed(0, spd_L, MOTOR_FORWARD);  // FL
            MOTOR_SetSpeed(1, spd_R, MOTOR_BACKWARD); // FR
            MOTOR_SetSpeed(2, spd_L, MOTOR_BACKWARD); // BL
            MOTOR_SetSpeed(3, spd_R, MOTOR_FORWARD);  // BR
            break;

        case MECANUM_BACKWARD_LEFT:
            // 후진 + 좌측 이동
            MOTOR_SetSpeed(0, spd_L, MOTOR_BACKWARD); // FL
            MOTOR_SetSpeed(1, spd_R, MOTOR_STOP);     // FR 정지
            MOTOR_SetSpeed(2, spd_L, MOTOR_STOP);     // BL 정지
            MOTOR_SetSpeed(3, spd_R, MOTOR_BACKWARD); // BR
            break;

        case MECANUM_BACKWARD_RIGHT:
            // 후진 + 우측 이동
            MOTOR_SetSpeed(0, spd_L, MOTOR_STOP);     // FL 정지
            MOTOR_SetSpeed(1, spd_R, MOTOR_BACKWARD); // FR
            MOTOR_SetSpeed(2, spd_L, MOTOR_BACKWARD); // BL
            MOTOR_SetSpeed(3, spd_R, MOTOR_STOP);     // BR 정지
            break;

        case MECANUM_ROTATE_LEFT:
            // 좌회전 (시계 반대 방향)
            MOTOR_SetSpeed(0, spd_L, MOTOR_BACKWARD); // FL
            MOTOR_SetSpeed(1, spd_R, MOTOR_FORWARD);  // FR
            MOTOR_SetSpeed(2, spd_L, MOTOR_BACKWARD); // BL
            MOTOR_SetSpeed(3, spd_R, MOTOR_FORWARD);  // BR
            break;

        case MECANUM_ROTATE_RIGHT:
            // 우회전 (시계 방향)
            MOTOR_SetSpeed(0, spd_L, MOTOR_FORWARD);  // FL
            MOTOR_SetSpeed(1, spd_R, MOTOR_BACKWARD); // FR
            MOTOR_SetSpeed(2, spd_L, MOTOR_FORWARD);  // BL
            MOTOR_SetSpeed(3, spd_R, MOTOR_BACKWARD); // BR
            break;

        case MECANUM_STOP:
        default:
            MECANUM_Stop();
            break;
    }
}

// 모든 모터 정지
void MECANUM_Stop(void)
{
    for (int i = 0; i < 4; i++) {
        MOTOR_SetSpeed(i, 0, MOTOR_STOP);
    }
}
