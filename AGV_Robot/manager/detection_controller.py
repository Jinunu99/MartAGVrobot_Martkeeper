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
        
        # DB 연결 설정 (recv_from_agv.py와 동일한 패턴)
        self.db_config = {
            'user': 'root',
            'password': '1234',
            'host': '100.123.1.124',
            'database': 'qr_reader'  # 기본값, 필요시 manager_db로 변경
        }
        
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
                # Detection 결과 함수들 호출 (존재하는 메서드만 사용)
                final_results = self.detector.get_final_results()
                count_summary = self.detector.get_count_summary()
                
                self.detection_results = {
                    'final_results': final_results,
                    'count_summary': count_summary,
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

        # Detection 결과 처리 (MQTT 전송 + DB 저장)
        if results and 'count_summary' in results:
            print(f"[DetectionController] 🎯 Detection 결과 처리: {results['count_summary']}")
            
            # MQTT 전송
            self._send_detection_to_mqtt(results['count_summary'])
            
            # DB 저장
            self._save_detection_to_db(results['count_summary'])
        else:
            print("[DetectionController] ❌ Detection 결과 없음 - 처리 건너뜀")
        
        # 4. Detection 중지
        self.stop_detection()
        
        print("[DetectionController] 🏁 Detection 사이클 완료")
        return results

    def _send_detection_to_mqtt(self, count_summary):
        """Detection 결과를 MQTT로 전송"""
        print(f"[DetectionController] 📡 MQTT 전송 시작...")
        print(f"[DetectionController] 전송할 데이터: {count_summary}")
        
        try:
            import paho.mqtt.client as mqtt
            import json
            
            # MQTT 클라이언트 생성
            client = mqtt.Client(client_id="DetectionController")
            print(f"[DetectionController] MQTT 클라이언트 생성 완료")
            
            # 브로커 연결
            client.connect("localhost", 1883, 60)
            print(f"[DetectionController] MQTT 브로커 연결 완료")
            
            # MQTT 데이터 구성
            mqtt_data = {
                "QR_info": "detection_complete",
                "snack_num": count_summary  # {'haetae_Osajjeu_60G': 1}
            }
            
            print(f"[DetectionController] 📦 MQTT 메시지 구성: {mqtt_data}")
            
            # managerAGV로 전송
            topic = "agv/managerAGV/qr_id"
            result = client.publish(topic, json.dumps(mqtt_data))
            
            print(f"[DetectionController] 📤 MQTT 전송 완료")
            print(f"[DetectionController] Topic: {topic}")
            print(f"[DetectionController] Message: {json.dumps(mqtt_data)}")
            print(f"[DetectionController] Result: {result}")
            
            client.disconnect()
            print(f"[DetectionController] MQTT 연결 종료")
            
        except ImportError as e:
            print(f"[DetectionController] ❌ MQTT 라이브러리 import 실패: {e}")
        except Exception as e:
            print(f"[DetectionController] ❌ MQTT 전송 실패: {e}")
            import traceback
            print(f"[DetectionController] 오류 상세: {traceback.format_exc()}")

    def _save_detection_to_db(self, count_summary):
        """Detection 결과를 DB에 저장"""
        print(f"[DetectionController] 💾 DB 저장 시작...")
        print(f"[DetectionController] 저장할 데이터: {count_summary}")
        
        # 제품명 매핑 테이블 (Detection 결과 → DB product_name)
        product_mapping = {
            'haetae_Osajjeu_60G': 'haetae_Osajjeu_60G',
            'crown_ChocoHaim_142G': 'crown_ChocoHaim_142G', 
            'crown_Concho_66G': 'crown_Concho_66G',
            'crown_Potto_Cheese_Tart_322G': 'crown_Potto_Cheese_Tart_322G',
            'orion_Pocachip_Original_66G': 'orion_Pocachip_Original_66G',
            'orion_Gosomi_80G': 'orion_Gosomi_80G'
        }
        
        try:
            import mysql.connector
            
            # DB 연결 설정 (manager_db 우선 시도)
            db_config = {
                'user': 'root',
                'password': '1234',
                'host': '100.123.1.124',
                'database': 'manager_db'  # 옵션 2: manager_db 사용
            }
            
            print(f"[DetectionController] DB 연결 시도: manager_db")
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Detection 결과를 DB에 업데이트
            for detected_name, count in count_summary.items():
                # 매핑된 제품명 가져오기
                product_name = product_mapping.get(detected_name, detected_name)
                
                # snack_stock 테이블 업데이트
                update_query = """
                UPDATE snack_stock 
                SET product_count = %s 
                WHERE product_name = %s
                """
                
                cursor.execute(update_query, (count, product_name))
                print(f"[DetectionController] DB 업데이트: {product_name} → {count}개")
            
            # 변경사항 커밋
            conn.commit()
            print(f"[DetectionController] ✅ DB 저장 완료")
            
            cursor.close()
            conn.close()
            
        except ImportError as e:
            print(f"[DetectionController] ❌ mysql.connector import 실패: {e}")
        except Exception as e:
            print(f"[DetectionController] ❌ DB 저장 실패: {e}")
            import traceback
            print(f"[DetectionController] 오류 상세: {traceback.format_exc()}")
        
    def get_last_results(self):
        """마지막 Detection 결과 반환"""
        return self.detection_results
        
    def is_active(self):
        """Detection 활성 상태 확인"""
        return self.detection_active