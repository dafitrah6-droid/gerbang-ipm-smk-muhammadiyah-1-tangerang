import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz # Tambahkan ini di requirements.txt: pytz

app = Flask(__name__)
app.secret_key = 'ipm_smkm1_tgr_luxury_2026_dafitrah_ultimate_v2'

# --- PERBAIKAN WAKTU & DATABASE ---
# Setting Waktu Indonesia Barat (WIB)
WIB = pytz.timezone('Asia/Jakarta')

def get_waktu_sekarang():
    return datetime.now(WIB)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/ipm_data_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"connect_args": {"check_same_thread": False}}
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='member') # member, moderator, admin
    nis = db.Column(db.String(20))
    kelas = db.Column(db.String(50))
    whatsapp = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=get_waktu_sekarang)

class Kas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipe = db.Column(db.String(10)) 
    jumlah = db.Column(db.Integer)
    keterangan = db.Column(db.String(200))
    tanggal = db.Column(db.DateTime, default=get_waktu_sekarang)

class Absensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nama_kader = db.Column(db.String(100))
    waktu_hadir = db.Column(db.DateTime, default=get_waktu_sekarang)

class Laporan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_pelapor = db.Column(db.String(100))
    pesan = db.Column(db.Text)
    waktu_lapor = db.Column(db.DateTime, default=get_waktu_sekarang)

# --- INITIALIZE DATABASE ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='dafitrah').first():
        db.session.add(User(
            username='dafitrah', 
            password=generate_password_hash('admin123'), 
            full_name='Muhammad Dafitrah', 
            role='admin'
        ))
        db.session.commit()

# --- UI COMPONENTS (ULTRA LUXURY ANIMATION) ---
UI_CORE_HEADER = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <style>
        :root { --gold: #d4af37; --dark: #050608; --glass: rgba(255, 255, 255, 0.03); }
        body { background: var(--dark); color: #f0f0f0; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .glass-card { 
            background: var(--glass); 
            backdrop-filter: blur(15px); 
            border: 1px solid rgba(255, 255, 255, 0.07); 
            border-radius: 24px; 
            transition: all 0.5s ease;
        }
        .glass-card:hover { 
            border-color: var(--gold); 
            transform: translateY(-8px); 
            box-shadow: 0 15px 40px rgba(212, 175, 55, 0.15); 
        }
        .btn-gold { 
            background: linear-gradient(135deg, #d4af37 0%, #f2d06b 100%); 
            color: #000; border: none; font-weight: 800; border-radius: 14px;
            padding: 14px; transition: 0.3s; width: 100%;
        }
        .btn-gold:hover { transform: scale(1.03); box-shadow: 0 0 20px var(--gold); }
        .nav-ipm { padding: 20px; border-bottom: 1px solid var(--glass); margin-bottom: 30px; }
        .text-gold { color: var(--gold) !important; text-shadow: 0 0 10px rgba(212, 175, 55, 0.3); }
        .form-control { background: rgba(0,0,0,0.3); border: 1px solid var(--glass); color: #fff; border-radius: 12px; }
        .form-control:focus { background: rgba(0,0,0,0.5); border-color: var(--gold); color: #fff; box-shadow: none; }
    </style>
</head>
<body>
    <nav class="nav-ipm d-flex justify-content-between align-items-center animate__animated animate__fadeIn">
        <a href="/" class="text-white fw-bold fs-4 text-decoration-none">IPM <span class="text-gold">PORTAL</span></a>
        <div>
            {% if session.user_id %}
                <span class="badge bg-dark border border-warning text-gold me-2">{{ session.role|upper }}</span>
                <a href="/logout" class="btn btn-sm btn-outline-danger">Keluar</a>
            {% endif %}
        </div>
    </nav>
    <div class="container">
"""

# --- ROUTES ---

@app.route('/')
def home():
    if 'user_id' not in session: return redirect('/login')
    return render_template_string(UI_CORE_HEADER + """
        <div class="text-center mt-5" data-aos="zoom-in">
            <h1 class="fw-bold display-3">SELAMAT DATANG</h1>
            <p class="text-secondary">Pimpinan Ranting SMK Muhammadiyah 1 Tangerang</p>
            
            <div class="row g-4 mt-5">
                <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="100">
                    <div class="glass-card p-4"><i class="bi bi-person-check fs-1 text-gold"></i><h5 class="mt-3">Absensi</h5><a href="/absen" class="btn-gold mt-2 d-block text-decoration-none">BUKA</a></div>
                </div>
                <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="200">
                    <div class="glass-card p-4"><i class="bi bi-wallet2 fs-1 text-gold"></i><h5 class="mt-3">Keuangan</h5><a href="/kas" class="btn-gold mt-2 d-block text-decoration-none">BUKA</a></div>
                </div>
                <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="300">
                    <div class="glass-card p-4"><i class="bi bi-shield-lock fs-1 text-gold"></i><h5 class="mt-3">Admin</h5><a href="/admin" class="btn-gold mt-2 d-block text-decoration-none">MANAJEMEN</a></div>
                </div>
                <div class="col-md-3 col-6" data-aos="fade-up" data-aos-delay="400">
                    <div class="glass-card p-4"><i class="bi bi-bug fs-1 text-danger"></i><h5 class="mt-3">Lapor</h5><a href="/lapor" class="btn btn-outline-danger w-100 mt-2 rounded-pill">HUBUNGI</a></div>
                </div>
            </div>
        </div>
    """ + "</div></body></html>")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['u'].lower()).first()
        if user and check_password_hash(user.password, request.form['p']):
            session.update({'user_id': user.id, 'user_name': user.full_name, 'role': user.role})
            return redirect('/')
    return render_template_string(UI_CORE_HEADER + """
        <div class="row justify-content-center mt-5">
            <div class="col-md-4" data-aos="flip-left">
                <div class="glass-card p-5">
                    <h2 class="text-gold fw-bold text-center mb-4">MASUK</h2>
                    <form method="POST">
                        <input name="u" class="form-control mb-3" placeholder="Username" required>
                        <input type="password" name="p" class="form-control mb-4" placeholder="Password" required>
                        <button type="submit" class="btn-gold">LOGIN SEKARANG</button>
                    </form>
                </div>
            </div>
        </div>
    """ + "</div></body></html>")

@app.route('/absen', methods=['GET', 'POST'])
def absen():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        # Cek sudah absen hari ini (WIB)
        hari_ini = get_waktu_sekarang().date()
        sudah = Absensi.query.filter(Absensi.user_id == session['user_id'], db.func.date(Absensi.waktu_hadir) == hari_ini).first()
        if not sudah:
            db.session.add(Absensi(user_id=session['user_id'], nama_kader=session['user_name'], waktu_hadir=get_waktu_sekarang()))
            db.session.commit()
            flash("Berhasil hadir!")
        else:
            flash("Anda sudah absen hari ini!")
        return redirect('/absen')
    
    logs = Absensi.query.order_by(Absensi.waktu_hadir.desc()).all()
    return render_template_string(UI_CORE_HEADER + """
        <h3 class="text-gold mb-4 animate__animated animate__fadeInDown">LOG KEHADIRAN KADER</h3>
        <div class="row">
            <div class="col-md-4 mb-4" data-aos="fade-right">
                <div class="glass-card p-4 text-center">
                    <form method="POST"><button class="btn-gold py-5 fs-2">KLIK HADIR</button></form>
                    <p class="mt-3 small text-secondary">Waktu Server: {{ jam }} WIB</p>
                </div>
            </div>
            <div class="col-md-8" data-aos="fade-left">
                <div class="glass-card p-4">
                    <table class="table table-dark table-hover small">
                        <thead><tr class="text-gold"><th>Nama</th><th>Tanggal</th><th>Jam (WIB)</th></tr></thead>
                        <tbody>
                            {% for l in logs %}
                            <tr>
                                <td>{{ l.nama_kader }}</td>
                                <td>{{ l.waktu_hadir.strftime('%d %b %Y') }}</td>
                                <td class="text-gold fw-bold">{{ l.waktu_hadir.strftime('%H:%M:%S') }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    """ + "</div></body></html>", logs=logs, jam=get_waktu_sekarang().strftime('%H:%M'))

@app.route('/admin')
def admin_panel():
    # Sistem Moderator: Moderator & Admin bisa masuk
    if session.get('role') not in ['admin', 'moderator']: 
        flash("Akses Khusus Pengurus!")
        return redirect('/')
    
    users = User.query.all()
    laporan = Laporan.query.order_by(Laporan.waktu_lapor.desc()).all()
    return render_template_string(UI_CORE_HEADER + """
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="text-gold fw-bold">PENGATURAN SISTEM</h2>
        </div>
        
        <div class="row g-4">
            <div class="col-md-6" data-aos="fade-up">
                <div class="glass-card p-4">
                    <h5 class="text-gold mb-3"><i class="bi bi-people"></i> Daftar Kader</h5>
                    <div style="max-height: 400px; overflow-y: auto;">
                        <table class="table table-dark table-sm">
                            {% for u in users %}
                            <tr>
                                <td>{{ u.full_name }} <br><small class="text-secondary">{{ u.role }}</small></td>
                                <td class="text-end">
                                    {% if session.role == 'admin' and u.username != 'dafitrah' %}
                                        <a href="/set-role/{{ u.id }}/moderator" class="btn btn-xs btn-outline-info">MOD</a>
                                        <a href="/hapus-user/{{ u.id }}" class="text-danger ms-2"><i class="bi bi-trash"></i></a>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-md-6" data-aos="fade-up" data-aos-delay="200">
                <div class="glass-card p-4">
                    <h5 class="text-danger mb-3"><i class="bi bi-bug"></i> Laporan Masuk</h5>
                    {% for lp in laporan %}
                    <div class="alert bg-dark border-secondary text-white small">
                        <strong>{{ lp.nama_pelapor }}</strong>: {{ lp.pesan }} <br>
                        <small class="text-secondary">{{ lp.waktu_lapor.strftime('%H:%M') }} WIB</small>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    """ + "</div></body></html>", users=users, laporan=laporan)

@app.route('/set-role/<int:id>/<role>')
def set_role(id, role):
    if session.get('role') == 'admin':
        u = User.query.get(id)
        u.role = role
        db.session.commit()
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

app = app # Support Vercel

if __name__ == '__main__':
    app.run(debug=True)
