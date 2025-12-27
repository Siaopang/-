import os
import sqlite3
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app)

def get_db_connection():
    db_path = os.path.join(base_dir, "books.db") 
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# --- [核心升級] 抓取更多 Metadata ---
def fetch_google_books(keyword):
    print(f"搜尋 Google API: {keyword}")
    if not keyword: return []
    
    url = f"https://www.googleapis.com/books/v1/volumes?q={keyword}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            books = []
            for item in data.get("items", [])[:10]:
                info = item.get("volumeInfo", {})
                
                # ISBN 處理
                isbn = "無ISBN"
                identifiers = info.get('industryIdentifiers', [])
                for ident in identifiers:
                    if ident['type'] == 'ISBN_13':
                        isbn = ident['identifier']
                        break
                    elif ident['type'] == 'ISBN_10':
                        isbn = ident['identifier']
                
                # --- 新增欄位抓取 ---
                subjects = info.get('categories', [])
                subject_str = ", ".join(subjects) if subjects else "未分類"

                desc = info.get('description', '暫無摘要')
                

                book = {
                    "id": None, 
                    "title": info.get("title", "未知名稱"),
                    "author": ", ".join(info.get("authors", ["未知作者"])),
                    "isbn": isbn,
                    "publisher": info.get("publisher", "未知出版社"), 
                    "pub_date": info.get("publishedDate", "未知日期"), 
                    "description": desc,                               
                    "subject": subject_str,                            
                    "image_url": info.get('imageLinks', {}).get('smallThumbnail', ''),
                    "source": "Google Books API"
                }
                books.append(book)
            return books
    except Exception as e:
        print(f"API 錯誤: {e}")
        return []
    return []

@app.route("/")
def home():
    return render_template("index.html")

# --- 讀取所有書 ---
@app.route("/books")
def get_all_books():
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM books ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    books = []
    for row in rows:
        books.append({
            "id": row['id'],
            "title": row['title'],
            "author": row['author'],
            "isbn": row['isbn'],
            "publisher": row['publisher'],   
            "pub_date": row['pub_date'],     
            "description": row['description'], 
            "subject": row['subject'],       
            "image_url": row['image_url'],   
            "source": "館藏"
        })
    return jsonify(books)

# --- 搜尋功能 ---
@app.route("/search")
def search():
    keyword = request.args.get("keyword", "").strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 同時搜尋 publisher 或 subject
    sql = """
    SELECT *
    FROM books
    WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? OR publisher LIKE ?
    """
    like = f"%{keyword}%"
    cursor.execute(sql, (like, like, like, like))
    local_results = []
    for row in cursor.fetchall():
        local_results.append({
            "id": row['id'],
            "title": row['title'],
            "author": row['author'],
            "isbn": row['isbn'],
            "publisher": row['publisher'],
            "pub_date": row['pub_date'],
            "description": row['description'],
            "subject": row['subject'],
            "image_url": row['image_url'],
            "source": "館藏"
        })
    conn.close()

    local_isbns = [book['isbn'] for book in local_results if book['isbn'] != '無ISBN']

    external_results = []
    if keyword: 
        google_books = fetch_google_books(keyword)
        for book in google_books:
            if book['isbn'] not in local_isbns:
                external_results.append(book)

    return jsonify(local_results + external_results)

# --- 新增書籍 ---
@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM books WHERE isbn = ? AND isbn != '無ISBN'", (data.get('isbn'),))
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "這本書已經在館藏裡囉！"}), 400

        # 寫入所有欄位
        sql = """
            INSERT INTO books (title, author, isbn, publisher, pub_date, description, subject, image_url) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        vals = (
            data.get('title'),
            data.get('author'),
            data.get('isbn'),
            data.get('publisher'),
            data.get('pub_date'),
            data.get('description'),
            data.get('subject'),
            data.get('image_url')
        )
        cursor.execute(sql, vals)
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"成功！《{data.get('title')}》已加入館藏。"})

    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = ?", (data.get('id'),))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "刪除成功！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)