/*
 * serial.h
 *
 *  Created on: Jul 12, 2025
 *      Author: User
 */

#ifndef DEVICES_SERIAL_H_
#define DEVICES_SERIAL_H_

#include "usart.h"

void SERIAL_Init(void);
void SERIAL_PutData(uint8_t* buff);
void SERIAL_GetData(uint8_t* buff);

#endif /* DEVICES_SERIAL_H_ */
