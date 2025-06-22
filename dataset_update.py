import pandas as pd

# Load the dataset
df = pd.read_csv('original_food_dataset.csv')

# Define the score calculation function
def calculate_score(L, D, A, w_l=1.0, w_d=1.5):
    if A > 0:
        return 0
    elif L + D == 0:
        return 50
    else:
        raw = (w_l * L - w_d * D) / (w_l * L + w_d * D)
        score = ((raw + 1) / 2) * 100
        return max(0, min(score, 100))

# Start updating from the 21st row (index 20)
for i in range(0, len(df)):
    try:
        L = int(df.at[i, 'num_liked_matches'])
        D = int(df.at[i, 'num_disliked_matches'])
        A = int(df.at[i, 'num_allergen_matches'])
        df.at[i, 'suitability_score'] = round(calculate_score(L, D, A), 2)
    except Exception as e:
        print(f"Error at row {i}: {e}")

# Save the updated dataset
df.to_csv('food_suitability_dataset_updated.csv', index=False)

print("Suitability scores updated and saved as 'food_suitability_dataset_updated.csv'")