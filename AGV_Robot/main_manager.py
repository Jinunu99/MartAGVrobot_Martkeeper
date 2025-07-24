from webcam.detection import detect_start, detect_stop
from webcam.config import OBSERVATION_CONFIG

def main_menu():
    print("🎯 관찰 빈도 기반 판정 모드")
    print(f"  - 총 {OBSERVATION_CONFIG['max_observations']}회 관찰 실행")
    print(f"  - 빈도 기반 최종 판정")
    print(f"  - 관찰 완료 후 결과 반환 함수 제공")
    print("-"*60)
    
    print("webcam 탐지 시작...")
    detector = detect_start()
    
    # 탐지 완료 후 결과 확인 예시
    if detector and detector.is_detection_complete():
        print("\n🎉 탐지 완료! 결과를 확인할 수 있습니다.")
        print("📋 결과 반환 함수 사용 방법:")
        print("  - get_final_results(): 최종 결과 반환")
        print("  - get_count_summary(): 개수 요약 반환")
        print("  - get_detection_results(): 현재 탐지 결과 반환")
        print("  - is_detection_complete(): 탐지 완료 여부 확인")
        print("\n💡 팀원은 이 함수들을 사용해서 서버에 업로드하세요!")

if __name__ == "__main__":
    # python main.py로 직접 실행할 때는 메뉴 표시
    main_menu()