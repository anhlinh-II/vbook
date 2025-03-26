from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify

reading_bp = Blueprint('reading', __name__)

# Dùng danh sách books từ app.py (giả lập)
books = [
    {
        "id": 1,
        "title": "Dune",
        "author": "Frank Herbert",
        "image": "https://307a0e78.vws.vegacdn.vn/view/v2/image/img.book/0/0/1/50986.jpg?v=1&w=350&h=510",
        "genre": "Science Fiction",
        "description": "Một tiểu thuyết khoa học viễn tưởng kinh điển kể về cuộc chiến giành quyền kiểm soát hành tinh sa mạc Arrakis.",
        "comments": [
            {"user": "Minh Trần", "rating": 5, "content": "Câu chuyện tuyệt vời! Không thể bỏ qua."},
            {"user": "Hà Nguyễn", "rating": 4, "content": "Thế giới trong truyện rất chi tiết, nhưng hơi dài."}
        ]
    },
    {
        "id": 2,
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "image": "https://307a0e78.vws.vegacdn.vn/view/v2/image/img.book/0/0/1/50986.jpg?v=1&w=350&h=510",
        "genre": "Fantasy",
        "description": "Cuộc phiêu lưu của Bilbo Baggins cùng những người lùn trên hành trình tìm lại kho báu.",
        "comments": [
            {"user": "Linh Hoàng", "rating": 5, "content": "Một câu chuyện phiêu lưu kỳ thú, rất cuốn hút!"},
            {"user": "Tùng Phạm", "rating": 4, "content": "Hay nhưng hơi chậm ở một số đoạn."}
        ]
    },
    {
        "id": 3,
        "title": "1984",
        "author": "George Orwell",
        "image": "https://307a0e78.vws.vegacdn.vn/view/v2/image/img.book/0/0/1/50986.jpg?v=1&w=350&h=510",
        "genre": "Dystopian",
        "description": "Một tác phẩm kinh điển về xã hội toàn trị, nơi chính phủ kiểm soát mọi suy nghĩ của công dân.",
        "comments": [
            {"user": "An Đặng", "rating": 5, "content": "Cuốn sách đáng suy ngẫm, thực sự đáng đọc."},
            {"user": "Bảo Lê", "rating": 4, "content": "Khá nặng nề nhưng rất ý nghĩa."}
        ]
    },
    {
        "id": 4,
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "image": "https://307a0e78.vws.vegacdn.vn/view/v2/image/img.book/0/0/1/50986.jpg?v=1&w=350&h=510",
        "genre": "Fantasy",
        "description": "Hành trình vĩ đại của Bilbo Baggins để tìm lại kho báu bị đánh cắp bởi rồng Smaug.",
        "comments": [
            {"user": "Duy Nguyễn", "rating": 5, "content": "Một tác phẩm tuyệt vời của Tolkien!"},
            {"user": "Hằng Trần", "rating": 4, "content": "Câu chuyện hấp dẫn nhưng có vài đoạn hơi dài dòng."}
        ]
    },
]

@reading_bp.route('/add_to_reading_list/<int:book_id>')
def add_to_reading_list(book_id):
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        flash('Sách không tồn tại!', 'error')
        return redirect(url_for('home'))
    if book_id not in session['reading_list']:
        session['reading_list'].append(book_id)
        session.modified = True
    return redirect(url_for('readEpub.read_epub', book_id=book_id))

@reading_bp.route('/reading')
def reading():
    reading_books = []
    for book_id in session.get('reading_list', []):
        book = next((b for b in books if b["id"] == book_id), None)
        if book:
            reading_books.append(book)
    return render_template('reading.html', books=reading_books)

@reading_bp.route('/remove_from_reading_list/<int:book_id>', methods=['POST'])
def remove_from_reading_list(book_id):
    if book_id in session['reading_list']:
        session['reading_list'].remove(book_id)
        session.modified = True
        return jsonify({"success": True, "message": "Đã xóa sách khỏi danh sách đang đọc!"})
    return jsonify({"success": False, "message": "Sách không có trong danh sách đang đọc!"})