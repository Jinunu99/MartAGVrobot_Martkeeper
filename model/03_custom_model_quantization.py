import requests
import subprocess
import sys
import shutil
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
        
        # 목표 경로: model/snack_detection/best_openvino_model/
        self.target_dir = Path("snack_detection/best_openvino_model")
        self.target_dir.mkdir(parents=True, exist_ok=True)

        print(f" OpenVINO 변환기 시작")
        print(f" 모델: {self.model_path}")
        print(f" 변환 목표 경로: {self.target_dir}")

        # 필수 과정 실행
        self.setup_utils()
        self.load_model()
        self.convert_to_openvino()

    def setup_utils(self):
        """notebook_utils.py 다운로드"""
        utils_file = Path("notebook_utils.py")

        if not utils_file.exists():
            print(" notebook_utils.py 다운로드 중...")
            try:
                url = "https://raw.githubusercontent.com/openvinotoolkit/openvino_notebooks/latest/utils/notebook_utils.py"
                r = requests.get(url)
                r.raise_for_status()

                with open(utils_file, "w", encoding="utf-8") as f:
                    f.write(r.text)
                print(" 유틸리티 다운로드 완료")
            except Exception as e:
                print(f" 유틸리티 다운로드 실패: {e}")
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
            self.model_name = self.model_path.stem  # 'best'
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

        # 최종 OpenVINO 모델 경로 설정
        final_xml_path = self.target_dir / f"{self.model_name}.xml"
        final_bin_path = self.target_dir / f"{self.model_name}.bin"

        # 이미 변환된 모델이 있는지 확인
        if final_xml_path.exists() and final_bin_path.exists():
            print(f" OpenVINO 모델이 이미 존재: {final_xml_path}")
            self.openvino_path = final_xml_path
            return str(final_xml_path)

        # OpenVINO 변환 실행 (임시 위치에 생성됨)
        print(f" OpenVINO 변환 시작...")

        try:
            # YOLO export는 모델과 같은 디렉토리에 생성
            exported_path = self.model.export(
                format="openvino",
                dynamic=True,  # 동적 입력 크기
                half=True  # FP16 정밀도
            )

            # 생성된 파일들을 목표 위치로 이동
            self._move_files_to_target(exported_path)

            print(f" OpenVINO 변환 완료!")
            print(f" 변환된 모델: {final_xml_path}")

            # 생성된 파일 확인
            self._show_files()

            return str(final_xml_path)

        except Exception as e:
            print(f" OpenVINO 변환 실패: {e}")
            return None

    def _move_files_to_target(self, exported_path):
        """생성된 OpenVINO 파일들을 목표 디렉토리로 이동"""
        print(f" Export 반환 경로: {exported_path}")
        
        # 가능한 경로들 시도
        possible_paths = [
            Path(exported_path),  # 직접 경로
            Path(exported_path).parent,  # 부모 디렉토리
            self.model_path.parent / f"{self.model_name}_openvino_model",  # 모델 옆 디렉토리
        ]
        
        exported_dir = None
        for path in possible_paths:
            print(f" 경로 확인: {path}")
            if path.exists():
                # XML, BIN 파일이 있는지 확인
                xml_files = list(path.glob("*.xml"))
                bin_files = list(path.glob("*.bin"))
                if xml_files and bin_files:
                    exported_dir = path
                    print(f" OpenVINO 파일 발견: {path}")
                    break
                else:
                    print(f" 디렉토리 내용 ({path}):")
                    for item in path.iterdir():
                        print(f"   - {item.name}")
        
        if not exported_dir:
            print(f" OpenVINO 파일을 찾을 수 없습니다")
            return
        
        # 생성된 파일들 찾기
        xml_files = list(exported_dir.glob("*.xml"))
        bin_files = list(exported_dir.glob("*.bin"))
        
        print(f" 찾은 XML 파일: {[f.name for f in xml_files]}")
        print(f" 찾은 BIN 파일: {[f.name for f in bin_files]}")
        
        # 파일 이동
        for xml_file in xml_files:
            target_xml = self.target_dir / f"{self.model_name}.xml"
            shutil.move(str(xml_file), str(target_xml))
            print(f" 이동: {xml_file.name} -> {target_xml}")
        
        for bin_file in bin_files:
            target_bin = self.target_dir / f"{self.model_name}.bin"
            shutil.move(str(bin_file), str(target_bin))
            print(f" 이동: {bin_file.name} -> {target_bin}")
        
        # 빈 디렉토리 제거
        try:
            if exported_dir.exists() and not any(exported_dir.iterdir()):
                exported_dir.rmdir()
                print(f" 빈 디렉토리 제거: {exported_dir}")
        except Exception as e:
            print(f" 디렉토리 제거 실패: {e}")
        
        self.openvino_path = self.target_dir / f"{self.model_name}.xml"

    def _show_files(self):
        """생성된 파일들 표시"""
        if self.target_dir.exists():
            print(f"\n 생성된 파일들 ({self.target_dir}):")
            for file in self.target_dir.iterdir():
                if file.is_file():
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"    {file.name}: {size_mb:.1f}MB")

    def get_model_path(self):
        """변환된 OpenVINO 모델 경로 반환"""
        return str(self.openvino_path) if hasattr(self, 'openvino_path') else None


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
        print(f"\n 변환 실패!")