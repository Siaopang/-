import os
import sqlite3

# 確保資料庫建立在正確的位置 (跟 app.py 同一層)
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, "books.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. 先刪除舊表 (如果存在)
cursor.execute("DROP TABLE IF EXISTS books")

# 2. 建立新表 (擴充欄位：符合 Dublin Core 精神)
# 新增了：publisher(出版者), pub_date(出版日), description(摘要), subject(主題)
cursor.execute("""
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT,
    isbn TEXT,
    publisher TEXT,
    pub_date TEXT,
    description TEXT,
    subject TEXT,
    image_url TEXT
)
""")

# 3. 預設資料 (這是給測試用的，你可以之後再手動刪除)
books = [
    (
        "資訊與圖書館學概論", 
        "王梅玲", 
        "978986000001", 
        "五南圖書", 
        "2020-01-01", 
        "本書介紹圖書館學的基礎理論與實務...", 
        "圖書館學", 
        ""
    ),
    (
        "Python 程式設計入門", 
        "廖雪峰", 
        "978986000002", 
        "歐萊禮", 
        "2023-05-20", 
        "適合初學者的 Python 入門書...", 
        "程式設計", 
        ""
    )
]

cursor.executemany(
    """
    INSERT INTO books (title, author, isbn, publisher, pub_date, description, subject, image_url) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    books
)

conn.commit()
conn.close()

print(f"資料庫已重建完成！位置：{db_path}")
print("包含欄位：Title, Author, ISBN, Publisher, PubDate, Description, Subject")