/*
 * obstacle.h
 *
 *  Created on: Jul 21, 2025
 *      Author: USER
 */

#ifndef DEVICES_OBSTACLE_OBSTACLE_H_
#define DEVICES_OBSTACLE_OBSTACLE_H_

#include "def.h"

typedef enum {
    VL53L0X_STATE_IDLE,
    VL53L0X_STATE_START,
    VL53L0X_STATE_WAITING,
    VL53L0X_STATE_READ
} VL53L0X_State_t;

void VL53L0X_Init(void);
VL53L0X_State_t VL53L0X_SingleRead(void);
uint16_t VL53L0X_GetDistance(void);

#endif /* DEVICES_OBSTACLE_OBSTACLE_H_ */
