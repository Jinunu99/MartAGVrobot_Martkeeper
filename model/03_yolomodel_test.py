import cv2
from ultralytics import YOLO
import os
import sys

def test_yolo_only():
    """YOLO 웹캠 테스트 - 윈도우 창 표시"""
    
    # 클래스 이름 정의 (data.yaml 기준)
    class_names = [
        'Alsaeuchip', 'BananaKick', 'CaramelCornMaple', 
        'Cheetos', 'CornChips', 'Gamjakkang', 'Jjanggu', 
        'JollyPong', 'Kkobugchip', 'Kkochgelang', 'Kkulkkwabaegi',
        'KokkalCorn', 'Koncho', 'Matdongsan', 'Ogamja',
        'Pocachip_Onion', 'Pocachip_Original', 'Postick', 'Saeukkang',
        'Sunchip', 'Swingchip', 'Yangpaling', 'konchi'
        ]

    
    # 모델 경로
    yolo_model_path = "/home/paper/workspace/MartAGVrobot_Martkeeper/model/best.pt"
    
    if not os.path.exists(yolo_model_path):
        print(f"❌ 모델을 찾을 수 없습니다: {yolo_model_path}")
        return
    
    # 모델 로드
    model = YOLO(yolo_model_path)
    print("✅ 모델 로드 완료")
    
    # 웹캠 시작
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ 웹캠을 열 수 없습니다!")
        return
    
    # 웹캠 설정
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("웹캠 테스트 시작")
    print("ESC: 종료, SPACE: 스크린샷 저장")
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ 프레임을 읽을 수 없습니다!")
                break
            
            frame_count += 1
            
            # YOLO 예측
            results = model(frame, conf=0.3, verbose=False)
            
            detection_count = 0
            detected_classes = []
            detected_names = []
            
            # 바운딩 박스 그리기
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    detection_count += len(boxes)
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        conf = float(box.conf[0].cpu().numpy())
                        cls = int(box.cls[0].cpu().numpy())
                        
                        # 클래스 이름 가져오기
                        class_name = class_names[cls] if cls < len(class_names) else f"Unknown{cls}"
                        
                        detected_classes.append(cls)
                        detected_names.append(class_name)
                        
                        # 신뢰도에 따른 색상 변경
                        if conf > 0.7:
                            color = (0, 255, 0)  # 녹색 (높은 신뢰도)
                        elif conf > 0.5:
                            color = (0, 255, 255)  # 노란색 (중간 신뢰도)
                        else:
                            color = (0, 165, 255)  # 주황색 (낮은 신뢰도)
                        
                        # 바운딩 박스
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # 라벨 텍스트
                        label = f"{class_name} {conf:.2f}"
                        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                        
                        # 라벨 배경
                        cv2.rectangle(frame, (x1, y1-label_height-10), (x1+label_width, y1), color, -1)
                        
                        # 라벨 텍스트 (검은색)
                        cv2.putText(frame, label, (x1, y1-5), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            # 상태 정보 표시
            status_y = 30
            cv2.putText(frame, f"Frame: {frame_count}", (10, status_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if detection_count > 0:
                status_text = f"Detected: {detection_count} snacks"
                cv2.putText(frame, status_text, (10, status_y + 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # 탐지된 과자 이름들
                unique_names = list(set(detected_names))
                if len(unique_names) <= 3:
                    names_text = f"Snacks: {', '.join(unique_names)}"
                else:
                    names_text = f"Snacks: {', '.join(unique_names[:3])}... (+{len(unique_names)-3})"
                
                cv2.putText(frame, names_text, (10, status_y + 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                
                # 콘솔에도 출력
                if frame_count % 30 == 0:  # 30프레임마다 출력
                    print(f"🎯 탐지된 과자: {', '.join(unique_names)}")
            else:
                cv2.putText(frame, "No snacks detected", (10, status_y + 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
                # 조작 안내
                cv2.putText(frame, "ESC: Exit, SPACE: Save, S: Show stats", (10, frame.shape[0]-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
            
            # 윈도우 창 표시 시도
            try:
                cv2.imshow('YOLO Webcam Test', frame)
                
                # 키 입력 처리
                key = cv2.waitKey(1) & 0xFF
                
                if key == 27:  # ESC
                    break
                elif key == ord(' '):  # SPACE
                    screenshot_name = f"screenshot_{frame_count}.jpg"
                    cv2.imwrite(screenshot_name, frame)
                    print(f"📸 스크린샷 저장: {screenshot_name}")
                elif key == ord('s') or key == ord('S'):  # S키
                    if detection_count > 0:
                        print(f"\n=== 현재 탐지 상태 ===")
                        print(f"프레임: {frame_count}")
                        print(f"탐지된 과자 수: {detection_count}")
                        for i, (cls, name, conf) in enumerate(zip(detected_classes, detected_names, [float(box.conf[0]) for result in results for box in result.boxes if result.boxes is not None])):
                            print(f"  {i+1}. {name} (신뢰도: {conf:.3f})")
                        print("=" * 25)
                
            except cv2.error as e:
                print(f"❌ OpenCV GUI 오류: {e}")
                print("GUI 지원이 없습니다. 이미지 파일로 저장합니다.")
                
                # GUI가 안되면 파일로 저장
                cv2.imwrite("latest_frame.jpg", frame)
                if detection_count > 0:
                    cv2.imwrite(f"detection_{frame_count}.jpg", frame)
                    print(f"🎯 Frame {frame_count}: {detection_count}개 객체 탐지됨 → detection_{frame_count}.jpg")
                else:
                    print(f"❌ Frame {frame_count}: 탐지 안됨")
                
                import time
                time.sleep(1)  # 1초 대기
            
    except KeyboardInterrupt:
        print("\n프로그램 종료")
    except Exception as e:
        print(f"오류 발생: {e}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("웹캠 테스트 완료")

def check_gui_support():
    """GUI 지원 확인"""
    try:
        # 테스트 윈도우 생성 시도
        test_img = cv2.imread('/dev/null')  # 빈 이미지
        if test_img is None:
            import numpy as np
            test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        cv2.imshow('Test', test_img)
        cv2.waitKey(1)
        cv2.destroyAllWindows()
        print("✅ OpenCV GUI 지원됨")
        return True
    except cv2.error:
        print("❌ OpenCV GUI 지원 안됨")
        print("해결 방법:")
        print("1. sudo apt install libgtk2.0-dev pkg-config")
        print("2. pip uninstall opencv-python && pip install opencv-python")
        print("3. export DISPLAY=:0 (SSH 사용 시)")
        return False

if __name__ == "__main__":
    print("=== OpenCV GUI 지원 확인 ===")
    gui_supported = check_gui_support()
    
    print("\n=== YOLO 웹캠 테스트 시작 ===")
    test_yolo_only()