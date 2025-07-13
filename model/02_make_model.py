import os
import yaml
from ultralytics import YOLO
import torch
from pathlib import Path


def create_data_yaml(dataset_path, class_names, output_path="data.yaml"):
    """
    YOLOv8용 데이터 설정 파일 생성

    Args:
        dataset_path: 분할된 데이터셋 경로
        class_names: 클래스 이름 리스트
        output_path: 출력 yaml 파일 경로
    """
    
    # 절대 경로로 변환
    abs_dataset_path = os.path.abspath(dataset_path)
    
    # 경로 존재 확인
    train_path = os.path.join(abs_dataset_path, 'train', 'images')
    val_path = os.path.join(abs_dataset_path, 'val', 'images')
    test_path = os.path.join(abs_dataset_path, 'test', 'images')
    
    print(f" 경로 확인:")
    print(f"  - 데이터셋 루트: {abs_dataset_path}")
    print(f"  - 훈련 이미지: {train_path} (존재: {os.path.exists(train_path)})")
    print(f"  - 검증 이미지: {val_path} (존재: {os.path.exists(val_path)})")
    print(f"  - 테스트 이미지: {test_path} (존재: {os.path.exists(test_path)})")

    data_config = {
        'path': abs_dataset_path,  # 절대 경로 사용
        'train': 'train/images',   # path 기준 상대 경로
        'val': 'val/images',       # path 기준 상대 경로
        'test': 'test/images',     # path 기준 상대 경로
        'nc': len(class_names),    # 클래스 수
        'names': class_names       # 클래스 이름
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data_config, f, default_flow_style=False, allow_unicode=True)

    print(f" 데이터 설정 파일 생성 완료: {output_path}")
    print(f" 클래스 수: {len(class_names)}")
    print(f" 클래스 목록: {class_names}")
    
    # 생성된 yaml 파일 내용 확인
    with open(output_path, 'r', encoding='utf-8') as f:
        yaml_content = f.read()
        print(f" 생성된 data.yaml 내용:")
        print(yaml_content)
    
    return output_path

""" epoch , image size 알맞게 조절 """
# 초기 epochs = 100
def train_custom_yolov8(data_yaml_path, model_size='s', epochs=40, imgsz=640):
    """
    YOLOv8 커스텀 모델 훈련

    Args:
        data_yaml_path: 데이터 설정 파일 경로
        model_size: 모델 크기 ('n', 's', 'm', 'l', 'x') - YOLOv8s 사용
        epochs: 훈련 에포크 수
        imgsz: 입력 이미지 크기
    """

    print(" YOLOv8 커스텀 모델 훈련 시작...")
    print(f" 모델 크기: YOLOv8{model_size}")
    print(f" 에포크: {epochs}")
    print(f" 이미지 크기: {imgsz}x{imgsz}")

    # 모델 로드 (사전 훈련된 COCO 모델을 기반으로 시작)
    print(f" YOLOv8{model_size} 사전 훈련 모델 로드 중...")
    model = YOLO(f'yolov8{model_size}.pt')

    # GPU 사용 가능 여부 확인
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f" 훈련 디바이스: {device}")

    if device == 'cuda':
        print(f" GPU 정보: {torch.cuda.get_device_name()}")
        print(f" GPU 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.1f}GB")

    # 모델 훈련
    print("\n" + "=" * 50)
    print(" 모델 훈련 시작!")
    print("=" * 50)

    results = model.train(
        data=data_yaml_path,
        epochs=epochs,
        imgsz=imgsz,
        device=device,
        batch=4,  # 배치 크기 (메모리에 따라 조정) # 기존 16
        patience=50,  # 조기 종료 patience
        save=True,
        project='snack_detection',
        name='yolov8s_custom',
        # 데이터 증강 설정 (overfitting 방지)
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
        # 학습률 및 최적화 설정
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        # 모니터링
        plots=True,
        save_period=3,  # 3 에포크마다 체크포인트 저장
    )

    print("\n" + "=" * 50)
    print(" 훈련 완료!")
    print("=" * 50)

    # 모델 검증
    print(" 모델 검증 중...")
    metrics = model.val()

    print(f" 검증 결과:")
    print(f"  - mAP50: {metrics.box.map50:.4f}")
    print(f"  - mAP50-95: {metrics.box.map:.4f}")
    print(f"  - Precision: {metrics.box.mp:.4f}")
    print(f"  - Recall: {metrics.box.mr:.4f}")

    return model, results

# 사용 예시
if __name__ == "__main__":
    print(" 스낵 탐지 모델 훈련 시작!")
    print("=" * 50)

    # 1. 데이터 설정 파일 생성
    dataset_path = "./split_snack_data"  # 분할된 데이터셋 경로

    # 현재 작업 디렉토리 확인
    print(f" 현재 작업 디렉토리: {os.getcwd()}")
    print(f" 데이터셋 경로 확인: {os.path.exists(dataset_path)}")

    # 클래스 이름 정의 (실제 snack 종류)
    class_names = ['crown_BigPie_Strawberry',
                   'crown_ChocoHaim', 'crown_Concho', 'crown_Potto_Cheese_Tart',
                   'haetae_Guun_Gamja', 'haetae_HoneyButterChip', 'haetae_Masdongsan',
                   'haetae_Osajjeu', 'haetae_Oyeseu', 'lotte_kkokkalkon_gosohanmas',
                   'nongshim_Alsaeuchip', 'nongshim_Banana_Kick', 'nongshim_ChipPotato_Original',
                   'nongshim_Ojingeojip', 'orion_Chocolate_Chip_Cookies', 'orion_Diget_Choco',
                   'orion_Diget_tongmil', 'orion_Fresh_Berry', 'orion_Gosomi',
                   'orion_Pocachip_Original', 'orion_chokchokhan_Chocochip'
    ]

    data_yaml = create_data_yaml(dataset_path, class_names)

    # 2. 모델 훈련
    model, results = train_custom_yolov8(
        data_yaml_path=data_yaml,
        model_size='s',  # YOLOv8s 사용
        epochs=40, # 기존 100
        imgsz=640   # 기존 640
    )

    print("\n 모델 훈련 완료!")
    print(" 결과 확인: snack_detection/yolov8s_custom/ 폴더를 확인")
    print(" best.pt 파일이 최종 훈련된 모델")