#ifndef INC_LED_H_
#define INC_LED_H_

#include "main.h"

// SER : 데이터 입력
// RCLK : latch되면 시프트 -> 저장
// SRCLK : 상승엣지에 데이터가 시프트 레지스터로

// 사용할 핀: PC10, PC11, PC12
#define SER_HIGH_1()   HAL_GPIO_WritePin(GPIOC, GPIO_PIN_10, GPIO_PIN_SET)
#define SER_LOW_1()    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_10, GPIO_PIN_RESET)

#define RCLK_HIGH_1()  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_11, GPIO_PIN_SET)
#define RCLK_LOW_1()   HAL_GPIO_WritePin(GPIOC, GPIO_PIN_11, GPIO_PIN_RESET)

#define SRCLK_HIGH_1() HAL_GPIO_WritePin(GPIOC, GPIO_PIN_12, GPIO_PIN_SET)
#define SRCLK_LOW_1()  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_12, GPIO_PIN_RESET)

// 사용할 핀: PC1, PC2, PC3
#define SER_HIGH_2()   HAL_GPIO_WritePin(GPIOC, GPIO_PIN_1, GPIO_PIN_SET)
#define SER_LOW_2()    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_1, GPIO_PIN_RESET)

#define RCLK_HIGH_2()  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_2, GPIO_PIN_SET)
#define RCLK_LOW_2()   HAL_GPIO_WritePin(GPIOC, GPIO_PIN_2, GPIO_PIN_RESET)

#define SRCLK_HIGH_2() HAL_GPIO_WritePin(GPIOC, GPIO_PIN_3, GPIO_PIN_SET)
#define SRCLK_LOW_2()  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_3, GPIO_PIN_RESET)


void shiftOut1(uint8_t data);
void shiftOut2(uint8_t data);
void LED1_on(uint8_t cnt);
void LED2_on(uint8_t cnt);
void LED1_off();
void LED2_off();

#endif /* INC_LED_H_ */
