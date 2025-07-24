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
        self.command_queue = []
        self.executing = False
        self.turning = False  # 회전 중 플래그

    def stm32_format_command(self, cmd):
        if cmd in ('F', 'B', 'L90', 'R90'):
            return cmd
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

    def follow_line_until_aligned(self, frame_getter, timeout=1.2):
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
            return False

        # 절대 방향 → 상대 명령어 변환
        print(f"\n 전체 경로: {path}")

        abs_dirs = DirectionResolver.get_movement_directions(path)
        print(f" 절대 방향: {abs_dirs}")

        rel_cmds = DirectionResolver.convert_to_relative_commands(abs_dirs, self.current_dir)
        print(f" RC카 명령어: {rel_cmds}")

        # 방향 상태 갱신
        if abs_dirs:
            self.current_dir = abs_dirs[-1]

        print(f" 남은 쇼핑 리스트: {self.planner.get_shopping_list()}")
        print("--------------------------------------------------\n")

        self.command_queue = rel_cmds
        self.executing = True
        return True

    def execute_next_command(self, frame_getter):
        if not self.command_queue:
            if self.executing:
                print("[PathExecutor]  경로 주행 완료")
                self.executing = False
            return

        cmd = self.command_queue.pop(0)  # peek!

        if cmd == 'F': # F는 current_dir은 그대로 진행
            self.send_uart('F\n')
            self.follow_line_until_aligned(frame_getter)

        elif cmd in ('L90', 'R90'):
            print("[PathExecutor] L90/R90: 먼저 전진 후 회전")
            self.send_uart('F\n')
            time.sleep(0.5)
            self.send_uart(cmd+'\n')
            print(f"[PathExecutor] 전송: {cmd}")
            time.sleep(1)

            # 회전 후 current_dir 갱신
            self.current_dir = self._get_next_direction(self.current_dir, cmd)

        else:
            self.send_uart(cmd+'\n')
            print(f"[PathExecutor] 전송: {cmd}")
            time.sleep(1)
            # 기타 회전류 명령도 current_dir 갱신 필요 시 처리
            if cmd in ('L90', 'R90', 'B'):
                self.current_dir = self._get_next_direction(self.current_dir, cmd)

    def plan_new_path(self, frame_getter):
        if self.planner.get_shopping_list():
            success = self.run_to_next_target(frame_getter=frame_getter)
            if not success:
                print("[PathExecutor]  경로 생성 실패, 중단합니다.")