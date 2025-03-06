from sqlalchemy import create_engine, text

def test_connection():
    try:
        # 数据库连接字符串
        DATABASE_URI = "postgresql://xbjyf_user:pKaqOTvViL8ZVxFIJxcEuD2vuFE1CBvX@dpg-cv2on7lumphs739t5f6g-a.singapore-postgres.render.com/xbjyf"
        
        # 创建数据库引擎
        engine = create_engine(DATABASE_URI)
        
        # 尝试连接
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).fetchone()
            if result:
                print("数据库连接成功！")
            else:
                print("数据库连接失败：无法执行查询")
    except Exception as e:
        print(f"数据库连接错误：{str(e)}")

if __name__ == "__main__":
    test_connection()