import numpy as np

def print_count_report(count_history, current_counts, current_total):
    """개수 카운팅 보고서 출력"""
    print("\n" + "="*60)
    print("📊 Level 2 Multi-frame Voting 개수 파악 보고서")
    print("="*60)
    
    if not count_history:
        print("❌ 충분한 데이터가 없습니다.")
        return
    
    # 최근 데이터 분석
    recent_counts = list(count_history)[-20:]  # 최근 20프레임
    
    # 안정성 분석
    total_counts = [entry['total'] for entry in recent_counts]
    if total_counts:
        avg_total = sum(total_counts) / len(total_counts)
        std_total = np.std(total_counts)
        stability = 1.0 - (std_total / max(avg_total, 1))
        
        print(f"📈 총 객체 수 안정성:")
        print(f"  현재: {current_total}개")
        print(f"  평균: {avg_total:.1f}개")
        print(f"  표준편차: {std_total:.2f}")
        print(f"  안정성: {stability:.2f} ({'안정' if stability > 0.8 else '불안정'})")
    
    # 클래스별 상세 분석
    print(f"\n🏷️ 클래스별 개수 현황:")
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
                
                short_name = class_name.split('_')[0] if '_' in class_name else class_name
                status = "🟢" if class_stability > 0.8 else "🟡" if class_stability > 0.6 else "🔴"
                
                print(f"  {status} {short_name}: {count}개 (평균:{avg_count:.1f}, 안정성:{class_stability:.2f})")
    
    print(f"\n💡 추천사항:")
    if stability > 0.8:
        print("  ✅ 개수 파악이 안정적입니다. 현재 결과를 신뢰할 수 있습니다.")
    elif stability > 0.6:
        print("  🟡 개수가 약간 변동됩니다. 몇 초 더 관찰해보세요.")
    else:
        print("  ⚠️ 개수가 불안정합니다. 조명이나 카메라 각도를 조정해보세요.")
    
    print("="*60 + "\n")