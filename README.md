# 사회적약자에게 효율적인 쇼핑과 직원에게 생산성을 향상시키는 AGV  

|고객용 |관리자용 |
|---|---|
|![고객용로봇GIF_용량압축](https://github.com/user-attachments/assets/886fb3ab-2629-4c03-8eb2-8ea1eafd7462)<br> | ![관리자로봇영상합본_gif_용량압축](https://github.com/user-attachments/assets/6c2fc62b-7269-42cb-a834-36549d08f7f8)<br> |



  
## 개요
사회적약자에게 만족스러운 쇼핑 경험을 제공하기 위해 구매하고자하는 물품의 위치로 안내하고  
직원의 생산성을 향상시키기 위해 일정시간마다 재고를 파악하는 프로젝트입니다
  
개발 기간 : 2025.07.12 ~ 08.10  
팀명 : Mart Keeper  
팀장 : 우진우  
팀원 : 오현수, 이윤성, 이종희  
  
  
## 프로젝트 핵심기능
1. 사용자 AGV  
   * 사용자는 GUI를 통해 원하는 물품을 선택한다.
   * 선택한 물품의 최소 이동 경로를 결정하여 AGV를 이동한다.
   * 모든 물품을 카트에 담으면 계산대로 이동한다.

2. 관리자 AGV  
   * 카메라를 통해 일정시간 마다 마트 내부의 재고를 파악한다.
   * 재고가 없는 매대를 발견하면 해당 위치정보를 DB에 저장한다.

3. 공통  
   * AGV는 QR 인식을 통해 자신의 위치를 파악하고 카메라를 통해 라인을 인식하며 이동한다.
   * Mesh 네트워크를 구축하여 서로의 위치를 공유한다.
  
## 하드웨어
`< Raspberry Pi >`  
1. GUI  
   * 고객 : 원하는 물품을 고를 수 있도록 구성  
   * 관리자 : 재고를 파악 및 AGV의 위치 정보  
2. 카메라  
   * 사용자 및 관리자 AGV : QR 인식(AGV의 위치 정보), 라인 감지(AGV의 안전한 이동)  
   * 관리자 AGV : 재고 파악  
3. LoRa  
   * Mesh 네트워크 구성 (AGV 위치 정보 공유)  
  
`< STM32 >`  
1. Motor Control  
2. 적외선 Sensor : 사용자 AGV가 관리자 AGV를 감지하면 길을 터줌  
3. IMU  

## System Architecture
<img width="1770" height="798" alt="Image" src="https://github.com/user-attachments/assets/d46841ea-9685-4149-aaf4-edaced206319" />  

## Usecase Diagram  
<img width="3748" height="2276" alt="Image" src="https://github.com/user-attachments/assets/e0a21bc7-ae8b-4e34-82d0-3ce75e1931cf" />  
  
## Sequence Diagram
<img width="3997" height="1786" alt="Image" src="https://github.com/user-attachments/assets/47097458-3134-48dc-85ab-14dadc62dade" />  

  
## Clone code

```shell
https://github.com/Jinunu99/MartAGVrobot_Martkeeper.git
```

## Raspberry Pi 4 Settings
Raspbian Legacy OS (64-bit) install  
### csi 카메라 활성화
Legacy Camera Disable (sudo raspi-config)  

sudo nano /boot/config  
```
# 주석 제거
# hdmi_force_hotplug=1 설정하면 모니터가 연결되지 않았더라도 HDMI 출력을 활성화
hdmi_force_hotplug=1

hdmi_group=2  # 모니터 (DMT 표준) 사용  
hdmi_mode=82  # 1920x1080 @ 60Hz (Full HD, 1080p)  

# IMX219 카메라 센서 드라이버 활성화  
camera_auto_detect=0
dtoverlay=imx219
```
```
libcamera-hello # 카메라 확인 
```

## Prerequite

```shell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Steps to build

* (프로젝트를 실행을 위해 빌드 절차 기술)

```shell
cd ~/xxxx
source .venv/bin/activate

make
make install
```

## Steps to run

* (프로젝트 실행방법에 대해서 기술, 특별한 사용방법이 있다면 같이 기술)

```shell
cd ~/xxxx
source .venv/bin/activate

cd /path/to/repo/xxx/
python demo.py -i xxx -m yyy -d zzz
```

## Output


