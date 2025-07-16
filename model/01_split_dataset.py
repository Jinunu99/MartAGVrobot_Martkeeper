import os
import shutil
import random
import yaml
from pathlib import Path


def create_split_data_yaml(dataset_path, class_names, output_path="split_data.yaml"):
    """
    분할된 데이터셋용 YAML 파일 생성 (기존 data.yaml과 구분)
    """
    
    # 절대 경로로 변환
    abs_dataset_path = os.path.abspath(dataset_path)
    
    # 경로 존재 확인
    train_path = os.path.join(abs_dataset_path, 'train', 'images')
    val_path = os.path.join(abs_dataset_path, 'val', 'images')
    test_path = os.path.join(abs_dataset_path, 'test', 'images')
    
    print(f"\n=== YAML 파일 생성 ===")
    print(f"데이터셋 루트: {abs_dataset_path}")
    print(f"훈련 이미지: {train_path} (존재: {os.path.exists(train_path)})")
    print(f"검증 이미지: {val_path} (존재: {os.path.exists(val_path)})")
    print(f"테스트 이미지: {test_path} (존재: {os.path.exists(test_path)})")

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

    print(f"✅ 분할 데이터용 YAML 생성 완료: {output_path}")
    print(f"클래스 수: {len(class_names)}")
    
    return output_path


def split_dataset(source_dir, output_dir, train_ratio=0.6, val_ratio=0.3, test_ratio=0.1):
    """
    YOLO 형식 데이터셋을 train/val/test로 분할
    
    snack_data_set 필요 URL : https://universe.roboflow.com/korea-nazarene-university/-d9kpq/dataset/3

    Args:
        source_dir: 원본 데이터 디렉토리 (images/, labels/ 폴더 포함)
        output_dir: 분할된 데이터를 저장할 디렉토리
        train_ratio: 훈련 데이터 비율 (기본값: 0.6)
        val_ratio: 검증 데이터 비율 (기본값: 0.3)
        test_ratio: 테스트 데이터 비율 (기본값: 0.1)
    """

    print("=== 데이터셋 분할 시작 ===")
    
    # 비율 검증
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "비율의 합이 1이 되어야 합니다"

    # 경로 설정 (전달받은 source_dir 사용)
    source_images = Path(source_dir) / "images"
    source_labels = Path(source_dir) / "labels"
    output_path = Path(output_dir)

    print(f"원본 이미지 경로: {source_images}")
    print(f"원본 라벨 경로: {source_labels}")
    print(f"출력 경로: {output_path}")

    # 경로 존재 확인
    if not source_images.exists():
        raise FileNotFoundError(f"이미지 디렉토리를 찾을 수 없습니다: {source_images}")
    if not source_labels.exists():
        raise FileNotFoundError(f"라벨 디렉토리를 찾을 수 없습니다: {source_labels}")

    # 출력 디렉토리 생성
    print("\n출력 디렉토리 생성 중...")
    for split in ['train', 'val', 'test']:
        (output_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (output_path / split / 'labels').mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {split} 폴더 생성 완료")

    # 이미지 파일 목록 가져오기
    print("\n이미지 파일 스캔 중...")
    image_files = list(source_images.glob("*.jpg")) + list(source_images.glob("*.png")) + list(source_images.glob("*.jpeg"))
    image_files = [f.stem for f in image_files]  # 확장자 제거

    # 이미지 파일 개수 확인
    if len(image_files) == 0:
        print(f"❌ 경고: {source_images} 에서 이미지 파일을 찾을 수 없습니다.")
        print("지원되는 형식: .jpg, .png, .jpeg")
        return [], [], []

    print(f"✅ 총 {len(image_files)}개 이미지 파일 발견")

    # 무작위 셔플
    random.seed(42)  # 재현 가능한 결과를 위한 시드 설정
    random.shuffle(image_files)

    # 분할 인덱스 계산
    n_total = len(image_files)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    # 데이터 분할
    train_files = image_files[:n_train]
    val_files = image_files[n_train:n_train + n_val]
    test_files = image_files[n_train + n_val:]

    print(f"\n=== 분할 계획 ===")
    print(f"훈련: {len(train_files)}개 ({len(train_files) / n_total * 100:.1f}%)")
    print(f"검증: {len(val_files)}개 ({len(val_files) / n_total * 100:.1f}%)")
    print(f"테스트: {len(test_files)}개 ({len(test_files) / n_total * 100:.1f}%)")

    # 파일 복사 함수
    def copy_files(file_list, split_name):
        copied_count = 0
        print(f"\n{split_name} 데이터 복사 중...")
        
        for i, file_stem in enumerate(file_list):
            if i % 100 == 0:  # 진행 상황 표시
                print(f"  진행: {i}/{len(file_list)} ({i/len(file_list)*100:.1f}%)")
            
            # 이미지 파일 복사
            image_copied = False
            for ext in ['.jpg', '.png', '.jpeg']:
                src_img = source_images / f"{file_stem}{ext}"
                if src_img.exists():
                    dst_img = output_path / split_name / 'images' / f"{file_stem}{ext}"
                    shutil.copy2(src_img, dst_img)
                    image_copied = True
                    break
            
            # 라벨 파일 복사 (선택사항)
            src_label = source_labels / f"{file_stem}.txt"
            if src_label.exists():
                dst_label = output_path / split_name / 'labels' / f"{file_stem}.txt"
                shutil.copy2(src_label, dst_label)
            
            if image_copied:
                copied_count += 1
        
        print(f"  ✅ {split_name} 완료: {copied_count}개 파일")
        return copied_count

    # 각 분할에 파일 복사
    train_copied = copy_files(train_files, 'train')
    val_copied = copy_files(val_files, 'val')
    test_copied = copy_files(test_files, 'test')

    # 결과 출력
    print(f"\n=== 데이터셋 분할 완료! ===")
    print(f"✅ Train: {len(train_files)}개 ({len(train_files) / n_total * 100:.1f}%) - 복사됨: {train_copied}")
    print(f"✅ Val: {len(val_files)}개 ({len(val_files) / n_total * 100:.1f}%) - 복사됨: {val_copied}")
    print(f"✅ Test: {len(test_files)}개 ({len(test_files) / n_total * 100:.1f}%) - 복사됨: {test_copied}")

    return train_files, val_files, test_files


def verify_split_result(output_dir):
    """분할 결과 검증"""
    
    print(f"\n=== 분할 결과 검증 ===")
    output_path = Path(output_dir)
    
    for split in ['train', 'val', 'test']:
        images_dir = output_path / split / 'images'
        labels_dir = output_path / split / 'labels'
        
        if images_dir.exists() and labels_dir.exists():
            image_count = len(list(images_dir.glob("*.jpg"))) + len(list(images_dir.glob("*.png")))
            label_count = len(list(labels_dir.glob("*.txt")))
            print(f"✅ {split}: 이미지 {image_count}개, 라벨 {label_count}개")
        else:
            print(f"❌ {split}: 폴더 누락")


if __name__ == "__main__":
    print("=" * 60)
    print("🍿 과자 데이터셋 분할 프로그램")
    print("=" * 60)
    
    # 경로 설정
    source_directory = "./snack_dataset/train"  # 원본 데이터셋 경로
    output_directory = "./split_snack_data/"    # 분할된 데이터셋 저장 경로
    
    print(f"소스 디렉토리: {source_directory}")
    print(f"출력 디렉토리: {output_directory}")
    
    # 경로 존재 확인
    if not os.path.exists(source_directory):
        print(f"❌ 소스 디렉토리를 찾을 수 없습니다: {source_directory}")
        exit(1)

    # 데이터셋 분할 실행
    try:
        train_files, val_files, test_files = split_dataset(
            source_dir=source_directory,
            output_dir=output_directory,
            train_ratio=0.85,
            val_ratio=0.1,
            test_ratio=0.05
        )
        
        # 분할 결과 검증
        verify_split_result(output_directory)
        
        # 클래스 이름 정의 (기존과 동일하게 유지)
        class_names = [
            'crown_BigPie_Strawberry', 'crown_ChocoHaim', 'crown_Concho', 'crown_Potto_Cheese_Tart',
            'haetae_Guun_Gamja', 'haetae_HoneyButterChip', 'haetae_Masdongsan', 'haetae_Osajjeu',
            'haetae_Oyeseu', 'lotte_kkokkalkon_gosohanmas', 'nongshim_Alsaeuchip', 'nongshim_Banana_Kick',
            'nongshim_ChipPotato_Original', 'nongshim_Ojingeojip', 'orion_Chocolate_Chip_Cookies',
            'orion_Diget_Choco', 'orion_Diget_tongmil', 'orion_Fresh_Berry', 'orion_Gosomi',
            'orion_Pocachip_Original', 'orion_chokchokhan_Chocochip'
        ]
        
        # 분할된 데이터용 YAML 생성
        yaml_path = create_split_data_yaml(output_directory, class_names, "split_data.yaml")
        
        print(f"\n🎉 모든 작업 완료!")
        print(f"📁 분할된 데이터: {output_directory}")
        print(f"📄 YAML 파일: split_data.yaml")
        print(f"📊 총 클래스: {len(class_names)}개")
        
        print(f"\n📋 다음 단계:")
        print(f"1. tree 명령으로 구조 확인")
        print(f"2. 02_make_model.py로 YOLO 모델 훈련")
        print(f"3. 03_model_CNN.py로 CNN 모델 훈련")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        exit(1)