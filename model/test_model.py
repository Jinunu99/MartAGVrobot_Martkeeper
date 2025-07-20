#!/usr/bin/env python3
"""
test_model.py
웹캠 최적화 모델 테스트 모듈
"""

import random
from pathlib import Path
from ultralytics import YOLO
import time

class WebcamModelTester:
    def __init__(self, config, model_path=None):
        self.config = config
        self.dataset_path = config.dataset_path
        self.enable_320 = config.enable_320
        self.model_path = model_path or self.find_best_model()
        
    def find_best_model(self):
        """최신 훈련된 모델 찾기"""
        possible_paths = [
            'webcam_detection/yolo11m_webcam_320/weights/best.pt',
            'webcam_detection/yolo11m_webcam_640/weights/best.pt',
            'webcam_detection/yolo11m_webcam/weights/best.pt',
            'runs/detect/train/weights/best.pt',
            'best.pt'
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                print(f"✅ 모델 발견: {path}")
                return path
        
        print("❌ 훈련된 모델을 찾을 수 없습니다")
        return None
    
    def load_model(self):
        """모델 로드"""
        if not self.model_path or not Path(self.model_path).exists():
            print(f"❌ 모델 파일이 없습니다: {self.model_path}")
            return None
        
        try:
            model = YOLO(self.model_path)
            print(f"📥 모델 로드 성공: {self.model_path}")
            return model
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            return None
    
    def get_test_images(self, num_samples=5):
        """테스트 이미지 선택"""
        # 테스트 이미지 폴더 찾기
        test_dirs = [
            self.dataset_path / "test" / "images",
            self.dataset_path / "valid" / "images",
            self.dataset_path / "val" / "images"
        ]
        
        test_images = []
        for test_dir in test_dirs:
            if test_dir.exists():
                images = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
                test_images.extend(images)
                break
        
        if not test_images:
            print("❌ 테스트 이미지를 찾을 수 없습니다")
            return []
        
        # 랜덤 샘플 선택
        sample_size = min(num_samples, len(test_images))
        selected = random.sample(test_images, sample_size)
        
        print(f"🖼️ 테스트 이미지: {sample_size}개 선택")
        return selected
    
    def test_single_resolution(self, model, test_images, resolution=640):
        """단일 해상도 테스트"""
        print(f"\n📐 {resolution} 해상도 테스트:")
        
        # 해상도별 설정
        if resolution == 320:
            conf_threshold = 0.08
            iou_threshold = 0.25
            max_det = 30
        else:
            conf_threshold = 0.15
            iou_threshold = 0.35
            max_det = 20
        
        total_detections = 0
        results_summary = []
        
        for i, img_file in enumerate(test_images, 1):
            try:
                start_time = time.time()
                
                results = model.predict(
                    source=str(img_file),
                    imgsz=resolution,
                    conf=conf_threshold,
                    iou=iou_threshold,
                    max_det=max_det,
                    save=True,
                    project='test_results',
                    name=f'{resolution}',
                    show_labels=True,
                    show_conf=True,
                    line_width=2,
                    exist_ok=True
                )
                
                inference_time = time.time() - start_time
                
                # 탐지 결과 분석
                if results[0].boxes is not None:
                    num_detections = len(results[0].boxes)
                    confidences = results[0].boxes.conf.cpu().numpy()
                    avg_confidence = confidences.mean() if len(confidences) > 0 else 0
                    
                    # 클래스별 탐지 수
                    classes = results[0].boxes.cls.cpu().numpy()
                    class_counts = {}
                    for cls in classes:
                        cls_name = self.config.classes[int(cls)]
                        class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                else:
                    num_detections = 0
                    avg_confidence = 0
                    class_counts = {}
                
                total_detections += num_detections
                
                result_info = {
                    'image': img_file.name,
                    'detections': num_detections,
                    'avg_confidence': avg_confidence,
                    'inference_time': inference_time,
                    'classes': class_counts
                }
                results_summary.append(result_info)
                
                print(f"  📷 {i:2d}. {img_file.name}: {num_detections}개 탐지 "
                      f"(평균 신뢰도: {avg_confidence:.3f}, 추론: {inference_time*1000:.1f}ms)")
                
                if class_counts:
                    class_str = ", ".join([f"{cls}({cnt})" for cls, cnt in class_counts.items()])
                    print(f"       🏷️ {class_str}")
                
            except Exception as e:
                print(f"  ⚠️ 테스트 오류 {img_file.name}: {e}")
                continue
        
        # 결과 요약
        avg_detections = total_detections / len(test_images) if test_images else 0
        avg_confidence = sum(r['avg_confidence'] for r in results_summary) / len(results_summary) if results_summary else 0
        avg_inference = sum(r['inference_time'] for r in results_summary) / len(results_summary) if results_summary else 0
        
        print(f"\n📊 {resolution} 해상도 요약:")
        print(f"  🎯 평균 탐지 수: {avg_detections:.1f}개")
        print(f"  💯 평균 신뢰도: {avg_confidence:.3f}")
        print(f"  ⚡ 평균 추론 시간: {avg_inference*1000:.1f}ms")
        print(f"  📁 결과 저장: test_results/{resolution}/")
        
        return results_summary
    
    def compare_resolutions(self, model, test_images):
        """해상도별 성능 비교"""
        print(f"\n🔍 해상도별 성능 비교")
        print("=" * 50)
        
        # 640 해상도 테스트
        results_640 = self.test_single_resolution(model, test_images, 640)
        
        if self.enable_320:
            # 320 해상도 테스트
            results_320 = self.test_single_resolution(model, test_images, 320)
            
            # 비교 분석
            print(f"\n⚖️ 비교 분석:")
            
            avg_detections_640 = sum(r['detections'] for r in results_640) / len(results_640) if results_640 else 0
            avg_detections_320 = sum(r['detections'] for r in results_320) / len(results_320) if results_320 else 0
            
            avg_confidence_640 = sum(r['avg_confidence'] for r in results_640) / len(results_640) if results_640 else 0
            avg_confidence_320 = sum(r['avg_confidence'] for r in results_320) / len(results_320) if results_320 else 0
            
            avg_inference_640 = sum(r['inference_time'] for r in results_640) / len(results_640) if results_640 else 0
            avg_inference_320 = sum(r['inference_time'] for r in results_320) / len(results_320) if results_320 else 0
            
            detection_ratio = (avg_detections_320 / avg_detections_640) * 100 if avg_detections_640 > 0 else 0
            confidence_ratio = (avg_confidence_320 / avg_confidence_640) * 100 if avg_confidence_640 > 0 else 0
            speed_ratio = (avg_inference_320 / avg_inference_640) * 100 if avg_inference_640 > 0 else 0
            
            print(f"  🎯 탐지 수: 320은 640의 {detection_ratio:.1f}%")
            print(f"  💯 신뢰도: 320은 640의 {confidence_ratio:.1f}%") 
            print(f"  ⚡ 속도: 320은 640의 {speed_ratio:.1f}% (낮을수록 빠름)")
            
            # 권장사항
            if detection_ratio >= 80 and confidence_ratio >= 85:
                print(f"🌟 320 해상도 권장: 성능 손실 최소, 속도 향상")
            elif detection_ratio >= 70:
                print(f"✅ 320 해상도 실용적: 약간의 성능 손실, 속도 향상")
            else:
                print(f"⚠️ 640 해상도 권장: 320에서 성능 손실 큼")
    
    def test_webcam_simulation(self, model):
        """웹캠 시뮬레이션 테스트"""
        print(f"\n🎥 웹캠 시뮬레이션 테스트")
        print("실제 웹캠을 연결하여 테스트하시겠습니까?")
        
        test_webcam = input("웹캠 테스트? (y/N): ").strip().lower()
        if test_webcam not in ['y', 'yes']:
            print("⏭️ 웹캠 테스트 건너뛰기")
            return
        
        try:
            print(f"🔄 웹캠 연결 중...")
            print(f"📱 해상도: {'320 + 640' if self.enable_320 else '640'}")
            print(f"💡 ESC 키를 눌러 종료하세요")
            
            if self.enable_320:
                print(f"\n📱 320 해상도 웹캠 테스트:")
                model.predict(
                    source=0,
                    imgsz=320,
                    conf=0.08,
                    iou=0.25,
                    show=True,
                    stream=True,
                    verbose=False
                )
            
            print(f"\n📐 640 해상도 웹캠 테스트:")
            model.predict(
                source=0,
                imgsz=640,
                conf=0.15,
                iou=0.35,
                show=True,
                stream=True,
                verbose=False
            )
            
        except Exception as e:
            print(f"⚠️ 웹캠 테스트 오류: {e}")
            print(f"💡 웹캠이 연결되어 있는지 확인하세요")
    
    def run_full_test(self, num_samples=5):
        """전체 테스트 실행"""
        print(f"🔍 웹캠 최적화 모델 테스트")
        print("=" * 50)
        
        # 모델 로드
        model = self.load_model()
        if not model:
            return False
        
        # 테스트 이미지 선택
        test_images = self.get_test_images(num_samples)
        if not test_images:
            return False
        
        print(f"\n📊 테스트 설정:")
        print(f"  🤖 모델: {self.model_path}")
        print(f"  🖼️ 테스트 이미지: {len(test_images)}개")
        print(f"  📱 320 지원: {self.enable_320}")
        
        start_time = time.time()
        
        # 해상도별 테스트
        self.compare_resolutions(model, test_images)
        
        # 웹캠 시뮬레이션 테스트
        self.test_webcam_simulation(model)
        
        end_time = time.time()
        test_time = end_time - start_time
        
        print(f"\n🎉 테스트 완료!")
        print(f"⏱️ 테스트 시간: {test_time:.1f}초")
        print(f"📁 결과 이미지: test_results/ 폴더")
        
        return True

def main():
    """독립 실행용"""
    from config import Config
    
    dataset_path = input("📂 데이터셋 경로: ").strip()
    if not dataset_path:
        dataset_path = "/workspace01/team06/jonghui/model/snack_data"
    
    enable_320 = input("📱 320 해상도 지원? (Y/n): ").strip().lower()
    enable_320_support = enable_320 in ['y', 'yes', '']
    
    model_path = input("🤖 모델 경로 (엔터시 자동 찾기): ").strip()
    
    config = Config(dataset_path, enable_320_support)
    if not config.yaml_path:
        print("❌ data.yaml을 찾을 수 없습니다")
        return
    
    config.print_info()
    
    num_samples = input("🖼️ 테스트 이미지 수 [5]: ").strip()
    try:
        num_samples = int(num_samples) if num_samples else 5
    except:
        num_samples = 5
    
    tester = WebcamModelTester(config, model_path if model_path else None)
    tester.run_full_test(num_samples)

if __name__ == "__main__":
    main()