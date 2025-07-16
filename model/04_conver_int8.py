import requests
from pathlib import Path
from ultralytics import YOLO


class INT8Converter:
    """YOLOv8을 INT8 양자화된 OpenVINO로 변환하는 클래스"""

    def __init__(self, model_path, data_yaml_path="data.yaml"):
        """
        Args:
            model_path (str): 훈련된 YOLOv8 모델 경로 (.pt 파일)
            data_yaml_path (str): 양자화용 데이터 설정 파일
        """
        self.model_path = Path(model_path)
        self.data_yaml_path = Path(data_yaml_path)
        self.models_dir = Path("./models")
        self.models_dir.mkdir(exist_ok=True)

        print(f" INT8 양자화 변환기 시작")
        print(f" 모델: {self.model_path}")
        print(f" 데이터: {self.data_yaml_path}")

        # 필수 과정 실행
        self.setup_utils()
        self.check_data_file()
        self.load_model()
        self.convert_to_int8()

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

    def check_data_file(self):
        """데이터 YAML 파일 확인"""
        if not self.data_yaml_path.exists():
            print(f" 데이터 파일이 없습니다: {self.data_yaml_path}")
            print(" INT8 양자화에는 데이터 파일이 필요합니다")
            print(" 훈련 시 생성된 data.yaml 파일을 사용하세요")
            return False

        print(f" 데이터 파일 확인: {self.data_yaml_path}")
        return True

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

            # 모델 정보 출력
            if hasattr(self.model, 'model') and hasattr(self.model.model, 'names'):
                class_count = len(self.model.model.names)
                print(f" 클래스 수: {class_count}")

            return True
        except Exception as e:
            print(f" 모델 로드 실패: {e}")
            return False

    def convert_to_int8(self):
        """INT8 양자화된 OpenVINO 모델로 변환"""
        if not hasattr(self, 'model'):
            print(" 모델이 로드되지 않았습니다")
            return None

        if not self.data_yaml_path.exists():
            print(" 데이터 파일이 없어 INT8 변환을 할 수 없습니다")
            return None

        # INT8 OpenVINO 모델 경로 설정
        openvino_dir = self.models_dir / f"{self.model_name}_int8_openvino_model"
        openvino_path = openvino_dir / f"{self.model_name}.xml"

        # 이미 변환된 모델이 있는지 확인
        if openvino_path.exists():
            print(f" INT8 OpenVINO 모델이 이미 존재: {openvino_path}")
            self.openvino_path = openvino_path
            return str(openvino_path)

        # INT8 양자화 변환 실행
        print(f" INT8 양자화 변환 시작...")
        print(" 양자화는 시간이 오래 걸릴 수 있습니다...")

        try:
            exported_path = self.model.export(
                format="openvino",
                dynamic=True,  # 동적 입력 크기
                int8=True,  # INT8 양자화 활성화
                data=str(self.data_yaml_path)  # 양자화용 데이터 제공
            )

            self.openvino_path = openvino_path

            print(f" INT8 양자화 변환 완료!")
            print(f" 변환된 모델: {openvino_path}")

            # 생성된 파일 확인
            self._show_files()

            # 모델 크기 비교
            self._show_size_comparison()

            return str(exported_path)

        except Exception as e:
            print(f" INT8 변환 실패: {e}")
            print(" NNCF 패키지가 설치되어 있는지 확인하세요: pip install nncf")
            return None

    def _show_files(self):
        """생성된 파일들 표시"""
        if hasattr(self, 'openvino_path') and self.openvino_path.parent.exists():
            print("\n 생성된 INT8 파일들:")
            total_size = 0
            for file in self.openvino_path.parent.iterdir():
                if file.is_file():
                    size_mb = file.stat().st_size / (1024 * 1024)
                    total_size += size_mb
                    print(f"  📄 {file.name}: {size_mb:.1f}MB")
            print(f" 총 크기: {total_size:.1f}MB")

    def _show_size_comparison(self):
        """원본 모델과 크기 비교"""
        if hasattr(self, 'openvino_path') and self.openvino_path.parent.exists():
            # 원본 모델 크기
            original_size = self.model_path.stat().st_size / (1024 * 1024)

            # INT8 모델 크기
            int8_size = 0
            for file in self.openvino_path.parent.iterdir():
                if file.is_file():
                    int8_size += file.stat().st_size / (1024 * 1024)

            # 압축률 계산
            compression_ratio = original_size / int8_size if int8_size > 0 else 0
            size_reduction = ((original_size - int8_size) / original_size) * 100 if original_size > 0 else 0

            print(f"\n 모델 크기 비교:")
            print(f"   원본 (.pt): {original_size:.1f}MB")
            print(f"   INT8 (.xml/.bin): {int8_size:.1f}MB")
            print(f"   크기 감소: {size_reduction:.1f}%")
            print(f"  ️ 압축률: {compression_ratio:.1f}x")

    def get_model_path(self):
        """변환된 INT8 OpenVINO 모델 경로 반환"""
        return str(self.openvino_path) if hasattr(self, 'openvino_path') else None

    def get_model_info(self):
        """모델 정보 반환"""
        if not hasattr(self, 'model'):
            return None

        info = {
            'original_model': str(self.model_path),
            'int8_model': self.get_model_path(),
            'data_file': str(self.data_yaml_path),
            'quantization': 'INT8',
            'dynamic_input': True
        }

        if hasattr(self.model, 'model') and hasattr(self.model.model, 'names'):
            info['num_classes'] = len(self.model.model.names)
            info['class_names'] = list(self.model.model.names.values())

        return info



if __name__ == "__main__":
    # INT8 양자화 변환
    converter = INT8Converter(
        model_path="snack_detection/yolov8s_custom/weights/best.pt",
        data_yaml_path="data.yaml"
    )

    # 변환된 모델 경로 확인
    model_path = converter.get_model_path()

    if model_path:
        print(f"\n INT8 변환 성공!")
        print(f" INT8 모델: {model_path}")
        print(f" 라즈베리파이에서 더 빠른 추론 가능")

        # 모델 정보 출력
        info = converter.get_model_info()
        print(f"\n 모델 정보:")
        print(f"  - 클래스 수: {info.get('num_classes', 'N/A')}")
        print(f"  - 양자화: {info.get('quantization')}")
        print(f"  - 동적 입력: {info.get('dynamic_input')}")

    else:
        print(f"\n INT8 변환 실패!")
        print(" data.yaml 파일이 있는지 확인하세요")
        print(" NNCF 패키지가 설치되어 있는지 확인하세요")