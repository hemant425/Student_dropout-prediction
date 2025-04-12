from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Load trained dropout prediction model
try:
    model_path = r"C:\Users\heman\OneDrive\Documents\Python projects\Mini project-5 sem\Jarvis\skin_condition_model_csv_only.h5"
    model = load_model(model_path)
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None  # Prevent crashes if model is missing

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create database tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return "Username already exists. Try another one."

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('predict_step1'))
        else:
            return "Invalid credentials"

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/predict_step1', methods=['GET', 'POST'])
@login_required
def predict_step1():
    if request.method == 'POST':
        total_subjects = request.form.get('total_subjects')

        # Validate input
        if not total_subjects or not total_subjects.isdigit():
            return "Error: Total subjects must be a number", 400
        
        total_subjects = int(total_subjects)
        
        if not (1 <= total_subjects <= 12):
            return "Error: Total subjects must be between 1 and 12", 400

        # Store the total number of subjects
        session['total_subjects'] = total_subjects
        
        return redirect(url_for('predict_step2'))

    return render_template('predict_step1.html')



@app.route('/predict_step2', methods=['GET', 'POST'])
@login_required
def predict_step2():
    if request.method == 'POST':
        try:
            if model is None:
                return jsonify({"error": "Model not loaded"}), 500

            # Get total subjects from session (default to 1 if missing)
            total_subjects = session.get('total_subjects', 1)

            # Collect input features dynamically
            input_features = []
            for i in range(1, total_subjects + 1):
                for j in range(1, 6):  # 5 CIE marks per subject
                    cie_mark = request.form.get(f'cie{i}_{j}')
                    if cie_mark is None or cie_mark.strip() == "":
                        return jsonify({"error": f"Missing CIE mark for Subject {i}, CIE {j}"}), 400
                    input_features.append(float(cie_mark))

            # Ensure collected features match expected input shape
            expected_features = total_subjects * 5
            if len(input_features) != expected_features:
                return jsonify({"error": f"Invalid number of input features! Expected {expected_features}, got {len(input_features)}"}), 400

            # Convert to NumPy array and reshape for model
            input_array = np.array(input_features).reshape(1, -1)

            # Ensure the model's input layer matches the dynamic size
            if input_array.shape[1] != model.input_shape[1]:
                return jsonify({"error": f"Model expects {model.input_shape[1]} features, but received {input_array.shape[1]}"}), 400

            # Predict using the model
            predicted_score = model.predict(input_array)[0][0]

            # Determine if the student will graduate
            status = "Graduate" if predicted_score >= 40 else "Drop Out"

            # Store prediction result
            session['prediction'] = {"score": int(predicted_score), "status": status}

            return jsonify({
                "predicted_final_exam_score": int(predicted_score),
                "status": status
            })

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return render_template('predict_step2.html', total_subjects=session.get('total_subjects', 1))



@app.route('/predict_result')
@login_required
def predict_result():
    prediction = session.get('prediction', {"score": "N/A", "status": "No prediction made yet"})
    return render_template('predict_result.html', prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)
