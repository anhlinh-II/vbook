from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Category, Book  # Ensure these are defined in models.py
from reading import reading_bp  # Import Blueprint from reading.py
from readEpub import readEpub_bp
from search_books import search_bp
import os
from flask_migrate import Migrate

# Sau khi khởi tạo db

app = Flask(__name__)

# Flask configuration
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
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
migrate = Migrate(app, db)

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
    books = Book.query.all()
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


@app.route('/bookDetails/<int:book_id>', methods=['GET', 'POST'])
def book_details(book_id):
    books = Book.query.all()
    book = next((b for b in books if b.id == book_id), None)
    book = Book.query.get(book_id)
    if not book:
        return "Book not found", 404  # Thay abort(404)
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
# Route để lấy danh sách thể loại dưới dạng JSON
@app.route('/get_categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([{'id': cat.id, 'name': cat.name, 'slug': cat.slug} for cat in categories])

@app.route('/api/categories')
def api_categories():
    categories = Category.query.all()
    data = [{"name": c.name, "slug": c.slug} for c in categories]
    return jsonify(data)

# Admin routes
@app.route('/admin/add_categories', methods=['POST'])
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

    # Kiểm tra nếu thể loại có sách thì không thể xóa
    if category.books:
        flash("Không thể xóa thể loại này vì có sách thuộc thể loại này!", "danger")
        return redirect(url_for('admin_panel'))

    db.session.delete(category)
    db.session.commit()
    flash("Thể loại đã được xóa thành công!", "success")
    return redirect(url_for('admin_panel'))


# Route hiển thị sách theo thể loại
@app.route('/category/<slug>')
def category(slug):
    try:
        category = Category.query.filter_by(slug=slug).first()
        if not category:
            flash("Không tìm thấy thể loại này", "error")
            return redirect(url_for('home'))

        books_in_category = Book.query.filter_by(category_id=category.id).all()

        if not books_in_category:
            flash("Chưa có sách trong thể loại này", "warning")
            return render_template('category.html', category=category, books=[])

        return render_template('category.html', category=category, books=books_in_category)

    except Exception as e:
        flash(f"Lỗi khi tải thể loại: {str(e)}", "error")
        return redirect(url_for('home'))


# Route admin panel (nếu có)
@app.route('/admin')
def admin_panel():
    categories = Category.query.all()

    # Gán sách cho mỗi thể loại dựa trên tên thể loại
    for category in categories:
        category.books = Book.query.filter(Book.category.has(name=category.name)).all()

    return render_template('admin.html', categories=categories)


# Book management routes
@app.route('/admin/add_book', methods=['POST'])
def add_book():
    title = request.form.get('title')
    author = request.form.get('author')
    category = request.form.get('genre')
    description = request.form.get('description')
    file = request.files.get('book_file')

    if not file or not allowed_file(file.filename):
        flash('Vui lòng upload file PDF hoặc ePub hợp lệ!', 'error')
        return redirect(url_for('admin_panel'))

    filename = secure_filename(file.filename)
    content = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(content)

    new_book = Book(
        title=title,
        author=author,
        genre=category,
        description=description,
        content=f"/{content}"
    )
    db.session.add(new_book)
    db.session.commit()

    flash('Thêm sách thành công!', 'success')
    return redirect(url_for('admin_panel'))

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
        if book.content and os.path.exists(book.content[1:]):
            os.remove(book.content[1:])
        filename = secure_filename(file.filename)
        content = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(content)
        book.content = f"/{content}"

    db.session.commit()
    flash('Chỉnh sửa sách thành công!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.content and os.path.exists(book.content[1:]):
        os.remove(book.content[1:])
    db.session.delete(book)
    db.session.commit()
    flash('Xóa sách thành công!', 'success')
    return redirect(url_for('admin_panel'))

# Register Blueprints
app.register_blueprint(readEpub_bp)
app.register_blueprint(reading_bp, url_prefix="/reading")
app.register_blueprint(search_bp)

if __name__ == '__main__':
    app.run(debug=True)







