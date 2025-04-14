from flask import Flask, Blueprint, render_template, send_from_directory, url_for
import os
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import sqlite3
import shutil
from werkzeug.utils import secure_filename, safe_join
from pathlib import Path

# Khởi tạo Flask app và Blueprint
app = Flask(__name__)
readEpub_bp = Blueprint('readEpub', __name__)

# Cấu hình thư mục
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
EXTRACT_FOLDER = os.path.join(BASE_DIR, 'static', 'extracted')
DB_PATH = os.path.join(BASE_DIR, 'instance', 'books.db')

# Tạo các thư mục nếu chưa tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)


@readEpub_bp.route('/serve-image/<int:book_id>/<path:filename>')
def serve_image(book_id, filename):
    """Phục vụ ảnh từ thư mục trích xuất"""
    book_folder = os.path.join(EXTRACT_FOLDER, str(book_id))
    safe_path = safe_join(book_folder, filename)

    if not safe_path or not os.path.exists(safe_path):
        print(f"Không tìm thấy ảnh: {safe_path} (filename: {filename})")
        return "Ảnh không tồn tại", 404

    print(f"Phục vụ ảnh: {safe_path}")
    return send_from_directory(book_folder, filename)


def get_epub_from_db(book_id):
    """Lấy dữ liệu EPUB BLOB và tiêu đề từ database theo book_id"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT content, title FROM book WHERE id = ?", (book_id,))
        result = cursor.fetchone()
        conn.close()
        return result if result else (None, None)
    except sqlite3.Error as e:
        print(f"Lỗi khi truy vấn database: {str(e)}")
        return None, None


def save_blob_to_file(blob_data, filename):
    """Lưu dữ liệu BLOB thành file tạm trong UPLOAD_FOLDER"""
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    try:
        with open(filepath, 'wb') as f:
            f.write(blob_data)  # Sửa lỗi: sử dụng blob_data trực tiếp
        return filepath
    except IOError as e:
        print(f"Lỗi khi lưu file tạm: {str(e)}")
        return None


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
        styles = []
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
                css_content = item.get_content().decode('utf-8', errors='ignore')
                styles.append(css_content)

        # Giai đoạn 2: Xử lý ITEM_DOCUMENT và thay thế src
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')

                # Trích xuất inline style từ thẻ <style> trong HTML
                for style_tag in soup.find_all('style'):
                    if style_tag.string:
                        styles.append(style_tag.string)
                    style_tag.decompose()

                # Thay thế src của thẻ <img>
                for img in soup.find_all('img'):
                    if 'src' in img.attrs:
                        img_src = Path(img['src']).as_posix()
                        img_src_normalized = img_src
                        while img_src_normalized.startswith('../'):
                            img_src_normalized = img_src_normalized[3:]
                        img_src_normalized = img_src_normalized.lstrip('/').lower()

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

    except Exception as e:  # Bắt tất cả các lỗi chung
        return f"Lỗi khi xử lý file EPUB: {str(e)}", ""



@readEpub_bp.route('/read/<int:book_id>')
def read_epub(book_id):
    """Đọc EPUB từ BLOB dựa trên book_id và hiển thị qua Jinja2"""
    filepath = None
    try:
        # Lấy dữ liệu từ database
        epub_data, title = get_epub_from_db(book_id)
        if not epub_data:
            return "Không tìm thấy file EPUB trong database!", 404

        # Lưu file tạm từ BLOB
        temp_filename = f"{book_id}.epub"
        filepath = save_blob_to_file(epub_data, temp_filename)
        if not filepath:
            return "Lỗi khi lưu file tạm!", 500

        # Trích xuất nội dung và style
        content, styles = extract_epub(filepath, book_id)

        # Kiểm tra lỗi trong nội dung
        if content.startswith("Lỗi"):
            return content, 500

        # Render template với Jinja2
        return render_template('readEpub.html', content=content, styles=styles, title=title)

    except Exception as e:
        return f"Lỗi khi xử lý yêu cầu: {str(e)}", 500
    finally:
        # Đảm bảo xóa file tạm
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Lỗi khi xóa file tạm: {str(e)}")


app.register_blueprint(readEpub_bp)

# Chạy ứng dụng
if __name__ == '__main__':
    os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
    app.run(debug=True)