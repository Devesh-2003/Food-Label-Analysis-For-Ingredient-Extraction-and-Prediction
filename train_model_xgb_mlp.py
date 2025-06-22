import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Load updated dataset
df = pd.read_csv("food_suitability_dataset_updated.csv")  # Use the new CSV

# Define input features and target (without 'num_additives')
feature_cols = [
    "num_ingredients", "num_liked_matches",
    "num_disliked_matches", "num_allergen_matches"
]
X = df[feature_cols]
y = df["suitability_score"]

# Split into train/test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale for MLP
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ---- Train XGBoost Regressor ----
xgb_model = XGBRegressor(
    n_estimators=50,
    max_depth=4,
    learning_rate=0.1,
    random_state=42,
    n_jobs=-1
)
xgb_model.fit(X_train, y_train)

# ---- Train MLP Regressor ----
mlp_model = MLPRegressor(
    hidden_layer_sizes=(64, 32),
    max_iter=500,
    random_state=42
)
mlp_model.fit(X_train_scaled, y_train)

# ---- Evaluate Models ----
def evaluate(model_name, y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"{model_name} RMSE: {rmse:.2f}")
    print(f"{model_name} R²: {r2:.4f}\n")

evaluate("XGBoost", y_test, xgb_model.predict(X_test))
evaluate("MLP", y_test, mlp_model.predict(X_test_scaled))

# ---- Save Models and Scaler ----
joblib.dump(xgb_model, "xgb_model.pkl")
joblib.dump(mlp_model, "mlp_model.pkl")
joblib.dump(scaler, "scaler.pkl")