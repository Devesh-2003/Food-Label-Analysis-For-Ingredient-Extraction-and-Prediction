import joblib
import numpy as np

# Load model and scaler
model = joblib.load("xgb_model.pkl")  # or "mlp_model.pkl"
scaler = joblib.load("scaler.pkl")

# Example input
ingredients = ["corn", "cheese", "salt", "flavor"]
likes = ["corn", "flavor","cheese"]
dislikes = []
allergens = []

# Feature extraction (without additives)
def extract_features(ingredients, likes, dislikes, allergens):
    ingredients_set = set([i.strip().lower() for i in ingredients])
    likes_set = set([i.strip().lower() for i in likes])
    dislikes_set = set([i.strip().lower() for i in dislikes])
    allergens_set = set([i.strip().lower() for i in allergens])

    return [
        len(ingredients_set),
        len(ingredients_set & likes_set),
        len(ingredients_set & dislikes_set),
        len(ingredients_set & allergens_set)
    ]

# Get features and predict
X = [extract_features(ingredients, likes, dislikes, allergens)]
if "MLP" in model.__class__.__name__:
    X = scaler.transform(X)

score = float(model.predict(X)[0])
print(f"Predicted Suitability Score: {max(0.0,min(100,round(score, 2)))}")