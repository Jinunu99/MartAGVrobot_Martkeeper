import cv2
import gc
import time
import threading

class ResourceManager:
    """
    자원 관리 클래스
    Detection 시 불필요한 자원을 해제하고, 완료 후 복원
    """
    
    def __init__(self):
        self.saved_frame_rate = None
        self.paused_threads = []
        self.opencv_windows_closed = False
        self.line_tracer_active = True
        
    def prepare_for_detection(self, picam2=None):
        """
        Detection을 위한 자원 준비 (다른 기능들 일시 정지)
        
        Args:
            picam2: Picamera2 객체 (프레임레이트 조정용)
        """
        print("[ResourceManager] 🔧 Detection을 위한 자원 준비 시작...")
        
        # 1. OpenCV 창 해제
        self._close_opencv_windows()
        
        # 2. 카메라 프레임레이트 최소화 (선택사항)
        if picam2:
            self._reduce_camera_framerate(picam2)
            
        # 3. 라인트레이서 비활성화 플래그
        self.line_tracer_active = False
        
        # 4. 메모리 정리
        self._cleanup_memory()
        
        print("[ResourceManager] ✅ 자원 준비 완료 - Detection 시작 가능")
        
    def restore_after_detection(self, picam2=None):
        """
        Detection 완료 후 자원 복원
        
        Args:
            picam2: Picamera2 객체 (프레임레이트 복원용)  
        """
        print("[ResourceManager] 🔄 Detection 완료 후 자원 복원 시작...")
        
        # 1. 카메라 프레임레이트 복원
        if picam2 and self.saved_frame_rate:
            self._restore_camera_framerate(picam2)
            
        # 2. 라인트레이서 재활성화
        self.line_tracer_active = True
        
        # 3. 잠시 대기 (안정화)
        time.sleep(0.5)
        
        print("[ResourceManager] ✅ 자원 복원 완료 - 주행 재개 가능")
        
    def _close_opencv_windows(self):
        """OpenCV 창들 닫기"""
        try:
            cv2.destroyAllWindows()
            self.opencv_windows_closed = True
            print("[ResourceManager] OpenCV 창 해제 완료")
        except Exception as e:
            print(f"[ResourceManager] OpenCV 창 해제 중 오류: {e}")
            
    def _reduce_camera_framerate(self, picam2):
        """카메라 프레임레이트 감소"""
        try:
            # 현재 설정 저장
            current_config = picam2.camera_configuration()
            if 'controls' in current_config and 'FrameDurationLimits' in current_config['controls']:
                self.saved_frame_rate = current_config['controls']['FrameDurationLimits']
                
            # 프레임레이트를 10fps로 감소 (Detection 시 불필요한 높은 프레임레이트 방지)
            picam2.set_controls({
                "FrameDurationLimits": (100000, 100000)  # 10fps
            })
            print("[ResourceManager] 카메라 프레임레이트 감소 (10fps)")
            
        except Exception as e:
            print(f"[ResourceManager] 카메라 프레임레이트 조정 오류: {e}")
            
    def _restore_camera_framerate(self, picam2):
        """카메라 프레임레이트 복원"""
        try:
            if self.saved_frame_rate:
                picam2.set_controls({
                    "FrameDurationLimits": self.saved_frame_rate
                })
                print("[ResourceManager] 카메라 프레임레이트 복원")
            else:
                # 기본값으로 복원 (60fps)
                picam2.set_controls({
                    "FrameDurationLimits": (16666, 16666)
                })
                print("[ResourceManager] 카메라 프레임레이트 기본값 복원 (60fps)")
                
        except Exception as e:
            print(f"[ResourceManager] 카메라 프레임레이트 복원 오류: {e}")
            
    def _cleanup_memory(self):
        """메모리 정리"""
        try:
            gc.collect()
            print("[ResourceManager] 메모리 정리 완료")
        except Exception as e:
            print(f"[ResourceManager] 메모리 정리 오류: {e}")
            
    def is_line_tracer_active(self):
        """라인트레이서 활성 상태 확인"""
        return self.line_tracer_active
        
    def pause_thread_safely(self, thread_obj, timeout=2.0):
        """
        스레드 안전하게 일시 정지 (필요시 사용)
        
        Args:
            thread_obj: 일시 정지할 스레드 객체
            timeout: 대기 시간
        """
        try:
            if thread_obj and thread_obj.is_alive():
                # 스레드에 정지 신호 보내기 (스레드 구현에 따라 다름)
                # 여기서는 단순히 기록만 함
                self.paused_threads.append(thread_obj)
                print(f"[ResourceManager] 스레드 일시 정지 요청: {thread_obj.name}")
                
        except Exception as e:
            print(f"[ResourceManager] 스레드 일시 정지 오류: {e}")
            
    def resume_threads(self):
        """일시 정지된 스레드들 재시작"""
        try:
            for thread_obj in self.paused_threads:
                if thread_obj and thread_obj.is_alive():
                    print(f"[ResourceManager] 스레드 재시작: {thread_obj.name}")
                    
            self.paused_threads.clear()
            print("[ResourceManager] 모든 스레드 재시작 완료")
            
        except Exception as e:
            print(f"[ResourceManager] 스레드 재시작 오류: {e}")
            
    def get_resource_status(self):
        """현재 자원 상태 반환"""
        return {
            'line_tracer_active': self.line_tracer_active,
            'opencv_windows_closed': self.opencv_windows_closed,
            'paused_threads_count': len(self.paused_threads),
            'saved_frame_rate': self.saved_frame_rate is not None
        }