import requests
import subprocess
import sys
from pathlib import Path
from ultralytics import YOLO
"""
FP 16 변환
"""

class OpenVINOConverter:
    """YOLOv8을 OpenVINO로 변환하는 간단한 클래스"""

    def __init__(self, model_path):
        """
        Args:
            model_path (str): 훈련된 YOLOv8 모델 경로 (.pt 파일)
        """
        self.model_path = Path(model_path)
        self.models_dir = Path("./models")
        self.models_dir.mkdir(exist_ok=True)

        print(f" OpenVINO 변환기 시작")
        print(f" 모델: {self.model_path}")

        # 필수 과정 실행
        self.setup_utils()
        self.load_model()
        self.convert_to_openvino()

    def setup_utils(self):
        """notebook_utils.py 다운로드"""
        utils_file = Path("notebook_utils.py")

        if not utils_file.exists():
            print("📥 notebook_utils.py 다운로드 중...")
            try:
                url = "https://raw.githubusercontent.com/openvinotoolkit/openvino_notebooks/latest/utils/notebook_utils.py"
                r = requests.get(url)
                r.raise_for_status()

                with open(utils_file, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print(" 유틸리티 다운로드 완료")
            except Exception as e:
                print(f"️ 유틸리티 다운로드 실패: {e}")
        else:
            print(" 유틸리티 이미 존재")

    def load_model(self):
        """YOLOv8 모델 로드"""
        if not self.model_path.exists():
            print(f" 모델 파일이 없습니다: {self.model_path}")
            return False

        print(f" 모델 로드 중: {self.model_path}")

        try:
            self.model = YOLO(str(self.model_path))
            self.model_name = self.model_path.stem
            print(f" 모델 로드 완료: {self.model_name}")
            return True
        except Exception as e:
            print(f" 모델 로드 실패: {e}")
            return False

    def convert_to_openvino(self):
        """OpenVINO 형식으로 변환"""
        if not hasattr(self, 'model'):
            print(" 모델이 로드되지 않았습니다")
            return None

        # OpenVINO 모델 경로 설정
        openvino_dir = self.models_dir / f"{self.model_name}_openvino_model"
        openvino_path = openvino_dir / f"{self.model_name}.xml"

        # 이미 변환된 모델이 있는지 확인
        if openvino_path.exists():
            print(f" OpenVINO 모델이 이미 존재: {openvino_path}")
            self.openvino_path = openvino_path
            return str(openvino_path)

        # OpenVINO 변환 실행
        print(f" OpenVINO 변환 시작...")

        try:
            exported_path = self.model.export(
                format="openvino",
                dynamic=True,  # 동적 입력 크기
                half=True  # FP16 정밀도
            )

            self.openvino_path = openvino_path

            print(f" OpenVINO 변환 완료!")
            print(f" 변환된 모델: {openvino_path}")

            # 생성된 파일 확인
            self._show_files()

            return str(exported_path)

        except Exception as e:
            print(f" OpenVINO 변환 실패: {e}")
            return None

    def _show_files(self):
        """생성된 파일들 표시"""
        if hasattr(self, 'openvino_path') and self.openvino_path.parent.exists():
            print("\n 생성된 파일들:")
            for file in self.openvino_path.parent.iterdir():
                if file.is_file():
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"   {file.name}: {size_mb:.1f}MB")

    def get_model_path(self):
        """변환된 OpenVINO 모델 경로 반환"""
        return str(self.openvino_path) if hasattr(self, 'openvino_path') else None


# 사용 예시
if __name__ == "__main__":
    # 커스텀 모델 변환
    converter = OpenVINOConverter("snack_detection/yolov8s_custom/weights/best.pt")

    # 변환된 모델 경로 확인
    model_path = converter.get_model_path()

    if model_path:
        print(f"\n 변환 성공!")
        print(f" OpenVINO 모델: {model_path}")
        print(f" 라즈베리파이에서 사용 가능")
    else:
        print(f"\n변환 실패!")