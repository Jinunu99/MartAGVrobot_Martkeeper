from webcam.detection import detect_start, detect_stop
from webcam.config import OBSERVATION_CONFIG

def main_menu():
    print("🎯 15회 관찰 빈도 기반 판정 모드")
    print(f"  - 총 {OBSERVATION_CONFIG['max_observations']}회 관찰 실행")
    print(f"  - 빈도 기반 최종 판정")
    print(f"  - 관찰 완료 후 서버 전송용 JSON 출력")
    print("-"*60)
    
    print("webcam 탐지 시작...")
    detect_start()

if __name__ == "__main__":
    # python main.py로 직접 실행할 때는 메뉴 표시
    main_menu()