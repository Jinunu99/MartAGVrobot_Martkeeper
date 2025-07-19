# main.py - 메인 실행 파일

"""
스낵 탐지 시스템 메인 실행 파일

사용법:
    python main.py

키보드 조작:
    'q': 종료
    'SPACE': 스크린샷
    's': 상태 확인
    '+/-': 신뢰도 조절
    'f': 안정화 모드 토글
"""

from detector import SnackDetector


def main():
    """메인 함수 - 간단한 실행"""
    print("🍪 스낵 탐지 시스템 시작")
    
    # 탐지기 생성 및 실행
    with SnackDetector() as detector:
        detector.run()


if __name__ == "__main__":
    main()