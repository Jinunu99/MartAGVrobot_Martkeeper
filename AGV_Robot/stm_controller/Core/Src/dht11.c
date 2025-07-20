#include "dht11.h"


// 온습도 경계값 초기화
void DHT_thres_init(DHT_THRES *dht_thr)
{
	dht_thr->T1 = 25;
	dht_thr->T2 = 25;
	dht_thr->H1 = 20;
	dht_thr->H2 = 20;
}

// 온습도 파싱 함수
void DHT_parse(DHT_THRES *dht_thr, char *recv_data)
{
	char type[3];
	int value = 0;

	sscanf(recv_data, "%2s:%d", type, &value);

	printf("type : %s\n", type);
	printf("value : %d\n", value);

	if (strcmp(type, "T1") == 0)
		dht_thr->T1 = (uint8_t)value;
	else if (strcmp(type, "T2") == 0)
		dht_thr->T2 = (uint8_t)value;
	else if (strcmp(type, "H1") == 0)
		dht_thr->H1	= (uint8_t)value;
	else if (strcmp(type, "H2") == 0)
		dht_thr->H2 = (uint8_t)value;
}




// DHT11 초기화
void dht11Init(DHT11 *dht, GPIO_TypeDef *port, uint16_t pinNumber, TIM_HandleTypeDef *tim)
{
	// 구조체의 포트와 핀 번호를 설정
	dht->port = port;
	dht->pinNumber = pinNumber;
	dht->tim = tim;
}

// 포트를 input으로 사용할지, output으로 사용할지 설정해주는 함수
void dht11GpioMode(DHT11 *dht, uint8_t mode)
{
	// 포트에 대한 구조체 선언 및 초기화 (gpio.c를 보면 참고할 수 있음)
	GPIO_InitTypeDef GPIO_InitStruct = {0};

	if(mode == OUTPUT)
	{
		// 아웃풋 설정
		GPIO_InitStruct.Pin = dht->pinNumber;
		GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
		GPIO_InitStruct.Pull = GPIO_NOPULL;
		GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
		HAL_GPIO_Init(dht->port, &GPIO_InitStruct);
	}
	else if(mode == INPUT)
	{
		// 인풋 설정
		GPIO_InitStruct.Pin = dht->pinNumber;
		GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
		GPIO_InitStruct.Pull = GPIO_NOPULL;
		GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
		HAL_GPIO_Init(dht->port, &GPIO_InitStruct);
	}
}

uint8_t dht11Read(DHT11 *dht)
{
	bool ret = true;

	uint16_t timeTick = 0; 		// 시간 측정을 위한 변수 초기화
	uint8_t pulse[40] = {0};  // 40비트 데이터를 저장할 배열 및 초기화

	// 온습도 데이터 변수
	uint8_t humValue1 = 0, humValue2 = 0; // 습도
	uint8_t temValue1 = 0, temValue2 = 0; // 온도
	uint8_t parityValue = 0;							// 체크썸

	// 타이머 시작
	HAL_TIM_Base_Start(dht->tim);

	// 통신 시작 신호 전송 (MCU signal)
	dht11GpioMode(dht, OUTPUT);											  // GPIO를 출력 모드로 설정
	HAL_GPIO_WritePin(dht->port, dht->pinNumber, 0);  // dht에 0을 전송
	HAL_Delay(20);																		// 시작 신호 (Low로 유지)
	HAL_GPIO_WritePin(dht->port, dht->pinNumber, 1);	// dht에 1을 전송
	delay_us(30, dht->tim);																			// 30us 대기
	dht11GpioMode(dht, INPUT);												// GPIO를 입력 모드로 설정

	// dht11의 응답 신호 대기
	__HAL_TIM_SET_COUNTER(dht->tim, 0);
	while(HAL_GPIO_ReadPin(dht->port, dht->pinNumber) == GPIO_PIN_RESET) // Low 신호 대기
	{
		if(__HAL_TIM_GET_COUNTER(dht->tim) > 100)
		{
			printf("Not Low Signal\n\r"); // 타임아웃 오류 출력
			ret = false;
			return ret;					  // 타임아웃 오류가 났으면 while문을 탈출
		}
	}

	__HAL_TIM_SET_COUNTER(dht->tim, 0);
	while(HAL_GPIO_ReadPin(dht->port, dht->pinNumber) == GPIO_PIN_SET)
	{
		if(__HAL_TIM_GET_COUNTER(dht->tim) > 100)
		{
			printf("Not High Signal\n\r"); // 타임아웃 오류 출력

			// 해결 부분
			ret = false;
			return ret;					  // 타임아웃 오류가 났으면 while문을 탈출
		}
	}

	// 데이터를 수신
	for(uint8_t i = 0; i < 40; i++)
	{
		// start to transmit 1-bit data
		while(HAL_GPIO_ReadPin(dht->port, dht->pinNumber) == GPIO_PIN_RESET);

		__HAL_TIM_SET_COUNTER(dht->tim, 0);
		while(HAL_GPIO_ReadPin(dht->port, dht->pinNumber) == GPIO_PIN_SET)
		{
			timeTick = __HAL_TIM_GET_COUNTER(dht->tim);	// high 신호 길이를 측정

			if(timeTick > 20 && timeTick < 30) // 신호 길이가 짧으면 data = 0
			{
				pulse[i] = 0;
			}
			else if(timeTick > 65 && timeTick < 85) // 신호 길이가 길면 data = 1
			{
				pulse[i] = 1;
			}
		}
	}

	// 타이머 정지
	HAL_TIM_Base_Stop(dht->tim);

	// 배열에 저장된 데이터 처리
	for(uint8_t i = 0; i < 8; i++)
		humValue1 = (humValue1 << 1) + pulse[i];			// 습도 상위 8비트 (정수부)

	for(uint8_t i = 8; i < 16; i++)
		humValue2 = (humValue2 << 1) + pulse[i];			// 습도 하위 8비트 (실수부)

	for(uint8_t i = 16; i < 24; i++)
		temValue1 = (temValue1 << 1) + pulse[i];			// 온도 상위 8비트 (정수부)

	for(uint8_t i = 24; i < 32; i++)
		temValue2 = (temValue2 << 1) + pulse[i];			// 온도 상위 8비트 (실수부)

	for(uint8_t i = 32; i < 40; i++)
		parityValue = (parityValue << 1) + pulse[i];	// 체크썸 8비트


	// 구조체에 온습도 값을 저장
	dht->temperature = temValue1;
	dht->humidity = humValue1;


	// 데이터 무결성 검증 (정상적인 값이 들어왔는지 체크해봄)
	uint8_t checkSum = humValue1 + humValue2 + temValue1 + temValue2;
	if(checkSum != parityValue)
	{
		printf("checkSum Not Value\n\r");
		ret = false;
	}

	return ret;
}
