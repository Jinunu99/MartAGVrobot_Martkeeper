from collections import deque

class PathPlanner:
    def __init__(self, position_map):
        self.position_map = position_map             # AGV 위치 맵
        self.now_pos_x, self.now_pos_y = [5, 0]      # 현재 위치
        self.next_pos_x, self.next_pos_y = [0, 0]    # 다음 위치

        # 쇼핑 가능한 모든 위치 : [0, 1], [0, 3], [0, 5], [4, 1], [4, 3], [4, 5]

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
    
    print("남은 쇼핑 리스트")
    print(path_planner.get_shopping_list())

    print("AGV가 가야할 경로")
    print(path_planner.path_find())

    print("남은 쇼핑 리스트")
    print(path_planner.get_shopping_list())

    print("AGV가 가야할 경로")
    print(path_planner.path_find())
    
    print("남은 쇼핑 리스트")
    print(path_planner.get_shopping_list())
