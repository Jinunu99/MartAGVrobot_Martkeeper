#ifndef INC_DELAY_H_
#define INC_DELAY_H_

#include "main.h"
#include "tim.h"


void delay_us(uint16_t us, TIM_HandleTypeDef *tim); // 16비트 카운터를 만들고 싶어서 uint16_t를 사용

#endif /* INC_DELAY_H_ */
