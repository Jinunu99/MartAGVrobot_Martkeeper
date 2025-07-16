/*
 * imu.c
 *
 *  Created on: Jul 14, 2025
 *      Author: User
 */

#include "def.h"
#include "i2c.h"
#include "usart.h"
#include "mpu6050.h"
#include "hmc5883l.h"
#include "imu.h"

#define I2C_BUS		&hi2c1

static MPU6050_Config_t cfg = {
	.accel_sens 	= 0.0f,
	.gyro_sens		= 0.0f,
	.dlpf_cfg 		= 0x03,		// 4.9ms
	.gyro_fs_sel 	= _250dps,
	.accel_fs_sel 	= _2g,
	.smplrt_div 	= 0x04,		// 1000 / (1 + 4) = 200Hz -> 5ms
};
static uint8_t mpu6050_buff[14];
static uint8_t hmc5883l_buff[6];
volatile uint8_t i2c1Flag = 0;

static int16_t accel_offset[3];
static int16_t gyro_offset[3];

static HAL_StatusTypeDef I2C_Write(uint8_t addr, uint8_t reg, uint8_t data)
{
	uint8_t buff = data;
	return HAL_I2C_Mem_Write(I2C_BUS, addr, reg, I2C_MEMADD_SIZE_8BIT, &buff, 1, 100);
}
static HAL_StatusTypeDef I2C_Read(uint8_t addr, uint8_t reg, uint8_t *data, uint8_t length)
{
	return HAL_I2C_Mem_Read(I2C_BUS, addr, reg, I2C_MEMADD_SIZE_8BIT, data, length, 100);
}


static HAL_StatusTypeDef MPU6050_Write(uint8_t reg, uint8_t data)
{
	return I2C_Write(MPU6050_ADDRESS << 1, reg, data);
}
static HAL_StatusTypeDef MPU6050_Read(uint8_t reg, uint8_t *data, uint8_t length)
{
	return I2C_Read(MPU6050_ADDRESS << 1, reg, data, length);
}

static HAL_StatusTypeDef HMC5883L_Write(uint8_t reg, uint8_t data)
{
	return I2C_Write(HMC5883L_ADDRESS << 1, reg, data);
}
static HAL_StatusTypeDef HMC5883L_Read(uint8_t reg, uint8_t *data, uint8_t length)
{
	return I2C_Read(HMC5883L_ADDRESS << 1, reg, data, length);
}

static void MPU6050_SetSensitivity(void)
{
	// 가속도 감도 설정 (LSB/g)
	switch(cfg.accel_fs_sel)
	{
		case _2g:	cfg.accel_sens = 16384.0f; break;
		case _4g:	cfg.accel_sens = 8192.0f;  break;
		case _8g:	cfg.accel_sens = 4096.0f;  break;
		case _16g:	cfg.accel_sens = 2048.0f;  break;
	}

	// 자이로 감도 설정 (LSB/°/s)
	switch(cfg.gyro_fs_sel)
	{
		case _250dps:	cfg.gyro_sens = 131.0f;   break;
		case _500dps:	cfg.gyro_sens = 65.5f;    break;
		case _1000dps:	cfg.gyro_sens = 32.8f;    break;
		case _2000dps:	cfg.gyro_sens = 16.4f;    break;
	}
}
static void MPU6050_Calibrate(void)
{
	switch (cfg.accel_fs_sel)
	{
		case _2g:
			accel_offset[0] = 1391;		accel_offset[1] = -708;		accel_offset[2] = -2544;
			break;
		case _4g:
			accel_offset[0] = 698;		accel_offset[1] = -363;		accel_offset[2] = -1272;
			break;
		case _8g:
			accel_offset[0] = 348;		accel_offset[1] = -181;		accel_offset[2] = -636;
			break;
		case _16g:
			accel_offset[0] = 172;		accel_offset[1] = -90;		accel_offset[2] = -319;
			break;
	}
	switch (cfg.gyro_fs_sel)
	{
		case _250dps:
			gyro_offset[0] = -414;	gyro_offset[1] = -50;	gyro_offset[2] = 96;
			break;
		case _500dps:
			gyro_offset[0] = -207;	gyro_offset[1] = -24;	gyro_offset[2] = 47;
			break;
		case _1000dps:
			gyro_offset[0] = -104;	gyro_offset[1] = -12;	gyro_offset[2] = 23;
			break;
		case _2000dps:
			gyro_offset[0] = -54;	gyro_offset[1] = -6;		gyro_offset[2] = 11;
			break;
	}
}

void MPU6050_Init(void)
{
	MPU6050_Write(MPU6050_PWR_MGMT_1, 0x00);	// 슬립 모드 해제
	HAL_Delay(100);

	uint8_t who = 0;
	MPU6050_Read(MPU6050_WHO_AM_I, &who, 1);

	if (who == 0x68)
		HAL_UART_Transmit(&huart2, (uint8_t *)"Success\r\n", sizeof("Success\r\n"), 100);
	else
		HAL_UART_Transmit(&huart2, (uint8_t *)"Failed\r\n", sizeof("Failed\r\n"), 100);

	MPU6050_Write(MPU6050_CONFIG, cfg.dlpf_cfg);
	MPU6050_Write(MPU6050_SMPLRT_DIV, cfg.smplrt_div);

	MPU6050_Write(MPU6050_ACCEL_CONFIG, cfg.accel_fs_sel << 3);
	MPU6050_Write(MPU6050_GYRO_CONFIG,  cfg.gyro_fs_sel << 3);

	MPU6050_SetSensitivity();
	MPU6050_Calibrate();
}

void HMC5883L_Init(void)
{
	uint8_t id = 0;

	// ID 레지스터 A(0x0A) 하나만 읽도록 설정
	HMC5883L_Read(HMC5883L_ID_REG_A, &id, 1);
	HAL_Delay(10);

	if (id == 0x48) {
		HAL_UART_Transmit(&huart2, (uint8_t *)"HMC5883L ID OK\r\n", sizeof("HMC5883L ID OK\r\n") - 1, 100);
	} else {
		HAL_UART_Transmit(&huart2, (uint8_t *)"HMC5883L ID Fail\r\n", sizeof("HMC5883L ID Fail\r\n") - 1, 100);
		return;
	}

    // Configuration Register A 설정 (75Hz, 정상 측정 모드)
    HMC5883L_Write(HMC5883L_CONFIG_A, HMC5883L_CONFIG_A_75HZ);
    HAL_Delay(10);

    // Configuration Register B 설정 (±1.3 Ga)
    HMC5883L_Write(HMC5883L_CONFIG_B, HMC5883L_CONFIG_B_1_3GA);
    HAL_Delay(10);

    // Mode Register: Continuous-Measurement 모드 설정
    HMC5883L_Write(HMC5883L_MODE, HMC5883L_MODE_CONTINUOUS);
    HAL_Delay(10);
}

// 오차 관련 함수
void MPU6050_ReadOffset(void)
{
	int32_t accel_sum[3] = {0};
	int32_t gyro_sum[3]  = {0};
	uint8_t buff[14];

	const uint16_t samples = 2000;

    int16_t expected_z = 0;
    switch (cfg.accel_fs_sel) {
        case _2g: 	expected_z = 16384; break; // ±2g
        case _4g: 	expected_z = 8192;  break; // ±4g
        case _8g: 	expected_z = 4096;  break; // ±8g
        case _16g: 	expected_z = 2048;  break; // ±16g
        default:   	expected_z = 4096;  break;
    }
	HAL_Delay(1000);

	for (uint16_t i = 0; i < samples; i++)
	{
		MPU6050_Read(MPU6050_ACCEL_XOUT_H, buff, 14);

		accel_sum[0] += (int16_t)((buff[0] << 8) | buff[1]);
		accel_sum[1] += (int16_t)((buff[2] << 8) | buff[3]);
		accel_sum[2] += (int16_t)((buff[4] << 8) | buff[5]);

		gyro_sum[0] += (int16_t)((buff[8]  << 8)  | buff[9]);
		gyro_sum[1] += (int16_t)((buff[10] << 8) | buff[11]);
		gyro_sum[2] += (int16_t)((buff[12] << 8) | buff[13]);

		HAL_Delay(5);  // 샘플 간격
	}
	accel_offset[0] = accel_sum[0] / samples;
	accel_offset[1] = accel_sum[1] / samples;
	accel_offset[2] = accel_sum[2] / samples - expected_z;

	gyro_offset[0] = gyro_sum[0] / samples;
	gyro_offset[1] = gyro_sum[1] / samples;
	gyro_offset[2] = gyro_sum[2] / samples;
}

// 데이터 읽기 (보정 데이터)
void MPU6050_ReadAccel(float accel[3])
{
	uint8_t buff[6] = {0};

	MPU6050_Read(MPU6050_ACCEL_XOUT_H, buff, 6);

	accel[0] = (float)((int16_t)((buff[0] << 8) | buff[1]) - accel_offset[0]) / cfg.accel_sens;
	accel[1] = (float)((int16_t)((buff[2] << 8) | buff[3]) - accel_offset[1]) / cfg.accel_sens;
	accel[2] = (float)((int16_t)((buff[4] << 8) | buff[5]) - accel_offset[2]) / cfg.accel_sens;
}
void MPU6050_ReadGyro(float gyro[3])
{
	uint8_t buff[6] = {0};

	MPU6050_Read(MPU6050_GYRO_XOUT_H, buff, 6);

	gyro[0] = (float)((int16_t)((buff[0] << 8) | buff[1]) - gyro_offset[0]) / cfg.gyro_sens;
	gyro[1] = (float)((int16_t)((buff[2] << 8) | buff[3]) - gyro_offset[1]) / cfg.gyro_sens;
	gyro[2] = (float)((int16_t)((buff[4] << 8) | buff[5]) - gyro_offset[2]) / cfg.gyro_sens;
}
void MPU6050_ReadTemp(float *temp)
{
	uint8_t buff[2] = {0};

	MPU6050_Read(MPU6050_TEMP_OUT_H, buff, 2);

	int16_t raw_temp = (int16_t)((buff[0] << 8) | buff[1]);
	*temp = (float)raw_temp / 340.0f + 36.53f;
}
void HMC5883L_ReadMag(float mag[3])
{
	uint8_t buff[6];
	HMC5883L_Read(HMC5883L_DATA_X_MSB, buff, 6);

	mag[0] = (float)(int16_t)((buff[0] << 8) | buff[1]) / HMC5883L_LSB_1_3G;
	mag[1] = (float)(int16_t)((buff[4] << 8) | buff[5]) / HMC5883L_LSB_1_3G;
	mag[2] = (float)(int16_t)((buff[2] << 8) | buff[3]) / HMC5883L_LSB_1_3G;
}

void MPU6050_ReadAll_DMA_Start(void)
{
    HAL_I2C_Mem_Read_DMA(&hi2c1, MPU6050_ADDRESS << 1, MPU6050_ACCEL_XOUT_H, I2C_MEMADD_SIZE_8BIT, mpu6050_buff, 14);
}
void HMC5883L_ReadAll_DMA_Start(void)
{
    HAL_I2C_Mem_Read_DMA(&hi2c1, HMC5883L_ADDRESS << 1, HMC5883L_DATA_X_MSB, I2C_MEMADD_SIZE_8BIT, hmc5883l_buff, 6);
}

void MPU6050_Parse_DMA(float accel[3], float gyro[3])
{
	accel[0] = (float)((int16_t)((mpu6050_buff[0] << 8) | mpu6050_buff[1]) - accel_offset[0]) / cfg.accel_sens;
	accel[1] = (float)((int16_t)((mpu6050_buff[2] << 8) | mpu6050_buff[3]) - accel_offset[1]) / cfg.accel_sens;
	accel[2] = (float)((int16_t)((mpu6050_buff[4] << 8) | mpu6050_buff[5]) - accel_offset[2]) / cfg.accel_sens;

	gyro[0] = (float)((int16_t)((mpu6050_buff[8]  << 8) | mpu6050_buff[9])  - gyro_offset[0]) / cfg.gyro_sens;
	gyro[1] = (float)((int16_t)((mpu6050_buff[10] << 8) | mpu6050_buff[11]) - gyro_offset[1]) / cfg.gyro_sens;
	gyro[2] = (float)((int16_t)((mpu6050_buff[12] << 8) | mpu6050_buff[13]) - gyro_offset[2]) / cfg.gyro_sens;
}

void HMC5883L_Parse_DMA(float mag[3])
{
	mag[0] = (float)(int16_t)((hmc5883l_buff[0] << 8) | hmc5883l_buff[1]) / HMC5883L_LSB_1_3G;
	mag[1] = (float)(int16_t)((hmc5883l_buff[2] << 8) | hmc5883l_buff[3]) / HMC5883L_LSB_1_3G;
	mag[2] = (float)(int16_t)((hmc5883l_buff[4] << 8) | hmc5883l_buff[5]) / HMC5883L_LSB_1_3G;
}

