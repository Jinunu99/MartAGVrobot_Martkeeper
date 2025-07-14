/*
 * gy271.h
 *
 *  Created on: Jul 13, 2025
 *      Author: User
 */

#ifndef DEVICES_HMC5883L_H_
#define DEVICES_HMC5883L_H_

// -----------------------------------------------------------------------------
// HMC5883L 기본 정보
// -----------------------------------------------------------------------------
#define HMC5883L_ADDRESS           	0x1E  	// HMC5883L I2C 주소
#define HMC5883L_ID_REG_A          	0x0A    // Identification Register A
#define HMC5883L_ID_REG_B          	0x0B    // Identification Register B
#define HMC5883L_ID_REG_C          	0x0C    // Identification Register C

// -----------------------------------------------------------------------------
// HMC5883L 레지스터 정의
// -----------------------------------------------------------------------------
#define HMC5883L_CONFIG_A          	0x00 	 // Configuration Register A
#define HMC5883L_CONFIG_B          	0x01	  // Configuration Register B
#define HMC5883L_MODE              	0x02  	// Mode Register
#define HMC5883L_DATA_X_MSB        	0x03  	// Data Output X MSB Register
#define HMC5883L_DATA_X_LSB        	0x04  	// Data Output X LSB Register
#define HMC5883L_DATA_Z_MSB        	0x05  	// Data Output Z MSB Register
#define HMC5883L_DATA_Z_LSB        	0x06  	// Data Output Z LSB Register
#define HMC5883L_DATA_Y_MSB        	0x07  	// Data Output Y MSB Register
#define HMC5883L_DATA_Y_LSB        	0x08  	// Data Output Y LSB Register
#define HMC5883L_STATUS            	0x09  	// Status Register

// HMC5883L 설정 값
#define HMC5883L_CONFIG_A_0_75HZ   	0x00  	// 0.75Hz
#define HMC5883L_CONFIG_A_1_5HZ    	0x04  	// 1.5Hz
#define HMC5883L_CONFIG_A_3HZ      	0x08  	// 3Hz
#define HMC5883L_CONFIG_A_7_5HZ    	0x0C  	// 7.5Hz
#define HMC5883L_CONFIG_A_15HZ     	0x10  	// 15Hz (기본값)
#define HMC5883L_CONFIG_A_30HZ     	0x14  	// 30Hz
#define HMC5883L_CONFIG_A_75HZ     	0x18  	// 75Hz

// HMC5883L Gain 설정값 (Config Register B, 0x01)
#define HMC5883L_CONFIG_B_0_88GA    0x00  	// ±0.88 Ga   → 1370 LSB/Gauss
#define HMC5883L_CONFIG_B_1_3GA     0x20  	// ±1.3  Ga   → 1090 LSB/Gauss
#define HMC5883L_CONFIG_B_1_9GA     0x40  	// ±1.9  Ga   → 820  LSB/Gauss
#define HMC5883L_CONFIG_B_2_5GA     0x60  	// ±2.5  Ga   → 660  LSB/Gauss
#define HMC5883L_CONFIG_B_4_0GA     0x80  	// ±4.0  Ga   → 440  LSB/Gauss
#define HMC5883L_CONFIG_B_4_7GA     0xA0  	// ±4.7  Ga   → 390  LSB/Gauss
#define HMC5883L_CONFIG_B_5_6GA     0xC0  	// ±5.6  Ga   → 330  LSB/Gauss
#define HMC5883L_CONFIG_B_8_1GA     0xE0  	// ±8.1  Ga   → 230  LSB/Gauss

#define HMC5883L_LSB_0_88G    		1370.0f
#define HMC5883L_LSB_1_3G     		1090.0f
#define HMC5883L_LSB_1_9G     		820.0f
#define HMC5883L_LSB_2_5G     		660.0f
#define HMC5883L_LSB_4_0G     		440.0f
#define HMC5883L_LSB_4_7G     		390.0f
#define HMC5883L_LSB_5_6G     		330.0f
#define HMC5883L_LSB_8_1G     		230.0f

#define HMC5883L_MODE_CONTINUOUS   	0x00  	// 연속 측정 모드
#define HMC5883L_MODE_SINGLE       	0x01  	// 단일 측정 모드

#endif /* DEVICES_HMC5883L_H_ */
