#include "delay.h"

// delay_us를 만드는 함수
void delay_us(uint16_t us, TIM_HandleTypeDef *tim)
{
	__HAL_TIM_SET_COUNTER(tim, 0);
	while((__HAL_TIM_GET_COUNTER(tim)) < us);
}
