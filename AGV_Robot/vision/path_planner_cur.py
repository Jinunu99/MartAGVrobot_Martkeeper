from collections import deque

class PathPlanner:
    def __init__(self, position_map):
        self.position_map = position_map             # AGV 위치 맵
        self.now_pos_x, self.now_pos_y = [6, 0]      # 현재 위치
        self.next_pos_x, self.next_pos_y = [0, 0]    # 다음 위치
        self.shopping_list = [[0, 1], [0, 3], [0, 5]]  # 쇼핑을 해야할 위치 (리스트)
        self.middle_path = []    # 현재 위치 ~ 다음 위치까지의 경로 (리스트)

    # 현재 위치 설정
    def set_now_position(self, x, y):
        self.now_pos_x = x
        self.now_pos_y = y

    # 장바구니를 담고 shopping_list의 위치들을 저장
    def set_shopping_list(self, snack_list):
        self.shopping_list = snack_list

    # 쇼핑을 해야할 위치를 반환
    def get_shopping_list(self):
        return self.shopping_list

    def bfs(self, target_x, target_y):
        print(f"[BFS] BFS 탐색 시작: 현재=({self.now_pos_x},{self.now_pos_y}) → 목표=({target_x},{target_y})")
        move = [[-1, 0], [0, 1], [1, 0], [0, -1]]   # AGV 이동방향 (상, 우, 하, 좌 순서로)
        
        n, m = len(self.position_map), len(self.position_map[0])
        visited = [[False]*m for _ in range(n)]         # 방문했는지 확인하는 맵
        prev = [[None]*m for _ in range(n)] # 방문 경로를 저장하는 맵 
        queue = deque()

        # 현재의 위치를 방문처리
        sx, sy = self.now_pos_x, self.now_pos_y
        queue.append((sx, sy))
        visited[sx][sy] = 1

        while queue:
            x, y = queue.popleft()

            if (x, y) == (target_x, target_y): # 목표 위치도달하면 경로를 복원
                path = []
                while (x, y) != (sx, sy):
                    path.append([x, y])
                    x, y = prev[x][y]
                path.append([sx, sy])
                path.reverse()
                return path

            for dx, dy in move:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < m and self.position_map[nx][ny] == 0:
                    if not visited[nx][ny]:
                        visited[nx][ny] = True
                        prev[nx][ny] = (x, y)
                        queue.append((nx, ny))
        
        return None # 경로가 없는 경우 None 반환

    # 쇼핑 리스트 중에 가장 최소 거리를 찾기 => 만약 쇼핑해야할 위치가 3개면 가장 짧은 거리의 위치 1개를 반환함
    def path_find(self):
        min_dist = float('inf') # 최소 거리
        best_path = None        # 최소 거리의 경로
        best_next_path = None   # AGV가 다음 가야할 과자의 위치
        for x, y in self.shopping_list:
            path = self.bfs(x, y)

            if path:
                if len(path) < min_dist: # 최소 경로라면
                    min_dist = len(path)
                    best_path = path
                    best_next_path = [x, y]
            
            else: # 반환된 경로가 없으면
                return None
        
        self.middle_path = best_path
        if best_next_path in self.shopping_list:
            self.shopping_list.remove(best_next_path)   # 가장 가까운 경로는 탐색했으니 삭제시켜주자
        self.now_pos_x, self.now_pos_y = best_next_path # 현재 위치를 업데이트     
        return self.middle_path # 가장 짧은 거리까지의 모든 경로를 반환함
    

# ================ 경로 방향 함수 전체 절대경로와 Rc상대방향============#
class DirectionResolver:
    """
    경로 리스트를 절대 방향(U/D/L/R) 및 RC카 상대 명령(F/L/R/B)으로 변환하는 도우미 클래스
    """
    @staticmethod
    def get_movement_directions(path):
        directions = []
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            dx, dy = x2 - x1, y2 - y1
            if dx == -1 and dy == 0:
                directions.append('U')
            elif dx == 1 and dy == 0:
                directions.append('D')
            elif dx == 0 and dy == -1:
                directions.append('L')
            elif dx == 0 and dy == 1:
                directions.append('R')
        return directions

    @staticmethod
    def get_relative_command(current_dir, next_dir):
        dirs = ['U', 'R', 'D', 'L']
        cur_idx = dirs.index(current_dir)
        next_idx = dirs.index(next_dir)
        diff = (next_idx - cur_idx) % 4
        if diff == 0:
            return 'F'
        elif diff == 1:
            return 'R'
        elif diff == 2:
            return 'B'
        elif diff == 3:
            return 'L'

    @staticmethod
    def convert_to_relative_commands(absolute_dirs, start_dir='U'):
        current_dir = start_dir
        commands = []
        for next_dir in absolute_dirs:
            cmd = DirectionResolver.get_relative_command(current_dir, next_dir)
            commands.append(cmd)
            current_dir = next_dir
        return commands


if __name__ == "__main__":
    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0]]

    # 현재위치
    now_pos_x, now_pos_y = [5, 0]

    path_planner = PathPlanner(grid)
    path_planner.set_now_position(now_pos_x, now_pos_y) # 현재 AGV의 위치를 설정
    path_planner.set_shopping_list([[0, 3], [0, 5], [0, 1]]) # 장바구니 리스트를 전달받아서


    # current_dir = 'U'  # 초기 방향: 위쪽

    # while path_planner.get_shopping_list():
    #     path = path_planner.path_find()
    #     if not path:
    #         print("❌ 경로를 찾을 수 없습니다.")
    #         break

    #     print("🔷 전체 경로:", path)
    #     abs_dirs = DirectionResolver.get_movement_directions(path)
    #     print("📍 절대 방향:", abs_dirs)

    #     # 상대방향 명령 생성 (이전 방향을 기반으로)
    #     rel_cmds = DirectionResolver.convert_to_relative_commands(abs_dirs, start_dir=current_dir)
    #     print("🧭 RC카 명령어:", rel_cmds)

    #     # RC카의 방향을 마지막으로 이동한 방향으로 갱신
    #     if abs_dirs:
    #         current_dir = abs_dirs[-1]

    #     print("남은 쇼핑 리스트:", path_planner.get_shopping_list())
    #     print("--------------------------------------------------")
