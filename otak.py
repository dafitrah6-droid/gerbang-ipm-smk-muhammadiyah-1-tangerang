import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'ipm_smkm1_tgr_luxury_2026_dafitrah_ultimate_full'

# --- CONFIGURATION DATABASE (VERCEL COMPATIBLE) ---
# Menggunakan folder /tmp/ agar bisa menulis data di Vercel tanpa Error 500
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/ipm_data_full.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- TIMEZONE SETUP ---
WIB = pytz.timezone('Asia/Jakarta')

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
    role = db.Column(db.String(20), default='member') # member, moderator, admin
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(WIB))

class Kas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipe = db.Column(db.String(10)) # masuk / keluar
    jumlah = db.Column(db.Integer)
    keterangan = db.Column(db.String(200))
    tanggal = db.Column(db.DateTime, default=lambda: datetime.now(WIB))

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
    waktu_hadir = db.Column(db.DateTime, default=lambda: datetime.now(WIB))

class Laporan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nama_pelapor = db.Column(db.String(100))
    pesan = db.Column(db.Text, nullable=False)
    waktu_lapor = db.Column(db.DateTime, default=lambda: datetime.now(WIB))

# --- INITIALIZE DATABASE ---
with app.app_context():
    db.create_all()
    # Buat Akun Utama jika belum ada
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

# --- UI STYLES & COMPONENTS ---
# Menggunakan Glassmorphism & Animasi AOS
STYLE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    :root { --gold: #d4af37; --dark-bg: #0b0d11; --card-bg: rgba(255, 255, 255, 0.03); }
    body { background-color: var(--dark-bg); color: #e0e0e0; font-family: 'Inter', sans-serif; min-height: 100vh; overflow-x: hidden; }
    .glass-card { background: var(--card-bg); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 25px; backdrop-filter: blur(10px); transition: 0.4s; }
    .glass-card:hover { transform: translateY(-5px); border-color: var(--gold); box-shadow: 0 10px 30px rgba(212, 175, 55, 0.1); }
    .btn-gold { background: linear-gradient(135deg, #d4af37 0%, #f2d06b 100%); color: #000; border: none; padding: 12px 25px; border-radius: 12px; font-weight: 700; width: 100%; text-decoration: none; text-transform: uppercase; display: inline-block; text-align: center; cursor: pointer; }
    .btn-gold:hover { transform: scale(1.02); box-shadow: 0 5px 20px rgba(212, 175, 55, 0.5); color: #000; }
    .form-control, .form-select { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: #fff !important; border-radius: 10px !important; padding: 12px !important; }
    .text-gold { color: var(--gold) !important; }
    .navbar-ipm { background: rgba(11, 13, 17, 0.98); border-bottom: 1px solid rgba(212, 175, 55, 0.3); padding: 15px 5%; position: sticky; top: 0; z-index: 1000; backdrop-filter: blur(15px); }
    .kta-card { width: 350px; height: 200px; background: linear-gradient(135deg, #1a1c20 0%, #0b0d11 100%); border: 2px solid var(--gold); border-radius: 15px; position: relative; overflow: hidden; margin: 0 auto; animation: floating 3s ease-in-out infinite; }
    @keyframes floating { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
    .fab-lapor { position: fixed; bottom: 30px; right: 30px; width: 60px; height: 60px; background: #ff4d4d; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 5px 20px rgba(255, 77, 77, 0.4); text-decoration: none; z-index: 9999; }
</style>
"""

HEADER = f"""
<!DOCTYPE html><html lang="id"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    {STYLE_CSS}
</head><body>
"""

# --- AUTH ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('u', '').lower().strip()
        p = request.form.get('p', '')
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            session.update({'user_id': user.id, 'user_name': user.full_name, 'role': user.role})
            return redirect('/')
        flash("Username atau Password salah!")
    return render_template_string(HEADER + """
    <div class="container mt-5 pt-5" data-aos="zoom-in"><div class="glass-card mx-auto shadow" style="max-width:400px; border: 1px solid var(--gold);">
        <h3 class="text-gold fw-bold text-center mb-4">MASUK KADER</h3>
        <form method="POST">
            <input name="u" class="form-control mb-3" placeholder="Username" required>
            <input type="password" name="p" class="form-control mb-4" placeholder="Password" required>
            <button type="submit" class="btn-gold">LOGIN</button>
        </form>
        <div class="text-center mt-3 small">Belum punya akun? <a href="/register" class="text-gold">Daftar di sini</a></div>
    </div></div></body></html>""")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u_name = request.form.get('u', '').lower().strip()
        if User.query.filter_by(username=u_name).first():
            flash("Username sudah terpakai!")
        else:
            new_user = User(
                username=u_name,
                password=generate_password_hash(request.form.get('p')),
                full_name=request.form.get('fn'),
                gmail=request.form.get('gm'),
                nis=request.form.get('nis'),
                kelas=request.form.get('kls'),
                whatsapp=request.form.get('wa')
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registrasi Berhasil! Silakan Login.")
            return redirect('/login')
    return render_template_string(HEADER + """
    <div class="container mt-4 mb-5" data-aos="fade-up">
        <div class="glass-card mx-auto" style="max-width:550px; border: 1px solid var(--gold);">
            <h3 class="text-gold fw-bold text-center">PENDAFTARAN KADER</h3>
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
                <input name="wa" class="form-control mb-4" placeholder="WhatsApp" required>
                <button type="submit" class="btn-gold">DAFTAR SEKARANG</button>
            </form>
        </div>
    </div></body></html>""")

# --- MAIN ROUTES ---

@app.route('/')
def home():
    if 'user_id' not in session: return redirect('/login')
    return render_template_string(HEADER + """
    <nav class="navbar-ipm d-flex justify-content-between align-items-center">
        <div class="fw-bold fs-4">IPM <span class="text-gold">PORTAL</span></div>
        <div>
            <a href="/profil" class="text-white text-decoration-none me-3">Profil</a>
            <a href="/logout" class="text-danger text-decoration-none">Logout</a>
        </div>
    </nav>
    <div class="container mt-5 text-center">
        <h1 class="text-gold fw-bold display-4 animate__animated animate__fadeInDown">IPM PORTAL</h1>
        <p class="text-secondary mb-5">Pimpinan Ranting SMK Muhammadiyah 1 Tangerang</p>
        <div class="row g-4 mt-2">
            <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="100"><div class="glass-card"><i class="bi bi-fingerprint text-gold fs-1"></i><h6 class="mt-2">Absensi</h6><a href="/absen" class="btn-gold btn-sm mt-3 w-100">Buka</a></div></div>
            <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="200"><div class="glass-card"><i class="bi bi-wallet2 text-gold fs-1"></i><h6 class="mt-2">Keuangan</h6><a href="/kas" class="btn-gold btn-sm mt-3 w-100">Buka</a></div></div>
            <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="300"><div class="glass-card"><i class="bi bi-diagram-3 text-gold fs-1"></i><h6 class="mt-2">Struktur</h6><a href="/struktur" class="btn-gold btn-sm mt-3 w-100">Buka</a></div></div>
            <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="400"><div class="glass-card"><i class="bi bi-calendar-event text-gold fs-1"></i><h6 class="mt-2">Agenda</h6><a href="/agenda" class="btn-gold btn-sm mt-3 w-100">Buka</a></div></div>
        </div>
        {% if session.role in ['admin', 'moderator'] %}
        <div class="mt-5"><a href="/admin" class="btn btn-outline-warning">KE PANEL ADMIN</a></div>
        {% endif %}
    </div>
    <a href="/lapor" class="fab-lapor animate__animated animate__bounceInUp"><i class="bi bi-exclamation-triangle"></i></a>
    <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script><script>AOS.init();</script></body></html>""")

@app.route('/kas', methods=['GET', 'POST'])
def kas():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST' and session.get('role') in ['admin', 'moderator']:
        try:
            nominal = int(request.form.get('j', 0))
            new_kas = Kas(tipe=request.form.get('t'), jumlah=nominal, keterangan=request.form.get('k'))
            db.session.add(new_kas)
            db.session.commit()
            flash("Data Kas Berhasil Disimpan!")
        except: flash("Gagal menyimpan data!")
        return redirect('/kas')
    
    data_kas = Kas.query.order_by(Kas.tanggal.desc()).all()
    masuk = sum(d.jumlah for d in data_kas if d.tipe == 'masuk')
    keluar = sum(d.jumlah for d in data_kas if d.tipe == 'keluar')
    saldo = masuk - keluar
    
    return render_template_string(HEADER + """
    <div class="container mt-4">
        <a href="/" class="text-gold text-decoration-none"><i class="bi bi-arrow-left"></i> Kembali</a>
        <div class="glass-card text-center my-4">
            <span class="text-secondary small">SALDO KAS SAAT INI</span>
            <h1 class="text-gold fw-bold">Rp {{ "{:,.0f}".format(saldo) }}</h1>
        </div>
        <div class="row">
            {% if session.role in ['admin', 'moderator'] %}
            <div class="col-md-4 mb-3"><div class="glass-card">
                <h5 class="text-gold mb-3">Input Transaksi</h5>
                <form method="POST">
                    <select name="t" class="form-select mb-2"><option value="masuk">Pemasukan (+)</option><option value="keluar">Pengeluaran (-)</option></select>
                    <input type="number" name="j" class="form-control mb-2" placeholder="Nominal" required>
                    <input name="k" class="form-control mb-3" placeholder="Keterangan" required>
                    <button type="submit" class="btn-gold">SIMPAN</button>
                </form>
            </div></div>
            {% endif %}
            <div class="col-md-{{ '8' if session.role in ['admin', 'moderator'] else '12' }}">
                <div class="glass-card">
                    <h5 class="text-gold mb-3">Riwayat Keuangan</h5>
                    <table class="table table-dark small">
                        <thead><tr class="text-gold"><th>Tanggal</th><th>Ket</th><th>Jumlah</th></tr></thead>
                        <tbody>{% for d in data_kas %}<tr>
                            <td>{{ d.tanggal.strftime('%d/%m') }}</td><td>{{ d.keterangan }}</td>
                            <td class="{{ 'text-success' if d.tipe == 'masuk' else 'text-danger' }}">{{ '+' if d.tipe == 'masuk' else '-' }} {{ "{:,.0f}".format(d.jumlah) }}</td>
                        </tr>{% endfor %}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </div></body></html>""", data_kas=data_kas, saldo=saldo)

# --- PANEL ADMIN (FULL SYSTEM) ---

@app.route('/admin')
def admin_panel():
    if session.get('role') not in ['admin', 'moderator']: return redirect('/')
    users = User.query.all()
    logs_absen = Absensi.query.order_by(Absensi.waktu_hadir.desc()).limit(10).all()
    laporan_bug = Laporan.query.order_by(Laporan.waktu_lapor.desc()).all()
    return render_template_string(HEADER + """
    <div class="container mt-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="text-gold fw-bold">ADMIN PANEL</h2>
            <a href="/" class="btn btn-sm btn-outline-light">Kembali ke Home</a>
        </div>
        <div class="row g-4">
            <div class="col-md-6"><div class="glass-card"><h5>Daftar Kader</h5>
                <table class="table table-dark small">{% for u in users %}<tr>
                    <td>{{ u.full_name }}</td><td>{{ u.role }}</td>
                    <td>{% if session.role == 'admin' and u.username != 'dafitrah' %}<a href="/hapus/user/{{ u.id }}" class="text-danger">Hapus</a>{% endif %}</td>
                </tr>{% endfor %}</table>
            </div></div>
            <div class="col-md-6"><div class="glass-card"><h5>Laporan Bug</h5>
                {% for l in laporan_bug %}<div class="alert bg-dark border-secondary text-white small">
                    <strong>{{ l.nama_pelapor }}:</strong> {{ l.pesan }} <br><small class="text-secondary">{{ l.waktu_lapor.strftime('%d %b %H:%M') }}</small>
                </div>{% endfor %}
            </div></div>
        </div>
    </div></body></html>""", users=users, laporan_bug=laporan_bug)

# --- SISA ROUTE (ABSEN, LAPOR, LOGOUT, DLL) ---
@app.route('/absen', methods=['GET', 'POST'])
def absen():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        db.session.add(Absensi(user_id=session['user_id'], nama_kader=session['user_name']))
        db.session.commit()
        flash("Absen Berhasil!")
        return redirect('/absen')
    logs = Absensi.query.order_by(Absensi.waktu_hadir.desc()).all()
    return render_template_string(HEADER + """
    <div class="container mt-4"><h3 class="text-gold mb-4">PRESENSI KADER</h3>
        <div class="row"><div class="col-md-4 mb-3"><div class="glass-card text-center"><form method="POST"><button class="btn-gold py-5 fs-2">HADIR</button></form></div></div>
        <div class="col-md-8"><div class="glass-card"><h5>Riwayat Hadir (WIB)</h5>
            <table class="table table-dark">{% for l in logs %}<tr><td>{{ l.nama_kader }}</td><td>{{ l.waktu_hadir.strftime('%d %b - %H:%M:%S') }} WIB</td></tr>{% endfor %}</table>
        </div></div></div>
    </div></body></html>""", logs=logs)

@app.route('/lapor', methods=['GET', 'POST'])
def lapor():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        db.session.add(Laporan(user_id=session['user_id'], nama_pelapor=session['user_name'], pesan=request.form.get('pesan')))
        db.session.commit()
        flash("Laporan terkirim ke Pimpinan!")
        return redirect('/')
    return render_template_string(HEADER + """<div class="container mt-5"><div class="glass-card mx-auto" style="max-width:500px"><h3 class="text-danger">LAPOR MASALAH</h3><form method="POST"><textarea name="pesan" class="form-control mb-3" rows="4"></textarea><button class="btn btn-danger w-100">KIRIM LAPORAN</button></form></div></div></body></html>""")

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

@app.route('/hapus/user/<int:id>')
def hapus_user(id):
    if session.get('role') == 'admin':
        u = User.query.get(id)
        if u and u.username != 'dafitrah': db.session.delete(u); db.session.commit()
    return redirect('/admin')

# --- PROFILE & KTA (SESUAI KODE ASLI) ---
@app.route('/profil')
def profil():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    return render_template_string(HEADER + """
    <div class="container mt-5"><div class="row justify-content-center"><div class="col-md-6"><div class="glass-card text-center">
        <i class="bi bi-person-circle text-gold fs-1"></i><h3 class="text-gold">{{ u.full_name }}</h3>
        <p class="small text-secondary">{{ u.role.upper() }} | {{ u.kelas }}</p>
        <div class="text-start mt-4 px-3 small">
            <div class="row"><div class="col-4 text-secondary">NIS</div><div class="col-8">: {{ u.nis }}</div></div>
            <div class="row"><div class="col-4 text-secondary">WhatsApp</div><div class="col-8">: {{ u.whatsapp }}</div></div>
        </div>
        <div class="mt-4"><a href="/kta" class="btn btn-outline-warning w-100">LIHAT KTA DIGITAL</a></div>
    </div></div></div></div></body></html>""", u=u)

@app.route('/kta')
def kta():
    if 'user_id' not in session: return redirect('/login')
    u = User.query.get(session['user_id'])
    return render_template_string(HEADER + """
    <div class="container mt-5 text-center">
        <div class="kta-card p-3 shadow-lg">
            <div class="d-flex justify-content-between text-start">
                <div><small class="text-gold fw-bold">IPM SMKM 1 TGR</small><br><small style="font-size:0.6rem">ID: {{ u.nis }}</small></div>
                <i class="bi bi-qr-code text-white fs-3"></i>
            </div>
            <div class="text-start mt-4"><h5 class="text-white mb-0 fw-bold">{{ u.full_name }}</h5><small class="text-gold">{{ u.role.upper() }} - {{ u.kelas }}</small></div>
        </div>
        <button onclick="window.print()" class="btn btn-gold mt-4 btn-sm">CETAK KTA</button>
    </div></body></html>""", u=u)

# --- VERCEL REQUIREMENT ---
app = app

if __name__ == '__main__':
    app.run(debug=True)
