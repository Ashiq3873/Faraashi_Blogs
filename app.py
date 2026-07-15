from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from datetime import datetime
import cloudinary
import cloudinary.uploader
from werkzeug.security import check_password_hash, generate_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-this-in-production'

# MongoDB Atlas
app.config["MONGO_URI"] = 'mongodb+srv://AshiqDE:Ashiqkkdi01@ashiqde.cepcb.mongodb.net/faraashi_blogs?retryWrites=true&w=majority'
mongo = PyMongo(app)

# Cloudinary
cloudinary.config(
    cloud_name='i8imsyyo',
    api_key='912812412396134',
    api_secret='N6mo5Rl7DITKSDDTj-RfXOmS_tI'
)

# Simple Admin Credentials (Change these!)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")  # Change password!

@app.route('/')
def index():
    blogs = list(mongo.db.blogs.find({"published": True}).sort("created_at", -1))
    for blog in blogs:
        blog['_id'] = str(blog['_id'])
    return render_template('index.html', blogs=blogs)

@app.route('/blog/<string:blog_id>')
def blog_detail(blog_id):
    blog = mongo.db.blogs.find_one({"_id": ObjectId(blog_id)})
    if blog:
        blog['_id'] = str(blog['_id'])
    return render_template('blog_detail.html', blog=blog)

# ====================== ADMIN ======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    blogs = list(mongo.db.blogs.find().sort("created_at", -1))
    for b in blogs:
        b['_id'] = str(b['_id'])
    return render_template('dashboard.html', blogs=blogs)

@app.route('/create', methods=['GET', 'POST'])
def create_blog():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        published = 'published' in request.form
        category = request.form.get('category', 'General')
        author = request.form.get('author', 'Admin')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else []
        tags = [tag.strip() for tag in tags if tag.strip()]

        image_url = None
        if 'image' in request.files and request.files['image'].filename:
            file = request.files['image']
            if file and file.filename:
                try:
                    upload_result = cloudinary.uploader.upload(
                        file,
                        folder='faraashi_blogs',
                        allowed_formats=['jpg', 'jpeg', 'png', 'gif', 'webp'],
                        max_bytes=10485760  # 10MB limit
                    )
                    image_url = upload_result['secure_url']
                except Exception as e:
                    flash(f'Image upload failed: {str(e)}', 'error')

        blog = {
            "title": title,
            "content": content,
            "author": author,
            "category": category,
            "tags": tags,
            "image_url": image_url,
            "published": published,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mongo.db.blogs.insert_one(blog)
        flash('Blog posted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create.html')

@app.route('/edit/<string:blog_id>', methods=['GET', 'POST'])
def edit_blog(blog_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update logic similar to create
        category = request.form.get('category', 'General')
        author = request.form.get('author', 'Admin')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else []
        tags = [tag.strip() for tag in tags if tag.strip()]

        mongo.db.blogs.update_one(
            {"_id": ObjectId(blog_id)},
            {"$set": {
                "title": request.form['title'],
                "content": request.form['content'],
                "author": author,
                "category": category,
                "tags": tags,
                "published": 'published' in request.form,
                "updated_at": datetime.utcnow()
            }}
        )
        flash('Blog updated!')
        return redirect(url_for('dashboard'))
    
    blog = mongo.db.blogs.find_one({"_id": ObjectId(blog_id)})
    return render_template('create.html', blog=blog, edit=True)

@app.route('/delete/<string:blog_id>', methods=['POST'])
def delete_blog(blog_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    mongo.db.blogs.delete_one({"_id": ObjectId(blog_id)})
    flash('Blog deleted')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)