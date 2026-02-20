import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ipm_smkm1_tgr_luxury_2026_dafitrah_ultimate'

# --- PERBAIKAN 1: KONFIGURASI DATABASE UNTUK VERCEL ---
# Menggunakan folder /tmp/ karena folder proyek di Vercel bersifat Read-Only
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/ipm_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Mengaktifkan engine options agar SQLite lebih stabil
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {"check_same_thread": False}
}
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
    created_at = db.Column(db.DateTime, default=datetime.now)

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

# --- PERBAIKAN 2: INISIALISASI DATABASE YANG LEBIH KUAT ---
with app.app_context():
    db.create_all()
    # Cek admin utama
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

# --- UI TEMPLATE COMPONENTS (Sama seperti sebelumnya) ---
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
        .btn-gold { background: linear-gradient(135deg, #d4af37 0%, #f2d06b 100%); color: #000; border: none; padding: 12px 25px; border-radius: 12px; font-weight: 700; width: 100%; text-decoration: none; text-transform: uppercase; display: inline-block; text-align: center; cursor: pointer; border: none; }
        .btn-gold:hover { transform: scale(1.02); box-shadow: 0 5px 20px rgba(212, 175, 55, 0.5); color: #000; }
        .form-control, .form-select { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: #fff !important; border-radius: 10px !important; padding: 12px !important; }
        .form-control:focus { border-color: var(--gold) !important; box-shadow: 0 0 10px rgba(212, 175, 55, 0.2); }
        .text-gold { color: var(--gold) !important; }
        .kta-card { width: 350px; height: 200px; background: linear-gradient(135deg, #1a1c20 0%, #0b0d11 100%); border: 2px solid var(--gold); border-radius: 15px; position: relative; overflow: hidden; margin: 0 auto; animation: floating 3s ease-in-out infinite; }
        .fab-lapor { position: fixed; bottom: 30px; right: 30px; width: 60px; height: 60px; background: #ff4d4d; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 5px 20px rgba(255, 77, 77, 0.4); text-decoration: none; z-index: 9999; border: 2px solid rgba(255,255,255,0.2); }
        @keyframes floating { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
    </style>
</head>
<body>
    {% if session.user_id %}
    <a href="/lapor" class="fab-lapor animate__animated animate__bounceInUp">
        <i class="bi bi-exclamation-triangle"></i>
    </a>
    {% endif %}
    <nav class="navbar-ipm d-flex justify-content-between align-items-center">
        <div class="fw-bold fs-4 animate__animated animate__fadeInLeft">
            <a href="/" class="text-white text-decoration-none">IPM <span class="text-gold">PORTAL</span></a>
        </div>
        <div class="d-flex align-items-center animate__animated animate__fadeInRight">
            {% if session.user_id %}
                {% if session.role == 'admin' %}
                    <a href="/admin" class="btn btn-outline-warning btn-sm me-3"><i class="bi bi-shield-lock"></i> Admin</a>
                {% endif %}
                <a href="/profil" class="text-white me-3 text-decoration-none small">Profil</a>
                <a href="/logout" class="text-danger text-decoration-none small">Logout</a>
            {% endif %}
        </div>
    </nav>
    <div class="container mt-3">
        {% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}
            <div class="alert alert-warning bg-dark text-warning border-warning alert-dismissible fade show" role="alert">
                {{ m }} <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
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
        u = request.form.get('u', '').lower().strip()
        p = request.form.get('p', '')
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
        username = request.form.get('u', '').lower().strip()
        if User.query.filter_by(username=username).first():
            flash("Username sudah digunakan!")
        else:
            hashed_p = generate_password_hash(request.form.get('p'))
            new_user = User(
                username=username, password=hashed_p, full_name=request.form.get('fn'),
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
            <h3 class="text-gold fw-bold text-center">PENDAFTARAN</h3>
            <form method="POST">
                <input name="fn" class="form-control mb-3" placeholder="Nama Lengkap" required>
                <div class="row mb-3">
                    <div class="col-6"><input name="u" class="form-control" placeholder="Username" required></div>
                    <div class="col-6"><input type="password" name="p" class="form-control" placeholder="Password" required></div>
                </div>
                <input name="gm" type="email" class="form-control mb-3" placeholder="Email" required>
                <div class="row mb-3">
                    <div class="col-6"><input name="nis" class="form-control" placeholder="NIS" required></div>
                    <div class="col-6"><input name="kls" class="form-control" placeholder="Kelas" required></div>
                </div>
                <input name="wa" class="form-control mb-4" placeholder="WhatsApp (08...)" required>
                <button type="submit" class="btn-gold">DAFTAR SEKARANG</button>
            </form>
        </div>
    </div>""" + UI_CORE_FOOTER)

@app.route('/')
def home():
    if 'user_id' not in session: return redirect('/login')
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5 text-center">
        <div data-aos="zoom-out"><h1 class="text-gold fw-bold display-4">IPM PORTAL</h1><p class="text-secondary">SMK Muhammadiyah 1 Tangerang</p></div>
        <div class="row g-4 mt-4">
            <div class="col-md-3 col-6"><div class="glass-card"><i class="bi bi-fingerprint text-gold fs-1"></i><h6>Absen</h6><a href="/absen" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div>
            <div class="col-md-3 col-6"><div class="glass-card"><i class="bi bi-wallet2 text-gold fs-1"></i><h6>Kas</h6><a href="/kas" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div>
            <div class="col-md-3 col-6"><div class="glass-card"><i class="bi bi-diagram-3 text-gold fs-1"></i><h6>Struktur</h6><a href="/struktur" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div>
            <div class="col-md-3 col-6"><div class="glass-card"><i class="bi bi-calendar-event text-gold fs-1"></i><h6>Agenda</h6><a href="/agenda" class="btn-gold btn-sm mt-2 w-100">Buka</a></div></div>
        </div>
    </div>""" + UI_CORE_FOOTER)

@app.route('/profil')
def profil():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5" data-aos="fade-up"><div class="row justify-content-center"><div class="col-md-6"><div class="glass-card">
        <div class="text-center mb-4"><i class="bi bi-person-circle text-gold fs-1"></i><h3 class="text-gold fw-bold">{{ u.full_name }}</h3></div>
        <div class="row small mb-4">
            <div class="col-5">NIS</div><div class="col-7">: {{ u.nis }}</div>
            <div class="col-5">Kelas</div><div class="col-7">: {{ u.kelas }}</div>
            <div class="col-5">Role</div><div class="col-7">: {{ u.role.upper() }}</div>
        </div>
        <div class="row g-2">
            <div class="col-6"><a href="/kta" class="btn btn-outline-warning w-100 btn-sm">KTA</a></div>
            <div class="col-6"><a href="/piagam" class="btn btn-outline-warning w-100 btn-sm">PIAGAM</a></div>
        </div>
        <a href="/edit-profil" class="btn btn-outline-info btn-sm w-100 mt-2">EDIT PROFIL</a>
    </div></div></div></div>""" + UI_CORE_FOOTER, u=u)

@app.route('/edit-profil', methods=['GET', 'POST'])
def edit_profil():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    if request.method == 'POST':
        u.full_name, u.gmail, u.nis, u.kelas, u.whatsapp = request.form.get('fn'), request.form.get('gm'), request.form.get('nis'), request.form.get('kls'), request.form.get('wa')
        db.session.commit()
        flash("Profil diperbarui!")
        return redirect('/profil')
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-4"><div class="glass-card mx-auto" style="max-width:500px;">
        <h3 class="text-gold text-center">EDIT PROFIL</h3>
        <form method="POST">
            <input name="fn" class="form-control mb-2" value="{{ u.full_name }}">
            <input name="gm" class="form-control mb-2" value="{{ u.gmail }}">
            <input name="nis" class="form-control mb-2" value="{{ u.nis }}">
            <input name="kls" class="form-control mb-2" value="{{ u.kelas }}">
            <input name="wa" class="form-control mb-3" value="{{ u.whatsapp }}">
            <button type="submit" class="btn-gold">SIMPAN</button>
        </form>
    </div></div>""" + UI_CORE_FOOTER, u=u)

@app.route('/kas', methods=['GET', 'POST'])
def kas():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        try:
            nominal = int(request.form.get('j', 0))
            db.session.add(Kas(tipe=request.form.get('t'), jumlah=nominal, keterangan=request.form.get('k')))
            db.session.commit()
            flash("Data Kas Berhasil Disimpan!")
        except: flash("Gagal simpan data!")
        return redirect('/kas')
    
    # PERBAIKAN 3: LOGIKA SALDO ANTI-CRASH
    data = Kas.query.order_by(Kas.tanggal.desc()).all()
    pemasukan = sum(d.jumlah for d in data if d.tipe == 'masuk' and d.jumlah)
    pengeluaran = sum(d.jumlah for d in data if d.tipe == 'keluar' and d.jumlah)
    saldo = pemasukan - pengeluaran
    
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-4">
        <div class="glass-card text-center mb-4">
            <span class="text-secondary small">SALDO KAS</span>
            <h1 class="text-gold fw-bold">Rp {{ "{:,.0f}".format(saldo) }}</h1>
        </div>
        <div class="row">
            <div class="col-md-4 mb-3"><div class="glass-card">
                <form method="POST">
                    <select name="t" class="form-select mb-2"><option value="masuk">Masuk (+)</option><option value="keluar">Keluar (-)</option></select>
                    <input type="number" name="j" class="form-control mb-2" placeholder="Nominal" required>
                    <input name="k" class="form-control mb-3" placeholder="Keterangan" required>
                    <button type="submit" class="btn-gold">SIMPAN</button>
                </form>
            </div></div>
            <div class="col-md-8"><div class="glass-card"><table class="table table-dark small">
                <thead><tr class="text-gold"><th>Ket</th><th>Jumlah</th></tr></thead>
                <tbody>{% for d in data %}<tr><td>{{ d.keterangan }}</td><td class="{{ 'text-success' if d.tipe == 'masuk' else 'text-danger' }}">{{ '+' if d.tipe == 'masuk' else '-' }} {{ "{:,.0f}".format(d.jumlah) }}</td></tr>{% endfor %}</tbody>
            </table></div></div>
        </div>
    </div>""" + UI_CORE_FOOTER, data=data, saldo=saldo)

# --- ROUTES STRUKTUR, ABSEN, AGENDA ---
@app.route('/struktur', methods=['GET', 'POST'])
def struktur():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST' and session.get('role') == 'admin':
        db.session.add(Struktur(jabatan=request.form.get('jabatan'), nama=request.form.get('nama'), bidang=request.form.get('bidang')))
        db.session.commit()
    pimpinan = Struktur.query.all()
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5"><h3 class="text-gold mb-4">STRUKTUR</h3>
        {% if session.role == 'admin' %}
        <form method="POST" class="row g-2 mb-4"><div class="col-md-4"><input name="jabatan" class="form-control" placeholder="Jabatan"></div><div class="col-md-4"><input name="nama" class="form-control" placeholder="Nama"></div><div class="col-md-2"><input name="bidang" class="form-control" placeholder="Bidang"></div><div class="col-md-2"><button class="btn-gold">TAMBAH</button></div></form>
        {% endif %}
        <div class="glass-card"><table class="table table-dark"><thead><tr class="text-gold"><th>Jabatan</th><th>Nama</th><th>Aksi</th></tr></thead>
        <tbody>{% for p in pimpinan %}<tr><td>{{ p.jabatan }}</td><td>{{ p.nama }}</td><td>{% if session.role == 'admin' %}<a href="/hapus/struktur/{{ p.id }}" class="text-danger">Hapus</a>{% endif %}</td></tr>{% endfor %}</tbody></table></div>
    </div>""" + UI_CORE_FOOTER, pimpinan=pimpinan)

@app.route('/absen', methods=['GET', 'POST'])
def absen():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        today = datetime.now().date()
        if Absensi.query.filter(Absensi.user_id == session['user_id'], db.func.date(Absensi.waktu_hadir) == today).first(): flash("Sudah absen!")
        else:
            db.session.add(Absensi(user_id=session['user_id'], nama_kader=session['user_name']))
            db.session.commit()
            flash("Absen Berhasil!")
        return redirect('/absen')
    logs = Absensi.query.order_by(Absensi.waktu_hadir.desc()).limit(15).all()
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5"><div class="row">
        <div class="col-md-4 mb-4"><div class="glass-card text-center"><form method="POST"><button type="submit" class="btn-gold py-4 fs-3">HADIR</button></form></div></div>
        <div class="col-md-8"><div class="glass-card"><h5 class="text-gold">Log Kehadiran</h5><table class="table table-dark small"><tbody>{% for l in logs %}<tr><td>{{ l.nama_kader }}</td><td>{{ l.waktu_hadir.strftime('%H:%M') }}</td></tr>{% endfor %}</tbody></table></div></div>
    </div></div>""" + UI_CORE_FOOTER, logs=logs)

@app.route('/agenda', methods=['GET', 'POST'])
def agenda():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST' and session.get('role') == 'admin':
        db.session.add(Agenda(judul=request.form.get('judul'), waktu=request.form.get('waktu'), lokasi=request.form.get('lokasi')))
        db.session.commit()
    semua_agenda = Agenda.query.all()
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5"><h3 class="text-gold text-center mb-4">AGENDA</h3>
        {% if session.role == 'admin' %}<form method="POST" class="row g-2 mb-4"><div class="col-4"><input name="judul" class="form-control" placeholder="Acara"></div><div class="col-3"><input name="waktu" class="form-control" placeholder="Waktu"></div><div class="col-3"><input name="lokasi" class="form-control" placeholder="Lokasi"></div><div class="col-2"><button class="btn-gold">OK</button></div></form>{% endif %}
        <div class="row">{% for a in semua_agenda %}<div class="col-md-4 mb-3"><div class="glass-card"><h5>{{ a.judul }}</h5><small>{{ a.waktu }} - {{ a.lokasi }}</small></div></div>{% endfor %}</div>
    </div>""" + UI_CORE_FOOTER, semua_agenda=semua_agenda)

@app.route('/lapor', methods=['GET', 'POST'])
def lapor():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        db.session.add(Laporan(user_id=session['user_id'], nama_pelapor=session['user_name'], pesan=request.form.get('pesan')))
        db.session.commit()
        flash("Laporan terkirim!")
        return redirect('/')
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5"><div class="glass-card mx-auto" style="max-width:500px; border-color: red;">
        <h3 class="text-danger">LAPOR BUG</h3>
        <form method="POST"><textarea name="pesan" class="form-control mb-3" rows="4" required></textarea><button class="btn btn-danger w-100">KIRIM</button></form>
    </div></div>""" + UI_CORE_FOOTER)

# --- ADMIN PANEL ---
@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': return redirect('/')
    users = User.query.all()
    kas_data = Kas.query.order_by(Kas.tanggal.desc()).all()
    laporan_data = Laporan.query.all()
    total_kas = sum(k.jumlah if k.tipe == 'masuk' else -k.jumlah for k in kas_data if k.jumlah)
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5">
        <h2 class="text-gold mb-4">ADMIN PANEL</h2>
        <div class="row mb-4">
            <div class="col-md-4"><div class="glass-card text-center">KADER: {{ users|length }}</div></div>
            <div class="col-md-4"><div class="glass-card text-center">SALDO: Rp {{ "{:,}".format(total_kas) }}</div></div>
            <div class="col-md-4"><div class="glass-card text-center">LAPORAN: {{ laporan_data|length }}</div></div>
        </div>
        <div class="glass-card mb-4"><h5 class="text-danger">Laporan Masuk</h5>
            {% for lp in laporan_data %}<div class="border-bottom border-secondary py-2 small"><strong>{{ lp.nama_pelapor }}:</strong> {{ lp.pesan }} <a href="/hapus/laporan/{{ lp.id }}" class="text-danger">Selesai</a></div>{% endfor %}
        </div>
        <div class="glass-card"><h5 class="text-gold">Data Kader</h5>
            <table class="table table-dark small">{% for u in users %}<tr><td>{{ u.full_name }}</td><td>{{ u.role }}</td><td><a href="/hapus/user/{{ u.id }}" class="text-danger">X</a></td></tr>{% endfor %}</table>
        </div>
    </div>""" + UI_CORE_FOOTER, users=users, total_kas=total_kas, laporan_data=laporan_data)

# --- SISTEM HAPUS ---
@app.route('/hapus/laporan/<int:id>')
def hapus_laporan(id):
    if session.get('role') == 'admin':
        db.session.delete(Laporan.query.get(id)); db.session.commit()
    return redirect('/admin')

@app.route('/hapus/user/<int:id>')
def hapus_user(id):
    if session.get('role') == 'admin':
        u = User.query.get(id)
        if u and u.username != 'dafitrah': db.session.delete(u); db.session.commit()
    return redirect('/admin')

@app.route('/hapus/struktur/<int:id>')
def hapus_struktur(id):
    if session.get('role') == 'admin':
        db.session.delete(Struktur.query.get(id)); db.session.commit()
    return redirect('/struktur')

# --- KTA & PIAGAM (Sesuai kode asli kamu) ---
@app.route('/kta')
def kta_digital():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-5 text-center"><div class="kta-card p-3 shadow-lg"><div class="d-flex justify-content-between text-start"><div><small class="text-gold fw-bold">IPM SMKM 1 TGR</small><br><small style="font-size:0.6rem">NUN: {{ u.nis }}</small></div><i class="bi bi-qr-code text-white fs-3"></i></div><div class="text-start mt-3"><h5 class="text-white mb-0 fw-bold">{{ u.full_name }}</h5><small class="text-gold">{{ u.role.upper() }} - {{ u.kelas }}</small></div></div><button onclick="window.print()" class="btn btn-gold mt-4 btn-sm">CETAK</button></div>""" + UI_CORE_FOOTER, u=u)

@app.route('/piagam')
def piagam():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    if Absensi.query.filter_by(user_id=u.id).count() < 1: flash("Absen dulu minimal 1 kali!"); return redirect('/profil')
    return render_template_string("""<html><body style="background:#0b0d11; color:white; text-align:center; padding:50px;"><div id="p" style="width:800px; height:500px; border:10px solid #d4af37; padding:40px; margin:auto; background:#1a1c20;"><h1>PIAGAM PENGHARGAAN</h1><h3>Diberikan kepada:</h3><h1 style="color:#d4af37;">{{ u.full_name }}</h1><p>Atas dedikasinya di IPM SMK Muhammadiyah 1 Tangerang</p></div><br><button onclick="window.print()" style="padding:10px 20px; background:#d4af37; border:none; font-weight:bold; cursor:pointer;">SIMPAN/CETAK</button><br><br><a href="/profil" style="color:gray; text-decoration:none;">KEMBALI</a></body></html>""", u=u)

# --- VERCEL REQUIREMENT ---
app = app # Agar dideteksi Vercel

if __name__ == '__main__':
    app.run(debug=True)
