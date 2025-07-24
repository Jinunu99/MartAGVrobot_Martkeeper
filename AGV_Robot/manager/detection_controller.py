import time
import sys
import os

# webcam.detection 모듈 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DetectionController:
    """
    Detection 기능을 제어하는 클래스
    webcam.detection 모듈과 연동하여 Detection 실행 및 결과 관리
    """
    
    def __init__(self):
        self.detector = None
        self.detection_active = False
        self.detection_results = None
        
    def start_detection(self):
        """
        Detection 시작
        """
        try:
            from webcam.detection import detect_start
            print("[DetectionController] 🔍 Detection 시작...")
            
            self.detector = detect_start()
            self.detection_active = True
            
            if self.detector:
                print("[DetectionController] Detection 모듈 초기화 완료")
                return True
            else:
                print("[DetectionController] ❌ Detection 모듈 초기화 실패")
                return False
                
        except ImportError as e:
            print(f"[DetectionController] ❌ webcam.detection 모듈 import 실패: {e}")
            return False
        except Exception as e:
            print(f"[DetectionController] ❌ Detection 시작 중 오류: {e}")
            return False
            
    def stop_detection(self):
        """
        Detection 중지
        """
        try:
            if self.detector:
                from webcam.detection import detect_stop
                detect_stop()
                print("[DetectionController] 🛑 Detection 중지")
                
            self.detection_active = False
            self.detector = None
            
        except Exception as e:
            print(f"[DetectionController] ❌ Detection 중지 중 오류: {e}")
            
    def is_detection_complete(self):
        """
        Detection 완료 여부 확인
        """
        if not self.detector:
            return False
            
        try:
            return self.detector.is_detection_complete()
        except Exception as e:
            print(f"[DetectionController] ❌ Detection 상태 확인 오류: {e}")
            return False
            
    def get_detection_results(self):
        """
        Detection 결과 가져오기
        """
        if not self.detector:
            return None
            
        try:
            if self.detector.is_detection_complete():
                # Detection 결과 함수들 호출
                final_results = self.detector.get_final_results()
                count_summary = self.detector.get_count_summary()
                detection_results = self.detector.get_detection_results()
                
                self.detection_results = {
                    'final_results': final_results,
                    'count_summary': count_summary,
                    'detection_results': detection_results,
                    'timestamp': time.time()
                }
                
                print("[DetectionController] 📋 Detection 결과 수집 완료")
                print(f"[DetectionController] 최종 결과: {final_results}")
                print(f"[DetectionController] 개수 요약: {count_summary}")
                
                return self.detection_results
            else:
                return None
                
        except Exception as e:
            print(f"[DetectionController] ❌ Detection 결과 가져오기 오류: {e}")
            return None
            
    def run_detection_cycle(self, max_wait_time=30):
        """
        Detection 전체 사이클 실행 (시작 → 대기 → 결과 수집 → 중지)
        
        Args:
            max_wait_time: 최대 대기 시간 (초)
            
        Returns:
            Detection 결과 또는 None
        """
        print("[DetectionController] 🔄 Detection 사이클 시작")
        
        # 1. Detection 시작
        if not self.start_detection():
            return None
            
        # 2. Detection 완료까지 대기
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            if self.is_detection_complete():
                print("[DetectionController] ✅ Detection 완료 감지")
                break
                
            print("[DetectionController] ⏳ Detection 진행 중...")
            time.sleep(1)
        else:
            print("[DetectionController] ⏰ Detection 타임아웃")
            self.stop_detection()
            return None
            
        # 3. 결과 수집
        results = self.get_detection_results()
        
        # 4. Detection 중지
        self.stop_detection()
        
        print("[DetectionController] 🏁 Detection 사이클 완료")
        return results
        
    def get_last_results(self):
        """마지막 Detection 결과 반환"""
        return self.detection_results
        
    def is_active(self):
        """Detection 활성 상태 확인"""
        return self.detection_active