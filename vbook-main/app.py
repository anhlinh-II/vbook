from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Category, Book  # Ensure these are defined in models.py
from reading import reading_bp  # Import Blueprint from reading.py
from readEpub import readEpub_bp
import os

app = Flask(__name__)

# Flask configuration
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///categories.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder for uploaded files
ALLOWED_EXTENSIONS = {'.pdf', '.epub'}  # Allowed file formats

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to check file extension
def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

# Initialize SQLAlchemy with Flask app
db.init_app(app)

# Create database and add sample data if empty
with app.app_context():
    print("Đang tạo database...")
    db.create_all()
    # Add sample categories if none exist
    if Category.query.count() == 0:
        sample_categories = [
            Category(name="Science Fiction", slug="science-fiction"),
            Category(name="Fantasy", slug="fantasy"),
            Category(name="Dystopian", slug="dystopian")
        ]
        db.session.bulk_save_objects(sample_categories)
        db.session.commit()
    print("Tạo database xong!")

app.secret_key = 'supersecretkey'  # For session management


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

# Initialize session data
@app.before_request
def initialize_session():
    if 'reading_list' not in session:
        session['reading_list'] = []
    if 'favorites' not in session:
        session['favorites'] = []

# Routes
@app.route('/')
def home():
    return render_template('home.html', books=books)

@app.route('/favorites')
def favorites():
    if 'user' not in session:
        print("User not logged in, redirecting to login")
        return redirect(url_for('login'))

    favorites = session.get('favorites', [])
    print(f"Favorites in session: {favorites}")
    favorite_books = Book.query.filter(Book.id.in_(favorites)).all()
    return render_template('favorites.html', books=favorite_books)

@app.route('/add_to_favorites/<int:book_id>', methods=['POST'])
def add_to_favorites(book_id):
    print(f"Received request to add book {book_id} to favorites")
    if 'user' not in session:
        print("User not logged in")
        return jsonify({"success": False, "message": "Vui lòng đăng nhập để thêm vào yêu thích!"}), 401

    favorites = session.get('favorites', [])
    print(f"Current favorites: {favorites}")
    if book_id not in favorites:
        favorites.append(book_id)
        session['favorites'] = favorites
        session.modified = True
        print(f"Updated favorites: {favorites}")
        return jsonify({"success": True, "message": "Đã thêm vào yêu thích!"})
    else:
        print("Book already in favorites")
        return jsonify({"success": False, "message": "Sách đã có trong danh sách yêu thích!"})

@app.route('/favorites/remove/<int:book_id>', methods=['POST'])
def remove_favorite(book_id):
    print(f"Received request to remove book {book_id} from favorites")
    if 'user' not in session:
        print("User not logged in")
        return jsonify({"success": False, "message": "Vui lòng đăng nhập!"}), 401

    favorites = session.get('favorites', [])
    print(f"Current favorites: {favorites}")
    if book_id in favorites:
        favorites.remove(book_id)
        session['favorites'] = favorites
        session.modified = True
        print(f"Updated favorites: {favorites}")
        return jsonify({"success": True, "message": "Đã xóa khỏi yêu thích!"})
    return jsonify({"success": False, "message": "Sách không có trong danh sách yêu thích!"})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        avatar_url = request.form.get('avatar_url', "https://via.placeholder.com/150")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', error="Email đã tồn tại!")

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, username=username, password=hashed_password, avatar_url=avatar_url)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            # Lưu thông tin user vào session
            session['id'] = user.id
            session['user'] = user.email
            session['username'] = user.username
            session['avatar_url'] = user.avatar_url

            if user.is_admin:
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Sai email hoặc mật khẩu!")

    return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/bookDetails/<int:book_id>')
def book_details(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('bookDetails.html', book=book)

@app.route('/account')
def account():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_data = {
        "username": session.get("username"),
        "email": session.get("user"),
        "avatar_url": session.get("avatar_url"),
        "books_read": ["Sách 1", "Sách 2", "Sách 3"],  # Replace with actual data later
    }
    return render_template('account.html', user=user_data)

@app.route('/update_account', methods=['POST'])
def update_account():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['id']
    user = User.query.get(user_id)

    if user:
        new_username = request.form.get("username")
        new_email = request.form.get("email")

        existing_user = User.query.filter(User.email == new_email, User.id != user_id).first()
        if existing_user:
            flash("Email này đã được sử dụng!", "error")
            return redirect(url_for('account'))

        user.username = new_username
        user.email = new_email
        db.session.commit()

        session["username"] = new_username
        session["user"] = new_email
        flash("Cập nhật thành công!", "success")
    else:
        flash("Không tìm thấy người dùng!", "error")

    return redirect(url_for('account'))

# API to fetch categories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([{'id': cat.id, 'name': cat.name, 'slug': cat.slug} for cat in categories])

# Admin routes
@app.route('/admin/add_category', methods=['POST'])
def add_category():
    name = request.form.get('name')
    slug = request.form.get('slug')

    if not name or not slug:
        flash("Vui lòng nhập đầy đủ thông tin.", "danger")
        return redirect(url_for('admin_panel'))

    existing_category = Category.query.filter_by(slug=slug).first()
    if existing_category:
        flash("Slug đã tồn tại, vui lòng nhập slug khác.", "danger")
        return redirect(url_for('admin_panel'))

    new_category = Category(name=name, slug=slug)
    db.session.add(new_category)
    db.session.commit()

    flash("Thể loại đã được thêm thành công!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit_category/<int:id>', methods=['POST'])
def edit_category(id):
    category = Category.query.get_or_404(id)
    category.name = request.form.get('name')
    category.slug = request.form.get('slug')
    db.session.commit()
    flash("Chỉnh sửa thể loại thành công!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_category/<int:id>', methods=['POST'])
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash("Xóa thể loại thành công!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin')
def admin_panel():
    categories = Category.query.all()
    for category in categories:
        category.books = Book.query.filter_by(genre=category.name).all()
    return render_template('admin.html', categories=categories)

# Category route
@app.route('/category/<slug>')
def category(slug):
    try:
        category = Category.query.filter_by(slug=slug).first()
        if not category:
            flash("Không tìm thấy thể loại này", "error")
            return redirect(url_for('home'))

        books_in_category = Book.query.filter_by(genre=category.name).all()

        if not books_in_category:
            flash("Chưa có sách trong thể loại này", "warning")
            return render_template('category.html', category=category, books=[])

        return render_template('category.html',
                               category=category,
                               books=books_in_category)
    except Exception as e:
        flash(f"Lỗi khi tải thể loại: {str(e)}", "error")
        return redirect(url_for('home'))

# Book management routes
@app.route('/admin/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    genre = request.form.get('genre')
    description = request.form.get('description')
    file = request.files.get('book_file')

    if not file or not allowed_file(file.filename):
        flash('Vui lòng upload file PDF hoặc ePub hợp lệ!', 'error')
        return redirect(url_for('admin_panel'))

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    new_book = Book(
        title=title,
        author=author,
        genre=genre,
        description=description,
        file_path=f"/{file_path}"
    )
    db.session.add(new_book)
    db.session.commit()

    flash('Thêm sách thành công!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/book/<int:book_id>/read')
def read_book(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('read_book.html', book=book)

@app.route('/admin/edit_book/<int:book_id>', methods=['POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    book.title = request.form.get('title')
    book.author = request.form.get('author')
    book.genre = request.form.get('genre')
    book.description = request.form.get('description')

    file = request.files.get('book_file')
    if file and file.filename:
        if not allowed_file(file.filename):
            flash('Chỉ hỗ trợ file PDF hoặc ePub!', 'error')
            return redirect(url_for('admin_panel'))
        if book.file_path and os.path.exists(book.file_path[1:]):
            os.remove(book.file_path[1:])
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        book.file_path = f"/{file_path}"

    db.session.commit()
    flash('Chỉnh sửa sách thành công!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.file_path and os.path.exists(book.file_path[1:]):
        os.remove(book.file_path[1:])
    db.session.delete(book)
    db.session.commit()
    flash('Xóa sách thành công!', 'success')
    return redirect(url_for('admin_panel'))

# Register Blueprints
app.register_blueprint(readEpub_bp)
app.register_blueprint(reading_bp, url_prefix="/reading")

if __name__ == '__main__':
    app.run(debug=True)