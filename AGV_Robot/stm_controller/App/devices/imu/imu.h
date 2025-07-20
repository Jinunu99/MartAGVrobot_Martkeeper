/*
 * imu.h
 *
 *  Created on: Jul 14, 2025
 *      Author: User
 */

#ifndef DEVICES_IMU_IMU_H_
#define DEVICES_IMU_IMU_H_

typedef enum
{
	_250dps,	_500dps,	_1000dps,	_2000dps
} gscale_t;

typedef enum
{
	_2g,	_4g, 	_8g, 	_16g
} ascale_t;

typedef struct {
	float accel_sens;
	float gyro_sens;
	ascale_t accel_fs_sel;  // ACCEL_CONFIG 레지스터 (0x1C)
	gscale_t gyro_fs_sel;   // GYRO_CONFIG 레지스터 (0x1B)
    uint8_t dlpf_cfg;       // CONFIG 레지스터 (0x1A)
    uint8_t smplrt_div;     // SMPLRT_DIV (0x19)
} MPU6050_Config_t;

// 초기화
void MPU6050_Init(void);

// 오차 관련 함수
void MPU6050_ReadOffset(void);

// 데이터 읽기 (보정 데이터)
void MPU6050_ReadAccel(float accel[3]);
void MPU6050_ReadGyro(float gyro[3]);
void MPU6050_ReadTemp(float *temp);

void MPU6050_ReadAll_DMA_Start(void);
void MPU6050_Parse_DMA(float accel[3], float gyro[3]);

// 초기화 함수
void HMC5883L_Init(void);

// 데이터 읽기 함수
void HMC5883L_ReadMag(float mag[3]);

void HMC5883L_ReadAll_DMA_Start(void);
void HMC5883L_Parse_DMA(float mag[3]);

void QMC5883L_Init(void);

void QMC5883L_ReadMag(float mag[3]);

void QMC5883L_ReadAll_DMA_Start(void);
void QMC5883L_Parse_DMA(float mag[3]);

#endif /* DEVICES_IMU_IMU_H_ */
