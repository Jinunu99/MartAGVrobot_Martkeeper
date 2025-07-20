""" 코랩에서 실행할 것 """

# 1단계: Colab 노트북 생성 및 라이브러리 설치
# Google Colab에서 실행
!pip install ultralytics

from google.colab import files
import os

# 방법 1: 직접 파일 업로드
uploaded = files.upload()
# 파일 선택 창이 나타나면 yolov11n.pt 파일 선택


# 2단계: 모델 파일 업로드
# 3단계: Edge TPU 형식으로 변환
from ultralytics import YOLO

# 업로드한 모델 로드
model_name = "yolov11n.pt"  # 업로드한 파일명
model = YOLO(model_name)

# Edge TPU 형식으로 내보내기
model.export(format="edgetpu", imgsz=320)

print("변환 완료!")


# 4단계: 생성된 파일 확인 및 다운로드
import os

# 생성된 파일들 확인
!ls -la *_saved_model/

# Edge TPU 파일 찾기
!find . -name "*_edgetpu.tflite" -type f

# 파일 다운로드
from google.colab import files

# Edge TPU 파일 다운로드
edgetpu_file = "yolov11n_full_integer_quant_edgetpu.tflite"
if os.path.exists(f"yolov11n_saved_model/{edgetpu_file}"):
    files.download(f"yolov11n_saved_model/{edgetpu_file}")
else:
    print("파일을 찾을 수 없습니다.")