""" 01_split.py """
import os
import shutil
import yaml
import random
from collections import defaultdict, Counter
from sklearn.model_selection import train_test_split
import numpy as np

def read_label_file(label_path):
    """라벨 파일에서 클래스 정보를 읽어옴"""
    classes = []
    if os.path.exists(label_path):
        with open(label_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    class_id = int(line.split()[0])
                    classes.append(class_id)
    return classes

def analyze_dataset(images_dir, labels_dir):
    """데이터셋의 클래스 분포를 분석"""
    class_counts = Counter()
    file_class_mapping = {}
    
    # 이미지 파일 목록 가져오기
    image_files = [f for f in os.listdir(images_dir) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    
    print(f"총 이미지 파일 수: {len(image_files)}")
    
    for img_file in image_files:
        # 라벨 파일명 생성 (확장자를 .txt로 변경)
        base_name = os.path.splitext(img_file)[0]
        label_file = base_name + '.txt'
        label_path = os.path.join(labels_dir, label_file)
        
        # 라벨 파일에서 클래스 정보 읽기
        classes = read_label_file(label_path)
        
        if classes:
            # 해당 이미지의 주요 클래스 (첫 번째 클래스 사용)
            main_class = classes[0]
            file_class_mapping[img_file] = main_class
            class_counts[main_class] += 1
        else:
            print(f"Warning: 라벨 파일이 없거나 비어있음: {label_file}")
    
    return file_class_mapping, class_counts

def create_stratified_split(file_class_mapping, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
    """클래스별로 균등하게 분할"""
    # 클래스별로 파일들을 그룹화
    class_files = defaultdict(list)
    for file_name, class_id in file_class_mapping.items():
        class_files[class_id].append(file_name)
    
    train_files = []
    val_files = []
    test_files = []
    
    print("\n클래스별 분할 현황:")
    print("-" * 60)
    
    for class_id, files in class_files.items():
        files = sorted(files)  # 일관된 결과를 위해 정렬
        n_files = len(files)
        
        # 각 세트별 파일 수 계산
        n_train = max(1, int(n_files * train_ratio))
        n_val = max(1, int(n_files * val_ratio)) if n_files > 2 else 0
        n_test = n_files - n_train - n_val
        
        # 파일이 너무 적은 경우 조정
        if n_test < 0:
            n_test = 0
            n_val = n_files - n_train
        
        # 랜덤 시드 설정으로 재현 가능한 분할
        random.seed(42)
        random.shuffle(files)
        
        # 분할 수행
        train_split = files[:n_train]
        val_split = files[n_train:n_train+n_val]
        test_split = files[n_train+n_val:]
        
        train_files.extend(train_split)
        val_files.extend(val_split)
        test_files.extend(test_split)
        
        print(f"클래스 {class_id:2d}: 총 {n_files:3d}개 -> train: {len(train_split):3d}, val: {len(val_split):3d}, test: {len(test_split):3d}")
    
    return train_files, val_files, test_files

def copy_files(file_list, source_images_dir, source_labels_dir, dest_images_dir, dest_labels_dir):
    """파일들을 목적지 디렉토리로 복사"""
    os.makedirs(dest_images_dir, exist_ok=True)
    os.makedirs(dest_labels_dir, exist_ok=True)
    
    copied_count = 0
    for img_file in file_list:
        # 이미지 파일 복사
        src_img = os.path.join(source_images_dir, img_file)
        dst_img = os.path.join(dest_images_dir, img_file)
        
        if os.path.exists(src_img):
            shutil.copy2(src_img, dst_img)
            
            # 라벨 파일 복사
            base_name = os.path.splitext(img_file)[0]
            label_file = base_name + '.txt'
            src_label = os.path.join(source_labels_dir, label_file)
            dst_label = os.path.join(dest_labels_dir, label_file)
            
            if os.path.exists(src_label):
                shutil.copy2(src_label, dst_label)
            
            copied_count += 1
    
    return copied_count

def update_yaml_file(yaml_path, base_dir):
    """data.yaml 파일을 업데이트"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # 경로 업데이트
    data['train'] = os.path.join(base_dir, 'train', 'images').replace('\\', '/')
    data['val'] = os.path.join(base_dir, 'val', 'images').replace('\\', '/')
    data['test'] = os.path.join(base_dir, 'test', 'images').replace('\\', '/')
    
    # 백업 파일 생성
    backup_path = yaml_path + '.backup'
    shutil.copy2(yaml_path, backup_path)
    print(f"기존 data.yaml을 {backup_path}로 백업했습니다.")
    
    # 새로운 yaml 파일 저장
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

def main():
    # 기본 경로 설정
    base_dir = "/home/team06/workspace/jonghui/model"
    yaml_path = os.path.join(base_dir, "data.yaml")
    
    # 원본 train 폴더 경로
    train_images_dir = os.path.join(base_dir, "train", "images")
    train_labels_dir = os.path.join(base_dir, "train", "labels")
    
    print("YOLO 데이터셋 분할을 시작합니다...")
    print(f"기본 디렉토리: {base_dir}")
    print(f"train images: {train_images_dir}")
    print(f"train labels: {train_labels_dir}")
    
    # 디렉토리 존재 확인
    if not os.path.exists(train_images_dir):
        print(f"Error: {train_images_dir} 디렉토리가 존재하지 않습니다.")
        return
    
    if not os.path.exists(train_labels_dir):
        print(f"Error: {train_labels_dir} 디렉토리가 존재하지 않습니다.")
        return
    
    # 1. 데이터셋 분석
    print("\n1. 데이터셋 분석 중...")
    file_class_mapping, class_counts = analyze_dataset(train_images_dir, train_labels_dir)
    
    print(f"\n클래스별 분포:")
    for class_id in sorted(class_counts.keys()):
        print(f"클래스 {class_id}: {class_counts[class_id]}개")
    
    if not file_class_mapping:
        print("Error: 분석할 데이터가 없습니다.")
        return
    
    # 2. 분할 비율 설정 (train: 70%, val: 20%, test: 10%)
    train_ratio = 0.7
    val_ratio = 0.2
    test_ratio = 0.1
    
    print(f"\n2. 데이터 분할 (train: {train_ratio*100}%, val: {val_ratio*100}%, test: {test_ratio*100}%)")
    train_files, val_files, test_files = create_stratified_split(
        file_class_mapping, train_ratio, val_ratio, test_ratio
    )
    
    print(f"\n분할 결과:")
    print(f"Train: {len(train_files)}개")
    print(f"Val: {len(val_files)}개") 
    print(f"Test: {len(test_files)}개")
    print(f"Total: {len(train_files) + len(val_files) + len(test_files)}개")
    
    # 3. 새로운 디렉토리 생성 및 파일 복사
    print("\n3. 파일 복사 중...")
    
    # val 폴더 생성 및 복사
    val_images_dir = os.path.join(base_dir, "val", "images")
    val_labels_dir = os.path.join(base_dir, "val", "labels")
    val_copied = copy_files(val_files, train_images_dir, train_labels_dir, 
                           val_images_dir, val_labels_dir)
    print(f"Val 세트: {val_copied}개 파일 복사 완료")
    
    # test 폴더 생성 및 복사
    test_images_dir = os.path.join(base_dir, "test", "images")
    test_labels_dir = os.path.join(base_dir, "test", "labels")
    test_copied = copy_files(test_files, train_images_dir, train_labels_dir,
                            test_images_dir, test_labels_dir)
    print(f"Test 세트: {test_copied}개 파일 복사 완료")
    
    # 4. train 폴더에서 이동된 파일들 제거
    print("\n4. Train 폴더에서 이동된 파일 제거 중...")
    removed_count = 0
    for img_file in val_files + test_files:
        # 이미지 파일 제거
        img_path = os.path.join(train_images_dir, img_file)
        if os.path.exists(img_path):
            os.remove(img_path)
            
            # 라벨 파일 제거
            base_name = os.path.splitext(img_file)[0]
            label_file = base_name + '.txt'
            label_path = os.path.join(train_labels_dir, label_file)
            if os.path.exists(label_path):
                os.remove(label_path)
            
            removed_count += 1
    
    print(f"Train 폴더에서 {removed_count}개 파일 제거 완료")
    
    # 5. data.yaml 파일 업데이트
    print("\n5. data.yaml 파일 업데이트 중...")
    if os.path.exists(yaml_path):
        update_yaml_file(yaml_path, base_dir)
        print("data.yaml 파일 업데이트 완료")
    else:
        print(f"Warning: {yaml_path} 파일을 찾을 수 없습니다.")
    
    print("\n데이터셋 분할이 완료되었습니다!")
    print(f"최종 구조:")
    print(f"├── train/")
    print(f"│   ├── images/ ({len(train_files)}개)")
    print(f"│   └── labels/ ({len(train_files)}개)")
    print(f"├── val/")
    print(f"│   ├── images/ ({len(val_files)}개)")
    print(f"│   └── labels/ ({len(val_files)}개)")
    print(f"└── test/")
    print(f"    ├── images/ ({len(test_files)}개)")
    print(f"    └── labels/ ({len(test_files)}개)")

if __name__ == "__main__":
    main()