/*
 * ap.h
 *
 *  Created on: Jul 12, 2025
 *      Author: User
 */

#ifndef AP_H_
#define AP_H_

#include "hw.h"

void apInit(void);
void apMain(void);

void Serial_Task(void);
void ImuSensor_Task(void);
void Motor_Task(void);

#endif /* AP_H_ */
