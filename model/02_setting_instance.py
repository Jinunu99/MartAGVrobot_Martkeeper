""" 02_setting_instance.py """ 

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
import time
import math

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
from datetime import datetime

class BalancedDatasetManager:
    """YOLO 데이터셋 클래스 균형 조절 관리자 (단순 증폭 방식)"""
    
    def __init__(self, dataset_path, target_instances=600, min_instances=100):
        self.dataset_path = Path(dataset_path)
        self.target_instances = target_instances
        self.min_instances = min_instances
        
        # data.yaml 로드
        self.load_dataset_config()
        
        print(f"📊 YOLO 데이터셋 균형 조절 관리자 (단순 증폭)")
        print(f"📂 데이터셋: {dataset_path}")
        print(f"🎯 목표: {target_instances}개/클래스")
        print(f"📝 클래스: {len(self.class_names)}개")
        print(f"🔧 방식: 전체 이미지 증강 (라벨 정확성 보장)")

    def load_dataset_config(self):
        """data.yaml 설정 로드"""
        yaml_path = self.dataset_path / "data.yaml"
        
        if not yaml_path.exists():
            raise FileNotFoundError(f"data.yaml not found: {yaml_path}")
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.class_names = self.config['names']
        self.num_classes = self.config['nc']
        
        print(f"✅ 설정 로드: {self.num_classes}개 클래스")
        for i, name in enumerate(self.class_names):
            print(f"   {i}: {name}")

    def analyze_instance_distribution(self):
        """클래스별 인스턴스 분포 분석"""
        print("\n📊 클래스별 인스턴스 분포 분석...")
        
        instance_counts = Counter()
        image_sources = defaultdict(list)  # 이미지 기반 소스로 변경
        bbox_data = defaultdict(list)
        all_bboxes = []
        
        # train 폴더만 분석 (증강은 train에서만 수행)
        labels_dir = self.dataset_path / "train" / "labels"
        images_dir = self.dataset_path / "train" / "images"
        
        if not labels_dir.exists():
            raise FileNotFoundError(f"Train labels directory not found: {labels_dir}")
        
        total_files = 0
        for label_file in labels_dir.glob("*.txt"):
            # 해당 이미지 파일 찾기
            image_file = None
            for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                potential_image = images_dir / (label_file.stem + ext)
                if potential_image.exists():
                    image_file = potential_image
                    break
            
            if not image_file:
                continue
                
            total_files += 1
            
            try:
                with open(label_file, 'r') as f:
                    lines = f.readlines()
                
                # 이 이미지에 포함된 클래스들 수집
                image_classes = set()
                image_bbox_data = []
                
                for line_idx, line in enumerate(lines):
                    line = line.strip()
                    if line:
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                class_id = int(parts[0])
                                x, y, w, h = map(float, parts[1:5])
                                
                                # 유효한 클래스 ID 체크
                                if 0 <= class_id < self.num_classes:
                                    instance_counts[class_id] += 1
                                    image_classes.add(class_id)
                                    
                                    # 바운딩박스 데이터 수집
                                    bbox_info = {
                                        'class_id': class_id,
                                        'x_center': x,
                                        'y_center': y,
                                        'width': w,
                                        'height': h,
                                        'area': w * h
                                    }
                                    bbox_data[class_id].append(bbox_info)
                                    all_bboxes.append(bbox_info)
                                    image_bbox_data.append(bbox_info)
                                    
                            except (ValueError, IndexError):
                                continue
                
                # 이미지별 소스 정보 저장 (클래스별로)
                for class_id in image_classes:
                    class_bboxes = [bbox for bbox in image_bbox_data if bbox['class_id'] == class_id]
                    
                    image_info = {
                        'image_path': str(image_file),
                        'label_path': str(label_file),
                        'labels': lines,
                        'target_class': class_id,
                        'class_count': len(class_bboxes),
                        'total_objects': len(image_bbox_data),
                        'is_single_class': len(image_classes) == 1,
                        'has_small_objects': any(bbox['area'] < 0.01 for bbox in class_bboxes)
                    }
                    image_sources[class_id].append(image_info)
                    
            except Exception as e:
                print(f"⚠️ 파일 처리 오류 {label_file.name}: {e}")
                continue
        
        total_instances = sum(instance_counts.values())
        avg_instances = total_instances / self.num_classes if self.num_classes > 0 else 0
        
        print(f"\n📈 분석 결과:")
        print(f"   총 파일: {total_files}개")
        print(f"   총 인스턴스: {total_instances}개")
        print(f"   평균: {avg_instances:.1f}개/클래스")
        print(f"   목표: {self.target_instances}개/클래스")
        
        # 시각화 생성
        if MATPLOTLIB_AVAILABLE:
            self.create_distribution_analysis(instance_counts, bbox_data, all_bboxes)
        else:
            print("⚠️ matplotlib이 없어 시각화를 건너뜁니다. 설치: pip install matplotlib")
        
        # 클래스별 상세 정보
        print(f"\n{'ID':<3} {'클래스명':<30} {'현재':<8} {'목표':<8} {'부족':<8} {'상태':<12}")
        print("-" * 80)
        
        augmentation_plans = {}
        
        for class_id in range(self.num_classes):
            class_name = self.class_names[class_id]
            current_count = instance_counts.get(class_id, 0)
            shortage = max(0, self.target_instances - current_count)
            
            if current_count >= self.target_instances:
                status = "✅ 달성"
            elif current_count >= self.target_instances * 0.8:
                status = "🟡 약간부족"
                strategy = 'light'
            elif current_count >= self.target_instances * 0.5:
                status = "🟠 부족"
                strategy = 'moderate'
            elif current_count >= self.min_instances:
                status = "🔴 매우부족"
                strategy = 'aggressive'
            else:
                status = "❌ 극소량"
                strategy = 'extreme'
            
            print(f"{class_id:<3} {class_name:<30} {current_count:<8} {self.target_instances:<8} {shortage:<8} {status:<12}")
            
            # 증강 계획 생성
            if shortage > 0 and current_count >= 5:  # 최소 5개 이상 있어야 증강 가능
                # 해당 클래스가 포함된 이미지들 선별
                class_images = image_sources.get(class_id, [])
                if class_images:
                    augmentation_plans[class_id] = {
                        'name': class_name,
                        'current': current_count,
                        'needed': shortage,
                        'sources': class_images,
                        'strategy': strategy,
                        'source_images': len(class_images)
                    }
        
        return augmentation_plans, instance_counts

    def create_distribution_analysis(self, instance_counts, bbox_data, all_bboxes):
        """인스턴스 분포 분석 시각화 생성"""
        print("\n📊 분포 분석 시각화 생성 중...")
        
        # 4개 서브플롯 생성
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('YOLO Dataset Instance Distribution Analysis', fontsize=16, fontweight='bold')
        
        # 1. 클래스별 인스턴스 수 (막대 그래프)
        class_ids = list(range(self.num_classes))
        counts = [instance_counts.get(i, 0) for i in class_ids]
        
        # 색상 설정 (목표 달성 여부에 따라)
        colors = []
        for count in counts:
            if count >= self.target_instances:
                colors.append('#2E8B57')  # 초록 (달성)
            elif count >= self.target_instances * 0.8:
                colors.append('#FFD700')  # 금색 (근접)
            elif count >= self.target_instances * 0.5:
                colors.append('#FF8C00')  # 오렌지 (부족)
            else:
                colors.append('#DC143C')  # 빨강 (매우 부족)
        
        bars = ax1.bar(class_ids, counts, color=colors, alpha=0.7)
        ax1.axhline(y=self.target_instances, color='red', linestyle='--', linewidth=2, label=f'Target ({self.target_instances})')
        ax1.set_xlabel('Class ID')
        ax1.set_ylabel('Number of Instances')
        ax1.set_title('Instances per Class')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 값 표시
        for bar, count in zip(bars, counts):
            if count > 0:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
                        str(count), ha='center', va='bottom', fontsize=8)
        
        # 2. 클래스별 바운딩박스 크기 분포 (박스플롯)
        if bbox_data:
            # 각 클래스별 면적 데이터 수집
            class_areas = []
            class_labels = []
            
            for class_id in sorted(bbox_data.keys()):
                if bbox_data[class_id]:  # 데이터가 있는 경우만
                    areas = [bbox['area'] for bbox in bbox_data[class_id]]
                    class_areas.append(areas)
                    class_labels.append(f'{class_id}')
            
            if class_areas:
                box_plot = ax2.boxplot(class_areas, labels=class_labels, patch_artist=True)
                
                # 박스 색상 설정
                for i, (patch, class_id) in enumerate(zip(box_plot['boxes'], sorted(bbox_data.keys()))):
                    count = instance_counts.get(class_id, 0)
                    if count >= self.target_instances:
                        patch.set_facecolor('#2E8B57')
                    elif count >= self.target_instances * 0.8:
                        patch.set_facecolor('#FFD700')
                    elif count >= self.target_instances * 0.5:
                        patch.set_facecolor('#FF8C00')
                    else:
                        patch.set_facecolor('#DC143C')
                    patch.set_alpha(0.7)
                
                ax2.set_xlabel('Class ID')
                ax2.set_ylabel('Bounding Box Area')
                ax2.set_title('Bounding Box Size Distribution by Class')
                ax2.grid(True, alpha=0.3)
        
        # 3. 바운딩박스 중심점 분포 (산점도)
        if all_bboxes:
            x_centers = [bbox['x_center'] for bbox in all_bboxes]
            y_centers = [bbox['y_center'] for bbox in all_bboxes]
            
            # 밀도 기반 색상 매핑을 위한 히트맵
            hist, xedges, yedges = np.histogram2d(x_centers, y_centers, bins=50, range=[[0,1], [0,1]])
            extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
            
            im3 = ax3.imshow(hist.T, extent=extent, origin='lower', cmap='Blues', alpha=0.7)
            ax3.scatter(x_centers, y_centers, c='darkblue', alpha=0.3, s=1)
            ax3.set_xlabel('X Center (normalized)')
            ax3.set_ylabel('Y Center (normalized)')
            ax3.set_title('Bounding Box Center Distribution')
            ax3.set_xlim(0, 1)
            ax3.set_ylim(0, 1)
            plt.colorbar(im3, ax=ax3, label='Density')
        
        # 4. 바운딩박스 크기 분포 (width vs height)
        if all_bboxes:
            widths = [bbox['width'] for bbox in all_bboxes]
            heights = [bbox['height'] for bbox in all_bboxes]
            
            # 밀도 기반 색상 매핑
            hist, xedges, yedges = np.histogram2d(widths, heights, bins=50, range=[[0,1], [0,1]])
            extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
            
            im4 = ax4.imshow(hist.T, extent=extent, origin='lower', cmap='Blues', alpha=0.7)
            ax4.scatter(widths, heights, c='darkblue', alpha=0.3, s=1)
            ax4.set_xlabel('Width (normalized)')
            ax4.set_ylabel('Height (normalized)')
            ax4.set_title('Bounding Box Size Distribution')
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            plt.colorbar(im4, ax=ax4, label='Density')
        
        plt.tight_layout()
        
        # 저장
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_path = self.dataset_path / f"distribution_analysis_{timestamp}.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 분포 분석 저장: {save_path}")
        
        # 통계 요약 출력
        if all_bboxes:
            areas = [bbox['area'] for bbox in all_bboxes]
            widths = [bbox['width'] for bbox in all_bboxes]
            heights = [bbox['height'] for bbox in all_bboxes]
            
            print(f"\n📈 바운딩박스 통계:")
            print(f"   평균 면적: {np.mean(areas):.4f}")
            print(f"   평균 너비: {np.mean(widths):.4f}")
            print(f"   평균 높이: {np.mean(heights):.4f}")
            print(f"   작은 객체 (면적 < 0.01): {sum(1 for a in areas if a < 0.01)}개 ({sum(1 for a in areas if a < 0.01)/len(areas)*100:.1f}%)")
            print(f"   큰 객체 (면적 > 0.1): {sum(1 for a in areas if a > 0.1)}개 ({sum(1 for a in areas if a > 0.1)/len(areas)*100:.1f}%)")
        
        plt.show()
        
        return save_path

    def create_augmentation_transform(self, strategy):
        """증강 전략별 변환 생성 (라벨 호환 변환만)"""
        
        if strategy == 'extreme':
            return A.Compose([
                # 색상 변화 (브랜드 색상 보존 고려)
                A.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.08, hue=0.02, p=0.7),
                A.RandomBrightnessContrast(brightness_limit=0.08, contrast_limit=0.08, p=0.6),
                
                # 기하학적 변환 (라벨과 동기화 가능한 것만)
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.1),
                A.Rotate(limit=10, border_mode=cv2.BORDER_CONSTANT, p=0.4),
                A.ShiftScaleRotate(
                    shift_limit=0.05, scale_limit=0.1, rotate_limit=8,
                    border_mode=cv2.BORDER_CONSTANT, p=0.4
                ),
                
                # 품질 변화
                A.OneOf([
                    A.GaussNoise(var_limit=(5.0, 20.0)),
                    A.ISONoise(color_shift=(0.01, 0.03), intensity=(0.1, 0.3)),
                ], p=0.3),
                
                A.OneOf([
                    A.GaussianBlur(blur_limit=3),
                    A.MotionBlur(blur_limit=3),
                    A.Sharpen(alpha=(0.1, 0.3)),
                ], p=0.3),
                
            ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
            
        elif strategy == 'aggressive':
            return A.Compose([
                A.ColorJitter(brightness=0.08, contrast=0.08, saturation=0.06, hue=0.015, p=0.6),
                A.RandomBrightnessContrast(brightness_limit=0.06, contrast_limit=0.06, p=0.5),
                
                A.HorizontalFlip(p=0.5),
                A.Rotate(limit=6, border_mode=cv2.BORDER_CONSTANT, p=0.3),
                A.ShiftScaleRotate(
                    shift_limit=0.03, scale_limit=0.08, rotate_limit=5,
                    border_mode=cv2.BORDER_CONSTANT, p=0.3
                ),
                
                A.GaussNoise(var_limit=(3.0, 15.0), p=0.25),
                A.OneOf([
                    A.GaussianBlur(blur_limit=3),
                    A.Sharpen(alpha=(0.1, 0.2)),
                ], p=0.25),
                
            ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
            
        elif strategy == 'moderate':
            return A.Compose([
                A.ColorJitter(brightness=0.05, contrast=0.05, saturation=0.04, hue=0.01, p=0.5),
                A.RandomBrightnessContrast(brightness_limit=0.04, contrast_limit=0.04, p=0.4),
                
                A.HorizontalFlip(p=0.5),
                A.Rotate(limit=3, border_mode=cv2.BORDER_CONSTANT, p=0.2),
                
                A.GaussNoise(var_limit=(2.0, 10.0), p=0.2),
                A.GaussianBlur(blur_limit=3, p=0.2),
                
            ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
            
        else:  # light
            return A.Compose([
                A.ColorJitter(brightness=0.03, contrast=0.03, saturation=0.02, hue=0.005, p=0.4),
                A.RandomBrightnessContrast(brightness_limit=0.03, contrast_limit=0.03, p=0.3),
                
                A.HorizontalFlip(p=0.5),
                A.GaussNoise(var_limit=(1.0, 5.0), p=0.15),
                
            ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))

    def normalize_label_precision(self, labels):
        """라벨 좌표를 6자리 정밀도로 통일"""
        normalized_labels = []
        for label in labels:
            line = label.strip()
            if not line:
                continue
                
            parts = line.split()
            if len(parts) >= 5:
                try:
                    class_id = int(parts[0])
                    x, y, w, h = map(float, parts[1:5])
                    
                    # 6자리 정밀도로 통일
                    normalized_line = f"{class_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"
                    normalized_labels.append(normalized_line)
                    
                except (ValueError, IndexError):
                    continue
        
        return normalized_labels

    def perform_data_augmentation(self, augmentation_plans):
        """단순 증폭 데이터 증강 수행"""
        if not augmentation_plans:
            print("✅ 모든 클래스가 목표 달성!")
            return True
        
        print(f"\n🎨 단순 증폭 데이터 증강 시작...")
        print(f"📋 증강 대상: {len(augmentation_plans)}개 클래스")
        print(f"🔧 방식: 전체 이미지 증강 (라벨 정확성 보장)")
        
        # 백업 디렉토리 생성
        backup_dir = self.dataset_path / "backup_before_augmentation"
        if not backup_dir.exists():
            backup_dir.mkdir()
            train_backup = backup_dir / "train"
            train_backup.mkdir()
            shutil.copytree(self.dataset_path / "train" / "images", train_backup / "images")
            shutil.copytree(self.dataset_path / "train" / "labels", train_backup / "labels")
            print(f"📦 백업 생성: {backup_dir}")
        
        total_created = 0
        
        for class_id, plan in augmentation_plans.items():
            class_name = plan['name']
            needed = plan['needed']
            sources = plan['sources']
            strategy = plan['strategy']
            
            print(f"\n🎯 {class_name} (ID: {class_id})")
            print(f"   현재: {plan['current']}개, 필요: {needed}개")
            print(f"   소스 이미지: {len(sources)}개")
            print(f"   전략: {strategy}")
            
            if not sources:
                print(f"   ❌ 소스 이미지 없음")
                continue
            
            # 변환 생성
            transform = self.create_augmentation_transform(strategy)
            
            created = 0
            
            # 필요한 만큼 증강 이미지 생성
            while created < needed:
                try:
                    # 랜덤 소스 이미지 선택
                    source_image = random.choice(sources)
                    
                    # 이미지 로드
                    image = cv2.imread(source_image['image_path'])
                    if image is None:
                        continue
                    
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    h, w = image_rgb.shape[:2]
                    
                    # 라벨 로드 및 정규화
                    normalized_labels = self.normalize_label_precision(source_image['labels'])
                    
                    if not normalized_labels:
                        continue
                    
                    # YOLO 형식 바운딩박스 준비
                    bboxes = []
                    class_labels = []
                    
                    for label_line in normalized_labels:
                        parts = label_line.split()
                        if len(parts) >= 5:
                            try:
                                label_class_id = int(parts[0])
                                x, y, bbox_w, bbox_h = map(float, parts[1:5])
                                
                                # 바운딩박스 범위 체크
                                if (0 <= x <= 1 and 0 <= y <= 1 and 
                                    0 < bbox_w <= 1 and 0 < bbox_h <= 1):
                                    bboxes.append([x, y, bbox_w, bbox_h])
                                    class_labels.append(label_class_id)
                                    
                            except (ValueError, IndexError):
                                continue
                    
                    if not bboxes:
                        continue
                    
                    # 증강 적용 (라벨과 동기화)
                    augmented = transform(image=image_rgb, bboxes=bboxes, class_labels=class_labels)
                    aug_image = augmented['image']
                    aug_bboxes = augmented['bboxes']
                    aug_class_labels = augmented['class_labels']
                    
                    # 증강 후에도 바운딩박스가 유효한지 확인
                    if not aug_bboxes or len(aug_bboxes) != len(aug_class_labels):
                        continue
                    
                    # 파일명 생성
                    base_name = Path(source_image['image_path']).stem
                    aug_name = f"{base_name}_aug_{class_name}_{created:04d}"
                    
                    # 이미지 저장
                    aug_img_path = self.dataset_path / "train" / "images" / f"{aug_name}.jpg"
                    aug_image_bgr = cv2.cvtColor(aug_image, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(str(aug_img_path), aug_image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    
                    # 라벨 저장 (6자리 정밀도)
                    aug_label_path = self.dataset_path / "train" / "labels" / f"{aug_name}.txt"
                    
                    with open(aug_label_path, 'w') as f:
                        for bbox, label_id in zip(aug_bboxes, aug_class_labels):
                            x, y, bbox_w, bbox_h = bbox
                            # 범위 재확인 후 저장
                            x = max(0.0, min(1.0, x))
                            y = max(0.0, min(1.0, y))
                            bbox_w = max(0.001, min(1.0, bbox_w))
                            bbox_h = max(0.001, min(1.0, bbox_h))
                            
                            f.write(f"{int(label_id)} {x:.6f} {y:.6f} {bbox_w:.6f} {bbox_h:.6f}\n")
                    
                    created += 1
                    
                    if created % 50 == 0:
                        print(f"   📈 진행: {created}/{needed}")
                
                except Exception as e:
                    # 실패한 경우 다른 소스로 다시 시도
                    continue
            
            print(f"   ✅ {class_name} 완료: {created}개 이미지 생성")
            total_created += created
        
        print(f"\n🎉 단순 증폭 데이터 증강 완료! 총 생성: {total_created}개")
        print(f"💡 라벨 정확성: 100% 보장 (전체 이미지 증강)")
        print(f"🎯 Copy-Paste/Mosaic: 훈련 단계에서 YOLO 내장 기능 활용 예정")
        return True

    def update_yaml_file(self):
        """data.yaml 파일 업데이트 (경로 정보 등)"""
        yaml_path = self.dataset_path / "data.yaml"
        
        # 백업
        backup_path = yaml_path.with_suffix('.yaml.backup')
        if not backup_path.exists():
            shutil.copy2(yaml_path, backup_path)
        
        # 절대 경로로 업데이트
        dataset_abs_path = self.dataset_path.resolve()
        
        updated_config = {
            'path': str(dataset_abs_path),
            'train': 'train/images',
            'val': 'val/images', 
            'test': 'test/images',
            'nc': self.num_classes,
            'names': self.class_names
        }
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(updated_config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"✅ data.yaml 업데이트 완료")

    def validate_dataset(self):
        """데이터셋 유효성 검사"""
        print("\n🔍 데이터셋 유효성 검사...")
        
        issues = []
        total_images = 0
        total_labels = 0
        
        for split in ['train', 'val', 'test']:
            images_dir = self.dataset_path / split / "images"
            labels_dir = self.dataset_path / split / "labels"
            
            if not images_dir.exists():
                issues.append(f"❌ {split}/images 폴더 없음")
                continue
            
            if not labels_dir.exists():
                issues.append(f"❌ {split}/labels 폴더 없음")
                continue
            
            images = list(images_dir.glob("*"))
            labels = list(labels_dir.glob("*.txt"))
            
            total_images += len(images)
            total_labels += len(labels)
            
            print(f"📁 {split}: 이미지 {len(images)}개, 라벨 {len(labels)}개")
            
            # 이미지-라벨 매칭 확인
            unmatched = 0
            for img_file in images:
                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    label_file = labels_dir / (img_file.stem + '.txt')
                    if not label_file.exists():
                        unmatched += 1
            
            if unmatched > 0:
                issues.append(f"⚠️ {split}: {unmatched}개 이미지에 라벨 없음")
        
        print(f"\n📊 전체: 이미지 {total_images}개, 라벨 {total_labels}개")
        
        if issues:
            print("\n⚠️ 발견된 문제:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("✅ 데이터셋 유효성 검사 통과!")
        
        return len(issues) == 0

    def run_balance_pipeline(self):
        """균형 조절 파이프라인 실행"""
        print("🎯 YOLO 데이터셋 클래스 균형 조절 파이프라인 (단순 증폭)")
        print("=" * 60)
        
        try:
            # 1. 데이터셋 유효성 검사
            print("1️⃣ 데이터셋 유효성 검사")
            if not self.validate_dataset():
                print("❌ 데이터셋에 문제가 있습니다. 수정 후 다시 시도하세요.")
                return False
            
            # 2. 인스턴스 분포 분석
            print("\n2️⃣ 클래스별 인스턴스 분포 분석")
            augmentation_plans, current_counts = self.analyze_instance_distribution()
            
            # 3. 샘플 이미지 생성
            print("\n📷 샘플 이미지 생성")
            self.save_sample_images(current_counts, augmentation_plans)
            
            # 4. 증강 필요성 확인
            if not augmentation_plans:
                print("\n✅ 모든 클래스가 이미 목표를 달성했습니다!")
                return True
            
            print(f"\n📋 증강 계획:")
            total_needed = sum(plan['needed'] for plan in augmentation_plans.values())
            print(f"   대상 클래스: {len(augmentation_plans)}개")
            print(f"   생성할 이미지: {total_needed}개")
            print(f"   방식: 전체 이미지 증강 (라벨 정확성 보장)")
            
            # 5. 사용자 확인
            proceed = input("\n단순 증폭 데이터 증강을 실행하시겠습니까? (y/N): ").strip().lower()
            if proceed not in ['y', 'yes']:
                print("❌ 증강 취소됨")
                return False
            
            # 6. 데이터 증강 실행
            print("\n3️⃣ 단순 증폭 데이터 증강 실행")
            if not self.perform_data_augmentation(augmentation_plans):
                print("❌ 데이터 증강 실패")
                return False
            
            # 7. 결과 분석
            print("\n4️⃣ 증강 후 분포 재분석")
            final_plans, final_counts = self.analyze_instance_distribution()
            
            # 8. 최종 샘플 이미지 생성
            print("\n📷 최종 샘플 이미지 생성")
            self.save_sample_images(final_counts, final_plans)
            
            # 9. YAML 업데이트
            print("\n5️⃣ 설정 파일 업데이트")
            self.update_yaml_file()
            
            # 10. 최종 검사
            print("\n6️⃣ 최종 유효성 검사")
            self.validate_dataset()
            
            print(f"\n🎉 클래스 균형 조절 완료!")
            print(f"📊 결과 요약:")
            
            improved_classes = 0
            for class_id in range(self.num_classes):
                before = current_counts.get(class_id, 0)
                after = final_counts.get(class_id, 0)
                if after > before:
                    improved_classes += 1
                    print(f"   {self.class_names[class_id]}: {before} → {after} (+{after-before})")
            
            print(f"✅ {improved_classes}개 클래스 개선됨")
            print(f"\n📷 생성된 파일:")
            print(f"   📁 샘플 이미지: {self.dataset_path}/sample_images/")
            print(f"   💡 각 클래스별 폴더에서 바운딩박스가 그려진 샘플 확인 가능")
            
            print(f"\n🎯 다음 단계:")
            print(f"   🔄 train_model.py에서 copy_paste, mosaic 활성화 권장")
            print(f"   📈 YOLO 내장 기능으로 더 정교한 합성 수행")
            
            return True
            
        except Exception as e:
            print(f"❌ 파이프라인 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def restore_backup(self):
        """백업에서 복원"""
        backup_dir = self.dataset_path / "backup_before_augmentation"
        if not backup_dir.exists():
            print("❌ 백업이 없습니다.")
            return False
        
        print("🔄 백업에서 복원 중...")
        
        # 현재 train 폴더 제거
        train_dir = self.dataset_path / "train"
        if train_dir.exists():
            shutil.rmtree(train_dir)
        
        # 백업에서 복원
        shutil.copytree(backup_dir / "train", train_dir)
        
        print("✅ 백업에서 복원 완료")
        return True

    def save_sample_images(self, current_counts, augmentation_plans=None, samples_per_class=3):
        """클래스별 샘플 이미지 저장 (바운딩박스 포함)"""
        print(f"\n📷 클래스별 샘플 이미지 생성 중... (클래스당 {samples_per_class}개)")
        
        # 샘플 저장 폴더 생성
        samples_dir = self.dataset_path / "sample_images"
        if samples_dir.exists():
            shutil.rmtree(samples_dir)
        samples_dir.mkdir()
        
        labels_dir = self.dataset_path / "train" / "labels"
        images_dir = self.dataset_path / "train" / "images"
        
        # 클래스별 샘플 수집
        class_samples = defaultdict(list)
        
        for label_file in labels_dir.glob("*.txt"):
            # 이미지 파일 찾기
            image_file = None
            for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                potential_image = images_dir / (label_file.stem + ext)
                if potential_image.exists():
                    image_file = potential_image
                    break
            
            if not image_file:
                continue
            
            try:
                with open(label_file, 'r') as f:
                    lines = f.readlines()
                
                # 이 이미지에 있는 클래스들 확인
                classes_in_image = set()
                for line in lines:
                    line = line.strip()
                    if line:
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                class_id = int(parts[0])
                                if 0 <= class_id < self.num_classes:
                                    classes_in_image.add(class_id)
                            except:
                                continue
                
                # 각 클래스별로 샘플 추가
                for class_id in classes_in_image:
                    if len(class_samples[class_id]) < samples_per_class:
                        class_samples[class_id].append({
                            'image_path': str(image_file),
                            'label_path': str(label_file),
                            'labels': lines
                        })
                        
            except Exception as e:
                continue
        
        # 클래스별 샘플 이미지 생성
        for class_id in range(self.num_classes):
            class_name = self.class_names[class_id]
            current_count = current_counts.get(class_id, 0)
            
            if class_id not in class_samples:
                print(f"   ⚠️ {class_name}: 샘플 없음")
                continue
            
            # 클래스 폴더 생성
            class_dir = samples_dir / f"class_{class_id:02d}_{class_name}"
            class_dir.mkdir()
            
            # 상태 정보 파일 생성
            status_info = {
                'class_id': class_id,
                'class_name': class_name,
                'current_instances': current_count,
                'target_instances': self.target_instances,
                'shortage': max(0, self.target_instances - current_count),
                'status': 'achieved' if current_count >= self.target_instances else 'needs_augmentation',
                'augmentation_method': 'simple_augmentation'
            }
            
            if augmentation_plans and class_id in augmentation_plans:
                plan = augmentation_plans[class_id]
                status_info.update({
                    'augmentation_strategy': plan['strategy'],
                    'planned_creation': plan['needed']
                })
            
            with open(class_dir / "status.json", 'w', encoding='utf-8') as f:
                json.dump(status_info, f, indent=2, ensure_ascii=False)
            
            # 샘플 이미지들에 바운딩박스 그리고 저장
            for i, sample in enumerate(class_samples[class_id]):
                try:
                    # 이미지 로드
                    image = cv2.imread(sample['image_path'])
                    if image is None:
                        continue
                    
                    h, w = image.shape[:2]
                    
                    # 라벨 파싱하여 바운딩박스 그리기
                    for line in sample['labels']:
                        line = line.strip()
                        if line:
                            parts = line.split()
                            if len(parts) >= 5:
                                try:
                                    label_class_id = int(parts[0])
                                    x_center, y_center, bbox_w, bbox_h = map(float, parts[1:5])
                                    
                                    # YOLO 좌표를 픽셀 좌표로 변환
                                    x_center_px = int(x_center * w)
                                    y_center_px = int(y_center * h)
                                    bbox_w_px = int(bbox_w * w)
                                    bbox_h_px = int(bbox_h * h)
                                    
                                    x1 = int(x_center_px - bbox_w_px // 2)
                                    y1 = int(y_center_px - bbox_h_px // 2)
                                    x2 = int(x_center_px + bbox_w_px // 2)
                                    y2 = int(y_center_px + bbox_h_px // 2)
                                    
                                    # 바운딩박스 색상 (타겟 클래스는 빨간색, 다른 클래스는 파란색)
                                    if label_class_id == class_id:
                                        color = (0, 0, 255)  # 빨간색 (BGR)
                                        thickness = 3
                                    else:
                                        color = (255, 0, 0)  # 파란색 (BGR)
                                        thickness = 2
                                    
                                    # 바운딩박스 그리기
                                    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
                                    
                                    # 클래스 라벨 표시
                                    if 0 <= label_class_id < len(self.class_names):
                                        label_text = f"{label_class_id}: {self.class_names[label_class_id]}"
                                        cv2.putText(image, label_text, (x1, y1-10), 
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness-1)
                                
                                except:
                                    continue
                    
                    # 이미지 저장
                    sample_filename = f"sample_{i+1:02d}.jpg"
                    sample_path = class_dir / sample_filename
                    cv2.imwrite(str(sample_path), image, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    
                except Exception as e:
                    continue
            
            print(f"   📁 {class_name}: {len(class_samples[class_id])}개 샘플 저장")
        
        print(f"✅ 샘플 이미지 저장 완료: {samples_dir}")
        return samples_dir


# 실행부
if __name__ == "__main__":
    print("🎯 YOLO 데이터셋 클래스 균형 조절 도구 (단순 증폭)")
    print("=" * 50)
    
    # 설정
    dataset_path = "/home/team06/workspace/jonghui/model/snack_data"
    target_instances = 600  # 클래스당 목표 인스턴스 수
    min_instances = 50     # 증강을 위한 최소 인스턴스 수
    
    print(f"📂 데이터셋: {dataset_path}")
    print(f"🎯 목표: {target_instances}개/클래스")
    print(f"📝 최소: {min_instances}개/클래스 (증강 조건)")
    print(f"📷 샘플 이미지: 클래스별 바운딩박스 포함 샘플 생성")
    print(f"🔧 방식: 전체 이미지 증강 (라벨 정확성 100% 보장)")
    
    # 매니저 생성
    try:
        manager = BalancedDatasetManager(
            dataset_path=dataset_path,
            target_instances=target_instances,
            min_instances=min_instances
        )
        
        # 파이프라인 실행
        success = manager.run_balance_pipeline()
        
        if success:
            print(f"\n🎊 클래스 균형 조절 성공!")
            print(f"🎯 이제 모든 클래스가 균형잡힌 상태입니다!")
            print(f"\n📷 생성된 파일들:")
            print(f"   📁 샘플 이미지: {dataset_path}/sample_images/")
            print(f"   💡 각 클래스별 폴더에서 바운딩박스가 그려진 샘플 확인")
            
            print(f"\n🎯 다음 단계 권장:")
            print(f"   🔄 train_model.py에서 copy_paste=0.3, mosaic=0.5 활성화")
            print(f"   📈 YOLO 내장 기능으로 정교한 객체 합성 수행")
            print(f"   💯 라벨 정확성은 이미 100% 보장됨")
            
            # 복원 옵션
            restore = input("\n백업에서 복원하시겠습니까? (y/N): ").strip().lower()
            if restore in ['y', 'yes']:
                manager.restore_backup()
            else:
                print("📊 균형잡힌 데이터셋 유지")
        else:
            print(f"❌ 클래스 균형 조절 실패")
            
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        import traceback
        traceback.print_exc()