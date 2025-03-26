from flask import Flask, Blueprint, render_template, send_from_directory, url_for
import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import sqlite3
import shutil
from werkzeug.utils import safe_join
from pathlib import Path

# Khởi tạo Flask app và Blueprint
app = Flask(__name__)
readEpub_bp = Blueprint('readEpub', __name__)

# Cấu hình thư mục
UPLOAD_FOLDER = 'uploads'
EXTRACT_FOLDER = 'static/extracted'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

# Đường dẫn database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'book_draft.db')

# Đăng ký Blueprint
@readEpub_bp.route('/serve-image/<book_id>/<path:filename>')
def serve_image(book_id, filename):
    """Phục vụ ảnh từ thư mục trích xuất"""
    book_folder = os.path.join(EXTRACT_FOLDER, str(book_id))
    file_path = safe_join(book_folder, filename)
    if not file_path or not os.path.exists(file_path):
        print(f"Không tìm thấy ảnh: {file_path} (filename: {filename})")
        return "Ảnh không tồn tại", 404
    print(f"Phục vụ ảnh: {file_path}")
    return send_from_directory(book_folder, filename)

def get_epub_from_db(book_id):
    """Lấy dữ liệu EPUB BLOB và tiêu đề từ database theo book_id"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT fileEpub, title FROM book WHERE id = ?", (book_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0], result[1] if result else (None, None)
    except sqlite3.Error as e:
        raise Exception(f"Lỗi khi truy vấn database: {str(e)}")

def save_blob_to_file(blob_data, filename):
    """Lưu dữ liệu BLOB thành file tạm trong UPLOAD_FOLDER"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(filepath, "wb") as f:
            f.write(blob_data)
        return filepath
    except IOError as e:
        raise Exception(f"Lỗi khi lưu file tạm: {str(e)}")

def clean_book_folder(book_id):
    """Xóa thư mục trích xuất cũ của book_id nếu tồn tại"""
    book_folder = os.path.join(EXTRACT_FOLDER, str(book_id))
    if os.path.exists(book_folder):
        shutil.rmtree(book_folder, ignore_errors=True)

def extract_epub(filepath, book_id):
    """Trích xuất nội dung EPUB và trả về HTML cùng với style"""
    book_folder = os.path.join(EXTRACT_FOLDER, str(book_id))

    try:
        book = epub.read_epub(filepath)
        clean_book_folder(book_id)
        os.makedirs(book_folder, exist_ok=True)

        image_map = {}
        styles = []  # Lưu trữ các style từ EPUB
        full_content = []

        # Giai đoạn 1: Xây dựng image_map và trích xuất style
        for item in book.get_items():
            item_name = Path(item.get_name()).as_posix()
            if item.get_type() == ebooklib.ITEM_IMAGE:
                if item_name.startswith('OEBPS/'):
                    item_name = item_name.replace('OEBPS/', '')
                item_name_normalized = item_name.lower()
                img_path = os.path.join(book_folder, item_name)
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                with open(img_path, 'wb') as f:
                    f.write(item.get_content())
                image_url = url_for('readEpub.serve_image', book_id=book_id, filename=item_name)
                image_map[item_name_normalized] = image_url

            elif item.get_type() == ebooklib.ITEM_STYLE:
                # Trích xuất nội dung CSS từ file style
                css_content = item.get_content().decode('utf-8')
                styles.append(css_content)

        # Giai đoạn 2: Xử lý ITEM_DOCUMENT và thay thế src
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                # Trích xuất inline style từ thẻ <style> trong HTML
                for style_tag in soup.find_all('style'):
                    styles.append(style_tag.string)
                    style_tag.decompose()  # Xóa thẻ <style> để tránh trùng lặp

                # Thay thế src của thẻ <img>
                for img in soup.find_all('img'):
                    if 'src' in img.attrs:
                        img_src = Path(img['src']).as_posix()
                        img_src_normalized = img_src
                        while img_src_normalized.startswith('../'):
                            img_src_normalized = img_src_normalized[3:]
                        img_src_normalized = img_src_normalized.lstrip('/')
                        img_src_normalized = img_src_normalized.lower()
                        if img_src_normalized in image_map:
                            img['src'] = image_map[img_src_normalized]
                        else:
                            img_name = Path(img_src).name.lower()
                            matching_key = next((k for k in image_map if Path(k).name.lower() == img_name), None)
                            if matching_key:
                                img['src'] = image_map[matching_key]

                full_content.append(str(soup))

        # Kết hợp nội dung HTML và style
        combined_content = "".join(full_content)
        combined_styles = "\n".join(styles)
        return combined_content, combined_styles

    except ebooklib.exceptions.EpubException as e:
        return f"Lỗi khi đọc file EPUB: {str(e)}", ""
    except IOError as e:
        return f"Lỗi khi ghi file ảnh: {str(e)}", ""
    except Exception as e:
        return f"Lỗi không xác định khi trích xuất EPUB: {str(e)}", ""

@readEpub_bp.route('/read/<int:book_id>')
def read_epub(book_id):
    """Đọc EPUB từ BLOB dựa trên book_id và hiển thị qua Jinja2"""
    try:
        # Lấy dữ liệu từ database
        epub_data, title = get_epub_from_db(book_id)
        if not epub_data:
            return "Không tìm thấy file EPUB trong database!", 404

        # Lưu file tạm từ BLOB
        temp_filename = f"{book_id}.epub"
        filepath = save_blob_to_file(epub_data, temp_filename)

        # Trích xuất nội dung và style
        content, styles = extract_epub(filepath, book_id)

        # Xóa file tạm ngay cả khi có lỗi
        if os.path.exists(filepath):
            os.remove(filepath)

        # Kiểm tra lỗi trong nội dung
        if content.startswith("Lỗi"):
            return content, 500

        # Render template với Jinja2
        return render_template('readEpub.html', content=content, styles=styles, title=title)

    except Exception as e:
        # Đảm bảo xóa file tạm nếu có lỗi
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return f"Lỗi khi xử lý yêu cầu: {str(e)}", 500

app.register_blueprint(readEpub_bp)

# Chạy ứng dụng
if __name__ == '__main__':
    os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
    app.run(debug=True)