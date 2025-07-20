#!/usr/bin/env python3
"""
coordinate_normalizer.py
기존 라벨 파일들의 좌표 정밀도를 6자리로 통일하는 독립 도구

사용법:
1. 전처리 전에 한번 실행
2. 4자리→6자리, 9자리→6자리로 정규화
3. 원본 백업 자동 생성
"""

import shutil
from pathlib import Path
import time

class CoordinateNormalizer:
    def __init__(self, dataset_path):
        self.dataset_path = Path(dataset_path)
        
    def analyze_precision(self):
        """현재 라벨들의 정밀도 분석"""
        print("📊 좌표 정밀도 분석 중...")
        
        precision_stats = {}
        total_files = 0
        total_coords = 0
        
        for split in ["train", "val", "valid", "test"]:
            labels_dir = self.dataset_path / split / "labels"
            
            if not labels_dir.exists():
                continue
                
            print(f"📁 {split} 분석 중...")
            
            for label_file in labels_dir.glob("*.txt"):
                try:
                    with open(label_file, 'r') as f:
                        lines = f.readlines()
                    
                    total_files += 1
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                # 좌표 4개 체크
                                coords = parts[1:5]
                                
                                for coord_str in coords:
                                    total_coords += 1
                                    
                                    # 소수점 자릿수 계산
                                    if '.' in coord_str:
                                        decimal_places = len(coord_str.split('.')[1])
                                    else:
                                        decimal_places = 0
                                    
                                    precision_stats[decimal_places] = precision_stats.get(decimal_places, 0) + 1
                                    
                            except (ValueError, IndexError):
                                continue
                                
                except Exception as e:
                    print(f"⚠️ 분석 오류 {label_file.name}: {e}")
                    continue
        
        print(f"\n📈 정밀도 분석 결과:")
        print(f"  📄 총 파일: {total_files}개")
        print(f"  📐 총 좌표: {total_coords}개")
        print(f"\n  정밀도별 분포:")
        
        for precision in sorted(precision_stats.keys()):
            count = precision_stats[precision]
            percentage = (count / total_coords) * 100 if total_coords > 0 else 0
            
            if precision <= 3:
                status = "🔴 부족"
            elif precision == 4:
                status = "🟡 최소"
            elif precision == 5:
                status = "🟢 양호"
            elif precision == 6:
                status = "✅ 최적"
            elif precision <= 8:
                status = "🟣 과도"
            else:
                status = "❌ 불필요"
            
            print(f"    {precision}자리: {count:6,}개 ({percentage:5.1f}%) {status}")
        
        # 권장사항
        needs_normalization = any(p != 6 for p in precision_stats.keys())
        
        if needs_normalization:
            print(f"\n💡 권장사항:")
            
            low_precision = sum(count for p, count in precision_stats.items() if p < 5)
            high_precision = sum(count for p, count in precision_stats.items() if p > 7)
            
            if low_precision > 0:
                print(f"  📐 저정밀도 ({low_precision:,}개): 320 해상도에서 문제 가능")
            if high_precision > 0:
                print(f"  📈 고정밀도 ({high_precision:,}개): 불필요한 정밀도")
            
            print(f"  ✅ 6자리 통일 권장")
        else:
            print(f"\n✅ 모든 좌표가 이미 6자리 정밀도입니다!")
        
        return precision_stats, needs_normalization
    
    def normalize_coordinates(self, target_precision=6):
        """좌표를 지정된 정밀도로 정규화"""
        print(f"\n📐 좌표 정밀도를 {target_precision}자리로 정규화 중...")
        
        # 백업 생성
        backup_dir = self.dataset_path / "labels_backup_precision"
        if not backup_dir.exists():
            print("💾 라벨 백업 생성...")
            for split in ["train", "val", "valid", "test"]:
                src_labels = self.dataset_path / split / "labels"
                if src_labels.exists():
                    dst_labels = backup_dir / split
                    shutil.copytree(src_labels, dst_labels)
            print(f"✅ 백업 생성: {backup_dir}")
        
        total_files = 0
        normalized_files = 0
        total_coords = 0
        normalized_coords = 0
        
        for split in ["train", "val", "valid", "test"]:
            labels_dir = self.dataset_path / split / "labels"
            
            if not labels_dir.exists():
                continue
                
            print(f"📁 {split} 정규화 중...")
            
            for label_file in labels_dir.glob("*.txt"):
                try:
                    with open(label_file, 'r') as f:
                        lines = f.readlines()
                    
                    total_files += 1
                    new_lines = []
                    file_changed = False
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                class_id = int(parts[0])
                                x, y, w, h = map(float, parts[1:5])
                                
                                total_coords += 4
                                
                                # 원본 정밀도 체크
                                original_precision = []
                                for coord_str in parts[1:5]:
                                    if '.' in coord_str:
                                        original_precision.append(len(coord_str.split('.')[1]))
                                    else:
                                        original_precision.append(0)
                                
                                # 정규화 필요한지 체크
                                if any(p != target_precision for p in original_precision):
                                    file_changed = True
                                    normalized_coords += 4
                                
                                # 새 라인 생성 (target_precision 자리)
                                format_str = f"{{}} {{:.{target_precision}f}} {{:.{target_precision}f}} {{:.{target_precision}f}} {{:.{target_precision}f}}"
                                new_line = format_str.format(class_id, x, y, w, h)
                                new_lines.append(new_line)
                                
                            except (ValueError, IndexError):
                                # 잘못된 형식은 그대로 유지
                                new_lines.append(line)
                        else:
                            # 5개 미만의 파트는 그대로 유지
                            new_lines.append(line)
                    
                    # 파일이 변경된 경우에만 저장
                    if file_changed:
                        with open(label_file, 'w') as f:
                            f.write('\n'.join(new_lines) + '\n')
                        normalized_files += 1
                    
                    if total_files % 100 == 0:
                        print(f"  📈 처리: {total_files}개 파일, {normalized_files}개 정규화")
                        
                except Exception as e:
                    print(f"⚠️ 정규화 오류 {label_file.name}: {e}")
                    continue
        
        print(f"\n✅ 좌표 정규화 완료!")
        print(f"  📄 총 파일: {total_files}개")
        print(f"  📝 정규화된 파일: {normalized_files}개")
        print(f"  📐 총 좌표: {total_coords:,}개")
        print(f"  🔄 정규화된 좌표: {normalized_coords:,}개")
        print(f"  💾 백업 위치: {backup_dir}")
        
        return normalized_files, normalized_coords
    
    def validate_normalization(self, target_precision=6):
        """정규화 결과 검증"""
        print(f"\n🔍 정규화 결과 검증...")
        
        valid_files = 0
        invalid_files = 0
        sample_errors = []
        
        for split in ["train", "val", "valid", "test"]:
            labels_dir = self.dataset_path / split / "labels"
            
            if not labels_dir.exists():
                continue
            
            for label_file in labels_dir.glob("*.txt"):
                try:
                    with open(label_file, 'r') as f:
                        lines = f.readlines()
                    
                    file_valid = True
                    
                    for line_idx, line in enumerate(lines):
                        line = line.strip()
                        if not line:
                            continue
                            
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                # 좌표 정밀도 체크
                                coords = parts[1:5]
                                
                                for coord_str in coords:
                                    if '.' in coord_str:
                                        decimal_places = len(coord_str.split('.')[1])
                                        if decimal_places != target_precision:
                                            file_valid = False
                                            if len(sample_errors) < 5:
                                                sample_errors.append(f"{label_file.name}:{line_idx+1} -> {coord_str} ({decimal_places}자리)")
                                            break
                                
                                if not file_valid:
                                    break
                                    
                            except (ValueError, IndexError):
                                continue
                    
                    if file_valid:
                        valid_files += 1
                    else:
                        invalid_files += 1
                        
                except Exception as e:
                    invalid_files += 1
                    continue
        
        total_files = valid_files + invalid_files
        success_rate = (valid_files / total_files) * 100 if total_files > 0 else 0
        
        print(f"📊 검증 결과:")
        print(f"  ✅ 올바른 파일: {valid_files}개")
        print(f"  ❌ 문제 파일: {invalid_files}개")
        print(f"  📈 성공률: {success_rate:.1f}%")
        
        if sample_errors:
            print(f"\n⚠️ 문제 샘플:")
            for error in sample_errors:
                print(f"    {error}")
        
        if success_rate >= 99:
            print(f"🎉 정규화 성공!")
        elif success_rate >= 95:
            print(f"✅ 정규화 거의 완료 (일부 수동 확인 필요)")
        else:
            print(f"⚠️ 정규화에 문제가 있습니다. 다시 확인하세요.")
        
        return success_rate >= 95
    
    def run_normalization(self, target_precision=6):
        """전체 정규화 실행"""
        print("📐 YOLO 라벨 좌표 정밀도 정규화 도구")
        print("=" * 50)
        print(f"🎯 목표: {target_precision}자리 정밀도 통일")
        print(f"📂 데이터셋: {self.dataset_path}")
        
        start_time = time.time()
        
        # 1. 현재 상태 분석
        precision_stats, needs_normalization = self.analyze_precision()
        
        if not needs_normalization:
            print(f"\n🎉 이미 모든 좌표가 {target_precision}자리입니다!")
            return True
        
        # 2. 사용자 확인
        proceed = input(f"\n📐 {target_precision}자리로 정규화하시겠습니까? (Y/n): ").strip().lower()
        if proceed not in ['', 'y', 'yes']:
            print("❌ 정규화 취소됨")
            return False
        
        # 3. 정규화 실행
        normalized_files, normalized_coords = self.normalize_coordinates(target_precision)
        
        # 4. 결과 검증
        validation_success = self.validate_normalization(target_precision)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"\n🎊 좌표 정밀도 정규화 완료!")
        print(f"⏱️ 소요 시간: {elapsed:.1f}초")
        print(f"📝 정규화된 파일: {normalized_files}개")
        print(f"📐 정규화된 좌표: {normalized_coords:,}개")
        print(f"✅ 검증 결과: {'성공' if validation_success else '일부 문제'}")
        
        if validation_success:
            print(f"\n💡 이제 전처리를 안전하게 실행할 수 있습니다!")
        else:
            print(f"\n⚠️ 일부 파일에 문제가 있습니다. 수동 확인 권장")
        
        return validation_success

def main():
    """독립 실행용"""
    print("📐 YOLO 라벨 좌표 정밀도 정규화 도구")
    print("=" * 50)
    
    dataset_path = input("📂 데이터셋 경로: ").strip()
    if not dataset_path:
        dataset_path = "/workspace01/team06/jonghui/model/snack_data"
    
    target_precision = input("🎯 목표 정밀도 [6]: ").strip()
    try:
        target_precision = int(target_precision) if target_precision else 6
        if target_precision < 1 or target_precision > 10:
            target_precision = 6
    except:
        target_precision = 6
    
    print(f"\n📊 설정:")
    print(f"  📂 데이터셋: {dataset_path}")
    print(f"  🎯 목표 정밀도: {target_precision}자리")
    
    normalizer = CoordinateNormalizer(dataset_path)
    
    try:
        success = normalizer.run_normalization(target_precision)
        
        if success:
            print(f"\n🎉 정규화 성공! 이제 전처리를 진행하세요.")
        else:
            print(f"\n⚠️ 정규화에 문제가 있습니다.")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()