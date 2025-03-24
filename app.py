import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Category, User, Book

app = Flask(__name__)

# Cấu hình Flask
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///categories.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Thư mục lưu file upload
ALLOWED_EXTENSIONS = {'.pdf', '.epub'}  # Các định dạng file cho phép

# Đảm bảo thư mục upload tồn tại
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Hàm kiểm tra định dạng file
def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


db.init_app(app)  # Khởi tạo SQLAlchemy với Flask app

with app.app_context():
    print("Đang tạo database...")
    db.create_all()
    print("Tạo database xong!")


app.secret_key = 'supersecretkey'  # Dùng để lưu session

# Giả lập tài khoản (sẽ thay thế bằng database sau)
users = {"user@example.com": "password123"}

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


@app.route('/')
def home():
    return render_template('home.html', books=books)

# API để lấy danh sách thể loại sách
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([{'id': cat.id, 'name': cat.name, 'slug': cat.slug} for cat in categories])

@app.route('/admin/add_category', methods=['POST'])
def add_category():
    name = request.form.get('name')
    slug = request.form.get('slug')

    if not name or not slug:
        flash("Vui lòng nhập đầy đủ thông tin.", "danger")
        return redirect(url_for('admin_panel'))

    # Kiểm tra slug đã tồn tại chưa
    existing_category = Category.query.filter_by(slug=slug).first()
    if existing_category:
        flash("Slug đã tồn tại, vui lòng nhập slug khác.", "danger")
        return redirect(url_for('admin_panel'))

    # Nếu slug chưa tồn tại, thêm vào database
    new_category = Category(name=name, slug=slug)
    db.session.add(new_category)
    db.session.commit()
    
    flash("Thể loại đã được thêm thành công!", "success")
    return redirect(url_for('admin_panel'))

# Route để admin sửa thể loại
@app.route('/admin/edit_category/<int:id>', methods=['POST'])
def edit_category(id):
    category = Category.query.get_or_404(id)
    category.name = request.form.get('name')
    category.slug = request.form.get('slug')
    db.session.commit()
    return redirect(url_for('admin_panel'))

# Route để admin xóa thể loại
@app.route('/admin/delete_category/<int:id>', methods=['POST'])
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('admin_panel'))

# Route để admin xem danh sách thể loại
@app.route('/admin')
def admin_panel():
    categories = Category.query.all()
    # Lấy danh sách sách cho mỗi thể loại
    for category in categories:
        category.books = Book.query.filter_by(genre=category.name).all()
    return render_template('admin.html', categories=categories)

# Route để xem trang thể loại
@app.route('/category/<slug>')
def category_page(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    return render_template('category.html', category=category)

# Route để xem danh sách sách theo thể loại
@app.route('/category/<slug>')
def category(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    books = Book.query.filter_by(genre=category.name).all()
    print(f"Category name: {category.name}")
    print(f"Books: {books}")
    return render_template('category.html', category=category, books=books)


# Route để thêm sách
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

    # Lưu file vào thư mục uploads
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Tạo sách mới và lưu vào database
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

@app.route('/favorites')
def favorites():
    return render_template('favorites.html')

# Route để xem chi tiết sách
@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('bookDetails.html', book=book)

# Route để đọc sách
@app.route('/book/<int:book_id>/read')
def read_book(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('read_book.html', book=book)

# Route để chỉnh sửa sách
@app.route('/admin/edit_book/<int:book_id>', methods=['POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    book.title = request.form.get('title')
    book.author = request.form.get('author')
    book.genre = request.form.get('genre')
    book.description = request.form.get('description')

    # Xử lý file upload (nếu có)
    file = request.files.get('book_file')
    if file and file.filename:
        if not allowed_file(file.filename):
            flash('Chỉ hỗ trợ file PDF hoặc ePub!', 'error')
            return redirect(url_for('admin_panel'))
        # Xóa file cũ nếu có
        if book.file_path and os.path.exists(book.file_path[1:]):  # Bỏ dấu / đầu tiên
            os.remove(book.file_path[1:])
        # Lưu file mới
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        book.file_path = f"/{file_path}"

    db.session.commit()
    flash('Chỉnh sửa sách thành công!', 'success')
    return redirect(url_for('admin_panel'))

# Route để xóa sách
@app.route('/admin/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    # Xóa file sách nếu có
    if book.file_path and os.path.exists(book.file_path[1:]):  # Bỏ dấu / đầu tiên
        os.remove(book.file_path[1:])
    db.session.delete(book)
    db.session.commit()
    flash('Xóa sách thành công!', 'success')
    return redirect(url_for('admin_panel'))

# API đang đọc sách
@app.route('/reading')
def reading():
    return render_template('reading.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        avatar_url = request.form['avatar_url'] or "https://via.placeholder.com/150"  # Nếu không có, dùng ảnh mặc định

        # Kiểm tra xem email đã tồn tại chưa
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', error="Email đã tồn tại!")

        # Hash mật khẩu
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Lưu user vào database
        new_user = User(email=email, username=username, password=hashed_password, avatar_url=avatar_url)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  # Chuyển hướng sau khi đăng ký thành công

    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Tìm user trong database
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['id'] = user.id
            session['user'] = user.email  # Lưu session với email
            session['username'] = user.username  # Lưu tên người dùng
            session['avatar_url'] = user.avatar_url  # Lưu ảnh đại diện
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Sai email hoặc mật khẩu!")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Xóa toàn bộ session khi logout
    return redirect(url_for('login'))

@app.route('/bookDetails/<int:book_id>')
def book_details(book_id):
    book = next((b for b in books if b["id"] == book_id), None)
    if book is None:
        return "Không tìm thấy sách", 404
    return render_template('bookDetails.html', book=book)


@app.route('/account')
def account():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_data = {
        "username": session.get("username"),
        "email": session.get("email"),
        "avatar_url": session.get("avatar_url"),
        "books_read": ["Sách 1", "Sách 2", "Sách 3"],  # Thay bằng dữ liệu thực tế từ DB
    }

    return render_template('account.html', user=user_data)


from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User

@app.route('/update_account', methods=['POST'])
def update_account():
    if 'user' not in session:  # Kiểm tra người dùng đã đăng nhập chưa
        return redirect(url_for('login'))

    user_id = session['id']
    user = User.query.get(user_id)  # Tìm người dùng theo ID

    if user:
        new_username = request.form.get("username")
        new_email = request.form.get("email")

        # Kiểm tra email đã tồn tại chưa
        existing_user = User.query.filter(User.email == new_email, User.id != user_id).first()
        if existing_user:
            flash("Email này đã được sử dụng!", "error")
            return redirect(url_for('account'))

        # Cập nhật thông tin người dùng
        user.username = new_username
        user.email = new_email
        db.session.commit()  # Lưu thay đổi vào DB

        # Cập nhật session
        session["username"] = new_username
        session["email"] = new_email

        flash("Cập nhật thành công!", "success")
    else:
        flash("Không tìm thấy người dùng!", "error")

    return redirect(url_for('account'))



if __name__ == '__main__':
    app.run(debug=True)
