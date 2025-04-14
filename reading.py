from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from models import Book  # Import model Book từ model.py


reading_bp = Blueprint('reading', __name__)


@reading_bp.route('/add_to_reading_list/<int:book_id>')
def add_to_reading_list(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Sách không tồn tại!', 'error')
        return redirect(url_for('home'))

    if 'reading_list' not in session:
        session['reading_list'] = []

    if book_id not in session['reading_list']:
        session['reading_list'].append(book_id)
        session.modified = True

    return redirect(url_for('readEpub.read_epub', book_id=book_id))


@reading_bp.route('/reading')
def reading():
    reading_books = []
    if 'reading_list' in session:
        reading_books = Book.query.filter(Book.id.in_(session['reading_list'])).all()
    return render_template('reading.html', books=reading_books)


@reading_bp.route('/remove_from_reading_list/<int:book_id>', methods=['POST'])
def remove_from_reading_list(book_id):
    if 'reading_list' in session and book_id in session['reading_list']:
        session['reading_list'].remove(book_id)
        session.modified = True
        return jsonify({"success": True, "message": "Đã xóa sách khỏi danh sách đang đọc!"})
    return jsonify({"success": False, "message": "Sách không có trong danh sách đang đọc!"})
