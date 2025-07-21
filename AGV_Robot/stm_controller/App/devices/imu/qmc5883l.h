/*
 * qmc5883l.h
 *
 *  Created on: Jul 18, 2025
 *      Author: User
 */

#ifndef DEVICES_IMU_QMC5883L_H_
#define DEVICES_IMU_QMC5883L_H_

// -----------------------------------------------------------------------------
// QMC5883L 기본 정보
// -----------------------------------------------------------------------------
#define QMC5883L_ADDRESS             0x0D    // QMC5883L I2C 주소 (7-bit)

// -----------------------------------------------------------------------------
// QMC5883L 레지스터 정의
// -----------------------------------------------------------------------------
#define QMC5883L_DATA_X_LSB          0x00    // X축 데이터 LSB
#define QMC5883L_DATA_X_MSB          0x01    // X축 데이터 MSB
#define QMC5883L_DATA_Y_LSB          0x02    // Y축 데이터 LSB
#define QMC5883L_DATA_Y_MSB          0x03    // Y축 데이터 MSB
#define QMC5883L_DATA_Z_LSB          0x04    // Z축 데이터 LSB
#define QMC5883L_DATA_Z_MSB          0x05    // Z축 데이터 MSB
#define QMC5883L_STATUS              0x06    // 상태 레지스터
#define QMC5883L_TOUT_LSB            0x07    // 온도 LSB
#define QMC5883L_TOUT_MSB            0x08    // 온도 MSB
#define QMC5883L_CONTROL_1           0x09    // 제어 레지스터 1
#define QMC5883L_CONTROL_2           0x0A    // 제어 레지스터 2
#define QMC5883L_SET_RESET_PERIOD    0x0B    // Set/Reset 주기 설정
#define QMC5883L_RESERVED            0x0C    // Reserved
#define QMC5883L_CHIP_ID             0x0D    // Chip ID (0xFF 반환)

// -----------------------------------------------------------------------------
// 상태 레지스터(0x06) 비트 정의
// -----------------------------------------------------------------------------
#define QMC5883L_STATUS_DRDY         0x01    // Data Ready
#define QMC5883L_STATUS_OVL          0x02    // Overflow
#define QMC5883L_STATUS_DOR          0x04    // Data skipped for reading

// -----------------------------------------------------------------------------
// 제어 레지스터 1 (0x09) 설정 값
// -----------------------------------------------------------------------------

// MODE 설정
#define QMC5883L_MODE_STANDBY        0x00
#define QMC5883L_MODE_CONTINUOUS     0x01

// ODR 설정 (출력 데이터 속도)
#define QMC5883L_ODR_10HZ             0x00
#define QMC5883L_ODR_50HZ             0x01
#define QMC5883L_ODR_100HZ            0x02
#define QMC5883L_ODR_200HZ            0x03

// RNG 설정 (측정 범위)
#define QMC5883L_RANGE_2G             0x00
#define QMC5883L_RANGE_8G             0x01

// OSR 설정 (오버샘플링 비율)
#define QMC5883L_OSR_512              0x00
#define QMC5883L_OSR_256              0x01
#define QMC5883L_OSR_128              0x02
#define QMC5883L_OSR_64               0x03

// -----------------------------------------------------------------------------
// 제어 레지스터 2 (0x0A) 비트 정의
// -----------------------------------------------------------------------------
#define QMC5883L_SOFT_RST             0x80
#define QMC5883L_ROL_PNT              0x40
#define QMC5883L_INT_ENB              0x01

// -----------------------------------------------------------------------------
// QMC5883L Gain 값 (LSB/Gauss)
// -----------------------------------------------------------------------------
#define QMC5883L_LSB_2G               12000.0f
#define QMC5883L_LSB_8G               3000.0f

#endif /* DEVICES_IMU_QMC5883L_H_ */
