#include <sensor.h>

// FAN
void FAN_on()
{
	HAL_GPIO_WritePin(GPIOC, GPIO_PIN_5, SET); // FAN on
}

void FAN_off()
{
	HAL_GPIO_WritePin(GPIOC, GPIO_PIN_5, RESET); // FAN off
}

// 선풍기
void PINWHEEL_on()
{
	TIM3->CCR1 = 1000;;
}

void PINWHEEL_off()
{
	TIM3->CCR1 = 0;;
}

// 수위센서 값
uint16_t WATER_Leftcheck()
{
	return adcValue[1];
}

uint16_t WATER_Rightcheck()
{
	return adcValue[2];
}

// 불꽃센서 값
uint16_t FIRE_check()
{
	return adcValue[0];
}
