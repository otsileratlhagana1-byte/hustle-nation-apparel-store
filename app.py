import os, json, secrets
from datetime import datetime
from zoneinfo import ZoneInfo
from functools import wraps
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-change-this-' + secrets.token_hex(8))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE, 'instance', 'hustle_nation.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(BASE, 'instance'), exist_ok=True)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client')
    active = db.Column(db.Boolean, default=True)
    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(100), default='Collection')
    description = db.Column(db.Text, default='')
    price = db.Column(db.Float, default=0)
    sale_price = db.Column(db.Float, nullable=True)
    sizes = db.Column(db.Text, default='')
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255), default='product-placeholder.svg')
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    @property
    def effective_price(self): return self.sale_price if self.sale_price is not None and self.sale_price > 0 else self.price
    @property
    def size_list(self): return [x.strip() for x in self.sizes.split(',') if x.strip()]

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(160), default='')
    address = db.Column(db.Text, default='')
    shipping = db.Column(db.String(80), default='PAXI (PEP)')
    payment = db.Column(db.String(80), default='WhatsApp confirmation')
    notes = db.Column(db.Text, default='')
    total = db.Column(db.Float, default=0)
    status = db.Column(db.String(40), default='Pending')
    paxi_reference = db.Column(db.String(100), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=True)
    product_name = db.Column(db.String(160), nullable=False)
    size = db.Column(db.String(40), default='')
    qty = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, default=0)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default='')

DEFAULTS = {
    'brand_name':'HUSTLE NATION', 'tagline':'THE STREET IS THE NAME. HUSTLE IN THE WAY.',
    'logo':'hustle-nation-logo.svg', 'hero_title':'HUSTLE IN THE WAY',
    'hero_text':'Streetwear built from hustle, culture and everyday movement.',
    'hero_image':'', 'background':'#f5f3ef', 'accent':'#d98b19', 'text_color':'#111111',
    'announcement':'NATIONWIDE DELIVERY • PAXI / PEP AVAILABLE', 'whatsapp':'27698881104',
    'currency':'R', 'country':'South Africa', 'delivery_note':'We deliver nation wide.',
    'site_enabled':'1', 'site_maintenance_start':'', 'site_maintenance_end':'',
    'client_lock_start':'', 'client_lock_end':'', 'maintenance_message':'Store temporarily unavailable for maintenance. Please check back soon.'
}

PRODUCTS = [
('Mind Full of Money Design — Hoodies','Mind Full of Money Design',290),
('Mind Full of Money Design — Sweatshirts','Mind Full of Money Design',250),
('Mind Full of Money Design — T-shirts','Mind Full of Money Design',150),
('Mind Full of Money Design — Sweatpants','Mind Full of Money Design',150),
('Young Money Design — Hoodies','Young Money Design',290),
('Young Money Design — Sweatshirts','Young Money Design',250),
('Young Money Design — T-shirts','Young Money Design',150),
('Young Money Design — Sweatpants','Young Money Design',150),
('Classic Design — Hoodies','Classic Design',290),
('Classic Design — Sweatshirts','Classic Design',250),
('Classic Design — T-shirts','Classic Design',150),
('Classic Design — Sweatpants','Classic Design',150),
('Boys and Girls Club Design — Hoodie','Boys and Girls Club Design',300),
('Boys and Girls Club Design — Sweatshirts','Boys and Girls Club Design',250),
('Boys and Girls Club Design — T-shirts','Boys and Girls Club Design',200),
('Boys and Girls Club Design — Sweatpants','Boys and Girls Club Design',190),
('Newspaper Design — Hoodies','Newspaper Design',340),
('Newspaper Design — Sweatshirts','Newspaper Design',250),
('Newspaper Design — T-shirts','Newspaper Design',200),
('Newspaper Design — Sweatpants','Newspaper Design',190),
('HN Design — Hoodies','HN Design',340),
('HN Design — Sweatshirts','HN Design',250),
('HN Design — T-shirts','HN Design',200),
('HN Design — Sweatpants','HN Design',190),
('Classic Edition Design — Hoodies','Classic Edition Design',340),
('Classic Edition Design — Sweatshirts','Classic Edition Design',250),
('Classic Edition Design — T-shirts','Classic Edition Design',200),
('Classic Edition Design — Sweatpants','Classic Edition Design',190),
('Classic Edition Design — School bags','Classic Edition Design',200),
('Headwear — Panel caps','Headwear',70),
('Headwear — Slouchy beanies','Headwear',80),
('Headwear — Beanies','Headwear',70),
('Headwear — Knitted beanies','Headwear',150),
('Mafia Tracksuits — Mafia top','Mafia Tracksuits',400),
('Mafia Tracksuits — Mafia pants','Mafia Tracksuits',300),
('Mafia Tracksuits — Mafia shorts','Mafia Tracksuits',150),
('Mafia Tracksuits — Two piece tracksuits','Mafia Tracksuits',650),
('Mafia Tracksuits 2nd Edition — Mafia top','Mafia Tracksuits 2nd Edition',450),
('Mafia Tracksuits 2nd Edition — Mafia Trackpants','Mafia Tracksuits 2nd Edition',350),
('Mafia Tracksuits 2nd Edition — Two piece','Mafia Tracksuits 2nd Edition',750),
]

def setting(k):
    s = Setting.query.filter_by(key=k).first()
    return s.value if s else DEFAULTS.get(k,'')

def set_setting(k,v):
    s=Setting.query.filter_by(key=k).first()
    if not s: s=Setting(key=k); db.session.add(s)
    s.value=str(v)

def parse_dt(v):
    if not v: return None
    try: return datetime.fromisoformat(v)
    except: return None

def in_window(start_key,end_key):
    s=parse_dt(setting(start_key)); e=parse_dt(setting(end_key)); now=datetime.now(ZoneInfo('Africa/Johannesburg')).replace(tzinfo=None)
    return bool(s and e and s <= now <= e)

def site_locked(): return setting('site_enabled') != '1' or in_window('site_maintenance_start','site_maintenance_end')
def client_locked(): return in_window('client_lock_start','client_lock_end')

def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a,**kw):
            if not session.get('user_id'): return redirect(url_for('login', area='owner' if role=='owner' else 'admin'))
            if role and session.get('role') != role:
                if not (role=='client' and session.get('role')=='owner'):
                    return redirect(url_for('login', area='owner' if role=='owner' else 'admin'))
            if role=='client' and session.get('role')=='client' and (client_locked() or site_locked()): return render_template('locked.html', kind='dashboard', settings=all_settings())
            return fn(*a,**kw)
        return wrapper
    return deco

def all_settings(): return {k:setting(k) for k in DEFAULTS}

@app.context_processor
def inject(): return {'store': all_settings(), 'cart_whatsapp': setting('whatsapp')}

@app.before_request
def enforce_site():
    if request.endpoint in {'static','login','logout','owner_login','owner_logout','locked','health','place_order'}: return
    if request.path.startswith('/owner'): return
    if request.path.startswith('/admin') and session.get('role') in ('owner','client'):
        if session.get('role') == 'client' and (site_locked() or client_locked()):
            return render_template('locked.html', kind='dashboard', settings=all_settings())
        return
    if site_locked() and not request.path.startswith('/owner'):
        return render_template('locked.html', kind='store', settings=all_settings())

@app.route('/health')
def health(): return 'OK',200

@app.route('/')
def home():
    products=Product.query.filter_by(active=True).order_by(Product.featured.desc(), Product.created_at.desc()).all()
    categories=sorted({p.category for p in products})
    return render_template('home.html', products=products, categories=categories)

@app.route('/product/<int:pid>')
def product(pid):
    p=Product.query.get_or_404(pid)
    return render_template('product.html', p=p)

@app.route('/place-order', methods=['POST'])
def place_order():
    data=request.get_json(silent=True) or {}
    items=data.get('items',[])
    if not items: return jsonify({'ok':False,'error':'Cart is empty'}),400
    total=0; order=Order(customer_name=data.get('customer_name','Customer'), phone=data.get('phone',''), email=data.get('email',''), address=data.get('address',''), shipping=data.get('shipping','PAXI (PEP)'), payment=data.get('payment','WhatsApp confirmation'), notes=data.get('notes',''))
    db.session.add(order); db.session.flush()
    for it in items:
        p=Product.query.get(int(it.get('id',0)))
        if not p or not p.active: continue
        qty=max(1,int(it.get('qty',1))); price=p.effective_price; total += price*qty
        if p.stock >= qty: p.stock -= qty
        db.session.add(OrderItem(order_id=order.id,product_id=p.id,product_name=p.name,size=it.get('size',''),qty=qty,price=price))
    order.total=total; db.session.commit()
    lines=[f"HUSTLE NATION ORDER #{order.id}",f"Customer: {order.customer_name}",f"Phone: {order.phone}",f"Shipping: {order.shipping}",f"Payment: {order.payment}","", "ITEMS:"]
    for i in order.items: lines.append(f"- {i.product_name} | Size: {i.size or 'N/A'} | Qty: {i.qty} | R{i.price:.2f}")
    lines += [f"TOTAL: R{order.total:.2f}", f"Address: {order.address}", f"Notes: {order.notes}"]
    wa=f"https://wa.me/{setting('whatsapp')}?text={quote(chr(10).join(lines))}"
    return jsonify({'ok':True,'order_id':order.id,'whatsapp':wa})

@app.route('/login/<area>', methods=['GET','POST'])
def login(area):
    role='owner' if area=='owner' else 'client'
    if request.method=='POST':
        u=User.query.filter_by(username=request.form.get('username'),role=role).first()
        if u and u.active and u.check_password(request.form.get('password','')):
            session.clear(); session['user_id']=u.id; session['role']=u.role; return redirect(url_for('owner_dashboard' if role=='owner' else 'admin_dashboard'))
        flash('Invalid login details.','error')
    return render_template('login.html', area=area, title='Creator Dashboard' if role=='owner' else 'Store Admin Dashboard')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

@app.route('/owner')
@login_required('owner')
def owner_dashboard():
    return render_template('owner.html', products=Product.query.count(), orders=Order.query.count(), settings=all_settings(), users=User.query.all())

@app.route('/owner/settings', methods=['POST'])
@login_required('owner')
def owner_settings():
    keys=['site_enabled','site_maintenance_start','site_maintenance_end','client_lock_start','client_lock_end','maintenance_message']
    for k in keys: set_setting(k,request.form.get(k,''))
    db.session.commit(); flash('Maintenance schedule saved.','success'); return redirect(url_for('owner_dashboard'))

@app.route('/owner/client-password', methods=['POST'])
@login_required('owner')
def client_password():
    u=User.query.filter_by(role='client').first()
    if u:
        u.set_password(request.form.get('password','')); u.active=True; db.session.commit(); flash('Client dashboard password updated.','success')
    return redirect(url_for('owner_dashboard'))

@app.route('/admin')
@login_required('client')
def admin_dashboard():
    products=Product.query.order_by(Product.created_at.desc()).all(); orders=Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin.html', products=products, orders=orders)

@app.route('/admin/product/save', methods=['POST'])
@login_required('client')
def save_product():
    pid=request.form.get('id'); p=Product.query.get(int(pid)) if pid else Product()
    p.name=request.form.get('name','Untitled'); p.category=request.form.get('category','Collection'); p.description=request.form.get('description','')
    p.price=float(request.form.get('price') or 0); sp=request.form.get('sale_price'); p.sale_price=float(sp) if sp else None
    p.sizes=request.form.get('sizes','S,M,L,XL'); p.stock=int(request.form.get('stock') or 0); p.featured=bool(request.form.get('featured')); p.active=bool(request.form.get('active','1'))
    f=request.files.get('image')
    if f and f.filename:
        name=secure_filename(f.filename); name=f"{secrets.token_hex(6)}_{name}"; f.save(os.path.join(app.config['UPLOAD_FOLDER'],name)); p.image='uploads/'+name
    if not pid: db.session.add(p)
    db.session.commit(); flash('Product saved.','success'); return redirect(url_for('admin_dashboard'))

@app.route('/admin/product/delete/<int:pid>', methods=['POST'])
@login_required('client')
def delete_product(pid):
    p=Product.query.get_or_404(pid); db.session.delete(p); db.session.commit(); flash('Product deleted.','success'); return redirect(url_for('admin_dashboard'))

@app.route('/admin/order/<int:oid>', methods=['POST'])
@login_required('client')
def update_order(oid):
    o=Order.query.get_or_404(oid); o.status=request.form.get('status',o.status); o.paxi_reference=request.form.get('paxi_reference',o.paxi_reference); db.session.commit(); flash('Order updated.','success'); return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings', methods=['POST'])
@login_required('client')
def admin_settings():
    keys=['brand_name','tagline','hero_title','hero_text','background','accent','text_color','announcement','whatsapp','delivery_note','currency']
    for k in keys:
        if k in request.form: set_setting(k,request.form.get(k,''))
    for field,key in [('logo','logo'),('hero_image','hero_image')]:
        f=request.files.get(field)
        if f and f.filename:
            name=f"{secrets.token_hex(6)}_{secure_filename(f.filename)}"; f.save(os.path.join(app.config['UPLOAD_FOLDER'],name)); set_setting(key,'uploads/'+name)
    db.session.commit(); flash('Store appearance and settings updated.','success'); return redirect(url_for('admin_dashboard'))

@app.route('/admin/seed', methods=['POST'])
@login_required('client')
def seed():
    if Product.query.count()==0:
        for n,c,price in PRODUCTS:
            desc=f"{c}. Original Hustle Nation streetwear collection piece. Add your own product photos and details from the dashboard."
            db.session.add(Product(name=n,category=c,price=price,sale_price=None,sizes='S,M,L,XL,XXL',stock=10,description=desc,image='product-placeholder.svg'))
        db.session.commit(); flash('Starter catalog added.','success')
    return redirect(url_for('admin_dashboard'))

@app.route('/locked')
def locked(): return render_template('locked.html',kind='store',settings=all_settings())

with app.app_context():
    db.create_all()
    for k,v in DEFAULTS.items():
        if not Setting.query.filter_by(key=k).first(): db.session.add(Setting(key=k,value=v))
    if not User.query.filter_by(role='owner').first():
        u=User(username=os.environ.get('OWNER_USERNAME','owner'),role='owner'); u.set_password(os.environ.get('OWNER_PASSWORD','change-me')); db.session.add(u)
    if not User.query.filter_by(role='client').first():
        u=User(username=os.environ.get('CLIENT_USERNAME','admin'),role='client'); u.set_password(os.environ.get('CLIENT_PASSWORD','change-me')); db.session.add(u)
    if Product.query.count()==0:
        for n,c,price in PRODUCTS:
            db.session.add(Product(name=n,category=c,price=price,sale_price=None,sizes='S,M,L,XL,XXL',stock=10,description=f'{c}. Hustle Nation collection item.',image='product-placeholder.svg'))
    db.session.commit()

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=True)
