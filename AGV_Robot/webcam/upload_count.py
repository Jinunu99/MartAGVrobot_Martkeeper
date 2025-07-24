""" 재고 탐지 결과 서버로 업로드 """

import requests
import json
from datetime import datetime
from webcam.config import SERVER_CONFIG

def send_to_server(final_results):
    """
    15회 관찰 완료 후 최종 결과를 서버로 전송
    
    Args:
        final_results: analyze_final_results()에서 생성한 결과 딕셔너리
    """
    print("\n🚀 서버로 결과 전송 시작...")
    
    if not final_results:
        print("❌ 전송할 데이터가 없습니다.")
        return False
    
    # 전송용 데이터 구성 (전체 클래스명 사용)
    upload_data = {}
    
    for class_name, result_info in final_results.items():
        count = result_info['count']
        upload_data[class_name] = count
        
        # 전송 데이터 미리보기
        name_parts = class_name.split('_')
        display_name = f"{name_parts[0]}_{name_parts[1]}" if len(name_parts) >= 2 else class_name
        print(f"  📦 {display_name}: {count}개")
    
    # JSON 데이터 구성
    payload = {
        "device_id": SERVER_CONFIG['device_id'],
        "timestamp": datetime.now().isoformat(),
        "products": upload_data
    }
    
    print(f"\n📡 서버 전송 중: {SERVER_CONFIG['url']}")
    print(f"📤 전송 데이터: {len(upload_data)}개 제품")
    
    try:
        # POST 요청 전송
        response = requests.post(
            url=SERVER_CONFIG['url'],
            json=payload,
            timeout=SERVER_CONFIG['timeout'],
            headers={'Content-Type': 'application/json'}
        )
        
        # 응답 처리
        if response.status_code == 200:
            print("✅ 서버 전송 성공!")
            print(f"  응답: {response.text}")
            return True
        else:
            print(f"❌ 서버 전송 실패: HTTP {response.status_code}")
            print(f"  오류 내용: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ 서버 연결 타임아웃 ({SERVER_CONFIG['timeout']}초)")
        return False
        
    except requests.exceptions.ConnectionError:
        print(f"🔌 서버 연결 실패: {SERVER_CONFIG['url']}")
        print("  네트워크 연결을 확인해주세요.")
        return False
        
    except Exception as e:
        print(f"⚠️ 예상치 못한 오류: {e}")
        return False

def test_server_connection():
    """서버 연결 테스트"""
    print(f"🔍 서버 연결 테스트: {SERVER_CONFIG['url']}")
    
    test_data = {
        "device_id": SERVER_CONFIG['device_id'],
        "timestamp": datetime.now().isoformat(),
        "products": {
            "test_product": 0
        }
    }
    
    try:
        response = requests.post(
            url=SERVER_CONFIG['url'],
            json=test_data,
            timeout=SERVER_CONFIG['timeout']
        )
        
        if response.status_code == 200:
            print("✅ 서버 연결 성공!")
            return True
        else:
            print(f"❌ 서버 응답 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False