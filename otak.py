import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz
# Tambahan Library Keamanan
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re

app = Flask(__name__)
app.secret_key = 'ipm_smkm1_tgr_luxury_2026_dafitrah_ultimate'

# --- SETTING TIMEZONE WIB ---
WIB = pytz.timezone('Asia/Jakarta')

def get_now_wib():
    """Fungsi pembantu untuk mendapatkan waktu WIB saat ini"""
    return datetime.now(WIB)

# --- FIREWALL & RATE LIMITER CONFIG ---
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per day", "100 per hour"],
    storage_uri="memory://",
)

# --- CONFIGURATION DATABASE ---
# Pakai /tmp/ agar Vercel tidak Error 500 saat mencoba menulis data
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/ipm_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- INPUT SANITIZATION FUNCTION ---
def sanitize_input(text):
    if text is None: return ""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    text = text.replace("'", "").replace('"', "").replace(";", "")
    return text.strip()

# --- DATABASE MODELS ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    gmail = db.Column(db.String(100))
    nis = db.Column(db.String(20))
    kelas = db.Column(db.String(50))
    whatsapp = db.Column(db.String(20))
    role = db.Column(db.String(20), default='member') # Role: admin, moderator, member
    created_at = db.Column(db.DateTime, default=get_now_wib)
    absensi = db.relationship('Absensi', backref='user', lazy=True)

class Kas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipe = db.Column(db.String(10)) 
    jumlah = db.Column(db.Integer)
    keterangan = db.Column(db.String(200))
    tanggal = db.Column(db.DateTime, default=get_now_wib)

class Agenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(100))
    waktu = db.Column(db.String(100))
    lokasi = db.Column(db.String(100))

class Struktur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jabatan = db.Column(db.String(100))
    nama = db.Column(db.String(100))
    bidang = db.Column(db.String(100))

class Absensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nama_kader = db.Column(db.String(100))
    waktu_hadir = db.Column(db.DateTime, default=get_now_wib)

class Laporan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nama_pelapor = db.Column(db.String(100))
    pesan = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Menunggu')
    waktu_lapor = db.Column(db.DateTime, default=get_now_wib)

# --- INITIALIZE DATABASE ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='dafitrah').first():
        admin_pass = generate_password_hash('admin123')
        admin = User(
            username='dafitrah', 
            password=admin_pass, 
            full_name='Muhammad Dafitrah', 
            role='admin', 
            nis='ADM-01', 
            kelas='Pimpinan', 
            whatsapp='08123', 
            gmail='admin@ipm.com'
        )
        db.session.add(admin)
        db.session.commit()

# --- UI TEMPLATE COMPONENTS ---

UI_CORE_HEADER = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>IPM PORTAL | SMKM 1 TGR</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        :root { --gold: #d4af37; --dark-bg: #0b0d11; --card-bg: rgba(255, 255, 255, 0.03); --smooth: cubic-bezier(0.4, 0, 0.2, 1); }
        body { background-color: var(--dark-bg); color: #e0e0e0; font-family: 'Inter', sans-serif; min-height: 100vh; overflow-x: hidden; }
        * { transition: all 0.6s var(--smooth); }
        .navbar-ipm { background: rgba(11, 13, 17, 0.9); border-bottom: 1px solid rgba(212, 175, 55, 0.2); padding: 15px 5%; position: sticky; top: 0; z-index: 1000; backdrop-filter: blur(20px); }
        .glass-card { background: var(--card-bg); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 24px; padding: 25px; backdrop-filter: blur(12px); }
        .glass-card:hover { transform: translateY(-8px) scale(1.01); border-color: var(--gold); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 20px rgba(212, 175, 55, 0.1); }
        .btn-gold { background: linear-gradient(135deg, #d4af37 0%, #f2d06b 100%); color: #000; border: none; padding: 14px 28px; border-radius: 14px; font-weight: 700; width: 100%; text-decoration: none; text-transform: uppercase; display: inline-block; text-align: center; cursor: pointer; letter-spacing: 1px; }
        .btn-gold:hover { transform: scale(1.03) translateY(-2px); box-shadow: 0 12px 25px rgba(212, 175, 55, 0.4); color: #000; }
        .form-control, .form-select { background: rgba(255, 255, 255, 0.04) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; color: #fff !important; border-radius: 12px !important; padding: 14px !important; }
        .form-control:focus { border-color: var(--gold) !important; background: rgba(255, 255, 255, 0.07) !important; box-shadow: 0 0 15px rgba(212, 175, 55, 0.15); }
        .kta-card { width: 350px; height: 210px; background: linear-gradient(145deg, #1e2024, #0b0d11); border: 1px solid rgba(212, 175, 55, 0.4); border-radius: 20px; position: relative; margin: 0 auto; animation: floatingSoft 4s ease-in-out infinite; box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
        @keyframes floatingSoft { 0%, 100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-12px) rotate(1deg); } }
        .fab-lapor { position: fixed; bottom: 35px; right: 35px; width: 65px; height: 65px; background: #ff4d4d; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 26px; z-index: 9999; box-shadow: 0 10px 30px rgba(255, 77, 77, 0.3); border: 2px solid rgba(255,255,255,0.1); }
        .badge-mod { background: #00d2ff; color: #000; font-weight: bold; border-radius: 8px; padding: 4px 10px; font-size: 0.7rem; }
    </style>
</head>
<body>
    {% if session.user_id %}<a href="/lapor" class="fab-lapor animate__animated animate__zoomIn"><i class="bi bi-exclamation-triangle"></i></a>{% endif %}
    <nav class="navbar-ipm d-flex justify-content-between align-items-center">
        <div class="fw-bold fs-4"><a href="/" class="text-white text-decoration-none">IPM <span class="text-gold">PORTAL</span></a></div>
        <div class="d-flex align-items-center">
            {% if session.user_id %}
                {% if session.role in ['admin', 'moderator'] %}
                    <a href="/admin" class="btn btn-outline-warning btn-sm me-3" style="border-radius:10px;"><i class="bi bi-shield-lock"></i> Panel Kendali</a>
                {% endif %}
                <a href="/profil" class="text-white me-3 text-decoration-none small"><i class="bi bi-person-circle"></i> Profil</a>
                <a href="/logout" class="text-danger text-decoration-none small">Logout</a>
            {% endif %}
        </div>
    </nav>
    <div class="container mt-3">{% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}<div class="alert alert-warning border-0 bg-dark text-warning animate__animated animate__fadeInDown" style="border-radius:15px; border-left: 5px solid var(--gold) !important;">{{ m }}</div>{% endfor %}{% endif %}{% endwith %}</div>
"""

UI_CORE_FOOTER = """<footer class="text-center py-5 mt-5 opacity-50 small"><p>&copy; 2026 IPM SMKM 1 TGR | Digitalized by <strong>Muhammad Dafitrah</strong></p></footer><script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script><script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script><script>AOS.init({duration: 1200, easing: 'ease-in-out-cubic', once: true});</script></body></html>"""

# --- ROUTES ---

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        u = sanitize_input(request.form.get('u').lower())
        p = request.form.get('p')
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            session.update({'user_id': user.id, 'user_name': user.full_name, 'role': user.role})
            return redirect('/')
        flash("Username/Password salah!")
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-5 pt-5" data-aos="zoom-out"><div class="glass-card mx-auto shadow" style="max-width:400px; border: 1px solid rgba(212, 175, 55, 0.2);"><h3 class="text-gold fw-bold text-center mb-4">LOGIN KADER</h3><form method="POST"><input name="u" class="form-control mb-3" placeholder="Username" required><input type="password" name="p" class="form-control mb-4" placeholder="Password" required><button type="submit" class="btn-gold">MASUK</button></form><div class="text-center mt-4 small">Belum terdaftar? <a href="/register" class="text-gold text-decoration-none">Daftar Akun</a></div></div></div>""" + UI_CORE_FOOTER)

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('u').lower().strip())
        password = request.form.get('p')
        if User.query.filter_by(username=username).first(): flash("Username sudah digunakan!")
        else:
            db.session.add(User(
                username=username, 
                password=generate_password_hash(password), 
                full_name=sanitize_input(request.form.get('fn')), 
                gmail=sanitize_input(request.form.get('gm')), 
                nis=sanitize_input(request.form.get('nis')), 
                kelas=sanitize_input(request.form.get('kls')), 
                whatsapp=sanitize_input(request.form.get('wa'))
            ))
            db.session.commit()
            flash("Registrasi Berhasil! Silakan Login."); return redirect('/login')
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-4 mb-5" data-aos="fade-up"><div class="glass-card mx-auto" style="max-width:550px;"><h3 class="text-gold fw-bold text-center">PENDAFTARAN KADER</h3><form method="POST"><input name="fn" class="form-control mb-3" placeholder="Nama Lengkap" required><div class="row mb-3"><div class="col-6"><input name="u" class="form-control" placeholder="Username" required></div><div class="col-6"><input type="password" name="p" class="form-control" placeholder="Password" required></div></div><input name="gm" type="email" class="form-control mb-3" placeholder="Email" required><div class="row mb-3"><div class="col-6"><input name="nis" class="form-control" placeholder="NIS" required></div><div class="col-6"><input name="kls" class="form-control" placeholder="Kelas" required></div></div><input name="wa" class="form-control mb-4" placeholder="WhatsApp" required><button type="submit" class="btn-gold">DAFTAR SEKARANG</button></form></div></div>""" + UI_CORE_FOOTER)

@app.route('/')
def home():
    if 'user_id' not in session: return redirect('/login')
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-5 text-center"><div data-aos="fade-down"><h1 class="text-gold fw-bold display-4" style="letter-spacing: 8px;">IPM PORTAL</h1><p class="text-secondary" style="letter-spacing: 2px;">SMK MUHAMMADIYAH 1 TANGERANG</p></div><div class="row g-4 mt-5"><div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="100"><div class="glass-card"><i class="bi bi-fingerprint text-gold fs-1"></i><h6 class="mt-3">Absensi</h6><a href="/absen" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div><div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="200"><div class="glass-card"><i class="bi bi-wallet2 text-gold fs-1"></i><h6 class="mt-3">Uang Kas</h6><a href="/kas" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div><div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="300"><div class="glass-card"><i class="bi bi-diagram-3 text-gold fs-1"></i><h6 class="mt-3">Struktur</h6><a href="/struktur" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div><div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="400"><div class="glass-card"><i class="bi bi-calendar-event text-gold fs-1"></i><h6 class="mt-3">Agenda</h6><a href="/agenda" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div></div></div>""" + UI_CORE_FOOTER)

@app.route('/admin')
def admin_panel():
    if session.get('role') not in ['admin', 'moderator']: return redirect('/')
    users = User.query.all(); lap = Laporan.query.all()
    kas_data = Kas.query.all()
    total_kas = sum(k.jumlah if k.tipe == 'masuk' else -k.jumlah for k in kas_data)
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5">
        <h2 class="text-gold fw-bold mb-5">Panel Kendali {{ session.role.upper() }}</h2>
        <div class="row g-3 mb-5">
            <div class="col-md-4"><div class="glass-card text-center"><small class="text-secondary">TOTAL KADER</small><h3 class="text-gold">{{ users|length }}</h3></div></div>
            {% if session.role == 'admin' %}
            <div class="col-md-4"><div class="glass-card text-center"><small class="text-secondary">SALDO KAS</small><h3 class="text-gold">Rp {{ "{:,}".format(total_kas) }}</h3></div></div>
            {% endif %}
            <div class="col-md-4"><div class="glass-card text-center"><small class="text-secondary">LAPORAN</small><h3 class="text-danger">{{ lap|length }}</h3></div></div>
        </div>
        
        <div class="glass-card mb-4">
            <h5 class="text-gold mb-4">Daftar Laporan Masuk</h5>
            <div class="table-responsive"><table class="table table-dark small">
                <thead><tr><th>Waktu (WIB)</th><th>Pelapor</th><th>Pesan</th><th>Aksi</th></tr></thead>
                <tbody>{% for l in lap %}<tr><td>{{ l.waktu_lapor.strftime('%d/%m %H:%M') }}</td><td>{{ l.nama_pelapor }}</td><td>{{ l.pesan }}</td><td><a href="/admin/lapor/selesai/{{ l.id }}" class="btn btn-success btn-sm">Selesai</a></td></tr>{% endfor %}</tbody>
            </table></div>
        </div>

        {% if session.role == 'admin' %}
        <div class="glass-card">
            <h5 class="text-gold mb-4">Manajemen Kader & Hak Akses</h5>
            <div class="table-responsive"><table class="table table-dark small">
                <thead><tr><th>Nama</th><th>Role</th><th>Ubah Role</th><th>Hapus</th></tr></thead>
                <tbody>{% for u in users %}{% if u.username != 'dafitrah' %}
                    <tr>
                        <td>{{ u.full_name }}</td>
                        <td><span class="{{ 'badge-mod' if u.role == 'moderator' else '' }}">{{ u.role }}</span></td>
                        <td>
                            <a href="/admin/set-role/{{ u.id }}/moderator" class="btn btn-outline-info btn-sm">Jadi Mod</a>
                            <a href="/admin/set-role/{{ u.id }}/member" class="btn btn-outline-secondary btn-sm">Jadi Member</a>
                        </td>
                        <td><a href="/hapus/user/{{ u.id }}" class="text-danger"><i class="bi bi-trash"></i></a></td>
                    </tr>
                {% endif %}{% endfor %}</tbody>
            </table></div>
        </div>
        {% endif %}
    </div>""" + UI_CORE_FOOTER, users=users, total_kas=total_kas, lap=lap)

@app.route('/admin/set-role/<int:uid>/<role>')
def set_role(uid, role):
    if session.get('role') != 'admin': abort(403)
    user = User.query.get(uid)
    if user and user.username != 'dafitrah':
        user.role = role
        db.session.commit()
        flash(f"Role {user.full_name} diubah menjadi {role}")
    return redirect('/admin')

@app.route('/admin/lapor/selesai/<int:lid>')
def lapor_selesai(lid):
    if session.get('role') not in ['admin', 'moderator']: abort(403)
    lap = Laporan.query.get(lid)
    if lap:
        db.session.delete(lap)
        db.session.commit()
        flash("Laporan diselesaikan.")
    return redirect('/admin')

@app.route('/absen', methods=['GET', 'POST'])
def absen():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        # Menggunakan waktu WIB untuk pengecekan hari ini
        today_wib = get_now_wib().date()
        already = Absensi.query.filter(Absensi.user_id == session['user_id'], db.func.date(Absensi.waktu_hadir) == today_wib).first()
        if already: flash("Kamu sudah presensi hari ini!")
        else:
            db.session.add(Absensi(user_id=session['user_id'], nama_kader=session['user_name'], waktu_hadir=get_now_wib()))
            db.session.commit(); flash("Berhasil Hadir (WIB)!")
        return redirect('/absen')
    logs = Absensi.query.order_by(Absensi.waktu_hadir.desc()).limit(15).all()
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-5"><div class="row g-4"><div class="col-md-5"><div class="glass-card text-center py-5"><h2 class="text-gold fw-bold mb-4">PRESENSI</h2><form method="POST"><button type="submit" class="btn-gold py-4 fs-2" style="border-radius:50%; width:150px; height:150px;"><i class="bi bi-fingerprint"></i></button></form></div></div><div class="col-md-7"><div class="glass-card"><h5 class="text-gold mb-4">KEHADIRAN TERBARU (WIB)</h5><table class="table table-dark small"><thead><tr><th>NAMA</th><th>WAKTU</th></tr></thead><tbody>{% for l in logs %}<tr><td>{{ l.nama_kader }}</td><td>{{ l.waktu_hadir.strftime('%H:%M:%S') }}</td></tr>{% endfor %}</tbody></table></div></div></div></div>""" + UI_CORE_FOOTER, logs=logs)

@app.route('/kas', methods=['GET', 'POST'])
def kas():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        db.session.add(Kas(tipe=request.form.get('t'), jumlah=int(request.form.get('j')), keterangan=sanitize_input(request.form.get('k')), tanggal=get_now_wib()))
        db.session.commit(); flash("Kas Dicatat!"); return redirect('/kas')
    data = Kas.query.order_by(Kas.tanggal.desc()).all()
    saldo = sum(d.jumlah if d.tipe == 'masuk' else -d.jumlah for d in data)
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-4"><div class="glass-card text-center mb-4"><small class="text-secondary">TOTAL SALDO</small><h1 class="text-gold fw-bold display-4">Rp {{ "{:,}".format(saldo) }}</h1></div><div class="row g-4"><div class="col-md-4"><div class="glass-card"><h6 class="text-gold mb-3">CATAT TRANSAKSI</h6><form method="POST"><select name="t" class="form-select mb-3"><option value="masuk">Pemasukan</option><option value="keluar">Pengeluaran</option></select><input type="number" name="j" class="form-control mb-3" placeholder="Nominal" required><input name="k" class="form-control mb-3" placeholder="Keterangan" required><button type="submit" class="btn-gold">SIMPAN</button></form></div></div><div class="col-md-8"><div class="glass-card"><table class="table table-dark small"><thead><tr><th>TGL (WIB)</th><th>KET</th><th>JUMLAH</th></tr></thead><tbody>{% for d in data %}<tr><td>{{ d.tanggal.strftime('%d/%m %H:%M') }}</td><td>{{ d.keterangan }}</td><td class="{{ 'text-success' if d.tipe == 'masuk' else 'text-danger' }}">{{ "{:,}".format(d.jumlah) }}</td></tr>{% endfor %}</tbody></table></div></div></div></div>""" + UI_CORE_FOOTER, data=data, saldo=saldo)

@app.route('/profil')
def profil():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-5"><div class="row justify-content-center"><div class="col-md-6"><div class="glass-card"><div class="text-center mb-4"><div class="d-inline-block p-1 rounded-circle mb-3" style="border: 2px solid var(--gold);"><i class="bi bi-person-circle text-gold" style="font-size: 80px;"></i></div><h3 class="text-gold fw-bold">{{ u.full_name }}</h3><span class="badge bg-dark border border-warning text-gold px-3">{{ u.role.upper() }}</span></div><div class="row g-2 small mb-4 px-3"><div class="col-5 text-secondary">NIS</div><div class="col-7 text-white">: {{ u.nis }}</div><div class="col-5 text-secondary">Kelas</div><div class="col-7 text-white">: {{ u.kelas }}</div><div class="col-5 text-secondary">Email</div><div class="col-7 text-white">: {{ u.gmail }}</div></div><div class="row g-2 mb-3"><div class="col-6"><a href="/kta" class="btn btn-outline-warning w-100 py-3" style="border-radius:15px;"><i class="bi bi-card-heading"></i><br>KTA</a></div><div class="col-6"><a href="/piagam" class="btn btn-outline-warning w-100 py-3" style="border-radius:15px;"><i class="bi bi-award"></i><br>PIAGAM</a></div></div><a href="/edit-profil" class="btn btn-outline-info btn-sm w-100 mb-2 py-2" style="border-radius:12px;">EDIT PROFIL</a><a href="/" class="btn-gold btn-sm w-100 mt-2 py-2">DASHBOARD</a></div></div></div></div>""" + UI_CORE_FOOTER, u=u)

@app.route('/edit-profil', methods=['GET', 'POST'])
def edit_profil():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    if request.method == 'POST':
        u.full_name = sanitize_input(request.form.get('fn')); u.gmail = sanitize_input(request.form.get('gm')); u.nis = sanitize_input(request.form.get('nis')); u.kelas = sanitize_input(request.form.get('kls')); u.whatsapp = sanitize_input(request.form.get('wa'))
        db.session.commit(); flash("Profil Diperbarui!"); return redirect('/profil')
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-4"><div class="glass-card mx-auto" style="max-width:500px;"><h4 class="text-gold fw-bold mb-4">EDIT PROFIL</h4><form method="POST"><input name="fn" class="form-control mb-3" value="{{ u.full_name }}"><input name="gm" class="form-control mb-3" value="{{ u.gmail }}"><input name="nis" class="form-control mb-3" value="{{ u.nis }}"><input name="kls" class="form-control mb-3" value="{{ u.kelas }}"><input name="wa" class="form-control mb-4" value="{{ u.whatsapp }}"><button type="submit" class="btn-gold">SIMPAN</button></form></div></div>""" + UI_CORE_FOOTER, u=u)

@app.route('/kta')
def kta_digital():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-5 text-center"><h3 class="text-gold fw-bold mb-4">KARTU TANDA ANGGOTA</h3><div class="kta-card p-4 shadow-lg"><div class="d-flex justify-content-between text-start"><div class="text-gold fw-bold small">IPM PORTAL<br><span class="text-white opacity-50" style="font-size:8px;">SMK MUHAMMADIYAH 1 TGR</span></div><i class="bi bi-qr-code text-white fs-2"></i></div><div class="text-start mt-3"><h5 class="text-white mb-0 fw-bold">{{ u.full_name }}</h5><small class="text-gold">{{ u.role.upper() }} - {{ u.kelas }}</small><div class="mt-2 opacity-75" style="font-size:10px;">ID: {{ u.nis }}</div></div></div><button onclick="window.print()" class="btn btn-gold mt-4 btn-sm" style="width: auto;">CETAK KTA</button></div>""" + UI_CORE_FOOTER, u=u)

@app.route('/piagam')
def piagam():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    count = Absensi.query.filter_by(user_id=u.id).count()
    if count < 1:
        flash("Minimal 1 kali absen untuk klaim Piagam!")
        return redirect('/profil')
    
    return render_template_string("""
    <html>
    <head>
        <title>Piagam Penghargaan - {{ u.full_name }}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Great+Vibes&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');
            body { background: #0b0d11; display: flex; flex-direction: column; align-items: center; min-height: 100vh; margin: 0; padding: 20px; color: white; }
            .piagam { width: 900px; height: 630px; background: #1a1c20; border: 15px solid #d4af37; padding: 60px; text-align: center; font-family: 'Cinzel', serif; position: relative; box-shadow: 0 0 50px rgba(0,0,0,0.5); overflow: hidden; }
            .piagam::before { content: ""; position: absolute; top: 10px; left: 10px; right: 10px; bottom: 10px; border: 2px solid rgba(212, 175, 55, 0.3); pointer-events: none; }
            .semboyan { color: #d4af37; letter-spacing: 5px; font-size: 0.9rem; margin-bottom: 30px; }
            .judul { font-size: 3.5rem; margin: 0; color: #fff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
            .presents { font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.2rem; margin-top: 10px; color: #aaa; }
            .nama { font-family: 'Great Vibes', cursive; font-size: 5rem; color: #d4af37; margin: 15px 0; }
            .isi { font-family: 'Playfair Display', serif; font-size: 1.15rem; line-height: 1.8; color: #e0e0e0; max-width: 700px; margin: 0 auto; font-style: italic; }
            .signature-container { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 60px; padding: 0 80px; }
            .sig-box { width: 220px; text-align: center; }
            .sig-line { border-top: 1px solid #d4af37; padding-top: 8px; font-size: 0.9rem; color: #d4af37; font-weight: bold; }
            .sig-space { height: 70px; }
            .date-info { font-family: 'Playfair Display', serif; font-size: 0.9rem; color: #aaa; margin-bottom: 5px; }
            .controls { margin-top: 30px; display: flex; gap: 10px; }
            .btn-action { background: #d4af37; color: black; border: none; padding: 12px 25px; font-weight: bold; cursor: pointer; border-radius: 8px; text-decoration: none; transition: 0.3s; }
            .btn-action:hover { background: #f2d06b; transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div id="piagam-area" class="piagam">
            <div class="semboyan">NUUN WALQOLAMI WAMAA YASTHURUUN</div>
            <h1 class="judul">PIAGAM PENGHARGAAN</h1>
            <div class="presents">Dengan bangga mempersembahkan kehormatan ini kepada:</div>
            <div class="nama">{{ u.full_name }}</div>
            <div class="isi">"Atas cahaya kegigihan yang kau pancarkan, melukis dedikasi dalam jejak langkah perjuangan, serta kesetiaan yang tak luntur dalam memajukan panji Ikatan Pelajar Muhammadiyah di Pimpinan Ranting SMK Muhammadiyah 1 Tangerang."</div>
            <div class="signature-container">
                <div class="sig-box"><div class="sig-space"></div><div class="sig-line">KETUA UMUM</div></div>
                <div class="sig-box">
                    <div class="date-info">Tangerang, {{ datetime.now(WIB).strftime('%d %B %Y') }}</div>
                    <div class="sig-space"></div>
                    <div class="sig-line">SEKRETARIS UMUM</div>
                </div>
            </div>
        </div>
        <div class="controls">
            <button onclick="saveAsImage()" class="btn-action">💾 SIMPAN SEBAGAI GAMBAR</button>
            <a href="/profil" class="btn-action" style="background: #333; color: white;">KEMBALI</a>
        </div>
        <script>
            function saveAsImage() {
                const element = document.getElementById('piagam-area');
                html2canvas(element, { scale: 2 }).then(canvas => {
                    const link = document.createElement('a');
                    link.download = 'Piagam_IPM_{{ u.full_name }}.png';
                    link.href = canvas.toDataURL();
                    link.click();
                });
            }
        </script>
    </body></html>""", u=u, datetime=datetime, WIB=WIB)

@app.route('/lapor', methods=['GET', 'POST'])
def lapor():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        db.session.add(Laporan(user_id=session['user_id'], nama_pelapor=session['user_name'], pesan=sanitize_input(request.form.get('pesan')), waktu_lapor=get_now_wib()))
        db.session.commit(); flash("Laporan terkirim!"); return redirect('/')
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-5"><div class="glass-card mx-auto" style="max-width:500px; border-left: 5px solid #ff4d4d;"><h4 class="text-danger fw-bold mb-3">LAPOR KENDALA</h4><form method="POST"><textarea name="pesan" class="form-control mb-3" rows="4" placeholder="Jelaskan masalah..."></textarea><button type="submit" class="btn btn-danger w-100 py-3">KIRIM ADUAN</button></form></div></div>""" + UI_CORE_FOOTER)

@app.route('/hapus/user/<int:id>')
def hapus_user(id):
    if session.get('role') == 'admin':
        u = User.query.get(id)
        if u and u.username != 'dafitrah': db.session.delete(u); db.session.commit()
    return redirect('/admin')

@app.route('/struktur')
def struktur(): return render_template_string(UI_CORE_HEADER + """<div class="container mt-5"><h3 class="text-gold fw-bold mb-4">STRUKTUR</h3><div class="glass-card">Data sedang diperbarui.</div></div>""" + UI_CORE_FOOTER)

@app.route('/agenda')
def agenda(): return render_template_string(UI_CORE_HEADER + """<div class="container mt-5"><h3 class="text-gold fw-bold mb-4">AGENDA</h3><div class="glass-card">Belum ada agenda.</div></div>""" + UI_CORE_FOOTER)

@app.errorhandler(429)
def ratelimit_handler(e): return render_template_string(UI_CORE_HEADER + """<div class="container mt-5 text-center"><div class="glass-card py-5"><h1 class="text-danger fw-bold">AKSES DIBATASI</h1><p class="text-secondary">Tunggu beberapa saat.</p></div></div>""" + UI_CORE_FOOTER), 429

if __name__ == '__main__':
    app.run(debug=True)

