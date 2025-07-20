import pymysql

class DbConnect:
    def __init__(self, host, user, password, db, charset):
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.charset = charset

    # DB 내의 agv_info 테이블 업데이트 하는 부분
    def update_agv_position(self, agv_name, x, y):
        conn = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db,
            charset=self.charset
        )
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE agv_info SET pos_x = %s, pos_y = %s WHERE agv_name = %s"
                cursor.execute(sql, (x, y, agv_name))
            conn.commit()
        finally:
            conn.close()

    # DB 내의 snack_stock 테이블 업데이트 하는 부분
    def update_snack_stock(self, qr_info, stock_count):
        conn = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db,
            charset=self.charset
        )
        try:
            with conn.cursor() as cursor:
                sql = "UPDATE snack_stock SET stock_count = %s WHERE qr_info = %s"
                cursor.execute(sql, (stock_count, qr_info))
            conn.commit()
        finally:
            conn.close()
