/*
 * serial.h
 *
 *  Created on: Jul 12, 2025
 *      Author: User
 */

#ifndef DEVICES_SERIAL_H_
#define DEVICES_SERIAL_H_

void SERIAL_Init(void);
void SERIAL_PutData(uint8_t* buff);
void SERIAL_GetData(uint8_t* buff);

void SERIAL_Print(void);
void SERIAL_Scanf(uint16_t Size);
void SERIAL_Flag(void);

#endif /* DEVICES_SERIAL_H_ */
