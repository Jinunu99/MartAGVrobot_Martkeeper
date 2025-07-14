#ifndef INC_SENSOR_H_
#define INC_SENSOR_H_

#include "main.h"
#include "tim.h"

extern volatile uint16_t adcValue[3];


void FAN_on();
void FAN_off();
void PINWHEEL_on();
void PINWHEEL_off();
uint16_t WATER_Leftcheck();
uint16_t WATER_Rightcheck();
uint16_t FIRE_check();

#endif /* INC_SENSOR_H_ */
