#!/usr/bin/env python3
"""
config.py
웹캠 최적화 훈련 기본 설정 (Instance 단순 증폭 + YOLO 내장 기능 조합)
"""

import os
import yaml
from pathlib import Path

class Config:
    def __init__(self, dataset_path, enable_320=True):
        self.dataset_path = Path(dataset_path)
        self.enable_320 = enable_320
        self.classes = []
        self.yaml_path = None
        self.load_yaml()
        
    def load_yaml(self):
        """기존 data.yaml 로드"""
        yaml_file = self.dataset_path / "data.yaml"
        if yaml_file.exists():
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                self.classes = config['names']
                self.yaml_path = str(yaml_file)
                print(f"✅ YAML 로드 성공: {len(self.classes)}개 클래스")
                return True
            except Exception as e:
                print(f"❌ YAML 로드 실패: {e}")
                return False
        else:
            print(f"❌ data.yaml을 찾을 수 없습니다: {yaml_file}")
            return False
    
    def get_train_config(self):
        """훈련 설정 반환 (Instance + YOLO 내장 기능 조합 최적화)"""
        return {
            'epochs': 70,
            'patience': 15,
            'batch_size': 16 if self.enable_320 else 32,
            'imgsz': 512 if self.enable_320 else 640,  # 단일 값으로 수정
            'lr0': 0.008 if self.enable_320 else 0.01,
            'lrf': 0.001,
            
            # 브랜드 색상 보존 (Instance에서 이미 처리됨)
            'hsv_h': 0.001,
            'hsv_s': 0.02,  # 약간 완화 (YOLO 내장 기능과 조합)
            'hsv_v': 0.08,
            
            # 기하학적 변환 최소화 (Instance에서 이미 처리됨)
            'degrees': 1.0,    # 더 줄임 (YOLO 내장에서 처리)
            'translate': 0.005, # 최소화
            'scale': 0.03,      # 최소화
            'perspective': 0.0,
            'flipud': 0.0,
            'fliplr': 0.4,      # 약간 줄임
            
            # YOLO 내장 증강 (Instance와 조합)
            'mosaic': 0.5,      # 적극 활용
            'copy_paste': 0.3,  # 활성화
            'mixup': 0.1,       # 약간 활용
            
            # 손실 함수 (YOLO 내장 기능 고려)
            'box': 8.5 if self.enable_320 else 7.0,  # Copy-Paste 고려 조정
            'cls': 0.5,         # 클래스 균형 달성으로 안정화
            'dfl': 1.8 if self.enable_320 else 1.3,
            
            # 탐지 설정
            'conf': 0.08 if self.enable_320 else 0.12,
            'iou': 0.25 if self.enable_320 else 0.35,
        }
    
    def print_info(self):
        """설정 정보 출력"""
        print(f"\n📊 현재 설정:")
        print(f"  📂 데이터셋: {self.dataset_path}")
        print(f"  📱 320 지원: {self.enable_320}")
        print(f"  📋 클래스 수: {len(self.classes)}")
        print(f"  📄 YAML: {self.yaml_path}")
        
        if self.classes:
            brands = {}
            for cls in self.classes:
                if '_' in cls:
                    brand = cls.split('_')[0]
                    brands[brand] = brands.get(brand, 0) + 1
            
            print(f"  🏢 브랜드별:")
            for brand, count in brands.items():
                print(f"    - {brand.title()}: {count}개")
        
        print(f"\n🎯 증강 전략:")
        print(f"  📈 Instance 단계: 단순 증폭 (클래스 균형 + 라벨 정확성)")
        print(f"  🧩 Train 단계: YOLO 내장 기능 (Copy-Paste/Mosaic)")
        print(f"  🎨 색상 보존: 최소 변경 (브랜드 보존)")
        print(f"  💯 라벨 품질: 완전 보장")
    
    def print_augmentation_strategy(self):
        """증강 전략 상세 설명"""
        config = self.get_train_config()
        
        print(f"\n🎨 상세 증강 전략:")
        print("=" * 50)
        
        print(f"📈 Instance 단계 (단순 증폭):")
        print(f"  ✅ 전체 이미지 증강")
        print(f"  ✅ 라벨 좌표 동기화 100%")
        print(f"  ✅ 클래스별 균형 달성")
        print(f"  ✅ 브랜드 색상 보존")
        
        print(f"\n🧩 Train 단계 (YOLO 내장):")
        print(f"  🔄 Mosaic: {config['mosaic']*100:.0f}% (4개 이미지 격자)")
        print(f"  ✂️ Copy-Paste: {config['copy_paste']*100:.0f}% (객체 복사-붙이기)")
        print(f"  🔀 MixUp: {config['mixup']*100:.0f}% (이미지 혼합)")
        print(f"  🎯 라벨 처리: YOLO 엔진 자동 보장")
        
        print(f"\n🎨 색상 변화 (최소화):")
        print(f"  🌈 HSV H: {config['hsv_h']} (색조 거의 변경 없음)")
        print(f"  💎 HSV S: {config['hsv_s']} (채도 최소 변경)")
        print(f"  ☀️ HSV V: {config['hsv_v']} (밝기 약간 변경)")
        
        print(f"\n📐 기하학적 변환 (최소화):")
        print(f"  🔄 회전: ±{config['degrees']}° (최소)")
        print(f"  📏 이동: ±{config['translate']*100:.1f}% (최소)")
        print(f"  📊 스케일: ±{config['scale']*100:.1f}% (최소)")
        print(f"  🪞 좌우반전: {config['fliplr']*100:.0f}%")
        
        print(f"\n🎯 최적화 결과:")
        print(f"  💯 라벨 정확성: 완벽 보장")
        print(f"  🌈 브랜드 색상: 최대 보존") 
        print(f"  📊 클래스 균형: 달성")
        print(f"  🎪 데이터 다양성: YOLO 내장 기능으로 확보")
        print(f"  🚀 훈련 안정성: 검증된 알고리즘 조합")
        
        if self.enable_320:
            print(f"\n📱 320 해상도 최적화:")
            print(f"  🎯 훈련 해상도: {config['imgsz']}")
            print(f"  ⚡ 추론 지원: 320/640 듀얼")
            print(f"  🔧 손실 함수: 320 특화 조정")
            print(f"  📈 성능 목표: 640 대비 85%+ 유지")