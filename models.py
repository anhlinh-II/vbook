# models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
# import os # Không cần os ở đây nữa nếu không xử lý path cục bộ cho ảnh bìa

db = SQLAlchemy()

# URL ảnh bìa mặc định trên Cloudinary (thay thế bằng URL thực tế của bạn)
# Bạn có thể định nghĩa nó ở đây hoặc trong app.py và truyền vào khi cần
CLOUDINARY_DEFAULT_BOOK_COVER_URL_MODEL = "URL_TO_YOUR_DEFAULT_CLOUDINARY_BOOK_COVER_IMAGE" # VÍ DỤ

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship('User', backref=db.backref('reviews_by_user', lazy=True))


class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # file_path = db.Column(db.String(500), nullable=True) # Cân nhắc bỏ nếu 'content' là đủ
    content = db.Column(db.LargeBinary, nullable=True)    # Nội dung file sách (epub, pdf)

    # Trường mới cho ảnh bìa từ Cloudinary
    cover_path = db.Column(db.String(500), nullable=True, default=CLOUDINARY_DEFAULT_BOOK_COVER_URL_MODEL)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('books_in_category', lazy=True))
    reviews = db.relationship('Review', backref='book_reviewed', lazy='dynamic', cascade="all, delete-orphan")

    @hybrid_property
    def avg_rating(self):
        if self.id:
            avg = db.session.query(func.avg(Review.rating)).filter(Review.book_id == self.id).scalar()
            return float(avg) if avg is not None else 0.0
        return 0.0

    @avg_rating.expression
    def avg_rating(cls):
        return db.session.query(func.avg(Review.rating)).filter(Review.book_id == cls.id).label('avg_rating')

    @hybrid_property
    def review_count(self):
        if self.id:
            return db.session.query(func.count(Review.id)).filter(Review.book_id == self.id).scalar()
        return 0

    @review_count.expression
    def review_count(cls):
        return db.session.query(func.count(Review.id)).filter(Review.book_id == cls.id).label('review_count')

    def __repr__(self):
        return f'<Book {self.title}>'

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True) # Đây có thể đã là URL Cloudinary
    is_admin = db.Column(db.Boolean, default=False)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)