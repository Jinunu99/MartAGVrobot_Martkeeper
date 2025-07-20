#!/usr/bin/env python3
"""
fix_yaml_paths.py
data.yaml 경로 문제 수정
"""

import yaml
from pathlib import Path

def fix_yaml_paths(dataset_path):
    """YAML 파일의 경로 문제 수정"""
    dataset_path = Path(dataset_path)
    yaml_file = dataset_path / "data.yaml"
    
    if not yaml_file.exists():
        print(f"❌ data.yaml을 찾을 수 없습니다: {yaml_file}")
        return False
    
    print(f"🔧 YAML 경로 수정 중...")
    
    try:
        # 기존 YAML 읽기
        with open(yaml_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"📄 기존 YAML 내용:")
        print(f"  path: {config.get('path', 'N/A')}")
        print(f"  train: {config.get('train', 'N/A')}")
        print(f"  val: {config.get('val', 'N/A')}")
        print(f"  test: {config.get('test', 'N/A')}")
        
        # 실제 폴더 구조 확인
        train_dir = dataset_path / "train" / "images"
        valid_dir = dataset_path / "valid" / "images"  
        val_dir = dataset_path / "val" / "images"
        test_dir = dataset_path / "test" / "images"
        
        print(f"\n📁 실제 폴더 구조:")
        print(f"  train/images: {'✅' if train_dir.exists() else '❌'}")
        print(f"  valid/images: {'✅' if valid_dir.exists() else '❌'}")
        print(f"  val/images: {'✅' if val_dir.exists() else '❌'}")
        print(f"  test/images: {'✅' if test_dir.exists() else '❌'}")
        
        # 경로 수정
        config['path'] = str(dataset_path.resolve())
        config['train'] = 'train/images'
        
        # val vs valid 확인
        if valid_dir.exists():
            config['val'] = 'valid/images'
            print(f"📝 val → valid로 수정")
        elif val_dir.exists():
            config['val'] = 'val/images'
            print(f"📝 val 경로 유지")
        else:
            print(f"⚠️ validation 폴더를 찾을 수 없습니다")
            return False
        
        # test 폴더 확인
        if test_dir.exists():
            config['test'] = 'test/images'
        else:
            # test가 없으면 valid를 test로도 사용
            config['test'] = config['val']
            print(f"📝 test 폴더가 없어 valid를 사용")
        
        # 백업 생성
        backup_file = yaml_file.with_suffix('.yaml.backup')
        if not backup_file.exists():
            with open(backup_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            print(f"💾 백업 생성: {backup_file}")
        
        # 수정된 YAML 저장
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"\n✅ YAML 수정 완료:")
        print(f"  path: {config['path']}")
        print(f"  train: {config['train']}")
        print(f"  val: {config['val']}")
        print(f"  test: {config['test']}")
        
        return True
        
    except Exception as e:
        print(f"❌ YAML 수정 실패: {e}")
        return False

def main():
    """독립 실행용"""
    dataset_path = input("📂 데이터셋 경로: ").strip()
    if not dataset_path:
        dataset_path = "/workspace01/team06/jonghui/model/snack_data"
    
    if fix_yaml_paths(dataset_path):
        print("\n🎉 YAML 경로 수정 완료!")
    else:
        print("\n❌ YAML 경로 수정 실패")

if __name__ == "__main__":
    main()