let extractedIngredients = [];

const dietaryAllergens = {
  vegan: [
    "milk", "cheese", "butter", "honey", "gelatin", "egg", "casein", "lactose", "whey"
  ],
  dairy_free: [
    "milk", "cheese", "butter", "cream", "yogurt", "curd", "lactose", "casein", "whey"
  ],
  halal: [
    "pork", "bacon", "gelatin (non-halal)", "alcohol", "ethanol", "vanilla extract"
  ],
  gluten_free: [
    "wheat", "barley", "rye", "malt", "semolina", "triticale"
  ]
};

// Show feedback messages
function showMessage(msg, type = 'success') {
  const box = document.getElementById("message-box");
  box.innerText = msg;
  box.className = type === 'success' ? "message-success" : "message-error";
  box.style.display = "block";
  setTimeout(() => {
    box.style.display = "none";
  }, 4000);
}

// Apply dietary preference to allergens input
function applyDietaryPreference() {
  const selected = document.getElementById("preference").value;
  const allergenInput = document.getElementById("allergens");

  if (selected && dietaryAllergens[selected]) {
    allergenInput.value = dietaryAllergens[selected].join(", ");
  } else {
    allergenInput.value = "";
  }
}

// Extract ingredients from uploaded image
async function extractIngredients() {
  const imageInput = document.getElementById("image");
  const file = imageInput.files[0];
  if (!file) {
    alert("Please upload an image first.");
    return;
  }

  const button = event.target;
  const originalText = button.innerText;
  button.innerText = "Extracting...";
  button.disabled = true;

  const formData = new FormData();
  formData.append("image", file);

  try {
    const response = await fetch("/extract", {
      method: "POST",
      body: formData
    });

    const result = await response.json();
    if (result.ingredients) {
      extractedIngredients = result.ingredients;
      document.getElementById("ingredients-list").innerText =
        "Extracted Ingredients:\n" + extractedIngredients.join(", ");
      showMessage("Ingredients extracted successfully!");
    } else {
      document.getElementById("ingredients-list").innerText = "Failed to extract ingredients.";
      showMessage("Extraction failed.", "error");
    }
  } catch (err) {
    showMessage("Network error during extraction.", "error");
  } finally {
    button.innerText = originalText;
    button.disabled = false;
  }
}

// Predict suitability based on preferences
async function predictSuitability() {
  const likes = document.getElementById("likes").value.split(",").map(i => i.trim()).filter(i => i);
  const dislikes = document.getElementById("dislikes").value.split(",").map(i => i.trim()).filter(i => i);
  const allergens = document.getElementById("allergens").value.split(",").map(i => i.trim()).filter(i => i);

  const data = {
    ingredients: extractedIngredients,
    likes: likes,
    dislikes: dislikes,
    allergens: allergens
  };

  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const result = await response.json();
    if (result.suitability_score !== undefined) {
      document.getElementById("score-result").innerText =
        `Suitability Score: ${result.suitability_score}`;
      showMessage("Suitability score calculated!");
    } else {
      document.getElementById("score-result").innerText =
        `Error: ${result.error || "Prediction failed."}`;
      showMessage("Prediction failed.", "error");
    }
  } catch (err) {
    showMessage("Network error during prediction.", "error");
  }
}

// Save user preferences
async function savePreferences() {
  const likes = document.getElementById("likes").value.split(",").map(i => i.trim()).filter(i => i);
  const dislikes = document.getElementById("dislikes").value.split(",").map(i => i.trim()).filter(i => i);
  const allergens = document.getElementById("allergens").value.split(",").map(i => i.trim()).filter(i => i);

  const button = event.target;
  const originalText = button.innerText;
  button.innerText = "Saving...";
  button.disabled = true;

  try {
    const response = await fetch("/save_preferences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ likes, dislikes, allergens })
    });

    const result = await response.json();
    if (result.success) {
      showMessage("Preferences saved!");
    } else {
      showMessage("Failed to save preferences: " + (result.message || "Unknown error"), "error");
    }
  } catch (err) {
    showMessage("Network error during save.", "error");
  } finally {
    button.innerText = originalText;
    button.disabled = false;
  }
}

// Load saved preferences on page load
window.onload = async () => {
  try {
    const response = await fetch("/get_preferences");
    const result = await response.json();
    if (result.success && result.preferences) {
      document.getElementById("likes").value = result.preferences.likes.join(", ");
      document.getElementById("dislikes").value = result.preferences.dislikes.join(", ");
      document.getElementById("allergens").value = result.preferences.allergens.join(", ");

      for (const [key, list] of Object.entries(dietaryAllergens)) {
        if (arraysEqualIgnoreOrder(result.preferences.allergens, list)) {
          document.getElementById("preference").value = key;
          break;
        }
      }
    }
  } catch (err) {
    console.log("Not logged in or error loading preferences.");
  }
};

// Helper: check if two arrays contain same values (ignoring order)
function arraysEqualIgnoreOrder(a, b) {
  return a.length === b.length && a.every(item => b.includes(item));
}
