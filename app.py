from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import desc, func # Đảm bảo func được import từ sqlalchemy
from models import db, User, Category, Book, Review
from reading import reading_bp  # Import Blueprint from reading.py
from readEpub import readEpub_bp
from search_books import search_bp
import os
from flask_migrate import Migrate
import cloudinary
import cloudinary.uploader
import cloudinary.api

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

cloudinary.config(
    cloud_name = "durtbvrao",
    api_key = "255949239751672",
    api_secret = "bFMvtdA8hl5DoFibGFEMs6rA2OA",
    secure = True # Nên dùng HTTPS
)

# Các định dạng file cho phép (giữ nguyên hoặc điều chỉnh)
ALLOWED_EXTENSIONS_BOOK_FILES = {'.pdf', '.epub'}
ALLOWED_EXTENSIONS_IMAGES = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in allowed_extensions

# ... (db.init_app(app), migrate = Migrate(app, db), các blueprint) ...

# URL ảnh bìa mặc định trên Cloudinary (thay thế bằng URL thực tế của bạn)
CLOUDINARY_DEFAULT_BOOK_COVER_URL = "https://res.cloudinary.com/YOUR_CLOUD_NAME/image/upload/vXXXXXXXXXX/folder/default_book_cover.png" # VÍ DỤ

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
    # Sách mới nhất (giữ nguyên hoặc điều chỉnh logic của bạn)
    newest_books = Book.query.order_by(Book.id.desc()).limit(10).all()

    # Sách được yêu thích nhất (đánh giá cao nhất)
    min_reviews_for_top_list = 2 # Số lượng đánh giá tối thiểu để sách được xét
    top_rated_books = Book.query \
        .join(Review, Book.id == Review.book_id) \
        .group_by(Book.id) \
        .having(func.count(Review.id) >= min_reviews_for_top_list) \
        .order_by(func.avg(Review.rating).desc(), func.count(Review.id).desc()) \
        .limit(10) \
        .all()
    # .order_by(func.avg(Review.rating).desc(), func.count(Review.id).desc()):
    # Sắp xếp theo đánh giá trung bình giảm dần, nếu bằng nhau thì ưu tiên sách có nhiều lượt đánh giá hơn.

    return render_template('home.html', newest_books=newest_books, top_rated_books=top_rated_books)

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


@app.route('/bookDetails/<int:book_id>', methods=['GET', 'POST'])  # Giữ nguyên POST nếu bạn có xử lý form khác ở đây
def book_details(book_id):
    book = Book.query.get_or_404(book_id)  # Sử dụng get_or_404 để tự động trả về 404 nếu không tìm thấy

    # Lấy danh sách đánh giá cho sách này, sắp xếp theo thời gian mới nhất trước
    # Cũng join với User để có thể lấy username
    reviews = Review.query.filter_by(book_id=book.id).join(User).order_by(Review.timestamp.desc()).all()

    # Tính toán điểm đánh giá trung bình (đã được xử lý bằng hybrid_property trong model Book)
    # avg_rating = book.avg_rating

    return render_template('bookDetails.html', book=book, reviews=reviews)

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

    return render_template('admin.html', categories=categories, cloudinary_default_cover=CLOUDINARY_DEFAULT_BOOK_COVER_URL)

@app.route('/admin/add_book', methods=['POST'])
def add_book():
    # ... (kiểm tra quyền admin)
    # ... (lấy title, author, category_name, description)
    title = request.form.get('title')
    author = request.form.get('author')
    category_name = request.form.get('genre')
    description = request.form.get('description')
    book_file_data = request.files.get('book_file') # File sách (epub, pdf)
    cover_image_file = request.files.get('cover_image') # Ảnh bìa

    category = Category.query.filter_by(name=category_name).first()
    if not category:
        flash(f'Thể loại "{category_name}" không tồn tại.', 'danger')
        return redirect(url_for('admin_panel'))

    book_content_blob = None # Để lưu nội dung file sách
    if book_file_data and book_file_data.filename != '' and allowed_file(book_file_data.filename, ALLOWED_EXTENSIONS_BOOK_FILES):
        book_content_blob = book_file_data.read()
    elif book_file_data and book_file_data.filename != '':
        flash('Định dạng file sách không hợp lệ. Chỉ chấp nhận PDF, EPUB.', 'warning')

    # Xử lý upload ảnh bìa lên Cloudinary
    cover_image_url_to_save = CLOUDINARY_DEFAULT_BOOK_COVER_URL # Mặc định

    if cover_image_file and cover_image_file.filename != '':
        if allowed_file(cover_image_file.filename, ALLOWED_EXTENSIONS_IMAGES):
            if True: # Chỉ thử upload nếu Cloudinary được cấu hình
                try:
                    upload_result = cloudinary.uploader.upload(
                        cover_image_file,
                        folder="vbook_covers",  # Thư mục trên Cloudinary (tùy chọn)
                        # public_id=f"book_{secure_filename(title)}_{category.slug}", # Tên file tùy chỉnh (tùy chọn)
                        overwrite=True,
                        resource_type="image"
                    )
                    uploaded_url = upload_result.get('secure_url')
                    if uploaded_url:
                        cover_image_url_to_save = uploaded_url
                    else:
                        flash('Upload ảnh bìa lên Cloudinary thất bại. Sử dụng ảnh mặc định.', 'warning')
                        app.logger.error(f"Cloudinary upload failed, no secure_url. Result: {upload_result}")
                except Exception as e:
                    flash(f'Lỗi khi upload ảnh bìa lên Cloudinary: {str(e)}. Sử dụng ảnh mặc định.', 'danger')
                    app.logger.error(f"Cloudinary upload exception: {e}")
            else:
                flash('Cloudinary chưa được cấu hình. Không thể upload ảnh bìa. Sử dụng ảnh mặc định.', 'danger')
        else:
            flash('Định dạng file ảnh bìa không hợp lệ. Sử dụng ảnh mặc định.', 'warning')

    new_book = Book(
        title=title,
        author=author,
        category_id=category.id,
        description=description,
        content=book_content_blob, # Nội dung file sách
        cover_image_url=cover_image_url_to_save
    )
    db.session.add(new_book)
    db.session.commit()

    flash('Thêm sách thành công!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit_book/<int:book_id>', methods=['POST'])
def edit_book(book_id):
    # ... (kiểm tra quyền admin)
    book = Book.query.get_or_404(book_id)
    # ... (cập nhật title, author, category, description)
    book.title = request.form.get('title', book.title)
    book.author = request.form.get('author', book.author)
    new_category_name = request.form.get('genre')
    book.description = request.form.get('description', book.description)

    if new_category_name:
        category = Category.query.filter_by(name=new_category_name).first()
        if category:
            book.category_id = category.id

    book_file_data = request.files.get('book_file') # File sách (epub, pdf)
    if book_file_data and book_file_data.filename != '' and allowed_file(book_file_data.filename, ALLOWED_EXTENSIONS_BOOK_FILES):
        book.content = book_file_data.read() # Cập nhật nội dung file sách
    elif book_file_data and book_file_data.filename != '':
        flash('Định dạng file sách mới không hợp lệ. File sách không thay đổi.', 'warning')

    # Xử lý cập nhật ảnh bìa
    cover_image_file = request.files.get('cover_image')
    if cover_image_file and cover_image_file.filename != '':
        if allowed_file(cover_image_file.filename, ALLOWED_EXTENSIONS_IMAGES):
            if True: # Chỉ thử upload nếu Cloudinary được cấu hình
                try:
                    # Lưu ý: Việc xóa ảnh cũ trên Cloudinary cần public_id.
                    # Nếu bạn muốn xóa ảnh cũ, bạn cần lưu public_id khi upload
                    # hoặc có cơ chế trích xuất public_id từ URL.
                    # Hiện tại, chúng ta sẽ chỉ upload ảnh mới và ghi đè URL.
                    upload_result = cloudinary.uploader.upload(
                        cover_image_file,
                        folder="vbook_covers",
                        overwrite=True,
                        resource_type="image"
                    )
                    uploaded_url = upload_result.get('secure_url')
                    if uploaded_url:
                        book.cover_path = uploaded_url
                    else:
                        flash('Upload ảnh bìa mới lên Cloudinary thất bại.', 'warning')
                        app.logger.error(f"Cloudinary edit upload failed, no secure_url. Result: {upload_result}")
                except Exception as e:
                    flash(f'Lỗi khi upload ảnh bìa mới lên Cloudinary: {str(e)}', 'danger')
                    app.logger.error(f"Cloudinary edit upload exception: {e}")
            else:
                flash('Cloudinary chưa được cấu hình. Không thể cập nhật ảnh bìa.', 'danger')
        else:
            flash('Định dạng file ảnh bìa mới không hợp lệ. Ảnh bìa không thay đổi.', 'warning')

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

@app.route('/submit_review/<int:book_id>', methods=['POST'])
def submit_review(book_id):
    if 'id' not in session: # Kiểm tra xem user_id có trong session không
        flash("Vui lòng đăng nhập để đánh giá.", "warning")
        return redirect(url_for('login'))

    user_id = session['id']
    rating = request.form.get('rating')
    comment = request.form.get('comment')

    if not rating:
        flash("Vui lòng chọn điểm đánh giá.", "danger")
        return redirect(url_for('book_details', book_id=book_id))

    # Kiểm tra xem người dùng đã đánh giá sách này chưa (tùy chọn)
    existing_review = Review.query.filter_by(book_id=book_id, user_id=user_id).first()
    if existing_review:
        flash("Bạn đã đánh giá sách này rồi.", "info")
        return redirect(url_for('book_details', book_id=book_id))

    new_review = Review(
        book_id=book_id,
        user_id=user_id,
        rating=int(rating),
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()

    flash("Cảm ơn bạn đã đánh giá!", "success")
    return redirect(url_for('book_details', book_id=book_id))

# Register Blueprints
app.register_blueprint(readEpub_bp)
app.register_blueprint(reading_bp, url_prefix="/reading")
app.register_blueprint(search_bp)

if __name__ == '__main__':
    app.run(debug=True)







