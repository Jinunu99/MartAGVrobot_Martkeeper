<!-- # snack_dataset url 
https://universe.roboflow.com/korea-nazarene-university/-d9kpq/dataset/3

/home/paper/workspace/MartAGVrobot_Martkeeper/agvenv/bin/python3.9 -m pip install --upgrade pip

requirements 설치 명령어
pip install -r requirements.txt

파이썬 3.9로 가상환경 생성
/usr/local/bin/python3.9 -m venv agvenv

liblzma-dev 설치
<!-- sudo apt update -->
<!-- sudo apt install liblzma-dev -->

<!-- find ~ -type d -name "Python-3.9*" 로 경로 확인 후 이동, 재빌드

make clean
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall -->



<!-- 
# bz2 설치
sudo apt update
sudo apt install libbz2-dev

cd ~/Python-3.9.2 이동
빌드 --> 

<!-- make clean
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall -->

<!-- /usr/local/bin/python3.9 -c "import bz2; print('✅ bz2 정상 작동')" -->

<!-- cd ~/workspace/MartAGVrobot_Martkeeper
rm -rf agvenv
/usr/local/bin/python3.9 -m venv agvenv
source agvenv/bin/activate
python -c "import bz2; print('✅ 가상환경에서 bz2 정상 작동')" -->


<!-- # pip upgade 
python -m pip install --upgrade pip

MariDB 실행 / 허용
sudo systemctl start mariadb.service
sudo systemctl enable mariadb.service -->


# Tree

```
MakeModel_snack
├── .venv/
│   ├── Lib/
│   ├── Scripts/
│   ├── share/
│   ├── .gitignore
│   ├── LICENSE
│   └── pyvenv.cfg
├── models/
├── snack_dataset/
│   ├── train/
│   │   ├── images/
│   │   ├── labels/
│   │   └── data.yaml
│   ├── README.dataset.txt
│   └── README.roboflow.txt
```
