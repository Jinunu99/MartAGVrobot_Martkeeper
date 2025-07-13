#include <led.h>

void shiftOut1(uint8_t data)
{
    for (int i = 7; i >= 0; i--)
    {
        if (data & (1 << i))
        	SER_HIGH_1();
        else
        	SER_LOW_1();

        SRCLK_HIGH_1();
        HAL_Delay(1);
        SRCLK_LOW_1();
    }

    RCLK_HIGH_1(); // latch
    HAL_Delay(1);
    RCLK_LOW_1();
}

void shiftOut2(uint8_t data)
{
    for (int i = 7; i >= 0; i--)
    {
        if (data & (1 << i))
        	SER_HIGH_2();
        else
        	SER_LOW_2();

        SRCLK_HIGH_2();
        HAL_Delay(1);
        SRCLK_LOW_2();
    }

    RCLK_HIGH_2(); // latch
    HAL_Delay(1);
    RCLK_LOW_2();
}

void LED1_on(uint8_t cnt)
{
	uint8_t on = 1;

	for(uint8_t i = 0; i < 2*cnt-1; i++)
	{
		on = on << 1 | 1;
	}

	shiftOut1(on);
}

void LED2_on(uint8_t cnt)
{
	uint8_t on = 1;

	for(uint8_t i = 0; i < 2*cnt-1; i++)
	{
		on = on << 1 | 1;
	}

	shiftOut2(on);
}

void LED1_off()
{
	shiftOut1(0);
}

void LED2_off()
{
	shiftOut2(0);
}

