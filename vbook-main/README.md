# VBook - Ứng Dụng Đọc Sách Trực Tuyến

## 🚀 Giới Thiệu
VBook là một ứng dụng đọc sách trực tuyến được xây dựng bằng **Flask**, **Jinja2**, và **Tailwind CSS**. Ứng dụng cho phép người dùng tải lên sách, đọc sách, tìm kiếm theo thể loại, quản lý danh sách yêu thích, và đăng ký/đăng nhập tài khoản.

## 🌟 Tính Năng Chính
- 📚 **Quản lý sách**: Tải lên sách, đọc sách, tìm kiếm theo thể loại.
- ❤️ **Danh sách yêu thích**: Thêm/xóa sách vào danh sách yêu thích.
- 🔍 **Tìm kiếm**: Lọc sách theo tên hoặc thể loại.
- 👤 **Quản lý tài khoản**: Đăng ký, đăng nhập, cập nhật thông tin cá nhân.
- 📖 **Tiếp tục đọc**: Hiển thị danh sách sách đang đọc dở.

## 🛠️ Công Nghệ Sử Dụng
- **Backend**: Flask (Python), Jinja2
- **Frontend**: Tailwind CSS, HTML, JavaScript
- **Database**: SQLite / PostgreSQL
- **Xác thực người dùng**: Flask-Login, Flask-Session

## 📌 Cách Cài Đặt
### 1️⃣ Clone repository
```sh
git clone https://github.com/yourusername/vbook.git
cd vbook
```
### 2️⃣ Tạo môi trường ảo và cài đặt dependencies
```sh
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
pip install -r requirements.txt
```
### 3️⃣ Chạy ứng dụng
```sh
flask run
```
Mặc định, ứng dụng sẽ chạy tại `http://127.0.0.1:5000/`

## 📂 Cấu Trúc Thư Mục
```
VBook/
│── static/                 # File CSS, JS, hình ảnh
│── templates/              # Giao diện HTML sử dụng Jinja2
│── app.py                  # File chính của Flask
│── models.py               # Định nghĩa database
│── routes.py               # Định nghĩa route
│── forms.py                # Định nghĩa form Flask-WTF
│── requirements.txt        # Danh sách thư viện cần cài đặt
│── README.md               # Hướng dẫn sử dụng
```

## 📌 Môi Trường Biến (Environment Variables)
Tạo file `.env` để lưu thông tin cấu hình:
```
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///vbook.db
```

## 🎯 Định Hướng Phát Triển
- 🌍 Hỗ trợ đa ngôn ngữ.
- 📱 Xây dựng ứng dụng mobile.
- 🌟 Gợi ý sách theo sở thích cá nhân.

## 📞 Liên Hệ
Nếu bạn có câu hỏi hoặc góp ý, vui lòng liên hệ qua email: `your.email@example.com` hoặc tạo issue trên GitHub!

---
💡 **VBook - Đọc sách dễ dàng, mọi lúc mọi nơi!** 🚀
