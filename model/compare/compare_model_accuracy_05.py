import os
import yaml
from pathlib import Path
from ultralytics import YOLO
import pandas as pd
"""
모델 정확도 비교
"""

class AccuracyComparator:
    """모델 정확도 비교 도구"""

    def __init__(self, data_yaml_path="data.yaml"):
        """
        Args:
            data_yaml_path (str): 데이터 설정 파일 경로
        """
        self.data_yaml_path = data_yaml_path
        self.results = {}

        # 데이터 설정 확인
        if not Path(data_yaml_path).exists():
            print(f"❌ 데이터 파일이 없습니다: {data_yaml_path}")
            return

        print("📊 정확도 비교기 초기화 완료")

    def evaluate_pytorch_model(self, model_path):
        """PyTorch 모델 정확도 평가"""
        print(f"\n🔍 PyTorch 모델 평가 중: {model_path}")

        try:
            model = YOLO(model_path)
            metrics = model.val(data=self.data_yaml_path, verbose=False)

            result = {
                'model_type': 'PyTorch',
                'model_path': model_path,
                'map50': float(metrics.box.map50),
                'map50_95': float(metrics.box.map),
                'precision': float(metrics.box.mp),
                'recall': float(metrics.box.mr),
                'f1_score': 2 * (float(metrics.box.mp) * float(metrics.box.mr)) / (
                            float(metrics.box.mp) + float(metrics.box.mr)) if (float(metrics.box.mp) + float(
                    metrics.box.mr)) > 0 else 0
            }

            self.results['pytorch'] = result
            print("✅ PyTorch 모델 평가 완료")
            return result

        except Exception as e:
            print(f"❌ PyTorch 모델 평가 실패: {e}")
            return None

    def evaluate_openvino_model(self, model_path, model_type="fp16"):
        """OpenVINO 모델 정확도 평가 (YOLO로 로드)"""
        print(f"\n🔍 OpenVINO {model_type.upper()} 모델 평가 중: {model_path}")

        try:
            # OpenVINO 모델을 YOLO로 로드 (간접적 방법)
            model = YOLO(model_path)
            metrics = model.val(data=self.data_yaml_path, verbose=False)

            result = {
                'model_type': f'OpenVINO {model_type.upper()}',
                'model_path': model_path,
                'map50': float(metrics.box.map50),
                'map50_95': float(metrics.box.map),
                'precision': float(metrics.box.mp),
                'recall': float(metrics.box.mr),
                'f1_score': 2 * (float(metrics.box.mp) * float(metrics.box.mr)) / (
                            float(metrics.box.mp) + float(metrics.box.mr)) if (float(metrics.box.mp) + float(
                    metrics.box.mr)) > 0 else 0
            }

            self.results[model_type] = result
            print(f"✅ OpenVINO {model_type.upper()} 모델 평가 완료")
            return result

        except Exception as e:
            print(f"❌ OpenVINO {model_type.upper()} 모델 평가 실패: {e}")
            return None

    def compare_all_models(self, pytorch_path, fp16_path=None, int8_path=None):
        """모든 모델 정확도 비교"""
        print("\n🎯 전체 모델 정확도 비교 시작!")
        print("=" * 60)

        # PyTorch 모델 평가
        if Path(pytorch_path).exists():
            self.evaluate_pytorch_model(pytorch_path)
        else:
            print(f"❌ PyTorch 모델 없음: {pytorch_path}")

        # FP16 모델 평가
        if fp16_path and Path(fp16_path).exists():
            self.evaluate_openvino_model(fp16_path, "fp16")
        else:
            print(f"⚠️ FP16 모델 건너뜀")

        # INT8 모델 평가
        if int8_path and Path(int8_path).exists():
            self.evaluate_openvino_model(int8_path, "int8")
        else:
            print(f"⚠️ INT8 모델 건너뜀")

        # 결과 출력
        self.show_accuracy_results()

        return self.results

    def show_accuracy_results(self):
        """정확도 결과 출력"""
        if not self.results:
            print("❌ 평가 결과가 없습니다.")
            return

        print("\n📊 정확도 비교 결과")
        print("=" * 80)

        # 표 형태로 결과 정리
        df_data = []
        for key, result in self.results.items():
            df_data.append({
                '모델': result['model_type'],
                'mAP@0.5': f"{result['map50']:.4f}",
                'mAP@0.5:0.95': f"{result['map50_95']:.4f}",
                'Precision': f"{result['precision']:.4f}",
                'Recall': f"{result['recall']:.4f}",
                'F1-Score': f"{result['f1_score']:.4f}"
            })

        df = pd.DataFrame(df_data)
        print(df.to_string(index=False))

        # 최고 성능 모델 찾기
        if len(self.results) > 1:
            best_map50 = max(self.results.values(), key=lambda x: x['map50'])
            best_map50_95 = max(self.results.values(), key=lambda x: x['map50_95'])

            print(f"\n🏆 최고 mAP@0.5: {best_map50['model_type']} ({best_map50['map50']:.4f})")
            print(f"🏆 최고 mAP@0.5:0.95: {best_map50_95['model_type']} ({best_map50_95['map50_95']:.4f})")

        # 정확도 손실 분석
        self.analyze_accuracy_loss()

    def analyze_accuracy_loss(self):
        """정확도 손실 분석"""
        if 'pytorch' not in self.results:
            print("⚠️ PyTorch 기준 모델이 없어 손실 분석을 건너뜁니다.")
            return

        print(f"\n📉 PyTorch 대비 정확도 손실 분석:")
        pytorch_map50 = self.results['pytorch']['map50']
        pytorch_map50_95 = self.results['pytorch']['map50_95']

        for key, result in self.results.items():
            if key == 'pytorch':
                continue

            map50_loss = (pytorch_map50 - result['map50']) / pytorch_map50 * 100
            map50_95_loss = (pytorch_map50_95 - result['map50_95']) / pytorch_map50_95 * 100

            print(f"  {result['model_type']}:")
            print(f"    - mAP@0.5 손실: {map50_loss:.2f}%")
            print(f"    - mAP@0.5:0.95 손실: {map50_95_loss:.2f}%")

    def save_results(self, output_path="accuracy_comparison.csv"):
        """결과를 CSV 파일로 저장"""
        if not self.results:
            print("❌ 저장할 결과가 없습니다.")
            return

        df_data = []
        for key, result in self.results.items():
            df_data.append(result)

        df = pd.DataFrame(df_data)
        df.to_csv(output_path, index=False)
        print(f"💾 결과 저장 완료: {output_path}")


# 사용 예시
if __name__ == "__main__":
    # 정확도 비교기 생성
    comparator = AccuracyComparator("data.yaml")

    # 모든 모델 정확도 비교
    results = comparator.compare_all_models(
        pytorch_path="snack_detection/yolov8s_custom/weights/best.pt",
        fp16_path="models/best_openvino_model/best.xml",
        int8_path="models/best_int8_openvino_model/best.xml"
    )

    # 결과 저장
    comparator.save_results("accuracy_comparison.csv")

    print("\n🎉 정확도 비교 완료!")