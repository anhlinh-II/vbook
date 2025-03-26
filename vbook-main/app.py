from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from reading import reading_bp  # Import Blueprint từ reading.py
from readEpub import readEpub_bp

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'  # Dùng để lưu session

db.init_app(app)  # Khởi tạo SQLAlchemy với Flask app

with app.app_context():
    print("Đang tạo database...")
    db.create_all()
    print("Tạo database xong!")

# Giả lập danh sách sách (có thể thay bằng database sau)
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

# Khởi tạo session
@app.before_request
def initialize_session():
    if 'reading_list' not in session:
        session['reading_list'] = []
    if 'favorites' not in session:
        session['favorites'] = []

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
    favorite_books = [book for book in books if book['id'] in favorites]
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
        avatar_url = request.form['avatar_url'] or "https://via.placeholder.com/150"

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
            session['id'] = user.id
            session['user'] = user.email
            session['username'] = user.username
            session['avatar_url'] = user.avatar_url
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
        "email": session.get("user"),  # Sửa từ 'email' thành 'user' để khớp với session
        "avatar_url": session.get("avatar_url"),
        "books_read": ["Sách 1", "Sách 2", "Sách 3"],  # Thay bằng dữ liệu thực tế từ DB
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
        session["user"] = new_email  # Cập nhật email trong session
        flash("Cập nhật thành công!", "success")
    else:
        flash("Không tìm thấy người dùng!", "error")

    return redirect(url_for('account'))



app.register_blueprint(readEpub_bp)
app.register_blueprint(reading_bp, url_prefix="/reading")

if __name__ == '__main__':
    app.run(debug=True)