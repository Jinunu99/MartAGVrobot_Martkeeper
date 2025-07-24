import threading
import time
import cv2
import numpy as np
from picamera2 import Picamera2

from utils.buffer import tx_queue, rx_queue
from communication import UARTHandler
from line_tracer import LineTracer
from qr import QRReader, SharedFrame, qr_thread_func
from communication.agv_to_server import AgvToServer
from vision import PathExecutor, PathPlanner, DirectionResolver


def start_uart():
    uart = UARTHandler(port='/dev/serial0', baudrate=19200)
    tx_t = threading.Thread(target=uart.uart_tx, daemon=True)
    rx_t = threading.Thread(target=uart.uart_rx, daemon=True)
    tx_t.start()
    rx_t.start()

if __name__ == "__main__":
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
    qr_reader = QRReader()
    agv_messenger = AgvToServer("userAGV1")
    agv_messenger.start()
    shared_frame = SharedFrame()  

    # 4) QR 인식 스레드 시작
    qr_thread = threading.Thread(
        target=qr_thread_func,
        args=(shared_frame, qr_reader, agv_messenger),
        daemon=True
    )
    qr_thread.start()

    # 4) 맵 정보 및 주행 관련 객체 초기화
    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0]]

    planner = PathPlanner(grid)
    planner.set_now_position(6, 0)
    executor = PathExecutor(planner, tx_queue, tracer, start_dir='U')

    #초기 쇼핑 리스트 설정 (향후 MQTT 또는 GUI로 동적으로 설정 가능하도록 확장해야함)
    planner.set_shopping_list([
    [0, 0],  # 첫 번째 목표
    [0, 2]  # 두 번째 목표
    #[2, 2]   # 세 번째 목표
])

    try:
        while True:
            frame = picam2.capture_array()
            shared_frame.set(frame)  # 항상 최신 프레임을 QR 스레드에 넘겨줌

            # 라인트레이서 메서드 사용
            direction, offset, annotated, binary, found = tracer.get_direction(frame)

            # QR ID로 현재 위치를 업데이트할 수 있을 때만 주행
            # 위치가 수신되었으면 planner에 적용 후 주행
            if agv_messenger.received_pos:
                print("[MAIN DEBUG] 위치 수신됨! 경로 계산 시작")
                x, y = agv_messenger.position_x, agv_messenger.position_y
                print(f"[MAIN] 현재 위치로 설정: {x}, {y}")

                planner.set_now_position(x, y)
                # 👉 QR 도착(위치수신)시에만 shopping_list에서 pop!
                if [x, y] in planner.shopping_list:
                    planner.shopping_list.remove([x, y])
                    print(f"[MAIN] {x}, {y} 좌표 쇼핑리스트에서 제거")

                executor.plan_new_path(frame)
                agv_messenger.received_pos = False
     
                     # 한 칸 전진 완료(F pop)
                if executor.command_queue and executor.command_queue[0] == 'F':
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

            # UART 송신
            tx_queue.put(direction + "\n")

            # line_tracer 값 출력
            print(f"[MAIN] Direction={direction}, Offset={offset}, Found={found}")

            # 디버깅 이미지 표시
            # combined = tracer.draw_debug(annotated, binary)
            # cv2.imshow("LineTracer (Annotated + Binary)", combined)

            # if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
            #     break

            # time.sleep(0.015)

    except KeyboardInterrupt:
        pass
    finally:
        tx_queue.put("S\n")
        picam2.stop()
        cv2.destroyAllWindows()


# import threading
# import time
# import cv2
# import numpy as np
# from picamera2 import Picamera2

# from utils.buffer import tx_queue, rx_queue
# from line_tracer import LineTracer
# from qr import QRReader, SharedFrame, qr_thread_func
# from communication import UARTHandler, AgvToServer, AgvToControll
# from vision import PathExecutor, PathPlanner, DirectionResolver


# def start_uart():
#     uart = UARTHandler(port='/dev/serial0', baudrate=19200)
#     tx_t = threading.Thread(target=uart.uart_tx, daemon=True)
#     rx_t = threading.Thread(target=uart.uart_rx, daemon=True)
#     tx_t.start()
#     rx_t.start()

# if __name__ == "__main__":
#     # 1) UART 송수신 스레드 시작
#     start_uart()

#     # 2) 카메라 설정
#     picam2 = Picamera2()
#     picam2.configure(
#         picam2.create_video_configuration(
#             main={"format": "RGB888", "size": (640, 480)},
#             # controls={"FrameDurationLimits": (10000, 10000)}  # 100fps 시도
#             controls={"FrameDurationLimits": (16666, 16666)}  # 60fps 안정
#         )
#     )

#     picam2.start()

#     # 3) 라인트레이서, QR 리더 초기화
#     tracer = LineTracer()
#     qr_reader = QRReader()
#     agv_messenger = AgvToServer("userAGV1")
#     agv_messenger.start()
#     shared_frame = SharedFrame()  

#     # AGV <--> 컨트롤러 통신 부분
#     agv_to_controll = AgvToControll("userAGV1")
#     threading.Thread(target=agv_to_controll.start, daemon=True).start()


#     # 4) QR 인식 스레드 시작
#     qr_thread = threading.Thread(
#         target=qr_thread_func,
#         args=(shared_frame, qr_reader, agv_messenger),
#         daemon=True
#     )
#     qr_thread.start()

#     # 4) 맵 정보 및 주행 관련 객체 초기화
#     grid = [[0, 0, 0, 0, 0, 0, 0],
#             [0, 1, 0, 1, 0, 1, 0],
#             [0, 0, 0, 0, 0, 0, 0],
#             [0, 1, 0, 1, 0, 1, 0],
#             [0, 0, 0, 0, 0, 0, 0],
#             [0, 1, 1, 1, 1, 1, 0],
#             [0, 0, 0, 0, 0, 0, 0]]

#     planner = PathPlanner(grid)
#     planner.set_now_position(6, 0)
#     executor = PathExecutor(planner, tx_queue, tracer, start_dir='U')

#     #초기 쇼핑 리스트 설정 (향후 MQTT 또는 GUI로 동적으로 설정 가능하도록 확장해야함)
#     planner.set_shopping_list([
#     [0, 0],  # 첫 번째 목표
#     [0, 2]  # 두 번째 목표
#     #[0, 2]   # 세 번째 목표
# ])

#     try:
#         while True:
#             frame = picam2.capture_array()
#             shared_frame.set(frame)  # 항상 최신 프레임을 QR 스레드에 넘겨줌

#             # 라인트레이서 메서드 사용
#             direction, offset, annotated, binary, found = tracer.get_direction(frame)

#             # QR ID로 현재 위치를 업데이트할 수 있을 때만 주행
#             # 위치가 수신되었으면 planner에 적용 후 주행
#             if agv_messenger.received_pos:
#                 print("[MAIN DEBUG] 위치 수신됨! 경로 계산 시작")
#                 x, y = agv_messenger.position_x, agv_messenger.position_y
#                 print(f"[MAIN] 현재 위치로 설정: {x}, {y}")

#                 planner.set_now_position(x, y)
#                 #  QR 도착(위치수신)시에만 shopping_list에서 pop!
#                 if [x, y] in planner.shopping_list:
#                     planner.shopping_list.remove([x, y])
#                     print(f"[MAIN] {x}, {y} 좌표 쇼핑리스트에서 제거")

#                 executor.plan_new_path(frame)


#                 # 컨트롤러에 현재위치 (x, y)와 목표위치 (t_x, t_y)를 송신함
#                 t_x, t_y = planner.middle_path[-1]
#                 agv_to_controll.set_position(x, y, t_x, t_y)


#                 agv_messenger.received_pos = False
     
#                      # 한 칸 전진 완료(F pop)
#                 if executor.command_queue and executor.command_queue[0] == 'F':
#                     executor.command_queue.pop(0)

#                 # 회전류 명령(도착 후) 바로 실행
#                 if executor.command_queue and executor.command_queue[0] in ('R90', 'L90', 'B', 'B90'):
#                     executor.execute_next_command(frame)

#                 # 경로 완료 시, 새 경로 계획
#                 if not executor.command_queue:
#                     executor.plan_new_path(frame)

#             # 모든 목표를 다 돈 경우 완전 정지!
#             if not planner.get_shopping_list() and not executor.command_queue:
#                 print("[MAIN] 모든 목표 완료! RC카 정지")
#                 tx_queue.put("S\n")   # 정지 명령 (또는 UART 직접 send)
#                 break                # 또는 while 루프 종료

#             # UART 송신
#             tx_queue.put(direction + "\n")

#             # line_tracer 값 출력
#             print(f"[MAIN] Direction={direction}, Offset={offset}, Found={found}")

#             # 디버깅 이미지 표시
#             combined = tracer.draw_debug(annotated, binary)
#             cv2.imshow("LineTracer (Annotated + Binary)", combined)

#             if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
#                 break

#             # time.sleep(0.015)

#     except KeyboardInterrupt:
#         pass
#     finally:
#         tx_queue.put("S\n")
#         picam2.stop()
#         cv2.destroyAllWindows()

