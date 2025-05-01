import os
import pickle
from pyngrok import ngrok
from flask import Flask, render_template, request, redirect, url_for, flash, send_file,session,jsonify
from flask_bcrypt import Bcrypt
from PIL import Image
from werkzeug.utils import secure_filename
import numpy as np
import cv2
import onnxruntime
from transformers import BlipProcessor, BlipForConditionalGeneration, BlipForQuestionAnswering
from werkzeug.utils import secure_filename
import pandas as pd
from duckduckgo_search import DDGS
import os
import urllib.request
import gdown
from flask_mail import Mail, Message
from flask_session import Session
from pymongo import MongoClient
import random
import string
from flask_session import Session

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)


app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['UPSCALED_FOLDER'] = 'static/upscaled'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPSCALED_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['SESSION_TYPE'] = 'mongodb'  
Session(app)

models_folder = "models"
os.makedirs(models_folder, exist_ok=True)
modelx2_file_path = os.path.join(models_folder, "modelx2.ort")


caption_processor = BlipProcessor.from_pretrained("models/blip-captioning")
caption_model = BlipForConditionalGeneration.from_pretrained("models/blip-captioning")

vqa_processor = BlipProcessor.from_pretrained("models/blip-vqa")
vqa_model = BlipForQuestionAnswering.from_pretrained("models/blip-vqa")


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'mupparajuk31@gmail.com'
app.config['MAIL_PASSWORD'] = 'mpcjrwyohvxpbdhf'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
# Download ONNX model

mail = Mail(app)

mongodb_uri = 'mongodb://localhost:27017/'
client = MongoClient(mongodb_uri)
db = client['Image_Chatbot']  
collection = db['users']

modelx2_file_id = "1Hvt3_t8S2W5CNYUCFgd2L_KitedAJEmH"
if not os.path.exists(modelx2_file_path):
    url = f"https://drive.google.com/uc?export=download&id={modelx2_file_id}"
    gdown.download(url, modelx2_file_path, quiet=False)

# OTP generation and storage
otps = {}
unique_titles_and_locations = []
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_pil_to_cv2(image):
    open_cv_image = np.array(image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image

def pre_process(img: np.array) -> np.array:
    img = np.transpose(img[:, :, 0:3], (2, 0, 1))
    img = np.expand_dims(img, axis=0).astype(np.float32)
    return img

def post_process(img: np.array) -> np.array:
    img = np.squeeze(img)
    img = np.transpose(img, (1, 2, 0))[:, :, ::-1].astype(np.uint8)
    return img

def inference(model_path: str, img_array: np.array) -> np.array:
    options = onnxruntime.SessionOptions()
    ort_session = onnxruntime.InferenceSession(model_path, options)
    ort_inputs = {ort_session.get_inputs()[0].name: img_array}
    ort_outs = ort_session.run(None, ort_inputs)
    return ort_outs[0]

def upscale(image_path: str):
    pil_image = Image.open(image_path)
    img = convert_pil_to_cv2(pil_image)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    image_output = post_process(inference(modelx2_file_path, pre_process(img)))
    image_output = cv2.cvtColor(image_output, cv2.COLOR_BGR2RGB)
    return image_output

def generate_caption(image_path: str):
    image = Image.open(image_path).convert("RGB")
    inputs = caption_processor(images=image, return_tensors="pt")
    output = caption_model.generate(**inputs)
    return caption_processor.decode(output[0], skip_special_tokens=True)

def answer_question(image_path: str, question: str):
    image = Image.open(image_path).convert("RGB")
    inputs = vqa_processor(images=image, text=question, return_tensors="pt")
    output = vqa_model.generate(**inputs)
    return vqa_processor.decode(output[0], skip_special_tokens=True)

@app.route('/caption_upload', methods=['POST'])
def caption_upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        session['current_image'] = filename
        # Generate caption immediately
        caption = generate_caption(file_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'caption': caption,
            'image_url': url_for('serve_uploaded_file', filename=filename)
        })
    
    return jsonify({'success': False, 'message': 'Invalid file type'})

@app.route('/enhance_upload', methods=['POST'])
def enhance_upload():
    if 'file' not in request.files:
        app.logger.error('No file part')
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            session['current_image'] = filename # Store the current image in session
            return jsonify({'success': True, 'filename': filename, 'image_url': url_for('serve_uploaded_file', filename=filename), 'original_resolution': 'resolution_here'})
        except Exception as e:
            app.logger.error(f"Error saving file: {e}")
            return jsonify({'success': False, 'message': 'Error saving file'})
    else:
        app.logger.error('Invalid file type')
        return jsonify({'success': False, 'message': 'Invalid file type'})

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('home'))
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        session['current_image'] = filename  # Store the current image in session#+
        return redirect(url_for('process_image', filename=filename))
    else:
        flash('Invalid file type. Please upload PNG, JPG, or JPEG.')
        return redirect(url_for('home'))
# {"source":"chat"}

@app.route('/process/<filename>')
def process_image(filename):
    session['current_image'] = filename  # Ensure current_image is set
    return render_template('process.html', filename=filename)


@app.route('/enhance/<filename>', methods=['GET', 'POST'])
def enhance_image(filename):
    current_image = session.get('current_image', filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], current_image)
    upscaled_filename = f'upscaled_{current_image}'
    upscaled_path = os.path.join(app.config['UPSCALED_FOLDER'], upscaled_filename)

    if request.method == 'POST':
        try:
            upscaled_image = upscale(file_path)
            cv2.imwrite(upscaled_path, upscaled_image)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'original_url': url_for('serve_uploaded_file', filename=current_image),
                    'enhanced_url': url_for('serve_upscaled_file', filename=upscaled_filename),
                    'download_url': url_for('download_enhanced', filename=upscaled_filename)
                })
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)}), 500

    # GET request handling
    if not os.path.exists(upscaled_path):
        upscaled_image = upscale(file_path)
        cv2.imwrite(upscaled_path, upscaled_image)

    return render_template('enhance.html', 
                         original_filename=current_image,
                         upscaled_filename=upscaled_filename)


@app.route('/download/<filename>')
def download_enhanced(filename):
    return send_file(
        os.path.join(app.config['UPSCALED_FOLDER'], filename),
        as_attachment=True,
        download_name=f"enhanced_{filename}"
    )

@app.route('/caption/<filename>')
def caption_image(filename):
    current_image = session.get('current_image', filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], current_image)
    caption = generate_caption(file_path)
    return render_template('caption.html', filename=current_image, caption=caption)

@app.route('/vqa_upload', methods=['POST'])
def vqa_upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Store in session
        session['current_image'] = filename
        
        return jsonify({
            'success': True,
            'filename': filename,
            'image_url': url_for('serve_uploaded_file', filename=filename)
        })
    
    return jsonify({'success': False, 'message': 'Invalid file type'})

@app.route('/vqa_answer', methods=['POST'])
def vqa_answer():
    if 'current_image' not in session:
        return jsonify({'success': False, 'message': 'No image uploaded'})
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], session['current_image'])
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Image not found'})
    
    question = request.form.get('question', '')
    if not question:
        return jsonify({'success': False, 'message': 'Question is required'})
    
    try:
        answer = answer_question(file_path, question)
        return jsonify({
            'success': True,
            'answer': answer,
            'filename': session['current_image']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })
    
@app.route('/get_current_image')
def get_current_image():
    current_image = session.get('current_image')
    return jsonify({'current_image': current_image})

@app.route('/similarity_upload', methods=['POST'])
def similarity_upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Store in session
        session['current_image'] = filename
        
        # Find similar images
        similar_images = find_similar_images(file_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'image_url': url_for('serve_uploaded_file', filename=filename),
            'similar_images': similar_images
        })
    
    return jsonify({'success': False, 'message': 'Invalid file type'})

@app.route('/vqa/<filename>', methods=['GET', 'POST'])
def vqa_image(filename):
    current_image = session['current_image']
    if not current_image :
        current_image = filename
        session['current_image'] = filename

    if request.method == 'POST':
        question = request.form.get('question')
        if not question:
            return jsonify({'success': False, 'message': 'Please enter a question'}), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], current_image)

        try:
            answer = answer_question(file_path, question)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'question': question,
                    'answer': answer,
                    'filename': current_image
                })
            else:
                return render_template('vqa.html', filename=current_image, question=question, answer=answer)

        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'filename': current_image,
            'message': 'Ready for questions'
        })
    return render_template('vqa.html', filename=current_image)

# Update the find_similar_images function to handle errors better
def find_similar_images(image_path: str):
    try:
        caption = generate_caption(image_path)  # Generate caption for input image
        query = f"{caption} similar images"
        
        with DDGS() as ddgs:
            results = [result["image"] for result in ddgs.images(query, max_results=6)]  # Increased to 6 results
            
        return results if results else ["https://via.placeholder.com/150"]
    except Exception as e:
        print(f"Error finding similar images: {str(e)}")
        return ["https://via.placeholder.com/150"] * 3  # Return placeholder images if error occurs

# Update the similarity_image route to handle errors

@app.route('/similarity/<filename>')
def similarity_image(filename):
    try:
        current_image = session.get('current_image', filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(current_image))
        similar_images = find_similar_images(file_path)
        return render_template('similarity.html', 
                            filename=current_image,
                            similar_images=similar_images)
    except Exception as e:
        print(f"Error in similarity route: {str(e)}")
        return render_template('similarity.html', 
                            filename=current_image,
                            similar_images=["https://via.placeholder.com/150"] * 3)


@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/upscaled/<filename>')
def serve_upscaled_file(filename):
    return send_file(os.path.join(app.config['UPSCALED_FOLDER'], filename))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('home'))
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            session['current_image'] = filename  # Store the current image in session
            return render_template('index.html', 
                                filename=filename,
                                email=session.get('email'),
                                fullname=session.get('fullname', 'User'))

    if 'email' in session:
        return render_template('index.html', 
                            email=session.get('email'),
                            fullname=session.get('fullname', 'User'),
                            filename=session.get('current_image'))
    return render_template('landing.html')


@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.json.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400

    otp = generate_otp()
    otps[email] = otp

    msg = Message('Your OTP', sender='mupparajuk31@gmail.com', recipients=[email])
    msg.body = f'Your OTP is {otp}'
    try:
        mail.send(msg)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    email = request.json.get('email')
    otp = request.json.get('otp')

    if not email or not otp:
        return jsonify({'success': False, 'message': 'Email and OTP are required'}), 400

    if otps.get(email) == otp:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid OTP'}), 400

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/registering', methods=['POST', 'GET'])
def register():
    fullname = request.form.get('fullname')
    email = request.form.get('email')
    password = request.form.get('password')  

    if not fullname or not email or not password:
        return "<h1>All fields are required</h1>"

    if collection.find_one({'email': email}):
        return "<h1>Email already present</h1>"

    result = collection.insert_one({
        'fullname': fullname,
        'email': email,
        'password': password,
        'Your_Properties':[]
    })

    
    
    if result.inserted_id:
        return redirect(url_for('login'))
    else:
        return "<h1>Failed to register user</h1>"


@app.route('/logging', methods=['POST', 'GET'])
def logging():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = collection.find_one({'email': email, 'password': password})
        if user:
            session['email'] = email
            session['fullname'] = user.get('fullname', 'User')
            return redirect(url_for('home'))
        flash('Invalid username or password. Please try again.')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('email', None)  # Remove the 'email' key from the session
    session.pop("current_image",None)
    return redirect(url_for('home'))  # Redirect to the home route


ngrok.set_auth_token("2rqni7Bv8lTlCg5eHlEJP15DxgE_2sqUrw3NDw4XpTjNu4GiZ")
public_url = ngrok.connect(5000)
print("Public URL:", public_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)

