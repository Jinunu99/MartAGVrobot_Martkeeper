import numpy as np
from collections import Counter

def print_final_report(observation_results):
    """15회 관찰 완료 후 최종 보고서 출력"""
    print("\n" + "="*60)
    print("📊 15회 관찰 완료 - 최종 보고서")
    print("="*60)
    
    if not observation_results:
        print("❌ 관찰 데이터가 없습니다.")
        return
    
    # 관찰 과정 요약
    print(f"📈 관찰 과정 요약:")
    print(f"  총 관찰 횟수: {len(observation_results)}회")
    
    # 총 객체 수 변화 분석
    total_counts = [result['total_count'] for result in observation_results]
    if total_counts:
        avg_total = sum(total_counts) / len(total_counts)
        std_total = np.std(total_counts)
        min_total = min(total_counts)
        max_total = max(total_counts)
        
        print(f"  총 객체 수 변화: {min_total}~{max_total}개 (평균: {avg_total:.1f}개)")
        
        if std_total < 1.0:
            stability_status = "매우 안정적"
        elif std_total < 2.0:
            stability_status = "안정적"
        else:
            stability_status = "변동적"
        print(f"  안정성: {stability_status} (표준편차: {std_total:.2f})")
    
    # 클래스별 상세 분석
    print(f"\n🏷️ 클래스별 빈도 분석:")
    
    # 모든 등장한 클래스 수집
    all_classes = set()
    for result in observation_results:
        all_classes.update(result['class_counts'].keys())
    
    if not all_classes:
        print("  탐지된 객체가 없습니다.")
        return
    
    for class_name in sorted(all_classes):
        # 각 클래스의 개수별 빈도 계산
        count_frequency = Counter()
        appearances = 0
        
        for result in observation_results:
            count = result['class_counts'].get(class_name, 0)
            count_frequency[count] += 1
            if count > 0:
                appearances += 1
        
        # 가장 빈번한 개수
        most_common = count_frequency.most_common(1)[0]
        most_frequent_count = most_common[0]
        frequency = most_common[1]
        
        # 브랜드_제품명까지 표시
        name_parts = class_name.split('_')
        if len(name_parts) >= 2:
            display_name = f"{name_parts[0]}_{name_parts[1]}"
        else:
            display_name = class_name
        
        if most_frequent_count > 0:
            frequency_ratio = frequency / len(observation_results)
            appearance_ratio = appearances / len(observation_results)
            
            # 안정성 평가
            if frequency_ratio >= 0.8:
                stability_icon = "✅"
                stability_text = "매우 안정"
            elif frequency_ratio >= 0.6:
                stability_icon = "🟡"
                stability_text = "안정"
            else:
                stability_icon = "⚠️"
                stability_text = "불안정"
            
            print(f"  {stability_icon} {display_name}:")
            print(f"    최종 개수: {most_frequent_count}개")
            print(f"    빈도: {frequency}/{len(observation_results)}회 ({frequency_ratio:.2f})")
            print(f"    등장률: {appearances}/{len(observation_results)}회 ({appearance_ratio:.2f})")
            print(f"    안정성: {stability_text}")
            
            # 개수 변화 패턴 표시
            all_counts = [result['class_counts'].get(class_name, 0) for result in observation_results]
            unique_counts = sorted(set(all_counts))
            if len(unique_counts) > 1:
                count_pattern = ", ".join([f"{c}개×{all_counts.count(c)}" for c in unique_counts if c >= 0])
                print(f"    변화 패턴: {count_pattern}")
    
    print("="*60)