#!/usr/bin/env python3
"""
Flask Image Gallery Application
A simple web application to upload and display images in a gallery format.
"""

import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import json

# Configuration
class Config:
    SECRET_KEY = 'your-secret-key-change-in-production'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Gallery data storage (in production, use a database)
GALLERY_DATA_FILE = 'gallery_data.json'

def load_gallery_data():
    """Load gallery data from JSON file"""
    try:
        if os.path.exists(GALLERY_DATA_FILE):
            with open(GALLERY_DATA_FILE, 'r') as f:
                data = json.load(f)
                return list(reversed(data))
    except:
        pass
    return []

def save_gallery_data(data):
    """Save gallery data to JSON file"""
    try:
        with open(GALLERY_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving gallery data: {e}")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_unique_filename(filename):
    """Generate unique filename to avoid conflicts"""
    ext = filename.rsplit('.', 1)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    return f"{unique_id}_{secure_filename(filename)}"

# Routes
@app.route('/')
def index():
    """Main gallery page"""
    gallery_data = load_gallery_data()
    return render_template('gallery.html', images=gallery_data)

# Routes
@app.route('/slideshow')
def slideshow():
    """Main gallery page"""
    gallery_data = load_gallery_data()
    return render_template('slideshow.html', images=gallery_data)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file upload"""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Generate unique filename
                filename = generate_unique_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save file
                file.save(filepath)
                
                # Get file info
                file_size = os.path.getsize(filepath)
                
                # Add to gallery data
                gallery_data = load_gallery_data()
                image_data = {
                    'id': str(uuid.uuid4()),
                    'filename': filename,
                    'original_name': file.filename,
                    'title': title or file.filename,
                    'description': description,
                    'upload_date': datetime.now().isoformat(),
                    'file_size': file_size
                }
                
                gallery_data.append(image_data)
                save_gallery_data(gallery_data)
                
                flash(f'Image "{image_data["title"]}" uploaded successfully!', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP files.', 'error')
    
    return render_template('upload.html')

@app.route('/image/<image_id>')
def view_image(image_id):
    """View single image details"""
    gallery_data = load_gallery_data()
    image = next((img for img in gallery_data if img['id'] == image_id), None)
    
    if not image:
        flash('Image not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('image_detail.html', image=image)

@app.route('/delete/<image_id>', methods=['POST'])
def delete_image(image_id):
    """Delete an image"""
    gallery_data = load_gallery_data()
    image = next((img for img in gallery_data if img['id'] == image_id), None)
    
    if image:
        try:
            # Delete file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], image['filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
            
            # Remove from gallery data
            gallery_data = [img for img in gallery_data if img['id'] != image_id]
            save_gallery_data(gallery_data)
            
            flash(f'Image "{image["title"]}" deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting image: {str(e)}', 'error')
    else:
        flash('Image not found', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/gallery')
def api_gallery():
    """API endpoint to get gallery data"""
    gallery_data = load_gallery_data()
    return jsonify(gallery_data)

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    flash('File too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('upload_file'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Template functions
@app.template_filter('filesize')
def filesize_format(size):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

@app.template_filter('datetime')
def datetime_format(date_string):
    """Format datetime string"""
    try:
        dt = datetime.fromisoformat(date_string)
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return date_string

if __name__ == '__main__':
    # Create some sample data if none exists
    if not load_gallery_data():
        sample_data = [
            {
                'id': str(uuid.uuid4()),
                'filename': 'sample1.jpg',
                'original_name': 'sample1.jpg',
                'title': 'Sample Image 1',
                'description': 'This is a sample image for demonstration',
                'upload_date': datetime.now().isoformat(),
                'file_size': 1024000
            }
        ]
        save_gallery_data(sample_data)
    
    app.run(debug=True, host='0.0.0.0', port=6000)