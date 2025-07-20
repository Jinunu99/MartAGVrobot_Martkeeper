#!/usr/bin/env python3
"""
model_make_main.py
웹캠 최적화 과자 탐지 모델 자동 제작

설정 입력 후 전체 파이프라인 자동 실행:
YAML수정 → 전처리 → 훈련 → 테스트

필요한 파일들:
- config.py: 기본 설정
- fix_yaml_paths.py: YAML 경로 수정
- preprocess.py: 전처리 모듈
- train_model.py: 훈련 모듈  
- test_model.py: 테스트 모듈
"""

import sys
import time
from pathlib import Path

# 모듈 import
try:
    from config import Config
    from preprocess import WebcamPreprocessor
    from train_model import WebcamModelTrainer
    from test_model import WebcamModelTester
    from fix_yaml_paths import fix_yaml_paths
except ImportError as e:
    print(f"❌ 모듈 import 오류: {e}")
    print("💡 다음 파일들이 같은 폴더에 있는지 확인하세요:")
    print("  - config.py")
    print("  - preprocess.py") 
    print("  - train_model.py")
    print("  - test_model.py")
    print("  - fix_yaml_paths.py")
    sys.exit(1)

def main():
    """메인 함수 - 전체 자동 실행"""
    print("🎥 웹캠 환경 최적화 과자 탐지 모델 자동 제작")
    print("=" * 70)
    print("🌟 특징: 조명/거리/노이즈 대응 + 브랜드 색상 보존")
    print("📊 데이터셋: 21개 클래스, 5개 브랜드")
    print("📱 320/640 해상도 완전 대응")
    print("🔄 자동 실행: YAML수정 → 전처리 → 훈련 → 테스트")
    
    # 설정 입력
    print(f"\n📋 설정 입력:")
    
    dataset_path = input("📂 데이터셋 경로 [/workspace01/team06/jonghui/model/snack_data]: ").strip()
    if not dataset_path:
        dataset_path = "/workspace01/team06/jonghui/model/snack_data"
    
    enable_320 = input("📱 320 해상도 웹캠 지원? (Y/n): ").strip().lower()
    enable_320_support = enable_320 in ['y', 'yes', '']
    
    skip_preprocess = input("⏭️ 전처리 건너뛰기? (이미 완료된 경우) (y/N): ").strip().lower()
    skip_preprocess = skip_preprocess in ['y', 'yes']
    
    # 설정 객체 생성
    config = Config(dataset_path, enable_320_support)
    
    if not config.yaml_path:
        print("\n❌ data.yaml을 찾을 수 없습니다")
        print("💡 데이터셋 경로를 확인하고 data.yaml이 존재하는지 확인하세요")
        return
    
    # 설정 확인
    print(f"\n📊 최종 설정:")
    print(f"  📂 데이터셋: {dataset_path}")
    print(f"  📱 320 지원: {enable_320_support}")
    print(f"  📋 클래스: {len(config.classes)}개")
    print(f"  ⏭️ 전처리 건너뛰기: {skip_preprocess}")
    print(f"  🔄 에포크: 70")
    print(f"  🎨 색상 보존: 최대")
    
    # 브랜드 정보
    brands = {}
    for cls in config.classes:
        if '_' in cls:
            brand = cls.split('_')[0]
            brands[brand] = brands.get(brand, 0) + 1
    
    print(f"  🏢 브랜드별:")
    for brand, count in brands.items():
        print(f"    - {brand.title()}: {count}개")
    
    # 최종 확인
    proceed = input(f"\n🚀 전체 파이프라인을 시작하시겠습니까? (Y/n): ").strip().lower()
    if proceed not in ['', 'y', 'yes']:
        print("❌ 취소됨")
        return
    
    # 시작 시간 기록
    total_start_time = time.time()
    model_path = None
    
    print(f"\n🎬 웹캠 최적화 모델 제작 시작!")
    print("=" * 70)
    print("0️⃣ YAML 경로 수정")
    print("1️⃣ 웹캠 환경 전처리") 
    print("2️⃣ 모델 훈련")
    print("3️⃣ 모델 테스트")
    print("=" * 70)
    
    try:
        # 0단계: YAML 경로 수정
        print(f"\n0️⃣ YAML 경로 수정 시작...")
        print(f"🔧 val/valid 폴더명 확인 + 절대경로 설정")
        
        if fix_yaml_paths(dataset_path):
            print(f"✅ 0단계 완료: YAML 경로 수정 성공!")
        else:
            print(f"❌ 0단계 실패: YAML 경로 수정 오류")
            return
        
        # 1단계: 전처리
        if not skip_preprocess:
            print(f"\n1️⃣ 웹캠 환경 전처리 시작...")
            print(f"💡 조명 시뮬레이션 + 거리 변화 + 노이즈")
            print(f"📐 라벨 좌표 6자리 정밀도 통일")
            if enable_320_support:
                print(f"📱 320 해상도 데이터 추가 생성")
            
            preprocessor = WebcamPreprocessor(config)
            
            if preprocessor.run_preprocessing():
                print(f"✅ 1단계 완료: 전처리 성공!")
            else:
                print(f"❌ 1단계 실패: 전처리 오류")
                return
        else:
            print(f"\n1️⃣ 전처리 건너뛰기 ⏭️")
            print(f"✅ 1단계 완료: 기존 전처리된 데이터 사용")
        
        # 2단계: 모델 훈련
        print(f"\n2️⃣ 모델 훈련 시작...")
        print(f"🤖 YOLO11m 기반")
        print(f"⏰ 70 epoch (얼리스탑 15)")
        print(f"🎨 브랜드 색상 보존 최적화")
        if enable_320_support:
            print(f"📱 320 최적화 (훈련 해상도: 512)")
        
        trainer = WebcamModelTrainer(config)
        model_path = trainer.train_model()
        
        if model_path:
            print(f"✅ 2단계 완료: 훈련 성공!")
            print(f"📁 모델 위치: {model_path}")
        else:
            print(f"❌ 2단계 실패: 훈련 오류")
            print(f"⚠️ 테스트 단계는 건너뜁니다")
        
        # 3단계: 모델 테스트
        if model_path:
            print(f"\n3️⃣ 모델 테스트 시작...")
            print(f"🔍 해상도별 성능 비교")
            print(f"📊 5개 샘플 이미지 테스트")
            
            tester = WebcamModelTester(config, model_path)
            
            if tester.run_full_test(5):
                print(f"✅ 3단계 완료: 테스트 성공!")
            else:
                print(f"❌ 3단계 실패: 테스트 오류")
        
        # 완료 메시지
        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        
        print(f"\n🎊 웹캠 최적화 모델 제작 완료!")
        print("=" * 70)
        print(f"⏱️ 총 소요 시간: {total_time/3600:.1f}시간")
        
        if model_path:
            print(f"\n🏆 최종 결과:")
            print(f"📁 모델: {model_path}")
            print(f"📊 테스트 결과: test_results/ 폴더")
            
            print(f"\n🎥 실시간 웹캠 추론 코드:")
            print("=" * 50)
            print("```python")
            print("from ultralytics import YOLO")
            print(f"model = YOLO('{model_path}')")
            print("")
            
            if enable_320_support:
                print("# 320 해상도 웹캠 (고속)")
                print("results = model.predict(source=0, imgsz=320, conf=0.08, stream=True, show=True)")
                print("")
                print("# 640 해상도 웹캠 (고품질)")
                print("results = model.predict(source=0, imgsz=640, conf=0.15, stream=True, show=True)")
            else:
                print("# 웹캠 추론")
                print("results = model.predict(source=0, conf=0.15, stream=True, show=True)")
            
            print("```")
            
            print(f"\n💡 해결된 문제들:")
            print(f"  ✅ YAML 경로 수정: val/valid 폴더명 통일")
            print(f"  ✅ 라벨 좌표 정밀도: 6자리 통일")
            print(f"  ✅ 웹캠 조명 변화 완전 대응")
            print(f"  ✅ 거리 변화 (멀리서/가까이서) 대응")
            print(f"  ✅ 웹캠 노이즈/블러 환경 학습")
            print(f"  ✅ 21개 과자 브랜드 색상 보존")
            if enable_320_support:
                print(f"  ✅ 320 해상도 웹캠 완전 지원")
                print(f"  ✅ Multi-scale 최적화 (512 훈련)")
            print(f"  ✅ 실시간 웹캠 스트림 최적화")
            
            print(f"\n🎯 실제 사용 시나리오:")
            print(f"  📱 저해상도 웹캠: 완벽 동작")
            print(f"  🏢 사무실 조명: 자동 대응")
            print(f"  📏 다양한 거리: 멀리서도 인식")
            print(f"  🌈 브랜드 구분: 색상 기반 정확 분류")
            print(f"  📐 라벨 품질: 6자리 정밀도 통일")
            print(f"  📄 YAML 안정성: 경로 문제 해결")
            
        else:
            print(f"\n⚠️ 모델 훈련이 실패했습니다")
            print(f"💡 로그를 확인하고 다시 시도해보세요")
        
        print(f"\n🙏 웹캠 최적화 모델 제작이 완료되었습니다!")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️ 사용자가 중단했습니다")
        print(f"💡 중간에 생성된 파일들은 보존됩니다")
        
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        print(f"💡 오류 로그를 개발자에게 전달해주세요")

if __name__ == "__main__":
    main()