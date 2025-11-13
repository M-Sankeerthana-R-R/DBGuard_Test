# import torch
# import torch.nn as nn
# import re

# # -------------------------------
# # 1️⃣ Define the same model structure
# # -------------------------------
# class SimpleNN(nn.Module):
#     def __init__(self, input_dim, hidden_dim=64, output_dim=1):
#         super(SimpleNN, self).__init__()
#         self.network = nn.Sequential(
#             nn.Linear(input_dim, hidden_dim),
#             nn.ReLU(),
#             nn.Linear(hidden_dim, hidden_dim),
#             nn.ReLU(),
#             nn.Linear(hidden_dim, output_dim)
#         )

#     def forward(self, x):
#         return self.network(x)

# # -------------------------------
# # 2️⃣ Load trained weights
# # -------------------------------
# # MODEL_PATH = "monitor/trained_model.pth"
# import os

# MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_model_final.pth")
# INPUT_DIM = 13  # same as your training feature size
# model = SimpleNN(INPUT_DIM)
# model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
# model.eval()

# # -------------------------------
# # 3️⃣ Feature extraction for queries
# # -------------------------------
# def extract_features(query: str):
#     """
#     Convert SQL query into numeric features for the model.
#     Example features (length 13):
#       - query length
#       - number of joins
#       - number of subqueries
#       - count of WHERE/AND/OR
#       - number of SELECT columns
#       - number of tables
#       - presence of *, DISTINCT, GROUP BY, ORDER BY
#       - etc.
#     """
#     q = query.lower()
#     features = [
#         len(q),  # total length
#         q.count("join"),
#         q.count("select"),
#         q.count("where"),
#         q.count("and"),
#         q.count("or"),
#         q.count("from"),
#         q.count("*"),
#         int("distinct" in q),
#         int("group by" in q),
#         int("order by" in q),
#         q.count("("),  # subqueries
#         q.count(")")   # subqueries
#     ]
#     return torch.tensor(features).float().unsqueeze(0)  # shape [1,13]

# # -------------------------------
# # 4️⃣ Root cause ranking
# # -------------------------------
# def analyze_root_causes(query: str):
#     """
#     Returns a ranked list of root causes contributing to query slowness.
#     Combines ML model prediction and rule-based heuristics.
#     """
#     # Extract features and predict
#     features = extract_features(query)
#     with torch.no_grad():
#         score = torch.sigmoid(model(features))[0][0].item()

#     q = query.lower()
#     causes = []

#     # 1. Full Table Scan
#     if re.search(r"select\s+\*", q):
#         causes.append({"cause": "full_table_scan", "score": 0.9})

#     # 2. Missing WHERE Filter
#     if "where" not in q:
#         causes.append({"cause": "missing_where_filter", "score": 0.85})

#     # 3. Excessive Joins
#     if q.count("join") >= 3:
#         causes.append({"cause": "too_many_joins", "score": 0.8})

#     # 4. Subquery Explosion
#     if q.count("(") > 3:
#         causes.append({"cause": "subquery_explosion", "score": 0.75})

#     # 5. Large GROUP BY / Aggregation
#     if "group by" in q:
#         causes.append({"cause": "large_group_by_aggregation", "score": 0.78})

#     # 6. Sorting Overhead
#     if "order by" in q:
#         causes.append({"cause": "sorting_overhead", "score": 0.76})

#     # 7. Function-based Filter (index ignored)
#     if re.search(r"where\s+\w+\s*\(", q):
#         causes.append({"cause": "function_based_filter", "score": 0.8})

#     # # 8. Cartesian Product
#     # try:
#     #     from_match = re.search(r"from\s+(.*)", q)
#     #     if from_match and "join" not in q:
#     #         table_section = from_match.group(1)
#     #         if "," in table_section:
#     #             causes.append({"cause": "cartesian_product", "score": 0.82})
#     # except Exception:
#     #     pass  # ignore if no FROM clause or invalid match


#     # 9. High Data Volume Access
#     if any(word in q for word in ["all", "distinct", "having"]):
#         causes.append({"cause": "high_data_volume_access", "score": 0.77})

#     # ML Predicted Score
#     causes.append({"cause": "ml_predicted_slow", "score": score})

#     # Sort descending by score
#     ranked = sorted(causes, key=lambda x: x["score"], reverse=True)
#     return ranked

import torch
import torch.nn as nn
import os
import re

# ------------------------------------------------
# 1️⃣ Model Definition
# ------------------------------------------------
class SimpleNN(nn.Module):
    def __init__(self, input_dim=13, hidden_dim=64, output_dim=1):
        super(SimpleNN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x):
        return self.network(x)


# ------------------------------------------------
# 2️⃣ Load Model Dynamically (no hardcoding)
# ------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_model_final.pth")

def load_model():
    model = SimpleNN(input_dim=13, output_dim=1)
    checkpoint = torch.load(MODEL_PATH, map_location="cpu")

    # Flexible key handling
    if isinstance(checkpoint, dict) and "model_state" in checkpoint:
        model.load_state_dict(checkpoint["model_state"])
        class_names = checkpoint.get("class_names", ["unknown_root_cause"])
    elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        model.load_state_dict(checkpoint["state_dict"])
        class_names = checkpoint.get("class_names", ["unknown_root_cause"])
    else:
        model.load_state_dict(checkpoint)
        class_names = ["missing_indexes", "too_many_joins", "subquery_explosion", "function_based_filter"]

    model.eval()
    return model, class_names


model, class_names = load_model()


# ------------------------------------------------
# 3️⃣ Feature Extraction
# ------------------------------------------------
def extract_features(query: str):
    q = query.lower()
    features = [
        len(q),
        q.count("join"),
        q.count("select"),
        q.count("where"),
        q.count("and"),
        q.count("or"),
        q.count("from"),
        q.count("*"),
        int("distinct" in q),
        int("group by" in q),
        int("order by" in q),
        q.count("("),
        q.count(")")
    ]
    # Normalize to smaller scale (avoid 1.0 saturation)
    tensor = torch.tensor(features, dtype=torch.float32)
    tensor = (tensor - tensor.mean()) / (tensor.std() + 1e-6)
    return tensor.unsqueeze(0)


# ------------------------------------------------
# 4️⃣ Analyze and Predict Root Cause
# ------------------------------------------------
def analyze_root_causes(query: str):
    features = extract_features(query)

    with torch.no_grad():
        raw_output = model(features)
        score = torch.sigmoid(raw_output)[0][0].item()

    # Clamp extreme scores
    score = max(0.0, min(score, 1.0))
    # score = 0.89

    # Categorize with lower thresholds for better detection
    if score >= 0.40:
        status = "Slow"
        alert = "🚨 Model detected likely performance issue."
        predicted_index = int((score * len(class_names)) % len(class_names))
        predicted_cause = class_names[predicted_index]
    elif 0.30 <= score < 0.40:
        status = "Near Slow"
        alert = "⚠️ Query nearing slowness threshold."
        predicted_index = int((score * len(class_names)) % len(class_names))
        predicted_cause = class_names[predicted_index]
    else:
        status = "Normal"
        alert = "✅ Query appears normal."
        predicted_cause = ""

    print(f"[ALERT] {alert}")
    print(f"[DEBUG] Predicted Score: {score:.4f}")
    if predicted_cause:
        print(f"[DEBUG] Predicted Root Cause: {predicted_cause}")

    return {
        "score": round(score, 4),
        "status": status,
        "root_cause": predicted_cause
    }
