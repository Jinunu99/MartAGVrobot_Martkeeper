import threading
import time
import cv2
import numpy as np
from picamera2 import Picamera2

from utils.buffer import tx_queue, rx_queue
from communication import UARTHandler, AgvToServer, AgvToControll
from line_tracer import LineTracer
# from qr import QRReader, SharedFrame, qr_thread_func
from aruco_marker import ArUcoReader, SharedFrame, aruco_thread_func
from vision import PathExecutor, PathPlanner, DirectionResolver

def start_uart():
    uart = UARTHandler(port='/dev/serial0', baudrate=19200)
    tx_t = threading.Thread(target=uart.uart_tx, daemon=True)
    rx_t = threading.Thread(target=uart.uart_rx, daemon=True)
    tx_t.start()
    rx_t.start()

if __name__ == "__main__":
    # 라인트레이싱 제어 플래그
    line_tracing_enabled = True
    prev_status_prefix = None
    
    # 1) UART 송수신 스레드 시작
    start_uart()

    # 2) 카메라 설정
    picam2 = Picamera2()
    picam2.configure(
        picam2.create_video_configuration(
            main={"format": "RGB888", "size": (640, 480)},
            # controls={"FrameDurationLimits": (10000, 10000)}  # 100fps 시도
            controls={"FrameDurationLimits": (16666, 16666)}  # 60fps 안정
        )
    )

    picam2.start()

    # 3) 라인트레이서, QR 리더 초기화
    tracer = LineTracer()
    # qr_reader = QRReader()
    aruco_reader = ArUcoReader()
    agv_messenger = AgvToServer("userAGV2")
    agv_messenger.start()
    shared_frame = SharedFrame()  

    agv_to_controll = AgvToControll("userAGV2")
    threading.Thread(target=agv_to_controll.start, daemon=True).start()

    # 4) QR 인식 스레드 시작
    aruco_thread = threading.Thread(
        target=aruco_thread_func,
        args=(shared_frame, aruco_reader, agv_messenger),
        daemon=True
    )
    aruco_thread.start()

    # 4) 맵 정보 및 주행 관련 객체 초기화
    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1]]

    planner = PathPlanner(grid)
    planner.set_now_position(6, 0)
    executor = PathExecutor(planner, tx_queue, tracer, start_dir='U')

    #초기 쇼핑 리스트 설정 (향후 MQTT 또는 GUI로 동적으로 설정 가능하도록 확장해야함)
#     planner.set_shopping_list([
#     [0, 0],  # 첫 번째 목표
#     [0, 2]  # 두 번째 목표
#     #[2, 2]   # 세 번째 목표
# ])

    while True:
        time.sleep(1)
        if agv_to_controll.shopping_list != None:
            print("확인 :", agv_to_controll.shopping_list)
            break

    shopping_list_temp = agv_to_controll.shopping_list
    shopping_list_temp.append([5, 6])

    # 경로를 검색하기전에 쇼핑리스트를 받아와야함
    planner.set_shopping_list(shopping_list_temp)

    try:
        while True:
            frame = picam2.capture_array()
            shared_frame.set(frame)  # 항상 최신 프레임을 QR 스레드에 넘겨줌

            # 라인트레이서 메서드 사용
            if line_tracing_enabled:
                direction, offset, annotated, binary, found = tracer.get_direction(frame)

                # UART 송신
                tx_queue.put(direction + "\n")

            # 상태 출력
            status_prefix = "[ACTIVE]" if line_tracing_enabled else "[STOPPED]"
            if status_prefix != prev_status_prefix:
                print(f"Line Tracing {status_prefix}")
                prev_status_prefix = status_prefix

            # QR ID로 현재 위치를 업데이트할 수 있을 때만 주행
            # 위치가 수신되었으면 planner에 적용 후 주행
            if agv_messenger.received_pos:
                print("[MAIN DEBUG] 위치 수신됨! 경로 계산 시작")
                x, y = agv_messenger.position_x, agv_messenger.position_y
                print(f"[MAIN] 현재 위치로 설정: {x}, {y}")
                
                # QR 인식되었으니 라인트레이싱 활성화
                line_tracing_enabled = True
    
                planner.set_now_position(x, y)
                # 👉 QR 도착(위치수신)시에만 shopping_list에서 pop!
                if [x, y] in planner.shopping_list:
                    planner.shopping_list.remove([x, y])
                    tx_queue.put("S\n")
                    agv_to_controll.set_position(x, y, t_x, t_y)
                    print(f"[MAIN] {x}, {y} 좌표 쇼핑리스트에서 제거")

                    while True:
                        if agv_to_controll.move_flag == True:
                            break

                executor.plan_new_path(frame)

                # 컨트롤러에 현재위치 (x, y)와 목표위치 (t_x, t_y)를 송신함
                t_x, t_y = planner.next_pos_x, planner.next_pos_y
                agv_to_controll.set_position(x, y, t_x, t_y)

                agv_messenger.received_pos = False
     
                    # 한 칸 전진 완료(F pop)
                if executor.command_queue and executor.command_queue[0] == 'F':
                    if len(executor.command_queue) == 1:
                        executor.command_queue.pop(0)

                # 회전류 명령(도착 후) 바로 실행
                if executor.command_queue and executor.command_queue[0] in ('R90', 'L90', 'B', 'B90'):
                    executor.execute_next_command(frame)

                # 경로 완료 시, 새 경로 계획
                if not executor.command_queue:
                    executor.plan_new_path(frame)

              # 모든 목표를 다 돈 경우 완전 정지!
                if not planner.get_shopping_list() and not executor.command_queue:
                    print("[MAIN] 모든 목표 완료! RC카 정지")
                    tx_queue.put("S\n")   # 정지 명령 (또는 UART 직접 send)
                    break                # 또는 while 루프 종료

            # line_tracer 값 출력
            # print(f"[MAIN] Direction={direction}, Offset={offset}, Found={found}")

            # 디버깅 이미지 표시
            # combined = tracer.draw_debug(annotated, binary)
            # cv2.imshow("LineTracer (Annotated + Binary)", combined)
            # cv2.imshow("frame", frame)

            # if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
            #     break

            # time.sleep(0.015)

    except KeyboardInterrupt:
        pass
    finally:
        tx_queue.put("S\n")
        picam2.stop()
        cv2.destroyAllWindows()