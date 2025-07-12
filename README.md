# 사회적약자에게 효율적인 쇼핑과 직원에게 생산성을 향상시키는 AGV
[Intel] 엣지 AI SW 아카데미 13기 - 팀명 : Mart Keeper

## "사회적약자에게 만족스러운 쇼핑 경험을 제공하기 위해 구매하고자하는 물품의 위치로 안내하고 직원의 생산성을 향상시키기 위해  일정시간 마다 재고를 파악하는 프로젝트입니다"

본 프로젝트에서 구현하고자 하는 핵심기능
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

## High Level Design

* (프로젝트 아키텍쳐 기술, 전반적인 diagram 으로 설명을 권장)

## Clone code

* (각 팀에서 프로젝트를 위해 생성한 repository에 대한 code clone 방법에 대해서 기술)

```shell
https://github.com/Jinunu99/MartAGVrobot_Martkeeper.git
```

## Prerequite

* (프로잭트를 실행하기 위해 필요한 dependencies 및 configuration들이 있다면, 설치 및 설정 방법에 대해 기술)

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

* (프로젝트 실행 화면 캡쳐)

![./result.jpg](./result.jpg)

## Appendix

* (참고 자료 및 알아두어야할 사항들 기술)
