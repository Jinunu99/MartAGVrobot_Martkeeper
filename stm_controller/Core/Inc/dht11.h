#ifndef INC_DHT11_H_
#define INC_DHT11_H_

#include "main.h"
#include "delay.h"
#include "tim.h"
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

enum
{
	INPUT,
	OUTPUT
};

typedef struct
{
	GPIO_TypeDef  *port;			// 데이터 포트
	uint16_t	  pinNumber;		// 데이터 핀번호
	uint8_t		  temperature;		// 온도 값
	uint8_t		  humidity;			// 습도 값
	TIM_HandleTypeDef *tim;			// 어떤 타이머?
}DHT11;


typedef struct
{
	uint8_t		T1;
	uint8_t		H1;
	uint8_t		T2;
	uint8_t		H2;
}DHT_THRES;

void DHT_thres_init(DHT_THRES *dht_thr);
void DHT_parse(DHT_THRES *dht_thr, char *recv_data);
void dht11Init(DHT11 *dht, GPIO_TypeDef *port, uint16_t pinNumber, TIM_HandleTypeDef *tim);
void dht11GpioMode(DHT11 *dht, uint8_t mode); // input 모드인지 output 모드인지 결정
uint8_t dht11Read(DHT11 *dht); // 8비트 단위로 데이터가 날라들어오니까



#endif /* INC_DHT11_H_ */
