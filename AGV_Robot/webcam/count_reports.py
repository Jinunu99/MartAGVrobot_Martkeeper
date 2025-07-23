import numpy as np

def print_count_report(count_history, current_counts, current_total):
    """개수 카운팅 보고서 출력 (터미널 최적화)"""
    print("\n" + "="*50)
    print("📊 Level 2 Multi-frame Voting 개수 파악 보고서")
    print("="*50)
    
    if not count_history:
        print("❌ 충분한 데이터가 없습니다.")
        return
    
    # 최근 데이터 분석
    recent_counts = list(count_history)[-15:]  # 20 → 15 (최적화)
    
    # 안정성 분석
    total_counts = [entry['total'] for entry in recent_counts]
    if total_counts:
        avg_total = sum(total_counts) / len(total_counts)
        std_total = np.std(total_counts)
        stability = 1.0 - (std_total / max(avg_total, 1))
        
        print(f"📈 총 객체 수 안정성:")
        print(f"  현재: {current_total}개, 평균: {avg_total:.1f}개")
        print(f"  안정성: {stability:.2f} ({'안정' if stability > 0.8 else '불안정'})")
    
    # 클래스별 상세 분석
    if current_counts:
        print(f"\n🏷️ 클래스별 개수:")
        for class_name, count in current_counts.items():
            if count > 0:
                # 최근 히스토리에서 해당 클래스 분석
                class_history = []
                for entry in recent_counts:
                    class_history.append(entry['classes'].get(class_name, 0))
                
                if class_history:
                    avg_count = sum(class_history) / len(class_history)
                    std_count = np.std(class_history)
                    class_stability = 1.0 - (std_count / max(avg_count, 1))
                    
                    # 브랜드_제품명까지 표시 (예: orion_Pocachip)
                    name_parts = class_name.split('_')
                    if len(name_parts) >= 2:
                        display_name = f"{name_parts[0]}_{name_parts[1]}"
                    else:
                        display_name = class_name
                    status = "✅" if class_stability > 0.8 else "⚠️" if class_stability > 0.6 else "❌"
                    
                    print(f"  {status} {display_name}: {count}개 (안정성: {class_stability:.2f})")
    
    # 간단한 추천사항
    print(f"\n💡 상태:")
    if stability > 0.8:
        print("  ✅ 개수 파악이 안정적입니다.")
    elif stability > 0.6:
        print("  ⚠️ 개수가 약간 변동됩니다. 더 관찰하세요.")
    else:
        print("  ❌ 개수가 불안정합니다. 조명/각도를 조정하세요.")
    
    print("="*50 + "\n")