import time
from .path_planner import DirectionResolver

class PathExecutor:
    """
    경로 기반으로 명령어를 생성하고 UART를 통해 RC카에 전달하는 클래스.
    LineTracer와 연동하여 'F' 명령 중 실시간 라인 중심 보정도 수행.
    """

    def __init__(self, planner, uart, tracer, start_dir='U'):
        """
        :param planner: PathPlanner 인스턴스
        :param uart: UARTHandler 또는 tx_queue 객체
        :param tracer: LineTracer 인스턴스
        :param start_dir: 초기 방향 (기본값 'U')
        """
        self.planner = planner
        self.uart = uart
        self.tracer = tracer
        self.current_dir = start_dir

    def stm32_format_command(self, cmd):
        """
        고수준 상대 명령어 ('F', 'L', 'R', 'B') → STM32용 명령 문자열로 변환
        """
        if cmd == 'F':
            return 'F'
        elif cmd == 'R':
            return 'R90'
        elif cmd == 'L':
            return 'L90'
        elif cmd == 'B':
            return 'B90'
        else:
            return 'S'

    def send_uart(self, msg):
        """
        UART 전송 처리 (UARTHandler.send() or queue.put())
        """
        if hasattr(self.uart, 'send'):
            self.uart.send(msg)
        else:
            self.uart.put(msg)

    def follow_line_until_aligned(self, frame_getter, timeout=2.0):
        """
        'F' 명령어 동안 라인트레이서를 이용해 라인을 따라가며 중심 보정
        :param frame_getter: 프레임을 리턴하는 함수 (예: picam2.capture_array)
        :param timeout: 최대 보정 시간
        """
        start_time = time.time()
        while True:
            frame = frame_getter()
            direction, offset, _, _, found = self.tracer.get_direction(frame)

            # 중심 정렬 성공 or 시간 초과 시 종료
            if direction == 'F' or time.time() - start_time > timeout:
                break

            self.send_uart(direction + '\n')
            time.sleep(0.05)

    def run_to_next_target(self, frame_getter):
        """
        PathPlanner를 기반으로 다음 목적지까지 주행 (자동 1타겟 수행)
        :param frame_getter: 카메라 프레임 가져오는 함수
        :return: True → 주행 성공, False → 경로 없음
        """
        path = self.planner.path_find()
        if not path:
            print("[PathExecutor] ❌ 경로 없음")
            return False

        # 절대 방향 → 상대 명령어 변환
        print(f"\n🔷 전체 경로: {path}")

        abs_dirs = DirectionResolver.get_movement_directions(path)
        print(f"📍 절대 방향: {abs_dirs}")

        rel_cmds = DirectionResolver.convert_to_relative_commands(abs_dirs, self.current_dir)
        print(f"🧭 RC카 명령어: {rel_cmds}")

        # 방향 상태 갱신
        if abs_dirs:
            self.current_dir = abs_dirs[-1]

        print(f"🧾 남은 쇼핑 리스트: {self.planner.get_shopping_list()}")
        print("--------------------------------------------------\n")

        # 명령어 순차 실행
        for cmd in rel_cmds:
            stm32_cmd = self.stm32_format_command(cmd)
            self.send_uart(stm32_cmd + '\n')
            print(f"[PathExecutor] 전송: {stm32_cmd}")

            if stm32_cmd == 'F':
                self.follow_line_until_aligned(frame_getter)
            else:
                time.sleep(1.5)  # 회전은 일정 시간 대기

        print("[PathExecutor] ✅ 경로 주행 완료")
        return True