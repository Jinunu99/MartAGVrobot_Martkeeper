from webcam.detection import detect_start, detect_stop

def main_menu():
    print("webcam 탐지 시작")
    detect_start()





# # 개별 기능 직접 실행용
# def start_webcam_detection():
#     """웹캠 탐지만 바로 시작"""
#     detect_start()

if __name__ == "__main__":
    # python main.py로 직접 실행할 때는 메뉴 표시
    main_menu()