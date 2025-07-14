#!/usr/bin/env python3
"""
통합 모델 성능 비교 도구
속도, 정확도, 크기를 종합적으로 비교
"""

import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# 로컬 모듈 임포트 (위에서 만든 클래스들)
from performance_comparison import ModelPerformanceComparator
from accuracy_comparison import AccuracyComparator


class CompleteModelComparison:
    """통합 모델 성능 비교"""

    def __init__(self, pytorch_path, fp16_path, int8_path, data_yaml="data.yaml"):
        """
        Args:
            pytorch_path (str): PyTorch 모델 경로
            fp16_path (str): OpenVINO FP16 모델 경로
            int8_path (str): OpenVINO INT8 모델 경로
            data_yaml (str): 데이터 설정 파일
        """
        self.pytorch_path = pytorch_path
        self.fp16_path = fp16_path
        self.int8_path = int8_path
        self.data_yaml = data_yaml

        print("🔄 통합 성능 비교기 초기화")

        # 비교기들 초기화
        self.perf_comparator = ModelPerformanceComparator(
            pytorch_path, fp16_path, int8_path
        )
        self.acc_comparator = AccuracyComparator(data_yaml)

        self.comparison_results = {}

    def run_complete_comparison(self, speed_iterations=100):
        """전체 비교 실행"""
        print("\n🚀 통합 성능 비교 시작!")
        print("=" * 80)

        # 1. 모델 크기 비교
        print("1️⃣ 모델 크기 분석...")
        size_results = self.perf_comparator.get_model_sizes()

        # 2. 추론 속도 비교
        print("\n2️⃣ 추론 속도 벤치마크...")
        speed_results = self.perf_comparator.run_full_benchmark(iterations=speed_iterations)

        # 3. 정확도 비교
        print("\n3️⃣ 정확도 평가...")
        accuracy_results = self.acc_comparator.compare_all_models(
            pytorch_path=self.pytorch_path,
            fp16_path=self.fp16_path,
            int8_path=self.int8_path
        )

        # 4. 종합 결과 생성
        self.generate_summary_report(size_results, speed_results, accuracy_results)

        return {
            'size': size_results,
            'speed': speed_results,
            'accuracy': accuracy_results
        }

    def generate_summary_report(self, size_results, speed_results, accuracy_results):
        """종합 리포트 생성"""
        print("\n📋 종합 성능 리포트")
        print("=" * 80)

        # 데이터 정리
        summary_data = []

        model_mapping = {
            'PyTorch': 'pytorch',
            'OpenVINO FP16': 'fp16',
            'OpenVINO INT8': 'int8'
        }

        for display_name, key in model_mapping.items():
            row = {'모델': display_name}

            # 크기 정보
            if display_name in size_results:
                row['크기 (MB)'] = f"{size_results[display_name]:.1f}"
            else:
                row['크기 (MB)'] = "N/A"

            # 속도 정보
            speed_info = next(
                (r for r in speed_results if r['model'].lower().replace(' ', '_').replace('openvino_', '') == key),
                None)
            if speed_info:
                row['추론시간 (ms)'] = f"{speed_info['avg_time'] * 1000:.1f}"
                row['FPS'] = f"{speed_info['fps']:.1f}"
            else:
                row['추론시간 (ms)'] = "N/A"
                row['FPS'] = "N/A"

            # 정확도 정보
            if key in accuracy_results:
                acc_info = accuracy_results[key]
                row['mAP@0.5'] = f"{acc_info['map50']:.4f}"
                row['mAP@0.5:0.95'] = f"{