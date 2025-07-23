# main.py
import time
from webcam import start_detect, stop_detect, get_results, is_running

def main():
    print("🍪 객체 검출 시스템 시작")
    
    # 검출 시작 (GUI 창 표시)
    if start_detect(show_window=True):
        print("✅ 검출 시작됨")
        
        try:
            # 메인 루프
            while is_running():
                time.sleep(2)
                
                # 결과 확인
                results = get_results()
                if results:
                    print(f"📊 객체 {results['total_count']}개 검출됨")
                
        except KeyboardInterrupt:
            print("\n사용자 중단")
        
        finally:
            stop_detect()
    
    else:
        print("❌ 검출 시작 실패")

if __name__ == "__main__":
    main()