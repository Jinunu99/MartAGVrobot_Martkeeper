import threading
import time
import cv2
import numpy as np
from picamera2 import Picamera2

# 기존 모듈들
from utils.buffer import tx_queue, rx_queue
from communication import UARTHandler
from line_tracer import LineTracer
from qr import QRReader, SharedFrame, qr_thread_func
from communication.agv_to_server import AgvToServer

# 관리자용 모듈들
from manager import ManagerPlanner, ManagerExecutor, DetectionController, ResourceManager

def start_uart():
    """UART 송수신 스레드 시작"""
    uart = UARTHandler(port='/dev/serial0', baudrate=19200)
    tx_t = threading.Thread(target=uart.uart_tx, daemon=True)
    rx_t = threading.Thread(target=uart.uart_rx, daemon=True)
    tx_t.start()
    rx_t.start()

def main_manager():
    """관리자 로봇 메인 함수 (순환 구조 제거)"""
    print("🤖 관리자 로봇 시작!")
    print("📋 Detection 포인트 도달 시 Detection 실행 모드")
    print("🎯 Detection 좌표: [0,1], [0,3], [0,5], [4,5], [4,3], [4,1]")
    print("-" * 60)

    # 1) UART 송수신 스레드 시작
    start_uart()

    # 2) 카메라 설정
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_video_configuration(
            main={"format": "RGB888", "size": (640, 480)},
            controls={"FrameDurationLimits": (16666, 16666)}  # 60fps 16666, 16666
        )
    )



    
    picam2.start()

    # 3) 기본 모듈들 초기화
    tracer = LineTracer()
    qr_reader = QRReader()
    agv_messenger = AgvToServer("managerAGV")
    agv_messenger.start()
    shared_frame = SharedFrame()

    # 4) QR 인식 스레드 시작
    qr_thread = threading.Thread(
        target=qr_thread_func,
        args=(shared_frame, qr_reader, agv_messenger),
        daemon=True
    )
    qr_thread.start()

    # 5) 맵 정보
    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    # 6) 관리자용 객체들 초기화
    planner = ManagerPlanner(grid)
    planner.set_now_position(6, 0)  # 시작 위치
    
    executor = ManagerExecutor(planner, tx_queue, tracer, start_dir='U')
    detection_controller = DetectionController()
    resource_manager = ResourceManager()

    # 상태 변수들
    last_detection_position = None  # 마지막 Detection 실행 위치
    detection_in_progress = False   # Detection 진행 중 플래그

    print(f"[MAIN] 관리자 로봇 초기화 완료")
    print(f"[MAIN] Detection 가능 좌표: {planner.get_detection_coordinates()}")

    try:
        while True:
            frame = picam2.capture_array()
            shared_frame.set(frame)

            # QR ID로 현재 위치 업데이트
            if agv_messenger.received_pos:
                print(f"[MAIN] 🎯 위치 수신됨! ({agv_messenger.position_x}, {agv_messenger.position_y})")
                x, y = agv_messenger.position_x, agv_messenger.position_y
                
                planner.set_now_position(x, y)
                current_position = [x, y]
                
                # Detection 위치 도달 체크 (이전에 실행하지 않은 위치에서만)
                if (planner.is_detection_point(x, y) and 
                    not detection_in_progress and
                    current_position != last_detection_position):
                    
                    print(f"[MAIN] 🎯 새로운 Detection 위치 도달: {current_position}")
                    
                    # Detection 시작
                    detection_in_progress = True
                    last_detection_position = current_position.copy()
                    
                    # 자원 절약을 위한 준비
                    resource_manager.prepare_for_detection(picam2)
                    executor.stop_execution()  # 현재 실행 중인 명령 중지
                    
                    # Detection 실행
                    print(f"[MAIN] 🔍 Detection 시작...")
                    detection_results = detection_controller.run_detection_cycle(max_wait_time=30)
                    
                    if detection_results:
                        print(f"[MAIN] ✅ Detection 완료!")
                        print(f"[MAIN] 📊 결과: {detection_results['count_summary']}")
                    else:
                        print(f"[MAIN] ❌ Detection 실패 또는 타임아웃")
                    
                    # 자원 복원
                    resource_manager.restore_after_detection(picam2)
                    
                    # 🔥 Detection 완료 후 라인을 따라가면서 조금씩 이동
                    print(f"[MAIN] 🚗 Detection 위치에서 라인을 따라 벗어나기...")
                    move_count = 0
                    max_moves = 8  # 최대 8번 시도
                    
                    while move_count < max_moves:
                        # 현재 프레임으로 라인 감지
                        current_frame = picam2.capture_array()
                        direction, offset, _, _, found = tracer.get_direction(current_frame)
                        
                        # 라인을 따라 이동
                        if found and direction in ['F', 'L', 'R']:
                            tx_queue.put(direction + "\n")
                            time.sleep(0.3)  # 짧은 이동
                            move_count += 1
                            print(f"[MAIN] 라인 추종 이동 {move_count}/{max_moves} - 방향: {direction}")
                        else:
                            # 라인이 없으면 조금만 전진
                            tx_queue.put("F\n")
                            time.sleep(0.2)
                            move_count += 1
                            print(f"[MAIN] 안전 전진 {move_count}/{max_moves}")
                    
                    tx_queue.put("S\n")  # 정지
                    time.sleep(0.3)
                    
                    # 🔥 추가: 프레임 버퍼 클리어 (카메라 안정화)
                    print(f"[MAIN] 📷 프레임 버퍼 클리어 중...")
                    for _ in range(5):  # 이전 프레임들 버리기
                        frame = picam2.capture_array()
                        time.sleep(0.02)
                    print(f"[MAIN] ✅ 프레임 버퍼 클리어 완료")

                    # 이제 라인트레이싱 재개 허용
                    detection_in_progress = False
                    print(f"[MAIN] 🔄 일반 주행 모드로 전환")
                
                agv_messenger.received_pos = False

            # 주행 명령 실행 (Detection 중이 아닐 때만)
            if resource_manager.is_line_tracer_active() and not detection_in_progress:
                # 라인트레이서 동작
                direction, offset, annotated, binary, found = tracer.get_direction(frame)
                
                # 실행 중인 명령이 있으면 처리
                if executor.is_executing():
                    # 한 칸 전진 완료 체크
                    if executor.command_queue and executor.command_queue[0] == 'F':
                        executor.command_queue.pop(0)

                    # 회전 명령 실행
                    if executor.command_queue and executor.command_queue[0] in ('R90', 'L90', 'B', 'B90'):
                        executor.execute_next_command(lambda: frame)

                # UART 송신 (일반 라인 추종)
                tx_queue.put(direction + "\n")
                
                # 상태 정보 출력
                status = planner.get_status()
                executor_status = executor.get_status()
                
                # print(f"[MAIN] Direction={direction}, Offset={offset}, Found={found}")
                # print(f"[MAIN] 현재위치: {status['current_position']}")
                # print(f"[MAIN] Detection포인트: {status['is_at_detection_point']}")
                # print(f"[MAIN] 실행중: {executor_status['executing']}, 남은명령: {executor_status['commands_remaining']}")
                
                # Detection 좌표 표시
                # if status['is_at_detection_point']:
                #     print(f"[MAIN] 💡 현재 Detection 가능 위치에 있음!")
            
            else:
                # Detection 중이므로 주행 정지
                tx_queue.put("S\n")

            # 디버깅 이미지 표시 (Detection 중이 아닐 때만)
            if resource_manager.is_line_tracer_active() and not detection_in_progress:
                combined = tracer.draw_debug(annotated, binary)
                
                # Detection 좌표 표시
                status = planner.get_status()
                if status['is_at_detection_point']:
                    cv2.putText(combined, "DETECTION POINT", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # cv2.imshow("Manager Robot - LineTracer", combined)

                # if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                #     break

            # time.sleep(0.015)

    except KeyboardInterrupt:
        print("\n[MAIN] 🛑 사용자 중단 요청")
    except Exception as e:
        print(f"\n[MAIN] ❌ 오류 발생: {e}")
    finally:
        print("[MAIN] 🏁 관리자 로봇 종료 중...")
        tx_queue.put("S\n")
        detection_controller.stop_detection()
        picam2.stop()
        cv2.destroyAllWindows()
        print("[MAIN] ✅ 관리자 로봇 종료 완료")

if __name__ == "__main__":
    main_manager()