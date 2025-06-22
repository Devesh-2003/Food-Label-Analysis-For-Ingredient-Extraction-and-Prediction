from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import joblib
import os
import json
import easyocr
from werkzeug.security import generate_password_hash, check_password_hash

# Setup
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for session and flashing messages
UPLOAD_FOLDER = 'uploads'
USER_FOLDER = 'users'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(USER_FOLDER, exist_ok=True)

# Load model and scaler
model = joblib.load("xgb_model.pkl")  # or "mlp_model.pkl"
scaler = joblib.load("scaler.pkl")

# EasyOCR reader
reader = easyocr.Reader(['en'], gpu=False)


# ---------- Feature Extraction ----------
def extract_features(ingredients, likes, dislikes, allergens):
    ingredients = [i.lower() for i in ingredients]
    likes = [l.lower() for l in likes]
    dislikes = [d.lower() for d in dislikes]
    allergens = [a.lower() for a in allergens]

    def count_partial_matches(keywords):
        return sum(
            any(keyword in ingredient for ingredient in ingredients)
            for keyword in keywords
        )

    return {
        "num_ingredients": len(ingredients),
        "num_liked_matches": count_partial_matches(likes),
        "num_disliked_matches": count_partial_matches(dislikes),
        "num_allergen_matches": count_partial_matches(allergens)
    }


# ---------- Home Route ----------
@app.route("/")
def home():
    return redirect(url_for("login"))


# ---------- Login ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        userid = request.form.get("userid")
        password = request.form.get("password")
        user_file = os.path.join(USER_FOLDER, f"{userid}.json")

        if not os.path.exists(user_file):
            return render_template("login.html", error="User does not exist")

        with open(user_file, "r") as f:
            user_data = json.load(f)

        if not check_password_hash(user_data["password"], password):
            return render_template("login.html", error="Invalid credentials")

        # ✅ Set session on successful login
        session['username'] = userid

        return redirect(url_for("index"))

    return render_template("login.html")


# ---------- Signup ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        userid = request.form.get("userid")
        password = request.form.get("password")

        if not userid or not password:
            return render_template("signup.html", error="All fields required")

        if len(password) < 8:
            return render_template("signup.html", error="Password must be at least 8 characters long")

        user_file = os.path.join(USER_FOLDER, f"{userid}.json")
        if os.path.exists(user_file):
            return render_template("signup.html", error="User already exists")

        hashed_pw = generate_password_hash(password)
        with open(user_file, "w") as f:
            json.dump({
                "userid": userid,
                "password": hashed_pw,
                "likes": [],
                "dislikes": [],
                "allergens": []
            }, f)

        flash("Signup successful! Please login.")
        return redirect(url_for("login"))

    return render_template("signup.html")



# ---------- Logout ----------
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.")
    return redirect(url_for("login"))


# ---------- Guest Access ----------
@app.route("/guest")
def guest():
    session.pop("username", None)
    return redirect(url_for("index"))


# ---------- Home Page ----------
@app.route("/index")
def index():
    return render_template("index.html")


# ---------- OCR Extraction ----------
@app.route("/extract", methods=["POST"])
def extract():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image = request.files['image']
    image_path = os.path.join(UPLOAD_FOLDER, "temp.jpg")
    image.save(image_path)

    try:
        results = reader.readtext(image_path, detail=0)
        extracted_text = " ".join(results).lower()
        clean_text = extracted_text.translate(str.maketrans(",;()[]", "\n\n\n\n\n\n"))
        ingredients = [i.strip() for i in clean_text.split("\n") if i.strip()]
        return jsonify({"ingredients": ingredients})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Suitability Prediction ----------
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    ingredients = data.get("ingredients", [])
    likes = data.get("likes", [])
    dislikes = data.get("dislikes", [])
    allergens = data.get("allergens", [])

    features = extract_features(ingredients, likes, dislikes, allergens)

    X = [[
        features["num_ingredients"],
        features["num_liked_matches"],
        features["num_disliked_matches"],
        features["num_allergen_matches"]
    ]]

    if "MLP" in model.__class__.__name__:
        X = scaler.transform(X)

    score = float(model.predict(X)[0])
    return jsonify({"suitability_score": max(0.0, min(100, round(score, 2)))})


# ---------- Get User Preferences ----------
@app.route("/get_preferences", methods=["GET"])
def get_preferences():
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "message": "User not logged in"})

    user_file = os.path.join(USER_FOLDER, f"{username}.json")
    if not os.path.exists(user_file):
        return jsonify({"success": False, "message": "Preferences not found"})

    with open(user_file, "r") as f:
        data = json.load(f)

    preferences = {
        "likes": data.get("likes", []),
        "dislikes": data.get("dislikes", []),
        "allergens": data.get("allergens", [])
    }

    return jsonify({"success": True, "preferences": preferences})


# ---------- Save User Preferences ----------
@app.route("/save_preferences", methods=["POST"])
def save_preferences():
    username = session.get('username')
    if not username:
        return jsonify({"success": False, "message": "User not logged in"})

    user_file = os.path.join(USER_FOLDER, f"{username}.json")
    if not os.path.exists(user_file):
        return jsonify({"success": False, "message": "User file not found"})

    data = request.get_json()
    likes = data.get("likes", [])
    dislikes = data.get("dislikes", [])
    allergens = data.get("allergens", [])

    with open(user_file, "r") as f:
        user_data = json.load(f)

    user_data["likes"] = likes
    user_data["dislikes"] = dislikes
    user_data["allergens"] = allergens

    with open(user_file, "w") as f:
        json.dump(user_data, f)

    return jsonify({"success": True})


# ---------- Run Server ----------
if __name__ == "__main__":
    app.run(debug=True)
    ##app.run(host='0.0.0.0', port=5000, debug=True)