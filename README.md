Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# ImageChatbot - AI-Powered Image Analysis Platform

![ImageChatbot Demo](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9.9-green)
![Flask](https://img.shields.io/badge/flask-3.0.3-red)
![License](https://img.shields.io/badge/license-MIT-yellow)

ImageChatbot is an advanced web application that leverages artificial intelligence to provide comprehensive image analysis and processing capabilities. Built with Flask, it offers a suite of powerful features for image enhancement, understanding, and exploration.

## 🚀 Key Features

### 🖼️ Image Enhancement
- **Super Resolution**: Upscale images while maintaining quality using ONNX Runtime
- **Quality Improvement**: Advanced noise reduction and detail enhancement
- **High-Resolution Generation**: Transform low-quality images into high-definition versions

### 📝 Intelligent Image Captioning
- **Automatic Description**: Generate natural language descriptions of images
- **BLIP Model**: Powered by state-of-the-art Bootstrapping Language-Image Pre-training
- **Contextual Understanding**: Generate meaningful and relevant captions

### ❓ Visual Question Answering
- **Interactive Analysis**: Ask questions about image content
- **Real-time Responses**: Get instant answers about visual elements
- **Deep Understanding**: Powered by advanced BLIP-VQA model

### 🔍 Image Similarity Search
- **Visual Matching**: Find similar images based on content
- **Advanced Comparison**: Sophisticated image matching algorithms
- **Content Discovery**: Explore visually related images

### 🔐 Secure User Management
- **Authentication System**: Secure login and registration
- **OTP Verification**: Email-based one-time password verification
- **Session Management**: Secure user sessions with Flask-Session
- **MongoDB Integration**: Robust user data storage

## 🛠️ Technical Architecture

### Backend Stack
- **Framework**: Flask 3.0.3
- **Database**: MongoDB
- **Authentication**: Flask-Bcrypt
- **Session Management**: Flask-Session
- **Email Service**: Flask-Mail

### AI/ML Infrastructure
- **Image Processing**: OpenCV, Pillow
- **Deep Learning**:
  - ONNX Runtime for image enhancement
  - BLIP models for captioning and VQA
  - Transformers library for NLP tasks
- **Computer Vision**: OpenCV, NumPy

### Frontend Technologies
- **HTML5 & CSS3**: Modern, responsive design
- **User Interface**: Intuitive and interactive
- **Responsive Design**: Mobile-friendly experience

## 🛠️ Installation Guide

1. **Clone the Repository**
   ```bash
   git clone https://github.com/lokeshpanthangi/Imagechatbot.git
   cd Imagechatbot
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   - Create a `.env` file with the following configurations:
     ```
     MONGODB_URI=your_mongodb_connection_string
     MAIL_SERVER=your_smtp_server
     MAIL_PORT=your_smtp_port
     MAIL_USERNAME=your_email
     MAIL_PASSWORD=your_email_password
     SECRET_KEY=your_secret_key
     ```

4. **Run the Application**
   ```bash
   python app.py
   ```
   Access the application at `http://localhost:5000`

## 📖 Usage Guide

### 1. User Authentication
- Register a new account
- Verify email through OTP
- Log in to access features

### 2. Image Processing
- Upload images (JPG, PNG, JPEG)
- Choose processing options:
  - Image Enhancement
  - Automatic Captioning
  - Visual Question Answering
  - Similarity Search

### 3. Results and Analysis
- View enhanced images
- Read generated captions
- Get answers to image-related questions
- Discover similar images

## 🔒 Security Implementation

- **Password Security**: Bcrypt hashing
- **Session Protection**: Secure session management
- **File Upload Security**: Safe file handling
- **Email Verification**: OTP-based authentication
- **Database Security**: MongoDB best practices

## 📧 Contact

For questions, suggestions, or support:
- Email: lokeshpantangi@gmail.com
- GitHub: [lokeshpanthangi](https://github.com/lokeshpanthangi)
