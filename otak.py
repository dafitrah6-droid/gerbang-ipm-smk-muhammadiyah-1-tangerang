import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz
from datetime import datetime

WIB = pytz.timezone('Asia/Jakarta')

def get_now_wib():
    return datetime.now(WIB)
app = Flask(__name__)
app.secret_key = 'ipm_smkm1_tgr_luxury_2026_dafitrah_ultimate'

# --- CONFIGURATION DATABASE (Hanya bagian ini yang disesuaikan agar tidak Error 500) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/ipm_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    role = db.Column(db.String(20), default='member')
    created_at = db.Column(db.DateTime, default=get_now_wib)
    absensi = db.relationship('Absensi', backref='user', lazy=True)

class Kas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipe = db.Column(db.String(10)) 
    jumlah = db.Column(db.Integer)
    keterangan = db.Column(db.String(200))
    tanggal = db.Column(db.DateTime, default=datetime.now)

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
    waktu_hadir = db.Column(db.DateTime, default=datetime.now)

class Laporan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nama_pelapor = db.Column(db.String(100))
    pesan = db.Column(db.Text, nullable=False)
    waktu_lapor = db.Column(db.DateTime, default=datetime.now)

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
            whatsapp='08123456789',
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
        :root { --gold: #d4af37; --dark-bg: #0b0d11; --card-bg: rgba(255, 255, 255, 0.03); }
        body { background-color: var(--dark-bg); color: #e0e0e0; font-family: 'Inter', sans-serif; min-height: 100vh; overflow-x: hidden; }
        * { transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1); }
        .navbar-ipm { background: rgba(11, 13, 17, 0.98); border-bottom: 1px solid rgba(212, 175, 55, 0.3); padding: 15px 5%; position: sticky; top: 0; z-index: 1000; backdrop-filter: blur(15px); }
        .glass-card { background: var(--card-bg); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 25px; backdrop-filter: blur(10px); }
        .glass-card:hover { transform: translateY(-5px); border-color: var(--gold); box-shadow: 0 10px 30px rgba(212, 175, 55, 0.1); }
        .btn-gold { background: linear-gradient(135deg, #d4af37 0%, #f2d06b 100%); color: #000; border: none; padding: 12px 25px; border-radius: 12px; font-weight: 700; width: 100%; text-decoration: none; text-transform: uppercase; display: inline-block; text-align: center; border: none; cursor: pointer;}
        .btn-gold:hover { transform: scale(1.02); box-shadow: 0 5px 20px rgba(212, 175, 55, 0.5); color: #000; }
        .form-control, .form-select { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: #fff !important; border-radius: 10px !important; padding: 12px !important; }
        .form-control:focus { border-color: var(--gold) !important; box-shadow: 0 0 10px rgba(212, 175, 55, 0.2); }
        .text-gold { color: var(--gold) !important; }
        .kta-card { width: 350px; height: 200px; background: linear-gradient(135deg, #1a1c20 0%, #0b0d11 100%); border: 2px solid var(--gold); border-radius: 15px; position: relative; overflow: hidden; margin: 0 auto; animation: floating 3s ease-in-out infinite; }
        
        .fab-lapor {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            background: #ff4d4d;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 5px 20px rgba(255, 77, 77, 0.4);
            text-decoration: none;
            z-index: 9999;
            border: 2px solid rgba(255,255,255,0.2);
        }
        .fab-lapor:hover {
            transform: scale(1.1) rotate(15deg);
            background: #ff3333;
            color: white;
            box-shadow: 0 8px 25px rgba(255, 77, 77, 0.6);
        }
        .fab-label {
            position: absolute;
            right: 70px;
            background: #ff4d4d;
            color: white;
            padding: 5px 15px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: bold;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: 0.3s;
        }
        .fab-lapor:hover .fab-label {
            opacity: 1;
            right: 80px;
        }

        @keyframes floating { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
    </style>
</head>
<body>
    {% if session.user_id %}
    <a href="/lapor" class="fab-lapor animate__animated animate__bounceInUp">
        <i class="bi bi-exclamation-triangle"></i>
        <span class="fab-label">LAPOR MASALAH</span>
    </a>
    {% endif %}

    <nav class="navbar-ipm d-flex justify-content-between align-items-center">
        <div class="fw-bold fs-4 animate__animated animate__fadeInLeft">
            <a href="/" class="text-white text-decoration-none">IPM <span class="text-gold">PORTAL</span></a>
        </div>
        <div class="d-flex align-items-center animate__animated animate__fadeInRight">
            {% if session.user_id %}
                {% if session.role == 'admin' %}
                    <a href="/admin" class="btn btn-outline-warning btn-sm me-3"><i class="bi bi-shield-lock"></i> Admin Panel</a>
                {% endif %}
                <a href="/profil" class="text-white me-3 text-decoration-none small"><i class="bi bi-person-circle"></i> Profil Saya</a>
                <a href="/logout" class="text-danger text-decoration-none small">Logout</a>
            {% endif %}
        </div>
    </nav>
    <div class="container mt-3">
        {% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}
            <div class="alert alert-warning border-warning bg-dark text-warning animate__animated animate__shakeX alert-dismissible fade show" role="alert">
                {{ m }}
                <button type="button" class="btn-close btn-close-white" data-bs-alert aria-label="Close"></button>
            </div>
        {% endfor %}{% endif %}{% endwith %}
    </div>
"""

UI_CORE_FOOTER = """
    <footer class="text-center py-5 mt-5 opacity-50 small"><p>&copy; 2026 IPM SMKM 1 TGR | Dev by <strong>Muhammad Dafitrah</strong></p></footer>
    <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script> AOS.init({ duration: 1000, once: true }); </script>
</body></html>
"""

# --- ROUTES ---

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('u').lower()
        p = request.form.get('p')
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            session.update({'user_id': user.id, 'user_name': user.full_name, 'role': user.role})
            return redirect('/')
        flash("Username/Password salah!")
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5 pt-5" data-aos="zoom-in"><div class="glass-card mx-auto shadow" style="max-width:400px; border: 1px solid var(--gold);">
        <h3 class="text-gold fw-bold text-center mb-4">LOGIN KADER</h3>
        <form method="POST">
            <input name="u" class="form-control mb-3" placeholder="Username" required>
            <input type="password" name="p" class="form-control mb-4" placeholder="Password" required>
            <button type="submit" class="btn-gold">MASUK</button>
        </form>
        <div class="text-center mt-3 small">Belum terdaftar? <a href="/register" class="text-gold">Daftar</a></div>
    </div></div>""" + UI_CORE_FOOTER)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('u').lower().strip()
        password = request.form.get('p')
        full_name = request.form.get('fn')
        
        if User.query.filter_by(username=username).first():
            flash("Username sudah digunakan!")
        else:
            hashed_p = generate_password_hash(password)
            new_user = User(
                username=username, password=hashed_p, full_name=full_name,
                gmail=request.form.get('gm'), nis=request.form.get('nis'),
                kelas=request.form.get('kls'), whatsapp=request.form.get('wa')
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registrasi Berhasil! Silakan Login.")
            return redirect('/login')
            
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-4 mb-5" data-aos="zoom-in">
        <div class="glass-card mx-auto" style="max-width:550px; border: 1px solid var(--gold);">
            <h3 class="text-gold fw-bold text-center">PENDAFTARAN KADER</h3>
            <p class="small text-secondary text-center">Isi data dengan benar untuk pembuatan KTA & Piagam otomatis.</p>
            <form method="POST">
                <label class="small text-gold">Nama Lengkap (Sesuai Ijazah)</label>
                <input name="fn" class="form-control mb-3" placeholder="Contoh: Muhammad Dafitrah" required>
                <div class="row mb-3">
                    <div class="col-6"><label class="small text-gold">Username</label><input name="u" class="form-control" placeholder="kecil & tanpa spasi" required></div>
                    <div class="col-6"><label class="small text-gold">Password</label><input type="password" name="p" class="form-control" placeholder="Min 6 Karakter" required></div>
                </div>
                <label class="small text-gold">Email Aktif</label>
                <input name="gm" type="email" class="form-control mb-3" placeholder="dafitrah@gmail.com" required>
                <div class="row mb-3">
                    <div class="col-6"><label class="small text-gold">NIS</label><input name="nis" class="form-control" required></div>
                    <div class="col-6"><label class="small text-gold">Kelas</label><input name="kls" class="form-control" placeholder="Contoh: XII RPL 1" required></div>
                </div>
                <label class="small text-gold">No. WhatsApp</label>
                <input name="wa" class="form-control mb-4" placeholder="08xxxx" required>
                <button type="submit" class="btn-gold">DAFTAR SEKARANG</button>
            </form>
        </div>
    </div>
    """ + UI_CORE_FOOTER)

@app.route('/')
def home():
    if 'user_id' not in session: return redirect('/login')
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5 text-center">
        <div data-aos="zoom-out">
            <h1 class="text-gold fw-bold display-4" style="letter-spacing: 5px;">IPM PORTAL</h1>
            <p class="text-secondary">Pimpinan Ranting SMK Muhammadiyah 1 Tangerang</p>
        </div>
        <div class="row g-4 mt-4">
            <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="100"><div class="glass-card"><i class="bi bi-fingerprint text-gold fs-1"></i><h6 class="mt-2">Absen</h6><a href="/absen" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div>
            <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="200"><div class="glass-card"><i class="bi bi-wallet2 text-gold fs-1"></i><h6 class="mt-2">Uang Kas</h6><a href="/kas" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div>
            <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="300"><div class="glass-card"><i class="bi bi-diagram-3 text-gold fs-1"></i><h6 class="mt-2">Struktur</h6><a href="/struktur" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div>
            <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="400"><div class="glass-card"><i class="bi bi-calendar-event text-gold fs-1"></i><h6 class="mt-2">Agenda</h6><a href="/agenda" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div>
        </div>
    </div>
    """ + UI_CORE_FOOTER)

@app.route('/profil')
def profil():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5" data-aos="fade-up"><div class="row justify-content-center"><div class="col-md-6"><div class="glass-card">
        <div class="text-center mb-4"><i class="bi bi-person-circle text-gold" style="font-size: 80px;"></i><h3 class="text-gold fw-bold">{{ u.full_name }}</h3></div>
        <div class="row g-2 small mb-4">
            <div class="col-5 text-secondary">NIS / ID</div><div class="col-7">: {{ u.nis }}</div>
            <div class="col-5 text-secondary">Kelas</div><div class="col-7">: {{ u.kelas }}</div>
            <div class="col-5 text-secondary">Status</div><div class="col-7">: {{ u.role.upper() }}</div>
        </div>
        <hr class="opacity-25">
        <h6 class="text-gold mb-3"><i class="bi bi-patch-check"></i> Menu Administrasi Kader</h6>
        <div class="row g-2 mb-2">
            <div class="col-6"><a href="/kta" class="btn btn-outline-warning w-100 btn-sm py-3"><i class="bi bi-card-heading"></i><br>KTA DIGITAL</a></div>
            <div class="col-6"><a href="/piagam" class="btn btn-outline-warning w-100 btn-sm py-3"><i class="bi bi-award"></i><br>PIAGAM</a></div>
        </div>
        <a href="/edit-profil" class="btn btn-outline-info btn-sm w-100 mb-2"><i class="bi bi-pencil-square"></i> EDIT DATA DIRI</a>
        <a href="/" class="btn btn-gold btn-sm w-100 mt-2">KEMBALI KE DASHBOARD</a>
    </div></div></div></div>
    """ + UI_CORE_FOOTER, u=u)

@app.route('/edit-profil', methods=['GET', 'POST'])
def edit_profil():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        u.full_name = request.form.get('fn')
        u.gmail = request.form.get('gm')
        u.nis = request.form.get('nis')
        u.kelas = request.form.get('kls')
        u.whatsapp = request.form.get('wa')
        session['user_name'] = u.full_name
        db.session.commit()
        flash("Profil Berhasil Diperbarui!")
        return redirect('/profil')
        
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-4 mb-5" data-aos="zoom-in">
        <div class="glass-card mx-auto" style="max-width:550px; border: 1px solid var(--gold);">
            <h3 class="text-gold fw-bold text-center">EDIT PROFIL SAYA</h3>
            <p class="small text-secondary text-center">Perbarui data diri kamu di sini.</p>
            <form method="POST">
                <label class="small text-gold">Nama Lengkap</label>
                <input name="fn" class="form-control mb-3" value="{{ u.full_name }}" required>
                <label class="small text-gold">Email Aktif</label>
                <input name="gm" type="email" class="form-control mb-3" value="{{ u.gmail }}" required>
                <div class="row mb-3">
                    <div class="col-6"><label class="small text-gold">NIS</label><input name="nis" class="form-control" value="{{ u.nis }}" required></div>
                    <div class="col-6"><label class="small text-gold">Kelas</label><input name="kls" class="form-control" value="{{ u.kelas }}" required></div>
                </div>
                <label class="small text-gold">No. WhatsApp</label>
                <input name="wa" class="form-control mb-4" value="{{ u.whatsapp }}" required>
                <div class="row g-2">
                    <div class="col-6"><a href="/profil" class="btn btn-outline-secondary w-100">BATAL</a></div>
                    <div class="col-6"><button type="submit" class="btn-gold">SIMPAN PERUBAHAN</button></div>
                </div>
            </form>
        </div>
    </div>
    """ + UI_CORE_FOOTER, u=u)

@app.route('/struktur', methods=['GET', 'POST'])
def struktur():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST' and session.get('role') == 'admin':
        db.session.add(Struktur(jabatan=request.form.get('jabatan'), nama=request.form.get('nama'), bidang=request.form.get('bidang')))
        db.session.commit()
        return redirect('/struktur')
    pimpinan = Struktur.query.all()
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5" data-aos="fade-left"><h3 class="text-gold fw-bold mb-4">STRUKTUR PIMPINAN</h3>
        {% if session.role == 'admin' %}
        <div class="glass-card mb-4" data-aos="fade-right">
            <h6 class="text-gold mb-3"><i class="bi bi-plus-circle"></i> Tambah Pengurus Baru</h6>
            <form method="POST" class="row g-2">
                <div class="col-md-4"><input name="jabatan" class="form-control" placeholder="Jabatan" required></div>
                <div class="col-md-4"><input name="nama" class="form-control" placeholder="Nama Lengkap" required></div>
                <div class="col-md-2"><input name="bidang" class="form-control" placeholder="Bidang"></div>
                <div class="col-md-2"><button type="submit" class="btn-gold">TAMBAH</button></div>
            </form>
        </div>
        {% endif %}
        <div class="glass-card" data-aos="zoom-in-up"><div class="table-responsive"><table class="table table-dark">
            <thead><tr class="text-gold"><th>Jabatan</th><th>Nama</th><th>Bidang</th>{% if session.role == 'admin' %}<th>Aksi</th>{% endif %}</tr></thead>
            <tbody>{% for p in pimpinan %}<tr><td>{{ p.jabatan }}</td><td>{{ p.nama }}</td><td>{{ p.bidang }}</td>
            {% if session.role == 'admin' %}<td><a href="/hapus/struktur/{{ p.id }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Hapus data ini?')">Hapus</a></td>{% endif %}</tr>{% endfor %}</tbody>
        </table></div></div>
    </div>
    """ + UI_CORE_FOOTER, pimpinan=pimpinan)

@app.route('/absen', methods=['GET', 'POST'])
def absen():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        today = get_now_wib().date()
        already = Absensi.query.filter(Absensi.user_id == session['user_id'], db.func.date(Absensi.waktu_hadir) == today).first()
        if already: flash("Sudah absen hari ini!")
        else:
    db.session.add(
        Absensi(
            user_id=session['user_id'],
            nama_kader=session['user_name'],
            waktu_hadir=get_now_wib()
        )
    )
    db.session.commit()
    flash("Absensi Berhasil!")
            flash("Absensi Berhasil!")
        return redirect('/absen')
    logs = Absensi.query.order_by(Absensi.waktu_hadir.desc()).limit(15).all()
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5"><div class="row">
        <div class="col-md-4 mb-4" data-aos="fade-right"><div class="glass-card text-center">
            <h4 class="text-gold fw-bold">PRESENSI</h4>
            <form method="POST"><button type="submit" class="btn-gold py-4 fs-3"><i class="bi bi-fingerprint"></i><br>HADIR</button></form>
        </div></div>
        <div class="col-md-8" data-aos="fade-left"><div class="glass-card"><h5 class="text-gold">Log Kehadiran Baru</h5>
            <table class="table table-dark small">
                <thead><tr><th>Kader</th><th>Waktu</th>{% if session.role == 'admin' %}<th>Aksi</th>{% endif %}</tr></thead>
                <tbody>{% for l in logs %}<tr>
                    <td>{{ l.nama_kader }}</td>
                    <td>{{ l.waktu_hadir.strftime('%H:%M - %d/%m') }}</td>
                    {% if session.role == 'admin' %}
                    <td><a href="/hapus/absen/{{ l.id }}" class="text-danger" onclick="return confirm('Hapus log?')"><i class="bi bi-trash"></i></a></td>
                    {% endif %}
                </tr>{% endfor %}</tbody>
            </table>
        </div></div>
    </div></div>""" + UI_CORE_FOOTER, logs=logs)

@app.route('/kas', methods=['GET', 'POST'])
def kas():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        try:
            nominal = int(request.form.get('j') or 0)
            db.session.add(Kas(tipe=request.form.get('t'), jumlah=nominal, keterangan=request.form.get('k')))
            db.session.commit()
            flash("Data Kas Berhasil Disimpan!")
        except Exception as e:
            flash("Gagal menyimpan data!")
        return redirect('/kas')
    
    data = Kas.query.order_by(Kas.tanggal.desc()).all()
    pemasukan = sum(d.jumlah for d in data if d.tipe == 'masuk' and d.jumlah is not None)
    pengeluaran = sum(d.jumlah for d in data if d.tipe == 'keluar' and d.jumlah is not None)
    saldo = pemasukan - pengeluaran
    
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-4">
        <div class="glass-card text-center mb-4" data-aos="zoom-in-down">
            <span class="text-secondary small">SALDO KAS RANTING</span>
            <h1 class="text-gold fw-bold">Rp {{ "{:,.0f}".format(saldo) if saldo else '0' }}</h1>
        </div>
        <div class="row">
            <div class="col-md-4 mb-3" data-aos="fade-up-right"><div class="glass-card">
                <h6 class="text-gold mb-3"><i class="bi bi-plus-slash-minus"></i> Catat Transaksi</h6>
                <form method="POST">
                    <select name="t" class="form-select mb-3"><option value="masuk">Pemasukan (+)</option><option value="keluar">Pengeluaran (-)</option></select>
                    <input type="number" name="j" class="form-control mb-3" placeholder="Nominal" required>
                    <input name="k" class="form-control mb-3" placeholder="Keterangan" required>
                    <button type="submit" class="btn-gold">SIMPAN DATA</button>
                </form>
            </div></div>
            <div class="col-md-8" data-aos="fade-up-left"><div class="glass-card"><table class="table table-dark small">
                <thead><tr class="text-gold"><th>Ket</th><th>Jumlah</th></tr></thead>
                <tbody>{% for d in data %}<tr><td>{{ d.keterangan }}</td><td class="{{ 'text-success' if d.tipe == 'masuk' else 'text-danger' }}">{{ '+' if d.tipe == 'masuk' else '-' }} {{ "{:,.0f}".format(d.jumlah) }}</td></tr>{% endfor %}</tbody>
            </table></div></div>
        </div>
    </div>""" + UI_CORE_FOOTER, data=data, saldo=saldo)

@app.route('/agenda', methods=['GET', 'POST'])
def agenda():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST' and session.get('role') == 'admin':
        db.session.add(Agenda(judul=request.form.get('judul'), waktu=request.form.get('waktu'), lokasi=request.form.get('lokasi')))
        db.session.commit()
        return redirect('/agenda')
    semua_agenda = Agenda.query.all()
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5">
        <h3 class="text-gold fw-bold mb-4 text-center" data-aos="fade-down">AGENDA KEGIATAN</h3>
        {% if session.role == 'admin' %}
        <div class="glass-card mb-4" data-aos="zoom-in">
            <h6 class="text-gold mb-3"><i class="bi bi-calendar-plus"></i> Buat Agenda Baru</h6>
            <form method="POST" class="row g-2">
                <div class="col-md-4"><input name="judul" class="form-control" placeholder="Nama Kegiatan" required></div>
                <div class="col-md-3"><input name="waktu" class="form-control" placeholder="Waktu" required></div>
                <div class="col-md-3"><input name="lokasi" class="form-control" placeholder="Lokasi" required></div>
                <div class="col-md-2"><button type="submit" class="btn-gold">SIMPAN</button></div>
            </form>
        </div>
        {% endif %}
        <div class="row">{% for a in semua_agenda %}<div class="col-md-4 mb-3" data-aos="flip-left" data-aos-delay="{{ loop.index * 100 }}"><div class="glass-card border-start border-gold border-4">
            <h5 class="text-gold">{{ a.judul }}</h5><p class="small text-white mb-0">{{ a.waktu }}</p><p class="small text-secondary">{{ a.lokasi }}</p>
            {% if session.role == 'admin' %}<a href="/hapus/agenda/{{ a.id }}" class="text-danger small text-decoration-none" onclick="return confirm('Hapus agenda?')">Hapus Agenda</a>{% endif %}
        </div></div>{% endfor %}</div>
    </div>""" + UI_CORE_FOOTER, semua_agenda=semua_agenda)

@app.route('/lapor', methods=['GET', 'POST'])
def lapor():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        pesan = request.form.get('pesan')
        if pesan:
            db.session.add(Laporan(user_id=session['user_id'], nama_pelapor=session['user_name'], pesan=pesan))
            db.session.commit()
            flash("Laporan berhasil dikirim! Admin akan segera mengecek.")
            return redirect('/')
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5" data-aos="zoom-in">
        <div class="glass-card mx-auto shadow" style="max-width:500px; border: 1px solid #ff4d4d;">
            <h3 class="text-danger fw-bold"><i class="bi bi-exclamation-triangle"></i> LAPOR MASALAH</h3>
            <p class="small text-secondary">Jelaskan error atau kendala yang kamu temukan di sistem ini.</p>
            <form method="POST">
                <textarea name="pesan" class="form-control mb-3" rows="5" placeholder="Tulis laporan di sini..." required></textarea>
                <button type="submit" class="btn btn-danger w-100 fw-bold py-2">KIRIM KE ADMIN</button>
                <a href="/" class="btn btn-outline-secondary w-100 mt-2 btn-sm">KEMBALI</a>
            </form>
        </div>
    </div>
    """ + UI_CORE_FOOTER)

@app.route('/hapus/laporan/<int:id>')
def hapus_laporan(id):
    if session.get('role') == 'admin':
        item = Laporan.query.get(id)
        if item:
            db.session.delete(item)
            db.session.commit()
            flash("Laporan Selesai/Dihapus!")
    return redirect('/admin')

@app.route('/hapus/user/<int:id>')
def hapus_user(id):
    if session.get('role') == 'admin':
        obj = User.query.get(id)
        if obj and obj.username != 'dafitrah':
            db.session.delete(obj)
            db.session.commit()
            flash("Kader Berhasil Dihapus!")
        else:
            flash("Tidak bisa menghapus Admin Utama!")
    return redirect('/admin')

@app.route('/hapus/struktur/<int:id>')
def hapus_struktur(id):
    if session.get('role') == 'admin':
        obj = Struktur.query.get(id)
        if obj:
            db.session.delete(obj)
            db.session.commit()
            flash("Data Struktur Dihapus!")
    return redirect('/struktur')

@app.route('/hapus/kas/<int:id>')
def hapus_kas(id):
    if session.get('role') == 'admin':
        item = Kas.query.get(id)
        if item:
            db.session.delete(item)
            db.session.commit()
            flash("Catatan Kas Dihapus!")
    return redirect('/admin')

@app.route('/hapus/agenda/<int:id>')
def hapus_agenda(id):
    if session.get('role') == 'admin':
        item = Agenda.query.get(id)
        if item:
            db.session.delete(item)
            db.session.commit()
            flash("Agenda Dihapus!")
    return redirect('/admin')

@app.route('/hapus/absen/<int:id>')
def hapus_absen(id):
    if session.get('role') == 'admin':
        item = Absensi.query.get(id)
        if item:
            db.session.delete(item)
            db.session.commit()
            flash("Log Absensi Berhasil Dihapus!")
    if request.referrer and 'admin' in request.referrer:
        return redirect('/admin')
    return redirect('/absen')

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': 
        flash("Akses ditolak! Khusus Admin.")
        return redirect('/')
    
    users = User.query.all()
    kas_data = Kas.query.order_by(Kas.tanggal.desc()).all()
    agenda_data = Agenda.query.all()
    absen_data = Absensi.query.order_by(Absensi.waktu_hadir.desc()).limit(20).all()
    laporan_data = Laporan.query.order_by(Laporan.waktu_lapor.desc()).all()
    total_kas = sum(k.jumlah if k.tipe == 'masuk' else -k.jumlah for k in kas_data)
    
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5">
        <h2 class="text-gold fw-bold mb-4 animate__animated animate__fadeInDown"><i class="bi bi-shield-check"></i> PANEL KONTROL PIMPINAN</h2>
        
        <div class="row mb-5 g-3">
            <div class="col-md-3"><div class="glass-card text-center"><small class="text-secondary">TOTAL KADER</small><h3 class="text-gold">{{ users|length }}</h3></div></div>
            <div class="col-md-3"><div class="glass-card text-center"><small class="text-secondary">SALDO KAS</small><h3 class="text-gold">Rp {{ "{:,}".format(total_kas) }}</h3></div></div>
            <div class="col-md-3"><div class="glass-card text-center"><small class="text-secondary">AGENDA AKTIF</small><h3 class="text-gold">{{ agenda_data|length }}</h3></div></div>
            <div class="col-md-3"><div class="glass-card text-center"><small class="text-secondary">LAPORAN MASUK</small><h3 class="text-danger">{{ laporan_data|length }}</h3></div></div>
        </div>

        <div class="row">
            <div class="col-12 mb-4">
                <div class="glass-card" style="border-left: 5px solid #ff4d4d;">
                    <h5 class="text-danger mb-3"><i class="bi bi-megaphone"></i> Laporan Masalah & Bug</h5>
                    <div class="table-responsive">
                        <table class="table table-dark table-hover small">
                            <thead>
                                <tr class="text-danger">
                                    <th>Waktu</th>
                                    <th>Pelapor</th>
                                    <th>Isi Laporan</th>
                                    <th>Aksi</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for lp in laporan_data %}
                                <tr>
                                    <td style="white-space:nowrap">{{ lp.waktu_lapor.strftime('%d/%m %H:%M') }}</td>
                                    <td><strong>{{ lp.nama_pelapor }}</strong></td>
                                    <td>{{ lp.pesan }}</td>
                                    <td>
                                        <a href="/hapus/laporan/{{ lp.id }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Hapus laporan?')">Selesai</a>
                                    </td>
                                </tr>
                                {% endfor %}
                                {% if not laporan_data %}<tr><td colspan="4" class="text-center opacity-50">Tidak ada laporan masuk.</td></tr>{% endif %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="col-12 mb-4">
                <div class="glass-card">
                    <h5 class="text-gold mb-3"><i class="bi bi-people"></i> Database Seluruh Kader</h5>
                    <div class="table-responsive">
                        <table class="table table-dark table-hover small">
                            <thead>
                                <tr class="text-gold"><th>Nama Lengkap</th><th>NIS</th><th>Kelas</th><th>WhatsApp</th><th>Role</th><th>Aksi</th></tr>
                            </thead>
                            <tbody>
                                {% for u in users %}
                                <tr>
                                    <td>{{ u.full_name }}</td><td>{{ u.nis }}</td><td>{{ u.kelas }}</td>
                                    <td><a href="https://wa.me/{{ u.whatsapp }}" class="text-info">{{ u.whatsapp }}</a></td>
                                    <td><span class="badge {{ 'bg-warning text-dark' if u.role == 'admin' else 'bg-secondary' }}">{{ u.role.upper() }}</span></td>
                                    <td>{% if u.username != 'dafitrah' %}<a href="/hapus/user/{{ u.id }}" class="text-danger"><i class="bi bi-trash"></i></a>{% endif %}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="col-md-6 mb-4"><div class="glass-card"><h5 class="text-gold mb-3">Kelola Uang Kas</h5><div class="table-responsive" style="max-height: 250px;">
                <table class="table table-dark table-sm small">
                <thead><tr><th>Ket</th><th>Jumlah</th><th>Aksi</th></tr></thead>
                <tbody>{% for k in kas_data %}<tr><td>{{ k.keterangan }}</td><td class="{{ 'text-success' if k.tipe == 'masuk' else 'text-danger' }}">{{ '{:,}'.format(k.jumlah) }}</td>
                <td><a href="/hapus/kas/{{ k.id }}" class="text-danger"><i class="bi bi-trash"></i></a></td></tr>{% endfor %}</tbody></table></div></div></div>

            <div class="col-md-6 mb-4"><div class="glass-card"><h5 class="text-gold mb-3">Log Absensi</h5><div class="table-responsive" style="max-height: 250px;">
                <table class="table table-dark table-sm small">
                <thead><tr><th>Nama</th><th>Waktu</th><th>Aksi</th></tr></thead>
                <tbody>{% for ab in absen_data %}<tr><td>{{ ab.nama_kader }}</td><td>{{ ab.waktu_hadir.strftime('%H:%M') }}</td>
                <td><a href="/hapus/absen/{{ ab.id }}" class="text-danger"><i class="bi bi-trash"></i></a></td></tr>{% endfor %}</tbody></table></div></div></div>
        </div>
    </div>""" + UI_CORE_FOOTER, users=users, kas_data=kas_data, agenda_data=agenda_data, total_kas=total_kas, absen_data=absen_data, laporan_data=laporan_data)

@app.route('/kta')
def kta_digital():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5 text-center" data-aos="flip-right">
        <h3 class="text-gold fw-bold mb-4">KARTU TANDA ANGGOTA</h3>
        <div class="kta-card p-3 shadow-lg">
            <div class="d-flex justify-content-between text-start">
                <div><small class="text-gold fw-bold">IPM SMKM 1 TGR</small><br><small style="font-size:0.6rem">NUN: {{ u.nis }}</small></div>
                <i class="bi bi-qr-code text-white fs-3"></i>
            </div>
            <div class="text-start mt-3">
                <h5 class="text-white mb-0 fw-bold">{{ u.full_name }}</h5>
                <small class="text-gold">{{ u.role.upper() }} - {{ u.kelas }}</small>
            </div>
        </div>
        <button onclick="window.print()" class="btn btn-gold mt-4 btn-sm" style="width: auto;">CETAK KTA</button>
    </div>
    """ + UI_CORE_FOOTER, u=u)

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
            .piagam { 
                width: 900px; 
                height: 630px; 
                background: #1a1c20; 
                border: 15px solid #d4af37; 
                padding: 60px; 
                text-align: center; 
                font-family: 'Cinzel', serif; 
                position: relative;
                box-shadow: 0 0 50px rgba(0,0,0,0.5);
                overflow: hidden;
            }
            .piagam::before {
                content: "";
                position: absolute;
                top: 10px; left: 10px; right: 10px; bottom: 10px;
                border: 2px solid rgba(212, 175, 55, 0.3);
                pointer-events: none;
            }
            .semboyan { color: #d4af37; letter-spacing: 5px; font-size: 0.9rem; margin-bottom: 30px; }
            .judul { font-size: 3.5rem; margin: 0; color: #fff; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
            .presents { font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.2rem; margin-top: 10px; color: #aaa; }
            .nama { font-family: 'Great Vibes', cursive; font-size: 5rem; color: #d4af37; margin: 15px 0; }
            .isi { 
                font-family: 'Playfair Display', serif; 
                font-size: 1.15rem; 
                line-height: 1.8; 
                color: #e0e0e0; 
                max-width: 700px; 
                margin: 0 auto;
                font-style: italic;
            }
            .signature-container {
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
                margin-top: 60px;
                padding: 0 80px;
            }
            .sig-box {
                width: 220px;
                text-align: center;
            }
            .sig-line {
                border-top: 1px solid #d4af37;
                padding-top: 8px;
                font-size: 0.9rem;
                color: #d4af37;
                font-weight: bold;
            }
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
            
            <div class="isi">
                "Atas cahaya kegigihan yang kau pancarkan, melukis dedikasi dalam jejak langkah perjuangan, 
                serta kesetiaan yang tak luntur dalam memajukan panji Ikatan Pelajar Muhammadiyah 
                di Pimpinan Ranting SMK Muhammadiyah 1 Tangerang."
            </div>

            <div class="signature-container">
                <div class="sig-box">
                    <div class="sig-space"></div>
                    <div class="sig-line">KETUA UMUM</div>
                </div>
                
                <div class="sig-box">
                    <div class="date-info">Tangerang, {{ datetime.now().strftime('%d %B %Y') }}</div>
                    <div class="sig-space"></div>
                    <div class="sig-line">SEKRETARIS UMUM</div>
                </div>
            </div>
        </div>

        <div class="controls">
            <button onclick="saveAsImage()" class="btn-action">💾 SIMPAN SEBAGAI GAMBAR</button>
            <a href="/profil" class="btn-action" style="background: #333; color: white;">KEMBALI KE PROFIL</a>
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
    </body></html>""", u=u, datetime=datetime)

if __name__ == '__main__':
    app.run(debug=True)

