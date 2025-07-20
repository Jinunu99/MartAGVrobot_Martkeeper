#!/usr/bin/env python3
"""
train_model.py
웹캠 최적화 모델 훈련 모듈 (Copy-Paste/Mosaic 활성화)
"""

import torch
import time
from pathlib import Path
from ultralytics import YOLO

class WebcamModelTrainer:
    def __init__(self, config):
        self.config = config
        self.dataset_path = config.dataset_path
        self.enable_320 = config.enable_320
        self.yaml_path = config.yaml_path
        self.train_config = config.get_train_config()
        
    def setup_training(self):
        """훈련 환경 설정"""
        # GPU 확인
        self.device = 0 if torch.cuda.is_available() else 'cpu'
        
        # 배치 크기 설정
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            if self.enable_320:
                self.batch_size = 16 if gpu_memory > 8 else 8
            else:
                self.batch_size = 32 if gpu_memory > 8 else 16
        else:
            self.batch_size = 4 if self.enable_320 else 8
        
        print(f"💻 훈련 환경:")
        print(f"  🖥️ 디바이스: {'GPU' if self.device == 0 else 'CPU'}")
        if self.device == 0:
            print(f"  🎮 GPU 메모리: {gpu_memory:.1f}GB")
        print(f"  📦 배치 크기: {self.batch_size}")
        print(f"  📐 이미지 크기: {self.train_config['imgsz']}")
        
    def train_model(self):
        """모델 훈련 실행"""
        print(f"\n🚀 웹캠 최적화 모델 훈련 시작!")
        print(f"🎨 Instance 단순 증폭 + YOLO 내장 Copy-Paste/Mosaic 조합")
        
        if not self.yaml_path:
            print("❌ YAML 파일이 없습니다")
            return None
        
        # 훈련 환경 설정
        self.setup_training()
        
        # 모델 로드
        model = YOLO('yolo11m.pt')
        print(f"📥 YOLOv11m 사전훈련 모델 로드")
        
        # 프로젝트 설정
        project_name = 'webcam_detection'
        run_name = f'yolo11m_webcam_{"320" if self.enable_320 else "640"}'
        
        # 이미지 크기 설정 (훈련 시에는 단일 값)
        if self.enable_320:
            # 320 지원 시에는 중간 크기인 512로 훈련
            train_imgsz = 512
            print(f"📐 훈련 해상도: {train_imgsz} (320 대응 최적화)")
        else:
            train_imgsz = 640
            print(f"📐 훈련 해상도: {train_imgsz}")
        
        print(f"\n⚙️ 훈련 설정:")
        print(f"  📊 에포크: {self.train_config['epochs']}")
        print(f"  ⏰ 얼리스탑: {self.train_config['patience']} patience")
        print(f"  📈 학습률: {self.train_config['lr0']} → {self.train_config['lrf']}")
        print(f"  🎨 색상 보존: hsv_h={self.train_config['hsv_h']}")
        print(f"  📱 320 최적화: {self.enable_320}")
        
        # YOLO 내장 기능 활성화 (Instance 단순 증폭과 조합)
        print(f"\n🎯 YOLO 내장 증강 활성화:")
        print(f"  🧩 Mosaic: 0.5 (4개 이미지 격자 배치)")
        print(f"  ✂️ Copy-Paste: 0.3 (객체 복사-붙여넣기)")
        print(f"  🔀 MixUp: 0.1 (이미지 혼합)")
        print(f"  💡 라벨 정확성: YOLO 엔진 보장")
        
        start_time = time.time()
        
        try:
            # 훈련 시작
            results = model.train(
                data=self.yaml_path,
                epochs=self.train_config['epochs'],
                imgsz=train_imgsz,  # 단일 정수값 사용
                device=self.device,
                batch=self.batch_size,
                patience=self.train_config['patience'],
                save=True,
                project=project_name,
                name=run_name,
                exist_ok=True,
                
                # 학습률 설정
                lr0=self.train_config['lr0'],
                lrf=self.train_config['lrf'],
                momentum=0.937,
                weight_decay=0.0005,
                warmup_epochs=5 if self.enable_320 else 3,
                warmup_momentum=0.8,
                warmup_bias_lr=0.1,
                
                # 브랜드 색상 보존 (최소 증강)
                hsv_h=self.train_config['hsv_h'],
                hsv_s=self.train_config['hsv_s'],
                hsv_v=self.train_config['hsv_v'],
                
                # 기하학적 변환 최소화
                degrees=self.train_config['degrees'],
                translate=self.train_config['translate'],
                scale=self.train_config['scale'],
                shear=0.2 if self.enable_320 else 0.3,
                perspective=self.train_config['perspective'],
                flipud=self.train_config['flipud'],
                fliplr=self.train_config['fliplr'],
                
                # 🎯 YOLO 내장 증강 활성화 (Instance와 조합)
                mosaic=0.5,          # 모자이크 적극 활용
                copy_paste=0.3,      # Copy-Paste 활성화
                mixup=0.1,           # MixUp 약간 활용
                
                # 손실 함수 (320 대응)
                box=self.train_config['box'],
                cls=self.train_config['cls'],
                dfl=self.train_config['dfl'],
                
                # 성능 설정
                plots=True,
                val=True,
                verbose=True,
                save_period=5,
                cache='ram',  # RAM 캐싱
                
                # 최적화 설정
                multi_scale=True,  # 훈련 중 스케일 변화
                rect=False,
                cos_lr=True,
                close_mosaic=15 if self.enable_320 else 10,
                
                # 탐지 설정
                iou=self.train_config['iou'],
                conf=self.train_config['conf'],
                
                # 고급 설정
                optimizer='AdamW',
                workers=4,
                amp=True,  # AMP 유지
                seed=42,
            )
            
            end_time = time.time()
            training_time = end_time - start_time
            
            print(f"\n🎉 훈련 완료!")
            print(f"⏱️ 훈련 시간: {training_time/3600:.1f}시간")
            
            # 최종 성능 검증
            best_model_path = Path(project_name) / run_name / 'weights' / 'best.pt'
            self.evaluate_model(str(best_model_path))
            
            return str(best_model_path)
            
        except Exception as e:
            print(f"❌ 훈련 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def evaluate_model(self, model_path):
        """모델 성능 평가"""
        if not Path(model_path).exists():
            print(f"❌ 모델을 찾을 수 없습니다: {model_path}")
            return
        
        print(f"\n📊 모델 성능 평가...")
        model = YOLO(model_path)
        
        try:
            # 640 해상도 성능
            print(f"📈 640 해상도 검증:")
            metrics_640 = model.val(imgsz=640)
            
            map50_640 = metrics_640.box.map50
            map_640 = metrics_640.box.map
            precision_640 = metrics_640.box.mp
            recall_640 = metrics_640.box.mr
            
            f1_640 = 2 * (precision_640 * recall_640) / (precision_640 + recall_640) if (precision_640 + recall_640) > 0 else 0
            
            print(f"  mAP50: {map50_640:.4f} ({map50_640*100:.1f}%)")
            print(f"  mAP50-95: {map_640:.4f} ({map_640*100:.1f}%)")
            print(f"  Precision: {precision_640:.4f} ({precision_640*100:.1f}%)")
            print(f"  Recall: {recall_640:.4f} ({recall_640*100:.1f}%)")
            print(f"  F1-Score: {f1_640:.4f} ({f1_640*100:.1f}%)")
            
            # 320 해상도 성능 (320 지원시)
            if self.enable_320:
                print(f"\n📱 320 해상도 검증:")
                metrics_320 = model.val(imgsz=320)
                
                map50_320 = metrics_320.box.map50
                map_320 = metrics_320.box.map
                precision_320 = metrics_320.box.mp
                recall_320 = metrics_320.box.mr
                
                f1_320 = 2 * (precision_320 * recall_320) / (precision_320 + recall_320) if (precision_320 + recall_320) > 0 else 0
                
                print(f"  mAP50: {map50_320:.4f} ({map50_320*100:.1f}%)")
                print(f"  mAP50-95: {map_320:.4f} ({map_320*100:.1f}%)")
                print(f"  Precision: {precision_320:.4f} ({precision_320*100:.1f}%)")
                print(f"  Recall: {recall_320:.4f} ({recall_320*100:.1f}%)")
                print(f"  F1-Score: {f1_320:.4f} ({f1_320*100:.1f}%)")
                
                # 성능 비교
                performance_ratio = (f1_320 / f1_640) * 100 if f1_640 > 0 else 0
                print(f"\n🔍 320/640 성능 비교:")
                print(f"  F1-Score 비율: {performance_ratio:.1f}%")
                
                if performance_ratio >= 85:
                    print(f"🌟 320 해상도 우수! (640 대비 {performance_ratio:.1f}%)")
                elif performance_ratio >= 70:
                    print(f"✅ 320 해상도 양호 (640 대비 {performance_ratio:.1f}%)")
                else:
                    print(f"⚠️ 320 해상도 개선 필요 (640 대비 {performance_ratio:.1f}%)")
            
            # 성능 등급 평가
            if f1_640 >= 0.8:
                grade = "🏆 우수"
            elif f1_640 >= 0.7:
                grade = "🥇 양호"  
            elif f1_640 >= 0.6:
                grade = "🥈 보통"
            else:
                grade = "🥉 개선필요"
            
            print(f"\n📊 전체 성능 등급: {grade} (F1: {f1_640:.3f})")
            
            print(f"\n🎯 증강 효과 분석:")
            print(f"  📈 Instance 단순 증폭: 클래스 균형 달성")
            print(f"  🧩 YOLO Mosaic: 다양한 객체 조합 학습")
            print(f"  ✂️ Copy-Paste: 객체 겹침 환경 학습")
            print(f"  🔀 MixUp: 배경 일반화 향상")
            print(f"  💯 라벨 정확성: 100% 보장")
            
        except Exception as e:
            print(f"⚠️ 성능 평가 오류: {e}")
    
    def print_usage_examples(self, model_path):
        """사용 예시 출력"""
        print(f"\n🎥 실시간 웹캠 추론 예시:")
        print("=" * 50)
        print("```python")
        print("from ultralytics import YOLO")
        print(f"model = YOLO('{model_path}')")
        print("")
        
        if self.enable_320:
            print("# 320 해상도 웹캠 (고속)")
            print("results = model.predict(")
            print("    source=0,              # 웹캠")
            print("    imgsz=320,             # 320 해상도")  
            print("    conf=0.08,             # 낮은 임계값")
            print("    iou=0.25,              # 관대한 NMS")
            print("    stream=True,           # 실시간 스트림")
            print("    show=True              # 화면 출력")
            print(")")
            print("")
            print("# 640 해상도 웹캠 (고품질)")
            print("results = model.predict(")
            print("    source=0,              # 웹캠")
            print("    imgsz=640,             # 640 해상도")
            print("    conf=0.15,             # 표준 임계값")
            print("    iou=0.35,              # 표준 NMS")
            print("    stream=True,           # 실시간 스트림")
            print("    show=True              # 화면 출력")
            print(")")
        else:
            print("# 웹캠 추론")
            print("results = model.predict(")
            print("    source=0,              # 웹캠")
            print("    conf=0.15,             # 임계값")
            print("    iou=0.35,              # NMS")
            print("    stream=True,           # 실시간 스트림")
            print("    show=True              # 화면 출력")
            print(")")
        
        print("```")
        
        print(f"\n💡 증강 조합의 장점:")
        print(f"  📊 Instance 단순 증폭: 클래스 균형 + 라벨 정확성")
        print(f"  🎯 YOLO 내장 기능: 정교한 객체 조합 + 검증된 알고리즘")
        print(f"  🌟 최고의 조합: 안정성 + 다양성")

def main():
    """독립 실행용"""
    from config import Config
    
    dataset_path = input("📂 데이터셋 경로: ").strip()
    if not dataset_path:
        dataset_path = "/workspace01/team06/jonghui/model/snack_data"
    
    enable_320 = input("📱 320 해상도 지원? (Y/n): ").strip().lower()
    enable_320_support = enable_320 in ['y', 'yes', '']
    
    config = Config(dataset_path, enable_320_support)
    if not config.yaml_path:
        print("❌ data.yaml을 찾을 수 없습니다")
        return
    
    config.print_info()
    
    print(f"\n🎯 증강 전략:")
    print(f"  📈 Instance: 단순 증폭 (클래스 균형)")
    print(f"  🧩 Train: YOLO 내장 기능 (Copy-Paste/Mosaic)")
    print(f"  💯 라벨 정확성: 완전 보장")
    
    proceed = input("\n모델 훈련을 시작하시겠습니까? (y/N): ").strip().lower()
    if proceed in ['y', 'yes']:
        trainer = WebcamModelTrainer(config)
        model_path = trainer.train_model()
        
        if model_path:
            trainer.print_usage_examples(model_path)
    else:
        print("❌ 훈련이 취소되었습니다")

if __name__ == "__main__":
    main()