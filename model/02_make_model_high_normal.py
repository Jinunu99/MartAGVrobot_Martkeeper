import os
import cv2
import numpy as np
import albumentations as A
import shutil
from pathlib import Path
import json
import random
from collections import Counter, defaultdict
import yaml
from ultralytics import YOLO
import torch
import time

class FinalSnackTrainer:
    """최종 과자 탐지 모델 훈련기 - 모든 문제 해결"""
    
    def __init__(self, dataset_path, target_instances=600, model_size='m', epochs=80, exclude_classes=None):
        self.dataset_path = Path(dataset_path)
        self.target_instances = target_instances
        self.model_size = model_size
        self.epochs = epochs
        self.exclude_classes = exclude_classes or [1]  # Backside 제외
        
        # 원본 data.yaml에서 확인된 정확한 24개 클래스
        self.original_classes = [
            'Alsaeuchip',           # 0
            'Backside',             # 1 ← 제외할 클래스
            'BananaKick',           # 2
            'CaramelCornMaple',     # 3
            'Cheetos',              # 4
            'CornChips',            # 5
            'Gamjakkang',           # 6
            'Jjanggu',              # 7
            'JollyPong',            # 8
            'Kkobugchip',           # 9
            'Kkochgelang',          # 10
            'Kkulkkwabaegi',        # 11
            'KokkalCorn',           # 12
            'Koncho',               # 13
            'Matdongsan',           # 14
            'Ogamja',               # 15
            'Pocachip_Onion',       # 16
            'Pocachip_Original',    # 17
            'Postick',              # 18
            'Saeukkang',            # 19
            'Sunchip',              # 20
            'Swingchip',            # 21
            'Yangpaling',           # 22
            'konchi'                # 23
        ]
        
        # 제외 후 클래스 (23개)
        self.valid_classes = [self.original_classes[i] for i in range(24) if i not in self.exclude_classes]
        
        # ID 매핑 테이블 (원본 ID → 새 ID)
        self.id_mapping = {}
        new_id = 0
        for old_id in range(24):
            if old_id not in self.exclude_classes:
                self.id_mapping[old_id] = new_id
                new_id += 1
        
        self.max_instances = int(target_instances * 1.2)  # 상한선
        
        print(f"🎯 최종 과자 탐지 모델 훈련기")
        print(f"📊 원본: 24개 클래스 → 정리 후: {len(self.valid_classes)}개 클래스")
        print(f"🚫 제외: {[self.original_classes[i] for i in self.exclude_classes]}")
        print(f"🎯 목표: {target_instances}개/클래스, 상한선: {self.max_instances}개")
        print(f"📋 ID 매핑: 0-23 → 0-{len(self.valid_classes)-1}")

    def scan_and_fix_all_labels(self):
        """모든 라벨 파일 스캔 및 수정"""
        print("\n🔧 모든 라벨 파일 스캔 및 수정 중...")
        
        # 백업 생성
        backup_dir = self.dataset_path / "labels_backup_final"
        if not backup_dir.exists():
            print("💾 라벨 백업 생성 중...")
            backup_dir.mkdir()
            for split in ["train", "valid", "test"]:
                src_dir = self.dataset_path / split / "labels"
                if src_dir.exists():
                    dst_dir = backup_dir / split
                    shutil.copytree(src_dir, dst_dir)
        
        total_files = 0
        total_fixed = 0
        total_removed_labels = 0
        total_removed_files = 0
        
        # 각 split 처리
        for split in ["train", "valid", "test"]:
            labels_dir = self.dataset_path / split / "labels"
            images_dir = self.dataset_path / split / "images"
            
            if not labels_dir.exists():
                continue
            
            print(f"\n📁 {split} 처리 중...")
            split_files = 0
            split_fixed = 0
            split_removed_labels = 0
            split_removed_files = 0
            
            for label_file in labels_dir.glob("*.txt"):
                total_files += 1
                split_files += 1
                
                try:
                    with open(label_file, 'r') as f:
                        lines = f.readlines()
                    
                    new_lines = []
                    file_changed = False
                    
                    for line in lines:
                        line = line.strip()
                        if line:
                            parts = line.split()
                            if len(parts) >= 5:
                                try:
                                    old_class_id = int(parts[0])
                                    
                                    # 범위 체크 (0-23만 유효)
                                    if old_class_id < 0 or old_class_id > 23:
                                        split_removed_labels += 1
                                        file_changed = True
                                        continue
                                    
                                    # 제외 클래스 제거
                                    if old_class_id in self.exclude_classes:
                                        split_removed_labels += 1
                                        file_changed = True
                                        continue
                                    
                                    # ID 재매핑
                                    new_class_id = self.id_mapping[old_class_id]
                                    parts[0] = str(new_class_id)
                                    new_lines.append(' '.join(parts) + '\n')
                                    
                                    if new_class_id != old_class_id:
                                        file_changed = True
                                        
                                except ValueError:
                                    split_removed_labels += 1
                                    file_changed = True
                                    continue
                    
                    # 파일 처리
                    if len(new_lines) == 0:
                        # 빈 파일 - 이미지와 라벨 모두 삭제
                        image_name = label_file.stem
                        for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                            image_file = images_dir / (image_name + ext)
                            if image_file.exists():
                                image_file.unlink()
                                break
                        label_file.unlink()
                        split_removed_files += 1
                        
                    elif file_changed:
                        # 파일 업데이트
                        with open(label_file, 'w') as f:
                            f.writelines(new_lines)
                        split_fixed += 1
                
                except Exception as e:
                    print(f"      ⚠️ 오류 {label_file.name}: {e}")
            
            print(f"   ✅ {split} 완료: {split_files}개 파일, {split_fixed}개 수정, {split_removed_labels}개 라벨 제거, {split_removed_files}개 파일 삭제")
            
            total_fixed += split_fixed
            total_removed_labels += split_removed_labels
            total_removed_files += split_removed_files
        
        print(f"\n🎉 라벨 정리 완료!")
        print(f"   총 파일: {total_files}개")
        print(f"   수정된 파일: {total_fixed}개")
        print(f"   제거된 라벨: {total_removed_labels}개")
        print(f"   삭제된 파일: {total_removed_files}개")
        print(f"   백업 위치: {backup_dir}")
        
        return True

    def validate_final_labels(self):
        """최종 라벨 검증"""
        print("\n🔍 최종 라벨 검증 중...")
        
        all_class_ids = set()
        total_files = 0
        total_labels = 0
        error_count = 0
        
        for split in ["train", "valid", "test"]:
            labels_dir = self.dataset_path / split / "labels"
            if not labels_dir.exists():
                continue
            
            for label_file in labels_dir.glob("*.txt"):
                total_files += 1
                
                try:
                    with open(label_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                parts = line.split()
                                if len(parts) >= 5:
                                    class_id = int(parts[0])
                                    all_class_ids.add(class_id)
                                    total_labels += 1
                                    
                                    # 범위 체크
                                    if class_id < 0 or class_id >= len(self.valid_classes):
                                        error_count += 1
                                        print(f"      ❌ 잘못된 ID {class_id} in {label_file.name}")
                
                except Exception as e:
                    error_count += 1
                    print(f"      ❌ 파일 오류 {label_file.name}: {e}")
        
        print(f"📊 최종 검증 결과:")
        print(f"   총 파일: {total_files}개")
        print(f"   총 라벨: {total_labels}개")
        print(f"   발견된 클래스 ID: {sorted(all_class_ids)}")
        print(f"   유효 범위: 0-{len(self.valid_classes)-1}")
        print(f"   오류 수: {error_count}개")
        
        if error_count == 0:
            print(f"   ✅ 모든 라벨이 올바름!")
            return True
        else:
            print(f"   ❌ {error_count}개 문제 발견")
            return False

    def create_final_yaml(self):
        """최종 YAML 파일 생성"""
        print("\n📝 최종 YAML 파일 생성 중...")
        
        # 절대 경로 사용
        dataset_abs_path = self.dataset_path.resolve()
        
        # 경로 검증
        train_path = dataset_abs_path / "train" / "images"
        val_path = dataset_abs_path / "valid" / "images" 
        test_path = dataset_abs_path / "test" / "images"
        
        print(f"📁 경로 검증:")
        print(f"   데이터셋: {dataset_abs_path}")
        print(f"   Train: {'✅' if train_path.exists() else '❌'}")
        print(f"   Valid: {'✅' if val_path.exists() else '❌'}")
        print(f"   Test: {'✅' if test_path.exists() else '❌'}")
        
        # YAML 내용 생성
        yaml_content = f"""path: {dataset_abs_path}/
train: train/images
val: valid/images
test: test/images

nc: {len(self.valid_classes)}
names: {self.valid_classes}

# 최종 정리된 과자 탐지 데이터
# 원본: 24개 클래스 → 정리 후: {len(self.valid_classes)}개 클래스
# 제외된 클래스: {[self.original_classes[i] for i in self.exclude_classes]}
# 목표: {self.target_instances}개/클래스, 상한선: {self.max_instances}개/클래스
# 생성 일시: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # 현재 작업 디렉토리에 저장
        yaml_path = Path.cwd() / "final_snack_data.yaml"
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        print(f"✅ YAML 파일 생성 완료:")
        print(f"   파일: {yaml_path}")
        print(f"   클래스 수: {len(self.valid_classes)}")
        
        # YAML 검증
        try:
            with open(yaml_path, 'r') as f:
                yaml_data = yaml.safe_load(f)
            print(f"   ✅ YAML 문법 검증 통과")
        except Exception as e:
            print(f"   ❌ YAML 검증 실패: {e}")
            return None
        
        return str(yaml_path)

    def augment_low_frequency_classes(self, need_augmentation):
        """저빈도 클래스 데이터 증강"""
        if not need_augmentation:
            print("✅ 모든 클래스가 목표에 도달함")
            return True
        
        print(f"\n🔄 {len(need_augmentation)}개 클래스 데이터 증강 시작...")
        
        # 증강 설정
        transform = A.Compose([
            # 색상 보존 중심의 가벼운 증강
            A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.15, hue=0.05, p=0.6),
            A.RandomBrightnessContrast(brightness_limit=0.15, contrast_limit=0.15, p=0.4),
            
            # 기하학적 변환
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.1),
            A.Rotate(limit=20, border_mode=cv2.BORDER_CONSTANT, value=0, p=0.7),
            A.ShiftScaleRotate(
                shift_limit=0.15, scale_limit=0.25, rotate_limit=15, 
                border_mode=cv2.BORDER_CONSTANT, value=0, p=0.6
            ),
            
            # 가벼운 노이즈
            A.OneOf([
                A.GaussNoise(var_limit=(5.0, 20.0)),
                A.GaussianBlur(blur_limit=3),
            ], p=0.3),
            
        ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels'], min_visibility=0.4))
        
        total_created = 0
        
        for class_id, class_name, needed in need_augmentation:
            print(f"\n📈 {class_name} (ID: {class_id}) 증강 중... 필요: {needed}개")
            
            # 해당 클래스가 포함된 이미지 찾기
            source_images = self._find_images_with_class(class_id)
            
            if not source_images:
                print(f"   ❌ 소스 이미지를 찾을 수 없음")
                continue
            
            print(f"   📷 소스 이미지: {len(source_images)}개")
            
            created = 0
            max_failures = 100
            failures = 0
            
            # 증강 루프
            for cycle in range(20):  # 최대 20 사이클
                if created >= needed:
                    break
                
                # 현재 개수 확인 (실시간)
                current_count = self._get_current_class_count(class_id)
                if current_count >= self.max_instances:
                    print(f"   🛑 상한선 도달: {current_count}개")
                    break
                
                for img_path, label_path in source_images:
                    if created >= needed:
                        break
                    
                    try:
                        # 이미지 로드
                        image = cv2.imread(str(img_path))
                        if image is None:
                            continue
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        
                        # 라벨 로드
                        bboxes, class_labels = self._load_labels(label_path)
                        
                        if class_id not in class_labels:
                            continue
                        
                        # 증강 적용
                        augmented = transform(image=image, bboxes=bboxes, class_labels=class_labels)
                        aug_image = augmented['image']
                        aug_bboxes = augmented['bboxes']
                        aug_labels = augmented['class_labels']
                        
                        # 타겟 클래스가 여전히 있는지 확인
                        if class_id not in aug_labels:
                            failures += 1
                            if failures > max_failures:
                                print(f"   ⚠️ 연속 실패 {max_failures}회, 중단")
                                break
                            continue
                        
                        # 파일 저장
                        base_name = img_path.stem
                        aug_name = f"{base_name}_aug_{class_name}_{created:04d}"
                        
                        # 이미지 저장
                        aug_img_path = self.dataset_path / "train" / "images" / f"{aug_name}.jpg"
                        aug_image_bgr = cv2.cvtColor(aug_image, cv2.COLOR_RGB2BGR)
                        cv2.imwrite(str(aug_img_path), aug_image_bgr)
                        
                        # 라벨 저장
                        aug_label_path = self.dataset_path / "train" / "labels" / f"{aug_name}.txt"
                        with open(aug_label_path, 'w') as f:
                            for bbox, label in zip(aug_bboxes, aug_labels):
                                x_center, y_center, bbox_width, bbox_height = bbox
                                f.write(f"{label} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}\n")
                        
                        created += 1
                        failures = 0  # 성공 시 실패 카운터 리셋
                        
                        if created % 50 == 0:
                            current_total = self._get_current_class_count(class_id)
                            print(f"   진행: {created}/{needed} (현재 총: {current_total}개)")
                        
                    except Exception as e:
                        failures += 1
                        continue
                
                if failures > max_failures:
                    break
            
            final_count = self._get_current_class_count(class_id)
            print(f"   ✅ {class_name} 완료: {created}개 생성 (최종: {final_count}개)")
            total_created += created
        
        print(f"\n🎉 데이터 증강 완료! 총 생성: {total_created}개")
        return True

    def _find_images_with_class(self, target_class_id):
        """특정 클래스가 포함된 이미지 찾기"""
        labels_dir = self.dataset_path / "train" / "labels"
        images_dir = self.dataset_path / "train" / "images"
        
        images_with_class = []
        
        for label_file in labels_dir.glob("*.txt"):
            image_file = None
            for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                potential_image = images_dir / (label_file.stem + ext)
                if potential_image.exists():
                    image_file = potential_image
                    break
            
            if image_file:
                try:
                    with open(label_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                parts = line.split()
                                if len(parts) >= 5:
                                    class_id = int(parts[0])
                                    if class_id == target_class_id:
                                        images_with_class.append((image_file, label_file))
                                        break
                except:
                    continue
        
        return images_with_class

    def _load_labels(self, label_path):
        """라벨 파일에서 bbox와 클래스 로드"""
        bboxes = []
        class_labels = []
        
        try:
            with open(label_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split()
                        if len(parts) >= 5:
                            cls = int(parts[0])
                            x_center, y_center, bbox_width, bbox_height = map(float, parts[1:5])
                            bboxes.append([x_center, y_center, bbox_width, bbox_height])
                            class_labels.append(cls)
        except:
            pass
        
        return bboxes, class_labels

    def _get_current_class_count(self, class_id):
        """특정 클래스의 현재 인스턴스 수 확인"""
        labels_dir = self.dataset_path / "train" / "labels"
        count = 0
        
        for label_file in labels_dir.glob("*.txt"):
            try:
                with open(label_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split()
                            if len(parts) >= 5 and int(parts[0]) == class_id:
                                count += 1
            except:
                continue
        
        return count

    def analyze_class_distribution(self):
        """클래스 분포 분석"""
        print("\n📊 클래스 분포 분석 중...")
        
        class_counts = Counter()
        
        labels_dir = self.dataset_path / "train" / "labels"
        for label_file in labels_dir.glob("*.txt"):
            try:
                with open(label_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split()
                            if len(parts) >= 5:
                                class_id = int(parts[0])
                                class_counts[class_id] += 1
            except:
                continue
        
        print(f"\n{'ID':<3} {'클래스명':<20} {'현재 수':<8} {'목표':<8} {'상태':<10}")
        print("-" * 60)
        
        need_augmentation = []
        
        for class_id in range(len(self.valid_classes)):
            class_name = self.valid_classes[class_id]
            current_count = class_counts.get(class_id, 0)
            
            if current_count >= self.max_instances:
                status = "🟢 상한초과"
            elif current_count >= self.target_instances:
                status = "✅ 목표달성"
            else:
                needed = self.target_instances - current_count
                status = f"🔴 {needed}개 필요"
                need_augmentation.append((class_id, class_name, needed))
            
            print(f"{class_id:<3} {class_name:<20} {current_count:<8} {self.target_instances:<8} {status:<10}")
        
        return need_augmentation
        """클래스 분포 분석"""
        print("\n📊 클래스 분포 분석 중...")
        
        class_counts = Counter()
        
        labels_dir = self.dataset_path / "train" / "labels"
        for label_file in labels_dir.glob("*.txt"):
            try:
                with open(label_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            parts = line.split()
                            if len(parts) >= 5:
                                class_id = int(parts[0])
                                class_counts[class_id] += 1
            except:
                continue
        
        print(f"\n{'ID':<3} {'클래스명':<20} {'현재 수':<8} {'목표':<8} {'상태':<10}")
        print("-" * 60)
        
        need_augmentation = []
        
        for class_id in range(len(self.valid_classes)):
            class_name = self.valid_classes[class_id]
            current_count = class_counts.get(class_id, 0)
            
            if current_count >= self.max_instances:
                status = "🟢 상한초과"
            elif current_count >= self.target_instances:
                status = "✅ 목표달성"
            else:
                needed = self.target_instances - current_count
                status = f"🔴 {needed}개 필요"
                need_augmentation.append((class_id, class_name, needed))
            
            print(f"{class_id:<3} {class_name:<20} {current_count:<8} {self.target_instances:<8} {status:<10}")
        
        return need_augmentation

    def safe_train_model(self, yaml_path):
        """서버 공유 환경용 안전한 모델 훈련 (15GB 메모리 최적화)"""
        print("\n🚀 서버 공유 환경용 안전한 훈련 시작!")
        
        # YAML 파일 검증
        if not Path(yaml_path).exists():
            print(f"❌ YAML 파일 없음: {yaml_path}")
            return None, None
        
        print(f"📄 YAML: {yaml_path}")
        
        # 모델 로드
        model = YOLO(f'yolo11{self.model_size}.pt')
        
        # GPU 메모리 확인 및 최적화
        if torch.cuda.is_available():
            device = 0  # 첫 번째 GPU
            gpu_memory = torch.cuda.get_device_properties(device).total_memory / (1024**3)
            print(f"💻 GPU 훈련: CUDA:{device} ({gpu_memory:.1f}GB 중 ~15GB 사용)")
            torch.cuda.empty_cache()
            
            # 서버 공유 환경용 안전한 배치 크기 (15GB 기준)
            batch_sizes = {
                'n': 64,   # nano: 15GB에서 충분히 안전
                's': 32,   # small: 안정적
                'm': 24,   # medium: 15GB에 최적화
                'l': 16,   # large: 보수적
                'x': 8     # xlarge: 매우 안전
            }
            print(f"🏢 서버 공유 환경 - 안전한 배치 크기 사용")
        else:
            device = 'cpu'
            batch_sizes = {'n': 16, 's': 8, 'm': 4, 'l': 2, 'x': 1}
            print(f"💻 CPU 훈련")
        
        batch_size = batch_sizes.get(self.model_size, 16)
        print(f"📦 배치 크기: {batch_size} (15GB 메모리 고려)")
        
        try:
            results = model.train(
                data=str(yaml_path),
                epochs=self.epochs,
                imgsz=640,
                device=device,
                batch=batch_size,
                patience=25,
                save=True,
                project='final_snack_detection',
                name=f'yolo11{self.model_size}_final',
                exist_ok=True,
                
                # 서버 공유 환경용 안전 설정
                workers=6,      # 적당한 워커 수
                cache='disk',   # 디스크 캐시 (RAM 절약)
                amp=True,       # 혼합 정밀도로 메모리 절약
                
                # 최적화된 훈련 설정
                lr0=0.01,
                lrf=0.01,
                momentum=0.937,
                weight_decay=0.0005,
                warmup_epochs=3,
                warmup_momentum=0.8,
                warmup_bias_lr=0.1,
                
                # 적당한 데이터 증강 (서버 리소스 고려)
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
                copy_paste=0.0,
                
                # 안전한 설정
                plots=True,
                val=True,
                verbose=True,
                save_period=10,
                
                # 메모리 효율성
                multi_scale=False,  # 메모리 절약
                rect=False,
                cos_lr=True,
                close_mosaic=10,
                
                # 손실 함수 가중치
                box=7.5,
                cls=0.5,
                dfl=1.5,
            )
            
            print("\n🎉 훈련 완료!")
            
            # 성능 확인
            try:
                metrics = model.val()
                print(f"\n📈 최종 성능:")
                print(f"  mAP50: {metrics.box.map50:.4f} ({metrics.box.map50*100:.1f}%)")
                print(f"  mAP50-95: {metrics.box.map:.4f} ({metrics.box.map*100:.1f}%)")
                print(f"  Precision: {metrics.box.mp:.4f} ({metrics.box.mp*100:.1f}%)")
                print(f"  Recall: {metrics.box.mr:.4f} ({metrics.box.mr*100:.1f}%)")
                
                # 성능 평가
                if metrics.box.map50 >= 0.7:
                    print(f"🌟 우수한 성능! mAP50 {metrics.box.map50:.3f}")
                elif metrics.box.map50 >= 0.5:
                    print(f"✅ 양호한 성능: mAP50 {metrics.box.map50:.3f}")
                else:
                    print(f"⚠️ 개선 필요: mAP50 {metrics.box.map50:.3f}")
                    
            except Exception as e:
                print(f"⚠️ 검증 오류: {e}")
            
            return model, results
            
        except Exception as e:
            print(f"❌ 훈련 오류: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    def run_complete_pipeline(self):
        """완전한 파이프라인 실행 (데이터 증강 포함)"""
        print("🎯 최종 과자 탐지 모델 파이프라인")
        print("=" * 50)
        print("1️⃣ 라벨 스캔 및 수정")
        print("2️⃣ 최종 검증")
        print("3️⃣ YAML 생성") 
        print("4️⃣ 클래스 분포 분석")
        print("5️⃣ 데이터 증강 (필요시)")
        print("6️⃣ 모델 훈련")
        print("=" * 50)
        
        try:
            # 1단계: 라벨 정리
            print("\n1️⃣ 라벨 스캔 및 수정...")
            if not self.scan_and_fix_all_labels():
                print("❌ 라벨 정리 실패")
                return None, None
            
            # 2단계: 검증
            print("\n2️⃣ 최종 검증...")
            if not self.validate_final_labels():
                print("❌ 라벨 검증 실패")
                return None, None
            
            # 3단계: YAML 생성
            print("\n3️⃣ YAML 생성...")
            yaml_path = self.create_final_yaml()
            if not yaml_path:
                print("❌ YAML 생성 실패")
                return None, None
            
            # 4단계: 분포 분석
            print("\n4️⃣ 클래스 분포 분석...")
            need_aug = self.analyze_class_distribution()
            
            # 5단계: 데이터 증강 (필요시)
            if need_aug:
                print(f"\n5️⃣ 데이터 증강...")
                print(f"📈 {len(need_aug)}개 클래스가 목표 미달")
                
                proceed_aug = input("데이터 증강을 실행하시겠습니까? (y/N): ").strip().lower()
                if proceed_aug in ['y', 'yes']:
                    if not self.augment_low_frequency_classes(need_aug):
                        print("❌ 데이터 증강 실패")
                        return None, None
                    
                    # 증강 후 재분석
                    print("\n📊 증강 후 분포 재분석...")
                    final_need_aug = self.analyze_class_distribution()
                    if final_need_aug:
                        print(f"⚠️ 여전히 {len(final_need_aug)}개 클래스가 목표 미달")
                else:
                    print("⏭️ 데이터 증강 건너뜀")
            else:
                print("✅ 모든 클래스가 목표에 도달!")
            
            # 6단계: 훈련
            print(f"\n6️⃣ 모델 훈련...")
            model, results = self.safe_train_model(yaml_path)
            
            if model and results:
                print(f"\n🎊 전체 파이프라인 완료!")
                print(f"📁 결과: final_snack_detection/yolo11{self.model_size}_final/")
                print(f"🏆 모델: weights/best.pt")
                print(f"📊 로그: results.csv")
                print(f"📈 그래프: results.png")
            
            return model, results
            
        except Exception as e:
            print(f"❌ 파이프라인 오류: {e}")
            import traceback
            traceback.print_exc()
            return None, None


# 실행부
if __name__ == "__main__":
    print("🎯 최종 과자 탐지 모델 훈련기")
    print("=" * 50)
    
    # 설정
    dataset_path = "snack_data_2"
    
    print(f"📂 데이터셋: {dataset_path}")
    print(f"🎯 목표: 600개/클래스")
    print(f"🤖 모델: YOLO11m")
    print(f"🔄 에포크: 80")
    print(f"🚫 제외: Backside")
    
    # 경로 확인
    if not Path(dataset_path).exists():
        print(f"❌ 데이터셋을 찾을 수 없습니다: {dataset_path}")
        print("올바른 경로를 입력하세요:")
        dataset_path = input("데이터셋 경로: ").strip() or dataset_path
    
    # 확인
    proceed = input("\n시작하시겠습니까? (y/N): ").strip().lower()
    if proceed not in ['y', 'yes']:
        print("❌ 취소됨")
        exit(0)
    
    # 실행
    trainer = FinalSnackTrainer(
        dataset_path=dataset_path,
        target_instances=600,
        model_size='m',
        epochs=80,
        exclude_classes=[1]  # Backside 제외
    )
    
    model, results = trainer.run_complete_pipeline()
    
    if model and results:
        print(f"\n🎉 성공!")
        print(f"📁 final_snack_detection/yolo11m_final/")
    else:
        print(f"❌ 실패")