import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = 'ipm_smkm1_tgr_luxury_2026_dafitrah_ultimate'

# --- CONFIGURATION DATABASE ---
# Menggunakan path /tmp/ agar aman saat deploy di Vercel/Cloud
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/ipm_data_ultimate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- TIMEZONE SETTING (WIB) ---
WIB = pytz.timezone('Asia/Jakarta')

def get_now_wib():
    return datetime.now(WIB)

# --- DATABASE MODELS ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    gmail = db.Column(db.String(100), nullable=False)
    nis = db.Column(db.String(20), nullable=False)
    kelas = db.Column(db.String(50), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
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
            role='admin', nis='ADM-01', kelas='Pimpinan', whatsapp='0812', gmail='admin@ipm.com'
        )
        db.session.add(admin)
        db.session.commit()

# --- UI COMPONENTS ---

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
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
        :root { --gold: #d4af37; --dark: #0b0d11; }
        body { background: var(--dark); color: #fff; font-family: 'Inter', sans-serif; }
        .glass { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; }
        .btn-gold { background: linear-gradient(135deg, #d4af37, #f2d06b); color: #000; border: none; font-weight: 800; border-radius: 10px; width: 100%; padding: 10px; text-decoration: none; display: block; text-align: center; }
        .text-gold { color: var(--gold); }
        .form-control { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #fff; }
        .form-control:focus { background: rgba(255,255,255,0.1); color: #fff; border-color: var(--gold); box-shadow: none; }
    </style>
</head>
<body>
    <nav class="p-3 border-bottom border-secondary mb-4">
        <div class="container d-flex justify-content-between">
            <a href="/" class="fw-bold text-white text-decoration-none">IPM <span class="text-gold">PORTAL</span></a>
            {% if session.user_id %}
                <div>
                    <a href="/profil" class="text-white me-3 small">{{ session.user_name }}</a>
                    <a href="/logout" class="text-danger small">Keluar</a>
                </div>
            {% endif %}
        </div>
    </nav>
"""

UI_CORE_FOOTER = """
    <footer class="text-center py-5 opacity-25 small">© 2026 IPM SMKM 1 TGR | Dev by Dafitrah</footer>
</body></html>
"""

# --- ROUTES ---

@app.route('/')
def home():
    if 'user_id' not in session: return redirect('/login')
    waktu = get_now_wib().strftime('%H:%M:%S')
    return render_template_string(UI_CORE_HEADER + """
    <div class="container mt-4 text-center">
        <h2 class="text-gold fw-bold">DASHBOARD KADER</h2>
        <p class="small text-secondary">WIB: {{ waktu }}</p>
        <div class="row g-3 mt-3">
            <div class="col-6 col-md-3"><div class="glass"><i class="bi bi-fingerprint fs-1 text-gold"></i><br>Absen<a href="/absen" class="btn-gold mt-2">MASUK</a></div></div>
            <div class="col-6 col-md-3"><div class="glass"><i class="bi bi-wallet2 fs-1 text-gold"></i><br>Uang Kas<a href="/kas" class="btn-gold mt-2">CEK</a></div></div>
            <div class="col-6 col-md-3"><div class="glass"><i class="bi bi-diagram-3 fs-1 text-gold"></i><br>Struktur<a href="/struktur" class="btn-gold mt-2">LIHAT</a></div></div>
            <div class="col-6 col-md-3"><div class="glass"><i class="bi bi-calendar-check fs-1 text-gold"></i><br>Agenda<a href="/agenda" class="btn-gold mt-2">LIHAT</a></div></div>
        </div>
        {% if session.role == 'admin' %}
        <div class="mt-4"><a href="/admin" class="btn btn-outline-warning w-100 fw-bold">PANEL ADMIN (KHUSUS PIMPINAN)</a></div>
        {% endif %}
    </div>
    """ + UI_CORE_FOOTER, waktu=waktu)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form.get('u').lower()
        if User.query.filter_by(username=u).first(): flash("Username sudah ada!")
        else:
            new = User(
                username=u, password=generate_password_hash(request.form.get('p')),
                full_name=request.form.get('fn'), gmail=request.form.get('gm'),
                nis=request.form.get('nis'), kelas=request.form.get('kls'), whatsapp=request.form.get('wa')
            )
            db.session.add(new); db.session.commit(); return redirect('/login')
    return render_template_string(UI_CORE_HEADER + """
    <div class="container"><div class="glass mx-auto" style="max-width: 500px;">
        <h4 class="text-gold text-center fw-bold">REGISTRASI KADER</h4>
        <form method="POST" class="mt-3">
            <input name="fn" class="form-control mb-2" placeholder="Nama Lengkap" required>
            <input name="u" class="form-control mb-2" placeholder="Username" required>
            <input type="password" name="p" class="form-control mb-2" placeholder="Password" required>
            <input name="gm" type="email" class="form-control mb-2" placeholder="Email (Gmail)" required>
            <input name="nis" class="form-control mb-2" placeholder="NIS" required>
            <input name="kls" class="form-control mb-2" placeholder="Kelas" required>
            <input name="wa" class="form-control mb-3" placeholder="No WhatsApp" required>
            <button class="btn-gold">DAFTAR SEKARANG</button>
        </form>
    </div></div>
    """ + UI_CORE_FOOTER)

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': return redirect('/')
    users = User.query.all()
    # Statistik User
    adm = User.query.filter_by(role='admin').count()
    mod = User.query.filter_by(role='moderator').count()
    mem = User.query.filter_by(role='member').count()
    
    return render_template_string(UI_CORE_HEADER + """
    <div class="container">
        <h3 class="text-gold fw-bold">DATABASE KADER</h3>
        <div class="row mb-4">
            <div class="col-md-4"><div class="glass text-center"><h6>Statistik Peran</h6><canvas id="chartUser"></canvas></div></div>
            <div class="col-md-8">
                <div class="glass">
                    <table class="table table-dark table-sm small">
                        <thead><tr><th>Nama</th><th>Role</th><th>NIS</th><th>Kelas</th><th>Aksi</th></tr></thead>
                        <tbody>
                            {% for u in users %}
                            <tr>
                                <td>{{ u.full_name }}</td><td>{{ u.role }}</td><td>{{ u.nis }}</td><td>{{ u.kelas }}</td>
                                <td>{% if u.username != 'dafitrah' %}<a href="/hapus/user/{{ u.id }}" class="text-danger">Hapus</a>{% endif %}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    <script>
        new Chart(document.getElementById('chartUser'), {
            type: 'pie',
            data: { labels:['Admin','Mod','Member'], datasets:[{ data:[{{adm}},{{mod}},{{mem}}], backgroundColor:['#ff4d4d','#d4af37','#6c757d'] }] },
            options: { plugins:{ legend:{ labels:{ color:'#fff' } } } }
        });
    </script>
    """ + UI_CORE_FOOTER, users=users, adm=adm, mod=mod, mem=mem)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('u').lower()).first()
        if u and check_password_hash(u.password, request.form.get('p')):
            session.update({'user_id': u.id, 'user_name': u.full_name, 'role': u.role})
            return redirect('/')
        flash("Gagal!")
    return render_template_string(UI_CORE_HEADER + """<div class="container mt-5 pt-5"><div class="glass mx-auto" style="max-width: 350px;"><h4 class="text-gold text-center fw-bold">LOGIN</h4><form method="POST" class="mt-3"><input name="u" class="form-control mb-2" placeholder="Username" required><input type="password" name="p" class="form-control mb-3" placeholder="Password" required><button class="btn-gold">MASUK</button></form><div class="text-center mt-3"><a href="/register" class="text-white small">Belum punya akun?</a></div></div></div>""" + UI_CORE_FOOTER)

@app.route('/kas', methods=['GET', 'POST'])
def kas():
    if 'user_id' not in session: return redirect('/login')
    if request.method == 'POST':
        db.session.add(Kas(tipe=request.form.get('t'), jumlah=int(request.form.get('j')), keterangan=request.form.get('k')))
        db.session.commit()
    data = Kas.query.order_by(Kas.tanggal.desc()).all()
    masuk = sum(d.jumlah for d in data if d.tipe == 'masuk')
    keluar = sum(d.jumlah for d in data if d.tipe == 'keluar')
    return render_template_string(UI_CORE_HEADER + """
    <div class="container">
        <h3 class="text-gold fw-bold">KEUANGAN RANTING</h3>
        <div class="row">
            <div class="col-md-4 mb-3">
                <div class="glass text-center mb-3">Saldo Akhir<h2 class="text-gold">Rp {{ "{:,}".format(masuk-keluar) }}</h2></div>
                <div class="glass">
                    <form method="POST">
                        <select name="t" class="form-control mb-2"><option value="masuk">Uang Masuk</option><option value="keluar">Uang Keluar</option></select>
                        <input name="j" type="number" class="form-control mb-2" placeholder="Jumlah" required>
                        <input name="k" class="form-control mb-2" placeholder="Keterangan" required>
                        <button class="btn-gold">INPUT DATA</button>
                    </form>
                </div>
            </div>
            <div class="col-md-8">
                <div class="glass"><table class="table table-dark small"><thead><tr><th>WIB</th><th>Ket</th><th>Nominal</th></tr></thead><tbody>{% for d in data %}<tr><td>{{ d.tanggal.strftime('%H:%M') }}</td><td>{{ d.keterangan }}</td><td class="{{ 'text-success' if d.tipe=='masuk' else 'text-danger' }}">{{ d.jumlah }}</td></tr>{% endfor %}</tbody></table></div>
            </div>
        </div>
    </div>
    """ + UI_CORE_FOOTER, data=data, masuk=masuk, keluar=keluar)

# RUTE LAINNYA (TETAP SAMA SEPERTI FILE ASLI)
@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

@app.route('/absen', methods=['GET', 'POST'])
def absen():
    if request.method == 'POST':
        db.session.add(Absensi(user_id=session['user_id'], nama_kader=session['user_name']))
        db.session.commit(); flash("Berhasil Absen!")
    logs = Absensi.query.order_by(Absensi.waktu_hadir.desc()).all()
    return render_template_string(UI_CORE_HEADER + """<div class="container"><div class="glass text-center"><form method="POST"><button class="btn-gold p-5 fs-2">ABSEN SEKARANG</button></form><hr><table class="table table-dark">{% for l in logs %}<tr><td>{{ l.nama_kader }}</td><td>{{ l.waktu_hadir.strftime('%H:%M:%S') }}</td></tr>{% endfor %}</table></div></div>""" + UI_CORE_FOOTER, logs=logs)

@app.route('/profil')
def profil():
    u = User.query.get(session['user_id'])
    return render_template_string(UI_CORE_HEADER + """<div class="container"><div class="glass mx-auto text-center" style="max-width:400px;"><i class="bi bi-person-circle fs-1 text-gold"></i><h3>{{ u.full_name }}</h3><p>{{ u.role.upper() }}</p><div class="text-start small"><p>NIS: {{ u.nis }}</p><p>Kelas: {{ u.kelas }}</p><p>Email: {{ u.gmail }}</p></div><div class="row g-2"><div class="col-6"><a href="/kta" class="btn btn-outline-warning btn-sm w-100">KTA</a></div><div class="col-6"><a href="/piagam" class="btn btn-outline-warning btn-sm w-100">PIAGAM</a></div></div></div></div>""" + UI_CORE_FOOTER, u=u)

@app.route('/kta')
def kta():
    u = User.query.get(session['user_id'])
    return render_template_string(UI_CORE_HEADER + """<div class="container text-center"><div class="glass mx-auto" style="max-width:350px; background: linear-gradient(135deg, #111, #222); border: 2px solid var(--gold);"><h5 class="text-gold">KTA DIGITAL IPM</h5><hr><p class="mb-0 fw-bold">{{ u.full_name }}</p><small>{{ u.nis }}</small></div></div>""" + UI_CORE_FOOTER, u=u)

@app.route('/piagam')
def piagam():
    u = User.query.get(session['user_id'])
    return render_template_string("<html><body style='background:#000; color:#d4af37; text-align:center; padding:100px; border:20px solid #d4af37;'><h1>PIAGAM PENGHARGAAN</h1><p>Diberikan Kepada:</p><h2>{{ u.full_name }}</h2><p>Aktif di IPM SMKM 1 TGR</p></body></html>", u=u)

@app.route('/hapus/user/<int:id>')
def hapus_user(id):
    if session.get('role') == 'admin':
        u = User.query.get(id)
        if u and u.username != 'dafitrah': db.session.delete(u); db.session.commit()
    return redirect('/admin')

@app.route('/struktur')
def struktur():
    s = Struktur.query.all()
    return render_template_string(UI_CORE_HEADER + "<div class='container'><div class='glass'><h3>STRUKTUR</h3><table class='table table-dark'>{% for x in s %}<tr><td>{{x.jabatan}}</td><td>{{x.nama}}</td></tr>{% endfor %}</table></div></div>" + UI_CORE_FOOTER, s=s)

@app.route('/agenda')
def agenda():
    a = Agenda.query.all()
    return render_template_string(UI_CORE_HEADER + "<div class='container'><div class='row'>{% for x in a %}<div class='col-md-4'><div class='glass'><h5>{{x.judul}}</h5><small>{{x.waktu}}</small></div></div>{% endfor %}</div></div>" + UI_CORE_FOOTER, a=a)

if __name__ == '__main__':
    app.run(debug=True)
