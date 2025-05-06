from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func # Thêm import này

db = SQLAlchemy()

class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Giả sử bạn có model User
    rating = db.Column(db.Integer, nullable=False) # Điểm đánh giá từ 1 đến 5
    comment = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Mối quan hệ với User (tùy chọn, nếu bạn muốn hiển thị tên người dùng)
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))

    def __repr__(self):
        return f'<Review {self.id} by User {self.user_id} for Book {self.book_id}>'

class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    content = db.Column(db.LargeBinary, nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('books', lazy=True))

    # Mối quan hệ với Review
    reviews = db.relationship('Review', backref='book', lazy='dynamic') # Sử dụng lazy='dynamic' để có thể query

    @hybrid_property
    def avg_rating(self):
        if self.reviews.count() > 0: # Kiểm tra xem có review nào không
            return db.session.query(func.avg(Review.rating)).filter(Review.book_id == self.id).scalar()
        return 0 # Trả về 0 nếu không có review

    @avg_rating.expression
    def avg_rating(cls): # cls ở đây là class Book
        return db.session.query(func.avg(Review.rating)).filter(Review.book_id == cls.id).label('avg_rating')


    def __repr__(self):
        return f'<Book {self.title}>'

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<User {self.username}>"

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'