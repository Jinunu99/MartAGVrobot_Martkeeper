import os
import yaml
from ultralytics import YOLO
import torch
from pathlib import Path


def train_improved_yolo11(data_yaml_path, model_size='n', epochs=100, imgsz=640):
    """
    개선된 YOLO11 모델 훈련 (배경 다양화 및 성능 중심)

    Args:
        data_yaml_path: 데이터 설정 파일 경로  
        model_size: 모델 크기 ('n', 's', 'm', 'l', 'x') - 성능을 위해 n부터 시작
        epochs: 훈련 에포크 수
        imgsz: 입력 이미지 크기
    """

    print("🚀 개선된 YOLO11 모델 훈련 시작... (배경 다양화 적용)")
    print(f"📱 모델 크기: YOLO11{model_size}")
    print(f"🔄 에포크: {epochs}")
    print(f"📐 이미지 크기: {imgsz}x{imgsz}")

    # 모델 로드 (사전 훈련된 COCO 모델을 기반으로 시작)
    print(f"📥 YOLO11{model_size} 사전 훈련 모델 로드 중...")
    model = YOLO(f'yolo11{model_size}.pt')

    # GPU 사용 가능 여부 확인
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"💻 훈련 디바이스: {device}")

    if device == 'cuda':
        print(f"🎮 GPU 정보: {torch.cuda.get_device_name()}")
        print(f"💾 GPU 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.1f}GB")
        # GPU 메모리 정리
        torch.cuda.empty_cache()

    # 배치 크기 GT 1030 최적화 (2GB VRAM)
    if model_size == 'n':
        batch_size = 8   # nano는 8로 제한 (GT 1030 고려)
    elif model_size == 's':
        batch_size = 4   # small은 4
    else:
        batch_size = 2   # medium 이상은 2
    
    print(f"📦 배치 크기: {batch_size}")

    # 모델 훈련
    print("\n" + "=" * 70)
    print("🎯 모델 훈련 시작! (배경 다양화 & 성능 최적화 설정)")
    print("=" * 70)

    results = model.train(
        data=data_yaml_path,
        epochs=epochs,
        imgsz=imgsz,
        device=device,
        batch=batch_size,
        patience=50,  # 배경 다양화로 인한 학습 안정성을 위해 patience 증가
        save=True,
        project='snack_detection',
        name=f'yolo11{model_size}_background_improved',
        exist_ok=True,
        
        # ========== 학습률 최적화 ==========
        lr0=0.008,           # 초기 학습률 약간 감소 (배경 다양화 고려)
        lrf=0.01,            # 최종 학습률
        momentum=0.937,      # 모멘텀
        weight_decay=0.0005, # 가중치 감소 조정
        warmup_epochs=5,     # 워밍업 에포크 증가 (배경 다양화로 인한 초기 불안정성 고려)
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        
        # ========== 배경 다양화를 위한 강화된 데이터 증강 ==========
        
        # 1. 색상 변화 증가 (흰색 배경 극복)
        hsv_h=0.03,          # 색상 변화 증가 (0.015 → 0.03)
        hsv_s=0.9,           # 채도 변화 증가 (0.7 → 0.9) - 배경 색상 다양화
        hsv_v=0.6,           # 명도 변화 증가 (0.4 → 0.6) - 조명 다양화
        
        # 2. 기하학적 변환 강화
        degrees=15.0,        # 회전 각도 증가 (10.0 → 15.0)
        translate=0.2,       # 이동 변환 증가 (0.1 → 0.2) - 배경 노출 다양화
        scale=0.8,           # 스케일 변화 증가 (0.5 → 0.8) - 배경 크기 다양화
        shear=3.0,           # 전단 변환 증가 (2.0 → 3.0)
        perspective=0.0002,  # 원근 변환 활성화 (배경 왜곡 효과)
        flipud=0.1,          # 상하 반전 활성화 (배경 패턴 다양화)
        fliplr=0.5,          # 좌우 반전 유지
        
        # 3. 고급 증강 기법 활성화 (배경 다양화 핵심)
        mosaic=1.0,          # 모자이크 유지 (다양한 배경 조합)
        mixup=0.2,           # 믹스업 활성화 (배경 혼합 효과)
        copy_paste=0.1,      # 복사-붙여넣기 활성화 (배경 다양화)
        
        # 4. 노이즈 및 블러 효과 (배경 복잡도 증가)
        # YOLOv8에서 직접 지원하지 않는 기능들은 제거
        
        # 5. 정규화 조정 (과적합 방지)
        dropout=0.1,         # 드롭아웃 활성화 (배경 과적합 방지)
        
        # 6. 모니터링 및 저장
        plots=True,          # 플롯 생성 활성화
        save_period=5,       # 5 에포크마다 체크포인트 저장 (배경 다양화 효과 모니터링)
        val=True,            # 검증 활성화
        verbose=True,        # 상세 로그
        
        # 7. 성능 최적화
        amp=True,            # Automatic Mixed Precision 사용
        fraction=1.0,        # 전체 데이터 사용
        
        # 8. 기타 설정
        rect=False,          # 직사각형 훈련 비활성화 (배경 다양화를 위해)
        cos_lr=True,         # 코사인 학습률 스케줄러
        close_mosaic=15,     # 마지막 15 에포크에서 모자이크 비활성화 (안정화)
        
        # 9. NMS 설정
        iou=0.65,            # IoU threshold 약간 감소 (배경 다양화로 인한 false positive 고려)
        
        # 10. 추가 설정
        single_cls=False,    # 다중 클래스 사용
        overlap_mask=True,   # 마스크 겹침 허용 (복잡한 배경 처리)
        mask_ratio=4,        # 마스크 다운샘플링 비율
        
        # 11. 학습 안정성 향상
        erasing=0.4,         # 랜덤 지우기 (배경 의존성 감소)
        crop_fraction=1.0,   # 전체 이미지 사용
    )

    print("\n" + "=" * 70)
    print("🎉 훈련 완료! (배경 다양화 적용)")
    print("=" * 70)

    # 모델 검증
    print("📊 모델 검증 중...")
    metrics = model.val()

    print(f"\n📈 최종 성능 결과:")
    print(f"  - mAP50: {metrics.box.map50:.4f} ({metrics.box.map50*100:.1f}%)")
    print(f"  - mAP50-95: {metrics.box.map:.4f} ({metrics.box.map*100:.1f}%)")
    print(f"  - Precision: {metrics.box.mp:.4f} ({metrics.box.mp*100:.1f}%)")
    print(f"  - Recall: {metrics.box.mr:.4f} ({metrics.box.mr*100:.1f}%)")

    # 성능 평가 (배경 다양화 고려)
    target_map50 = 0.25  # 배경 다양화로 인한 초기 성능 저하 고려하여 25%로 조정
    print(f"\n🎯 성능 평가 (배경 다양화 적용):")
    if metrics.box.map50 >= target_map50:
        print(f"✅ 목표 달성! mAP50 {metrics.box.map50:.3f} >= {target_map50}")
        print("🚀 배경 다양화 성공! 다양한 환경에서 테스트 가능!")
    elif metrics.box.map50 >= 0.15:
        print(f"⚠️  개선 필요: mAP50 {metrics.box.map50:.3f} (목표: {target_map50})")
        print("💡 배경 다양화 초기 단계 - 더 많은 에포크 필요")
    else:
        print(f"❌ 성능 부족: mAP50 {metrics.box.map50:.3f} < 0.15")
        print("🔧 데이터 품질 확인 또는 배경 다양화 정도 조정 필요")

    # 배경 다양화 효과 분석
    print(f"\n🎨 배경 다양화 효과:")
    print(f"  - 색상 변화: HSV 증강 강화 적용")
    print(f"  - 기하학적 변환: 회전, 이동, 스케일 증가")
    print(f"  - 고급 증강: 모자이크, 믹스업, 복사-붙여넣기 활성화")
    print(f"  - 정규화: 드롭아웃 0.1, 랜덤 지우기 0.4 적용")

    print(f"\n💾 저장된 모델 위치:")
    print(f"   📁 프로젝트: snack_detection/yolo11{model_size}_background_improved/")
    print(f"   🏆 Best: weights/best.pt")
    print(f"   📋 Last: weights/last.pt")
    print(f"   📊 Results: results.csv")
    print(f"   🖼️  이미지: train_batch*.jpg, val_batch*.jpg (5 에포크마다)")
    print(f"   📈 그래프: results.png, confusion_matrix.png")

    print(f"\n🔍 다음 단계 추천:")
    print(f"1. 훈련 이미지 확인: train_batch*.jpg에서 배경 다양화 확인")
    print(f"2. 다양한 배경에서 테스트 (흰색 외 배경)")
    print(f"3. 성능이 부족하면 더 많은 배경 데이터 수집")
    print(f"4. 실제 환경과 유사한 배경에서 추가 검증")

    return model, results

# 배경 다양화를 위한 추가 도구 함수
def analyze_background_diversity(image_folder):
    """
    이미지 폴더의 배경 다양성 분석
    """
    print("🔍 배경 다양성 분석 중...")
    # 실제 구현은 OpenCV 등을 사용하여 배경 색상 분포 분석
    print("💡 별도 스크립트로 배경 색상 히스토그램 분석을 추천합니다.")

def suggest_background_augmentation():
    """
    배경 다양화 방법 제안
    """
    print("\n🎨 배경 다양화 추가 방법:")
    print("1. 실제 환경 데이터 수집 (다양한 테이블, 선반 등)")
    print("2. 배경 교체 도구 사용 (remove.bg + 새 배경 합성)")
    print("3. 조명 조건 다양화 (자연광, 실내등, 형광등 등)")
    print("4. 텍스처 배경 추가 (나무, 천, 플라스틱 등)")
    print("5. 노이즈 및 그라데이션 배경 생성")

# 사용 예시
if __name__ == "__main__":
    print("=" * 80)
    print("🍿 과자 탐지 모델 훈련 시작! (배경 다양화 & 성능 최적화)")
    print("=" * 80)

    # 현재 작업 디렉토리 확인
    current_dir = os.getcwd()
    print(f"📂 현재 작업 디렉토리: {current_dir}")

    # 분할된 데이터셋 사용
    yaml_path = "snack_data_2/data.yaml"
    
    # YAML 파일 존재 확인
    if not os.path.exists(yaml_path):
        print(f"❌ {yaml_path} 파일을 찾을 수 없습니다!")
        print("01_split_dataset.py를 먼저 실행하세요.")
        exit(1)
    
    # YAML 파일 내용 확인
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        print(f"📋 데이터셋 정보:")
        # path 키가 있으면 출력, 없으면 생략
        if 'path' in config:
            print(f"   - 경로: {config['path']}")
        print(f"   - 클래스 수: {config['nc']}개")
        print(f"   - 훈련: {config['train']}")
        print(f"   - 검증: {config['val']}")
        print(f"   - 테스트: {config['test']}")

    # 배경 다양화 정보 출력
    print(f"\n🎨 배경 다양화 설정:")
    print(f"   - 색상 변화: 강화됨 (HSV 증강)")
    print(f"   - 기하학적 변환: 확대됨")
    print(f"   - 고급 증강: 모자이크, 믹스업, 복사-붙여넣기 활성화")
    print(f"   - 정규화: 드롭아웃 및 랜덤 지우기 적용")

    # 모델 크기 선택
    print(f"\n🤖 모델 크기 선택:")
    print(f"1. YOLO11n (nano) - 빠름, 가벼움 (추천)")
    print(f"2. YOLO11s (small) - 균형")
    print(f"3. YOLO11m (medium) - 정확함, 무거움")
    
    choice = input("선택하세요 (1-3, 기본값: 1): ").strip()
    
    if choice == "2":
        model_size = 's'
        epochs = 120  # 배경 다양화로 인해 더 많은 에포크 필요
        print("✅ YOLO11s 선택")
    elif choice == "3":
        model_size = 'm'  
        epochs = 100  # 배경 다양화로 인해 더 많은 에포크 필요
        print("✅ YOLO11m 선택")
    else:  # 기본값 또는 "1"
        model_size = 'n'
        epochs = 10  # 배경 다양화로 인해 더 많은 에포크 필요
        print("✅ YOLO11n 선택 (추천)")

    print(f"🔄 에포크: {epochs} (배경 다양화 고려)")
    
    # 훈련 시간 예상 (GT 1030 기준, 배경 다양화로 인한 시간 증가)
    if model_size == 'n':
        time_estimate = "25-40분"
    elif model_size == 's':
        time_estimate = "40-60분"
    else:
        time_estimate = "60-90분"
    
    print(f"\n⚠️  GT 1030 기준 훈련 시간 예상: {time_estimate}")
    print(f"💡 배경 다양화로 인해 기존보다 시간이 더 소요됩니다.")
    print(f"🎨 하지만 다양한 환경에서 더 견고한 성능을 보일 것입니다!")
    
    # 배경 다양화 방법 제안
    suggest_background_augmentation()
    
    confirm = input("\n배경 다양화 훈련을 시작하시겠습니까? (y/N): ").strip().lower()
    
    if confirm not in ['y', 'yes']:
        print("❌ 훈련이 취소되었습니다.")
        exit(0)

    try:
        # 모델 훈련 실행
        model, results = train_improved_yolo11(
            data_yaml_path=yaml_path,
            model_size=model_size,
            epochs=epochs,
            imgsz=640
        )

        print(f"\n🎊 배경 다양화 훈련 완료!")
        print(f"📁 결과 확인: snack_detection/yolo11{model_size}_background_improved/ 폴더")
        print(f"🏆 최고 모델: weights/best.pt")
        
        print(f"\n📋 다음 단계:")
        print(f"1. train_batch*.jpg에서 배경 다양화 확인")
        print(f"2. 다양한 배경에서 04_1_yolomodel_test.py로 테스트")
        print(f"3. 흰색 외 배경에서 성능 검증")
        print(f"4. 필요시 더 많은 배경 데이터 수집")
        
        # 배경 다양화 효과 분석 권장
        print(f"\n🔍 배경 다양화 효과 분석:")
        print(f"- 훈련 이미지에서 다양한 색상과 패턴 확인")
        print(f"- 실제 환경(색상 있는 배경)에서 테스트 필수")
        print(f"- 성능 저하 시 배경 데이터 추가 수집 권장")
        
    except Exception as e:
        print(f"❌ 훈련 중 오류 발생: {e}")
        print("💡 GPU 메모리 부족 시 모델 크기를 줄이거나 배치 크기를 조정하세요.")
        print("🎨 배경 다양화로 인한 메모리 사용량 증가를 고려하세요.")
        exit(1)