import time
import cv2
import numpy as np
import openvino as ov
from pathlib import Path
from ultralytics import YOLO
import matplotlib.pyplot as plt
import pandas as pd

"""
모델 성능 비교
"""


class ModelPerformanceComparator:
    """모델 성능 비교 도구"""

    def __init__(self, pytorch_model_path, openvino_fp16_path, openvino_int8_path):
        """
        Args:
            pytorch_model_path (str): PyTorch 모델 경로 (.pt)
            openvino_fp16_path (str): OpenVINO FP16 모델 경로 (.xml)
            openvino_int8_path (str): OpenVINO INT8 모델 경로 (.xml)
        """
        self.pytorch_path = Path(pytorch_model_path)
        self.fp16_path = Path(openvino_fp16_path)
        self.int8_path = Path(openvino_int8_path)

        # 모델들 로드
        self.models = {}
        self.load_models()

        print("🔍 모델 성능 비교기 초기화 완료")

    def load_models(self):
        """모든 모델 로드"""

        # 1. PyTorch 모델 로드
        try:
            if self.pytorch_path.exists():
                self.models['pytorch'] = YOLO(str(self.pytorch_path))
                print("✅ PyTorch 모델 로드 완료")
            else:
                print(f"❌ PyTorch 모델 없음: {self.pytorch_path}")
        except Exception as e:
            print(f"❌ PyTorch 모델 로드 실패: {e}")

        # 2. OpenVINO 모델들 로드
        core = ov.Core()

        # FP16 모델
        try:
            if self.fp16_path.exists():
                model_fp16 = core.read_model(str(self.fp16_path))
                self.models['fp16'] = core.compile_model(model_fp16, "CPU")
                print("✅ OpenVINO FP16 모델 로드 완료")
            else:
                print(f"❌ FP16 모델 없음: {self.fp16_path}")
        except Exception as e:
            print(f"❌ FP16 모델 로드 실패: {e}")

        # INT8 모델
        try:
            if self.int8_path.exists():
                model_int8 = core.read_model(str(self.int8_path))
                self.models['int8'] = core.compile_model(model_int8, "CPU")
                print("✅ OpenVINO INT8 모델 로드 완료")
            else:
                print(f"❌ INT8 모델 없음: {self.int8_path}")
        except Exception as e:
            print(f"❌ INT8 모델 로드 실패: {e}")

    def prepare_test_data(self, image_path=None, num_test_images=100):
        """테스트 데이터 준비"""

        if image_path and Path(image_path).exists():
            # 실제 이미지 사용
            image = cv2.imread(image_path)
            self.test_images = [image] * num_test_images
            print(f"📸 실제 이미지로 테스트: {image_path}")
        else:
            # 더미 이미지 생성
            self.test_images = []
            for _ in range(num_test_images):
                dummy_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
                self.test_images.append(dummy_image)
            print(f"🖼️ 더미 이미지로 테스트: {num_test_images}개")

    def benchmark_pytorch(self, warmup=10, iterations=100):
        """PyTorch 모델 벤치마크"""
        if 'pytorch' not in self.models:
            return None

        model = self.models['pytorch']

        print("🔥 PyTorch 모델 워밍업...")
        # 워밍업
        for i in range(warmup):
            _ = model(self.test_images[i % len(self.test_images)], verbose=False)

        print("⏱️ PyTorch 모델 벤치마크 실행...")
        # 벤치마크
        times = []
        for i in range(iterations):
            start_time = time.time()
            _ = model(self.test_images[i % len(self.test_images)], verbose=False)
            end_time = time.time()
            times.append(end_time - start_time)

        return {
            'model': 'PyTorch',
            'times': times,
            'avg_time': np.mean(times),
            'std_time': np.std(times),
            'fps': 1.0 / np.mean(times)
        }

    def benchmark_openvino(self, model_type, warmup=10, iterations=100):
        """OpenVINO 모델 벤치마크"""
        if model_type not in self.models:
            return None

        compiled_model = self.models[model_type]
        input_layer = compiled_model.input(0)
        output_layer = compiled_model.output(0)

        # 이미지 전처리
        def preprocess_image(image):
            resized = cv2.resize(image, (640, 640))
            rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            input_tensor = rgb_image.astype(np.float32) / 255.0
            input_tensor = input_tensor.transpose(2, 0, 1)  # HWC → CHW
            input_tensor = np.expand_dims(input_tensor, 0)  # 배치 차원 추가
            return input_tensor

        # 테스트 데이터 전처리
        preprocessed_images = [preprocess_image(img) for img in self.test_images[:iterations]]

        print(f"🔥 {model_type.upper()} 모델 워밍업...")
        # 워밍업
        for i in range(warmup):
            _ = compiled_model([preprocessed_images[i % len(preprocessed_images)]])[output_layer]

        print(f"⏱️ {model_type.upper()} 모델 벤치마크 실행...")
        # 벤치마크
        times = []
        for i in range(iterations):
            start_time = time.time()
            _ = compiled_model([preprocessed_images[i]])[output_layer]
            end_time = time.time()
            times.append(end_time - start_time)

        return {
            'model': f'OpenVINO {model_type.upper()}',
            'times': times,
            'avg_time': np.mean(times),
            'std_time': np.std(times),
            'fps': 1.0 / np.mean(times)
        }

    def run_full_benchmark(self, test_image_path=None, iterations=100):
        """전체 벤치마크 실행"""
        print("\n🚀 전체 성능 벤치마크 시작!")
        print("=" * 60)

        # 테스트 데이터 준비
        self.prepare_test_data(test_image_path, iterations)

        results = []

        # 각 모델 벤치마크
        if 'pytorch' in self.models:
            pytorch_result = self.benchmark_pytorch(iterations=iterations)
            if pytorch_result:
                results.append(pytorch_result)

        if 'fp16' in self.models:
            fp16_result = self.benchmark_openvino('fp16', iterations=iterations)
            if fp16_result:
                results.append(fp16_result)

        if 'int8' in self.models:
            int8_result = self.benchmark_openvino('int8', iterations=iterations)
            if int8_result:
                results.append(int8_result)

        # 결과 출력 및 분석
        self.show_results(results)
        self.plot_results(results)

        return results

    def show_results(self, results):
        """결과 출력"""
        print("\n📊 성능 비교 결과")
        print("=" * 60)

        # 표 형태로 출력
        df_data = []
        for result in results:
            df_data.append({
                '모델': result['model'],
                '평균 시간 (ms)': f"{result['avg_time'] * 1000:.2f}",
                '표준편차 (ms)': f"{result['std_time'] * 1000:.2f}",
                'FPS': f"{result['fps']:.2f}",
                '상대 속도': f"{result['fps'] / results[0]['fps']:.2f}x" if results else "1.00x"
            })

        df = pd.DataFrame(df_data)
        print(df.to_string(index=False))

        # 최고 성능 모델 표시
        if results:
            best_model = max(results, key=lambda x: x['fps'])
            print(f"\n🏆 최고 성능: {best_model['model']} ({best_model['fps']:.2f} FPS)")

    def plot_results(self, results, save_path="performance_comparison.png"):
        """결과 시각화"""
        if not results:
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # 평균 추론 시간 비교
        models = [r['model'] for r in results]
        avg_times = [r['avg_time'] * 1000 for r in results]  # ms 단위

        bars1 = ax1.bar(models, avg_times, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax1.set_ylabel('평균 추론 시간 (ms)')
        ax1.set_title('모델별 추론 시간 비교')
        ax1.set_ylim(0, max(avg_times) * 1.2)

        # 막대 위에 값 표시
        for bar, time in zip(bars1, avg_times):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(avg_times) * 0.01,
                     f'{time:.1f}ms', ha='center', va='bottom')

        # FPS 비교
        fps_values = [r['fps'] for r in results]
        bars2 = ax2.bar(models, fps_values, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax2.set_ylabel('FPS (Frames Per Second)')
        ax2.set_title('모델별 FPS 비교')
        ax2.set_ylim(0, max(fps_values) * 1.2)

        # 막대 위에 값 표시
        for bar, fps in zip(bars2, fps_values):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(fps_values) * 0.01,
                     f'{fps:.1f}', ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

        print(f"📈 그래프 저장: {save_path}")

    def accuracy_comparison(self, test_dataset_path):
        """정확도 비교 (별도 구현 필요)"""
        print("📊 정확도 비교는 별도 구현이 필요합니다")
        print("💡 각 모델로 동일한 테스트 데이터셋에서 mAP 측정을 권장합니다")

    def get_model_sizes(self):
        """모델 크기 비교"""
        sizes = {}

        # PyTorch 모델 크기
        if self.pytorch_path.exists():
            sizes['PyTorch'] = self.pytorch_path.stat().st_size / (1024 * 1024)

        # FP16 모델 크기
        if self.fp16_path.exists():
            fp16_dir = self.fp16_path.parent
            fp16_size = sum(f.stat().st_size for f in fp16_dir.iterdir() if f.is_file()) / (1024 * 1024)
            sizes['OpenVINO FP16'] = fp16_size

        # INT8 모델 크기
        if self.int8_path.exists():
            int8_dir = self.int8_path.parent
            int8_size = sum(f.stat().st_size for f in int8_dir.iterdir() if f.is_file()) / (1024 * 1024)
            sizes['OpenVINO INT8'] = int8_size

        print("\n💾 모델 크기 비교:")
        for model, size in sizes.items():
            print(f"  {model}: {size:.1f}MB")

        return sizes


# 사용 예시
if __name__ == "__main__":
    # 모델 경로 설정
    pytorch_model = "snack_detection/yolov8s_custom/weights/best.pt"
    fp16_model = "models/best_openvino_model/best.xml"
    int8_model = "models/best_int8_openvino_model/best.xml"

    # 성능 비교기 생성
    comparator = ModelPerformanceComparator(
        pytorch_model_path=pytorch_model,
        openvino_fp16_path=fp16_model,
        openvino_int8_path=int8_model
    )

    # 모델 크기 비교
    comparator.get_model_sizes()

    # 성능 벤치마크 실행
    results = comparator.run_full_benchmark(
        test_image_path=None,  # 실제 이미지 경로 또는 None (더미 이미지)
        iterations=100
    )

    print("\n🎉 성능 비교 완료!")