import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz # INTEGRASI WIB

app = Flask(__name__)
app.secret_key = 'ipm_smkm1_tgr_luxury_2026_dafitrah_ultimate'

# --- CONFIGURATION DATABASE (VERCEL & LOCAL SAFE) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/ipm_data_ultimate_2026.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- TIMEZONE SETTING (ASIA/JAKARTA) ---
WIB = pytz.timezone('Asia/Jakarta')

def get_now_wib():
    return datetime.now(WIB)

# --- DATABASE MODELS (LENGKAP SESUAI OTAK.PY + ENHANCEMENT) ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    gmail = db.Column(db.String(100), nullable=False) # Wajib
    nis = db.Column(db.String(20), nullable=False)   # Wajib
    kelas = db.Column(db.String(50), nullable=False) # Wajib
    whatsapp = db.Column(db.String(20), nullable=False) # Wajib
    role = db.Column(db.String(20), default='member')
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
    waktu_lapor = db.Column(db.DateTime, default=get_now_wib)

# --- INITIALIZE DATABASE ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='dafitrah').first():
        admin_pass = generate_password_hash('admin123')
        admin = User(
            username='dafitrah', password=admin_pass, full_name='Muhammad Dafitrah', 
            role='admin', nis='ADM-01', kelas='Pimpinan', whatsapp='08123456789', gmail='admin@ipm.com'
        )
        db.session.add(admin)
        db.session.commit()

# --- UI CORE (CSS & JS CHART) ---

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
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
        :root { --gold: #d4af37; --dark: #0b0d11; --card: rgba(255,255,255,0.03); }
        body { background: var(--dark); color: #e0e0e0; font-family: 'Inter', sans-serif; }
        .glass { background: var(--card); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 25px; backdrop-filter: blur(10px); }
        .btn-gold { background: linear-gradient(135deg, #d4af37 0%, #f2d06b 100%); color: #000; border: none; padding: 12px; border-radius: 12px; font-weight: 800; text-decoration: none; display: block; text-align: center; }
        .text-gold { color: var(--gold) !important; }
        .form-control { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #fff; border-radius: 10px; }
        .form-control:focus { background: rgba(255,255,255,0.1); color: #fff; border-color: var(--gold); box-shadow: none; }
        .navbar-ipm { border-bottom: 1px solid rgba(212,175,55,0.3); padding: 15px 5%; background: rgba(11,13,17,0.9); backdrop-filter: blur(10px); position: sticky; top: 0; z-index: 1000; }
        .kta-card { width: 350px; height: 210px; background: linear-gradient(135deg, #1a1c20 0%, #000 100%); border: 2px solid var(--gold); border-radius: 15px; margin: 0 auto; position: relative; overflow: hidden; }
    </style>
</head>
<body>
    <nav class="navbar-ipm d-flex justify-content-between align-items-center">
        <a href="/" class="fw-bold fs-4 text-white text-decoration-none">IPM <span class="text-gold">PORTAL</span></a>
        {% if session.user_id %}
        <div>
            {% if session.role == 'admin' %}<a href="/admin" class="btn btn-outline-warning btn-sm me-2">Admin</a>{% endif %}
            <a href="/profil" class="text-white text-decoration-none small"><i class="bi bi-person-circle"></i> {{ session.user_name }}</a>
        </div>
        {% endif %}
    </nav>
"""

UI_CORE_FOOTER = """
    <footer class="text-center py-5 mt-5 opacity-50 small">
        <p>© 2026 IPM SMKM 1 TGR | Powered by Muhammad Dafitrah</p>
    </footer>
</body></html>
"""

# --- ROUTES: AUTH & REGISTRATION (DATA WAJIB LENGKAP) ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form.get('u').lower()
        if User.query.filter_by(username=u).first():
            flash("Username sudah dipakai!")
        else:
            # Validasi data lengkap di tingkat server
            new_user = User(
                username=u,
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
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-4 mb-5">
        <div class="glass mx-auto" style="max-width: 550px;">
            <h3 class="text-gold fw-bold text-center">PENDAFTARAN KADER LENGKAP</h3>
            <form method="POST" class="mt-4">
                <label class="small text-gold">Nama Lengkap</label>
                <input name="fn" class="form-control mb-3" required>
                <div class="row">
                    <div class="col-6">
                        <label class="small text-gold">Username</label>
                        <input name="u" class="form-control mb-3" required>
                    </div>
                    <div class="col-6">
                        <label class="small text-gold">Password</label>
                        <input type="password" name="p" class="form-control mb-3" required>
                    </div>
                </div>
                <label class="small text-gold">Gmail Aktif</label>
                <input name="gm" type="email" class="form-control mb-3" required>
                <div class="row">
                    <div class="col-6">
                        <label class="small text-gold">NIS</label>
                        <input name="nis" class="form-control mb-3" required>
                    </div>
                    <div class="col-6">
                        <label class="small text-gold">Kelas (Contoh: XII RPL 1)</label>
                        <input name="kls" class="form-control mb-3" required>
                    </div>
                </div>
                <label class="small text-gold">WhatsApp Aktif</label>
                <input name="wa" class="form-control mb-4" required>
                <button type="submit" class="btn-gold w-100">DAFTAR SEKARANG</button>
            </form>
            <div class="text-center mt-3 small">Sudah punya akun? <a href="/login" class="text-gold">Login</a></div>
        </div>
    </div>""" + UI_CORE_FOOTER)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('u').lower()).first()
        if u and check_password_hash(u.password, request.form.get('p')):
            session.update({'user_id': u.id, 'user_name': u.full_name, 'role': u.role})
            return redirect('/')
        flash("Username atau Password salah!")
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5 pt-5"><div class="glass mx-auto" style="max-width: 400px;">
        <h3 class="text-gold fw-bold text-center mb-4">MASUK KADER</h3>
        <form method="POST">
            <input name="u" class="form-control mb-3" placeholder="Username" required>
            <input type="password" name="p" class="form-control mb-4" placeholder="Password" required>
            <button class="btn-gold w-100">LOGIN</button>
        </form>
        <div class="text-center mt-3 small">Kader baru? <a href="/register" class="text-gold">Daftar Akun</a></div>
    </div></div>""" + UI_CORE_FOOTER)

# --- ROUTES: ADMIN (MELIHAT SEMUA DATA + STATISTIK) ---

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': return redirect('/')
    all_users = User.query.all()
    
    # Statistik untuk Chart
    adm = User.query.filter_by(role='admin').count()
    mod = User.query.filter_by(role='moderator').count()
    mem = User.query.filter_by(role='member').count()
    
    kas_data = Kas.query.all()
    masuk = sum(k.jumlah for k in kas_data if k.tipe == 'masuk')
    keluar = sum(k.jumlah for k in kas_data if k.tipe == 'keluar')

    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5">
        <h2 class="text-gold fw-bold mb-4">ADMIN DASHBOARD (WIB SYSTEM)</h2>
        
        <div class="row mb-5">
            <div class="col-md-6 mb-3">
                <div class="glass h-100">
                    <h5 class="text-gold">Statistik Kader</h5>
                    <canvas id="userChart"></canvas>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="glass h-100">
                    <h5 class="text-gold">Aliran Dana Kas</h5>
                    <canvas id="kasChart"></canvas>
                </div>
            </div>
        </div>

        <div class="glass">
            <h5 class="text-gold mb-3">Database Seluruh Kader (Admin & Moderator & Member)</h5>
            <div class="table-responsive">
                <table class="table table-dark table-hover small">
                    <thead>
                        <tr>
                            <th>Nama</th><th>Username</th><th>Role</th><th>NIS</th><th>Kelas</th><th>WhatsApp</th><th>Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for u in users %}
                        <tr>
                            <td>{{ u.full_name }}</td>
                            <td>{{ u.username }}</td>
                            <td><span class="badge {{ 'bg-danger' if u.role=='admin' else 'bg-warning text-dark' if u.role=='moderator' else 'bg-secondary' }}">{{ u.role.upper() }}</span></td>
                            <td>{{ u.nis }}</td>
                            <td>{{ u.kelas }}</td>
                            <td><a href="https://wa.me/{{ u.whatsapp }}" class="text-info text-decoration-none">{{ u.whatsapp }}</a></td>
                            <td>
                                {% if u.username != 'dafitrah' %}
                                <a href="/hapus/user/{{ u.id }}" class="text-danger" onclick="return confirm('Hapus kader ini?')"><i class="bi bi-trash"></i></a>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <script>
        new Chart(document.getElementById('userChart'), {
            type: 'doughnut',
            data: {
                labels: ['Admin', 'Moderator', 'Member'],
                datasets: [{
                    data: [{{adm}}, {{mod}}, {{mem}}],
                    backgroundColor: ['#ff4d4d', '#d4af37', '#6c757d'],
                    borderWidth: 0
                }]
            },
            options: { plugins: { legend: { labels: { color: 'white' } } } }
        });

        new Chart(document.getElementById('kasChart'), {
            type: 'bar',
            data: {
                labels: ['Kas Masuk', 'Kas Keluar'],
                datasets: [{
                    label: 'Dalam Rupiah',
                    data: [{{masuk}}, {{keluar}}],
                    backgroundColor: ['#28a745', '#dc3545']
                }]
            },
            options: { 
                scales: { y: { ticks: { color: 'white' } }, x: { ticks: { color: 'white' } } },
                plugins: { legend: { display: false } }
            }
        });
    </script>
    """ + UI_CORE_FOOTER, users=all_users, adm=adm, mod=mod, mem=mem, masuk=masuk, keluar=keluar)

# --- ROUTES: KAS (WIB & STATISTIK) ---

@app.route('/kas', methods=['GET', 'POST'])
def kas():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        db.session.add(Kas(tipe=request.form.get('t'), jumlah=int(request.form.get('j')), keterangan=request.form.get('k')))
        db.session.commit()
        return redirect('/kas')
    
    data = Kas.query.order_by(Kas.tanggal.desc()).all()
    masuk = sum(d.jumlah for d in data if d.tipe == 'masuk')
    keluar = sum(d.jumlah for d in data if d.tipe == 'keluar')
    
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-4">
        <h3 class="text-gold fw-bold mb-4">KEUANGAN RANTING (WIB)</h3>
        <div class="row">
            <div class="col-md-4">
                <div class="glass text-center mb-4">
                    <small class="text-secondary">SALDO TERKINI</small>
                    <h2 class="text-gold fw-bold">Rp {{ "{:,}".format(masuk - keluar) }}</h2>
                </div>
                <div class="glass mb-4">
                    <form method="POST">
                        <select name="t" class="form-select mb-3"><option value="masuk">Uang Masuk</option><option value="keluar">Uang Keluar</option></select>
                        <input name="j" type="number" class="form-control mb-3" placeholder="Nominal" required>
                        <input name="k" class="form-control mb-3" placeholder="Keterangan" required>
                        <button class="btn-gold w-100">SIMPAN DATA</button>
                    </form>
                </div>
            </div>
            <div class="col-md-8">
                <div class="glass h-100">
                    <table class="table table-dark small">
                        <thead><tr class="text-gold"><th>Tanggal (WIB)</th><th>Keterangan</th><th>Jumlah</th></tr></thead>
                        <tbody>
                            {% for d in data %}
                            <tr><td>{{ d.tanggal.strftime('%d/%m %H:%M') }}</td><td>{{ d.keterangan }}</td><td class="{{ 'text-success' if d.tipe == 'masuk' else 'text-danger' }}">Rp {{ "{:,}".format(d.jumlah) }}</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>""" + UI_CORE_FOOTER, data=data, masuk=masuk, keluar=keluar)

# --- FITUR LAINNYA (ABSEN, PROFIL, KTA, PIAGAM, STRUKTUR, AGENDA - NO CUT) ---

@app.route('/')
def home():
    if 'user_id' not in session: return redirect('/login')
    current_time = get_now_wib().strftime('%H:%M:%S')
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5 text-center">
        <h1 class="text-gold fw-bold display-4 animate__animated animate__fadeInDown">IPM PORTAL</h1>
        <p class="text-secondary small">SMK Muhammadiyah 1 Tangerang | {{ current_time }} WIB</p>
        <div class="row g-4 mt-4">
            <div class="col-md-3 col-6"><div class="glass"><i class="bi bi-fingerprint text-gold fs-1"></i><h6>Absen</h6><a href="/absen" class="btn-gold btn-sm mt-2">BUKA</a></div></div>
            <div class="col-md-3 col-6"><div class="glass"><i class="bi bi-wallet2 text-gold fs-1"></i><h6>Kas</h6><a href="/kas" class="btn-gold btn-sm mt-2">BUKA</a></div></div>
            <div class="col-md-3 col-6"><div class="glass"><i class="bi bi-diagram-3 text-gold fs-1"></i><h6>Struktur</h6><a href="/struktur" class="btn-gold btn-sm mt-2">BUKA</a></div></div>
            <div class="col-md-3 col-6"><div class="glass"><i class="bi bi-calendar-event text-gold fs-1"></i><h6>Agenda</h6><a href="/agenda" class="btn-gold btn-sm mt-2">BUKA</a></div></div>
        </div>
    </div>""" + UI_CORE_FOOTER, current_time=current_time)

@app.route('/absen', methods=['GET', 'POST'])
def absen():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        db.session.add(Absensi(user_id=session['user_id'], nama_kader=session['user_name']))
        db.session.commit()
        flash("Absen Berhasil!")
    logs = Absensi.query.order_by(Absensi.waktu_hadir.desc()).all()
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5">
        <div class="glass text-center mb-4">
            <form method="POST"><button class="btn-gold py-4 fs-2 w-100">ABSEN HADIR (WIB)</button></form>
        </div>
        <div class="glass"><h5>Riwayat Absensi</h5>
        <table class="table table-dark small">{% for l in logs %}<tr><td>{{ l.nama_kader }}</td><td>{{ l.waktu_hadir.strftime('%H:%M:%S') }}</td></tr>{% endfor %}</table>
        </div>
    </div>""" + UI_CORE_FOOTER, logs=logs)

@app.route('/profil')
def profil():
    u = User.query.get(session['user_id'])
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5"><div class="row justify-content-center"><div class="col-md-6"><div class="glass text-center">
        <i class="bi bi-person-circle text-gold display-1"></i>
        <h3 class="text-gold">{{ u.full_name }}</h3>
        <p class="text-secondary small">{{ u.role.upper() }} | {{ u.kelas }}</p>
        <hr class="opacity-25">
        <div class="text-start small mb-4">
            <p>NIS: {{ u.nis }}</p><p>GMAIL: {{ u.gmail }}</p><p>WA: {{ u.whatsapp }}</p>
        </div>
        <div class="row g-2">
            <div class="col-6"><a href="/kta" class="btn btn-outline-warning w-100">KTA DIGITAL</a></div>
            <div class="col-6"><a href="/piagam" class="btn btn-outline-warning w-100">PIAGAM</a></div>
        </div>
    </div></div></div></div>""" + UI_CORE_FOOTER, u=u)

@app.route('/kta')
def kta_digital():
    u = User.query.get(session['user_id'])
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-5 text-center">
        <div class="kta-card text-start p-3" id="kta-area">
            <div class="d-flex justify-content-between"><small class="text-gold">IPM SMKM 1 TGR</small><i class="bi bi-qr-code text-white fs-4"></i></div>
            <div style="margin-top: 40px;">
                <h5 class="mb-0">{{ u.full_name }}</h5>
                <small class="text-gold">{{ u.role.upper() }}</small><br>
                <small class="text-secondary">NIS: {{ u.nis }}</small>
            </div>
        </div>
        <button onclick="saveKta()" class="btn btn-gold mt-4">SIMPAN KTA</button>
        <script>
            function saveKta() {
                html2canvas(document.getElementById('kta-area')).then(canvas => {
                    let link = document.createElement('a');
                    link.download = 'KTA_{{ u.username }}.png';
                    link.href = canvas.toDataURL();
                    link.click();
                });
            }
        </script>
    </div>""" + UI_CORE_FOOTER, u=u)

@app.route('/piagam')
def piagam():
    u = User.query.get(session['user_id'])
    return render_template_string("""<html><body style="background:#0b0d11; color:white; text-align:center; padding:50px; font-family:serif;">
        <div id="piagam" style="border:15px solid #d4af37; padding:50px; background:#1a1c20; position:relative;">
            <h1 style="color:#d4af37; font-size:3rem;">PIAGAM PENGHARGAAN</h1>
            <p>Diberikan kepada:</p>
            <h2 style="font-size:4rem; color:#fff;">{{ u.full_name }}</h2>
            <p>Atas dedikasinya sebagai Kader IPM SMK Muhammadiyah 1 Tangerang</p>
            <br><p>Tangerang, {{ tgl }}</p>
        </div><br>
        <button onclick="save()" style="padding:10px 20px; background:#d4af37; border:none; font-weight:bold; cursor:pointer;">SAVE PIAGAM</button>
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <script>
            function save() { html2canvas(document.getElementById('piagam')).then(c => {
                let l = document.createElement('a'); l.download='Piagam.png'; l.href=c.toDataURL(); l.click();
            }); }
        </script>
    </body></html>""", u=u, tgl=get_now_wib().strftime('%d %B %Y'))

@app.route('/struktur')
def struktur():
    s = Struktur.query.all()
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-5"><h3>STRUKTUR RANTING</h3>
    <div class="glass"><table class="table table-dark">{% for x in s %}<tr><td>{{x.jabatan}}</td><td>{{x.nama}}</td></tr>{% endfor %}</table></div></div>""" + UI_CORE_FOOTER, s=s)

@app.route('/agenda')
def agenda():
    a = Agenda.query.all()
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-5"><h3>AGENDA KEGIATAN</h3><div class="row">
    {% for x in a %}<div class="col-md-4 mb-3"><div class="glass"><h5>{{x.judul}}</h5><small>{{x.waktu}}</small><br><small>{{x.lokasi}}</small></div></div>{% endfor %}
    </div></div>""" + UI_CORE_FOOTER, a=a)

@app.route('/hapus/user/<int:id>')
def hapus_user(id):
    if session.get('role') == 'admin':
        u = User.query.get(id)
        if u and u.username != 'dafitrah': db.session.delete(u); db.session.commit()
    return redirect('/admin')

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
