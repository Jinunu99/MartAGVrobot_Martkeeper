import time
import sys
import os

# 상위 vision 폴더의 모듈들 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vision.path_planner import DirectionResolver

class ManagerExecutor:
    """
    관리자 로봇용 경로 실행 클래스
    순환 구조 제거, 설정된 목표로만 이동
    """
    
    def __init__(self, planner, uart, tracer, start_dir='U'):
        self.planner = planner
        self.uart = uart
        self.tracer = tracer
        self.current_dir = start_dir
        self.command_queue = []
        self.executing = False
        self.target_reached = False  # 목표 도달 플래그
        
    def send_uart(self, msg):
        """UART 전송 처리"""
        if hasattr(self.uart, 'send'):
            self.uart.send(msg)
        else:
            self.uart.put(msg)
            
    def follow_line_until_aligned(self, frame_getter, timeout=1.2):
        """
        라인 중심 정렬
        """
        start_time = time.time()
        while True:
            frame = frame_getter()
            direction, offset, _, _, found = self.tracer.get_direction(frame)

            if direction == 'F' or time.time() - start_time > timeout:
                break

            self.send_uart(direction + '\n')
            time.sleep(0.05)
            
    def run_to_target(self, frame_getter):
        """
        설정된 목표까지 주행
        """
        path = self.planner.path_find_to_target()
        if not path:
            print("[ManagerExecutor] 경로 생성 실패 - 목표가 설정되지 않았거나 경로를 찾을 수 없음")
            return False

        print(f"\n[ManagerExecutor] 전체 경로: {path}")

        # 절대 방향 → 상대 명령어 변환
        abs_dirs = DirectionResolver.get_movement_directions(path)
        print(f"[ManagerExecutor] 절대 방향: {abs_dirs}")

        rel_cmds = DirectionResolver.convert_to_relative_commands(abs_dirs, self.current_dir)
        print(f"[ManagerExecutor] RC카 명령어: {rel_cmds}")

        # 현재 상태 출력
        status = self.planner.get_status()
        current_target = status['current_target']
        if current_target:
            print(f"[ManagerExecutor] 목표: {current_target}")
        print("--------------------------------------------------\n")

        self.command_queue = rel_cmds
        self.executing = True
        self.target_reached = False
        return True
        
    def execute_next_command(self, frame_getter):
        """
        다음 명령 실행
        """
        if not self.command_queue:
            if self.executing:
                print("[ManagerExecutor] 경로 주행 완료")
                self.executing = False
                self.target_reached = True
            return

        cmd = self.command_queue.pop(0)

        if cmd == 'F':
            self.send_uart('F\n')
            self.follow_line_until_aligned(frame_getter)

        elif cmd in ('L90', 'R90'):
            print(f"[ManagerExecutor] {cmd}: 먼저 전진 후 회전")
            self.send_uart('F\n')
            time.sleep(0.85)
            self.send_uart(cmd + '\n')
            print(f"[ManagerExecutor] 전송: {cmd}")
            time.sleep(0.9)

            # 회전 후 current_dir 갱신
            self.current_dir = self._get_next_direction(self.current_dir, cmd)

        else:
            self.send_uart(cmd + '\n')
            print(f"[ManagerExecutor] 전송: {cmd}")
            time.sleep(1)
            
            if cmd in ('L90', 'R90', 'B'):
                self.current_dir = self._get_next_direction(self.current_dir, cmd)
                
    def _get_next_direction(self, current_dir, cmd):
        """방향 전환 계산"""
        dirs = ['U', 'R', 'D', 'L']
        idx = dirs.index(current_dir)
        if cmd == 'R90':
            return dirs[(idx + 1) % 4]
        elif cmd == 'L90':
            return dirs[(idx - 1) % 4]
        elif cmd == 'B':
            return dirs[(idx + 2) % 4]
        else:
            return current_dir
            
    def plan_path_to_target(self, target_x, target_y, frame_getter):
        """
        특정 좌표로 경로 계획 및 시작
        
        Args:
            target_x, target_y: 목표 좌표
            frame_getter: 프레임 획득 함수
            
        Returns:
            bool: 경로 계획 성공 여부
        """
        self.planner.set_target(target_x, target_y)
        return self.run_to_target(frame_getter)
        
    def is_target_reached(self):
        """목표 도달 여부 확인"""
        return self.target_reached
        
    def reset_target_flag(self):
        """목표 도달 플래그 리셋"""
        self.target_reached = False
        
    def stop_execution(self):
        """실행 중지"""
        self.send_uart('S\n')
        self.command_queue.clear()
        self.executing = False
        print("[ManagerExecutor] 실행 중지")
        
    def is_executing(self):
        """실행 중 여부 확인"""
        return self.executing
        
    def get_status(self):
        """실행 상태 반환"""
        return {
            'executing': self.executing,
            'target_reached': self.target_reached,
            'commands_remaining': len(self.command_queue),
            'current_direction': self.current_dir
        }