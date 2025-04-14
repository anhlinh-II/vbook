# search.py
from flask import Blueprint, request, render_template
from models import Book

search_bp = Blueprint('search_books', __name__)

@search_bp.route('/search_books', methods=['GET'])
def search_books():
    query = request.args.get('q', '').strip()
    books = Book.query.all()

    if query:
        books = Book.query.filter(
            Book.title.ilike(f"%{query}%") | Book.author.ilike(f"%{query}%")
        ).all()

    return render_template('search.html', books=books, query=query)
