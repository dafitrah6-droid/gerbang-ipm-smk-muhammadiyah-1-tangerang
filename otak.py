import os
from flask import Flask, render_template_string, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

# =========================
# CONFIG TIMEZONE (WIB)
# =========================
WIB = pytz.timezone("Asia/Jakarta")

def get_now_wib():
    return datetime.now(WIB)

# =========================
# INIT APP
# =========================
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "ipm_data.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================
# DATABASE MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    gmail = db.Column(db.String(100))
    nis = db.Column(db.String(20))
    kelas = db.Column(db.String(50))
    whatsapp = db.Column(db.String(20))
    role = db.Column(db.String(20), default="member")
    created_at = db.Column(db.DateTime, default=get_now_wib)

class Kas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipe = db.Column(db.String(10))
    jumlah = db.Column(db.Integer)
    keterangan = db.Column(db.String(200))
    tanggal = db.Column(db.DateTime, default=get_now_wib)

class Absensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    nama_kader = db.Column(db.String(100))
    waktu_hadir = db.Column(db.DateTime, default=get_now_wib)

class Laporan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    nama_pelapor = db.Column(db.String(100))
    pesan = db.Column(db.Text, nullable=False)
    waktu_lapor = db.Column(db.DateTime, default=get_now_wib)

# =========================
# INIT DATABASE
# =========================
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            password=generate_password_hash("admin123"),
            full_name="Administrator",
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return f"""
    <h2>IPM Portal</h2>
    <p>Welcome, {session['user_name']} ({session['role']})</p>
    <a href='/absen'>Absen</a> |
    <a href='/kas'>Kas</a> |
    <a href='/lapor'>Lapor</a> |
    <a href='/logout'>Logout</a>
    """

# =========================
# AUTH
# =========================

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("u").lower()
        password = request.form.get("p")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.full_name
            session["role"] = user.role
            return redirect("/")
        else:
            flash("Login gagal")

    return """
    <h3>Login</h3>
    <form method='POST'>
    Username: <input name='u'><br>
    Password: <input type='password' name='p'><br>
    <button type='submit'>Login</button>
    </form>
    """

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("u").lower().strip()
        password = request.form.get("p")
        full_name = request.form.get("fn")

        if len(password) < 6:
            flash("Password minimal 6 karakter")
            return redirect("/register")

        if User.query.filter_by(username=username).first():
            flash("Username sudah dipakai")
            return redirect("/register")

        new_user = User(
            username=username,
            password=generate_password_hash(password),
            full_name=full_name
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registrasi berhasil")
        return redirect("/login")

    return """
    <h3>Register</h3>
    <form method='POST'>
    Nama: <input name='fn'><br>
    Username: <input name='u'><br>
    Password: <input type='password' name='p'><br>
    <button type='submit'>Daftar</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# ABSENSI
# =========================

@app.route("/absen", methods=["GET","POST"])
def absen():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        today = get_now_wib().date()

        already = Absensi.query.filter(
            Absensi.user_id == session["user_id"],
            db.func.date(Absensi.waktu_hadir) == today
        ).first()

        if already:
            flash("Sudah absen hari ini")
        else:
            db.session.add(Absensi(
                user_id=session["user_id"],
                nama_kader=session["user_name"]
            ))
            db.session.commit()
            flash("Absen berhasil")

        return redirect("/absen")

    return """
    <h3>Absensi</h3>
    <form method='POST'>
    <button type='submit'>Hadir</button>
    </form>
    <a href='/'>Kembali</a>
    """

# =========================
# KAS (ADMIN ONLY)
# =========================

@app.route("/kas", methods=["GET","POST"])
def kas():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        if session.get("role") != "admin":
            flash("Hanya admin boleh mengubah kas")
            return redirect("/kas")

        nominal = int(request.form.get("j"))
        db.session.add(Kas(
            tipe=request.form.get("t"),
            jumlah=nominal,
            keterangan=request.form.get("k")
        ))
        db.session.commit()
        flash("Data kas ditambahkan")
        return redirect("/kas")

    data = Kas.query.all()
    pemasukan = sum(d.jumlah for d in data if d.tipe == "masuk")
    pengeluaran = sum(d.jumlah for d in data if d.tipe == "keluar")
    saldo = pemasukan - pengeluaran

    return f"""
    <h3>Kas</h3>
    <p>Saldo: Rp {saldo}</p>

    {"<form method='POST'>\
    <select name='t'><option value='masuk'>Masuk</option><option value='keluar'>Keluar</option></select><br>\
    Nominal: <input type='number' name='j'><br>\
    Ket: <input name='k'><br>\
    <button type='submit'>Tambah</button>\
    </form>" if session.get("role")=="admin" else ""}

    <a href='/'>Kembali</a>
    """

# =========================
# LAPORAN
# =========================

@app.route("/lapor", methods=["GET","POST"])
def lapor():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        pesan = request.form.get("pesan")
        db.session.add(Laporan(
            user_id=session["user_id"],
            nama_pelapor=session["user_name"],
            pesan=pesan
        ))
        db.session.commit()
        flash("Laporan terkirim")
        return redirect("/")

    return """
    <h3>Lapor Masalah</h3>
    <form method='POST'>
    <textarea name='pesan'></textarea><br>
    <button type='submit'>Kirim</button>
    </form>
    <a href='/'>Kembali</a>
    """

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
