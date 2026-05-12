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
# import torch
# import torch.nn as nn
# import os
# import random   # ✅ added for randomness

# # ============================================================
# # 1️⃣ Feature-to-Embedding Adapter (13 → 256)
# # ============================================================
# class SQLFeatureAdapter(nn.Module):
#     def __init__(self, in_dim=13, out_dim=256):
#         super().__init__()
#         self.adapter = nn.Sequential(
#             nn.Linear(in_dim, 128),
#             nn.ReLU(),
#             nn.Linear(128, out_dim),
#             nn.ReLU()
#         )

#     def forward(self, x):
#         return self.adapter(x)


# # ============================================================
# # 2️⃣ Core Architectures from Trained Model
# # ============================================================
# class FusionModel(nn.Module):
#     def __init__(self, fused_dim=256, nhead=4, num_layers=2):
#         super().__init__()
#         encoder_layer = nn.TransformerEncoderLayer(d_model=fused_dim, nhead=nhead)
#         self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
#         self.fc = nn.Linear(fused_dim, fused_dim)

#     def forward(self, bert, log, ts, qf):
#         # Stack the four modality embeddings
#         x = torch.stack([bert, log, ts, qf], dim=1)  # (B, 4, fused_dim)
#         x = x.transpose(0, 1)                        # (4, B, fused_dim)
#         x = self.transformer(x)
#         x = x.mean(dim=0)                            # (B, fused_dim)
#         return self.fc(x)


# class GateComDiffPretrainModel(nn.Module):
#     def __init__(self, emb_dim=256, n_label=9, cross_model=None, weight=0.5):
#         super().__init__()
#         self.n_label = n_label
#         self.weight = weight
#         self.rootcause_cross_model = cross_model
#         self.sigmoid = nn.Sigmoid()

#         # Gating + prediction heads for each label
#         self.pred_label_cross_list = nn.ModuleList([nn.Linear(emb_dim, 1) for _ in range(n_label)])
#         self.pred_opt_cross_list = nn.ModuleList([nn.Linear(emb_dim, 1) for _ in range(n_label)])
#         self.gate_sql = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])
#         self.gate_plan = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])
#         self.gate_log = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])
#         self.gate_metrics = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])

#     def forward(self, sql_emb, plan_emb, log_emb, time_emb, common_emb):
#         for i in range(self.n_label):
#             sql_gate = self.sigmoid(self.gate_sql[i](sql_emb)) * sql_emb
#             plan_gate = self.sigmoid(self.gate_plan[i](plan_emb)) * plan_emb
#             log_gate = self.sigmoid(self.gate_log[i](log_emb)) * log_emb
#             time_gate = self.sigmoid(self.gate_metrics[i](time_emb)) * time_emb

#             emb = self.rootcause_cross_model(sql_gate, plan_gate, log_gate, time_gate)
#             emb = (1 - self.weight) * common_emb + self.weight * emb

#             pred_label = torch.sigmoid(self.pred_label_cross_list[i](emb))
#             pred_opt = self.pred_opt_cross_list[i](emb)

#             if i == 0:
#                 pred_label_output = pred_label
#                 pred_opt_output = pred_opt
#             else:
#                 pred_label_output = torch.cat([pred_label_output, pred_label], dim=-1)
#                 pred_opt_output = torch.cat([pred_opt_output, pred_opt], dim=-1)

#         return pred_label_output, pred_opt_output


# # ============================================================
# # 3️⃣ Load the Trained Model + Adapter
# # ============================================================
# MODEL_PATH = os.path.join(os.path.dirname(__file__), "final_model (1).pth")

# def load_model():
#     cross_model = FusionModel()
#     model = GateComDiffPretrainModel(emb_dim=256, cross_model=cross_model)
#     checkpoint = torch.load(MODEL_PATH, map_location="cpu")
#     model.load_state_dict(checkpoint, strict=False)
#     model.eval()

#     adapter = SQLFeatureAdapter()
#     adapter.eval()

#     class_names = [
#         "Bad Join Order", "Missing Index", "Complex Joins",
#         "Table-wide Updates", "Bulk Inserts", "inappropriate distribution keys",
#         "repeatedly executing subqueries", "redundant indexes", "outdated statistical information"
#     ]
#     return model, adapter, class_names


# model, adapter, class_names = load_model()


# # ============================================================
# # 4️⃣ Feature Extraction
# # ============================================================
# def extract_features(query: str):
#     q = query.lower()
#     features = [
#         len(q),
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
#         q.count("("),
#         q.count(")")
#     ]
#     tensor = torch.tensor(features, dtype=torch.float32)
#     tensor = (tensor - tensor.mean()) / (tensor.std() + 1e-6)
#     return tensor.unsqueeze(0)  # shape: [1, 13]


# # ============================================================
# # 5️⃣ Root-Cause Analyzer (🎲 randomness added)
# # ============================================================
# def analyze_root_causes(query: str):
#     # Extract and adapt features
#     features = extract_features(query)
#     features_256 = adapter(features)  # [1, 256]

#     with torch.no_grad():
#         # Feed the same embedding into all 4 input branches for inference
#         _, preds = model(features_256, features_256, features_256, features_256, features_256)
#         score = torch.sigmoid(preds.mean()).item()

#     # # ✅ Add randomness while keeping same structure
#     # # Sometimes similar, sometimes random high/low
#     # noise = random.uniform(-0.25, 0.25)
#     # if random.random() < 0.7:
#     #     score = score + noise
#     # else:
#     #     score = random.uniform(0.3, 0.95)
#     score = max(0.0, min(1.0, score))  # clamp between 0–1
#     # score=0.2312
#     # Categorize based on score
#     if score >= 0.75:
#         status = "Slow"
#         alert = "🚨 Likely performance issue"
#         cause = class_names[int(score * len(class_names)) % len(class_names)]
#     elif 0.55 <= score < 0.75:
#         status = "Near Slow"
#         alert = "⚠️ Query nearing slowness threshold"
#         cause = class_names[int(score * len(class_names)) % len(class_names)]
#     else:
#         status = "Normal"
#         alert = "✅ Query appears normal"
#         cause = ""

#     print(f"[ALERT] {alert}")
#     print(f"[DEBUG] Score: {score:.4f}")
#     if cause:
#         print(f"[DEBUG] Root Cause: {cause}")

#     return {
#         "score": round(score, 4),
#         "status": status,
#         "root_cause": cause
#     }


# # # ============================================================
# # # 6️⃣ Quick Test
# # # ============================================================
# # if __name__ == "__main__":
# #     result = analyze_root_causes("select * from employees where salary > 50000")
# #     print("\nFinal Output:", result)


# # multimodal_backend.py
import os
import time
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
import mysql.connector
from transformers import BertTokenizer

# ==============================================================
# 0️⃣ System Config
# ==============================================================
DEVICE = torch.device("cpu")

DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "rootpassword",
    "database": "mydb"
}

MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_model_final1.pth")

FUSED_DIM = 256
BERT_DIM = 768
PLAN_DIM = 256
LOG_DIM = 32
TS_DIM = 128

proj_bert = nn.Linear(BERT_DIM, FUSED_DIM).to(DEVICE)
proj_qf   = nn.Linear(PLAN_DIM, FUSED_DIM).to(DEVICE)
proj_log  = nn.Linear(LOG_DIM, FUSED_DIM).to(DEVICE)
proj_ts   = nn.Linear(TS_DIM, FUSED_DIM).to(DEVICE)

tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# ==============================================================
# 1️⃣ Define Models (Fusion + Gate)
# ==============================================================
class FusionModel(nn.Module):
    def __init__(self, fused_dim=FUSED_DIM, nhead=4, num_layers=2):
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(d_model=fused_dim, nhead=nhead)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Linear(fused_dim, fused_dim)

    def forward(self, bert, log, ts, qf):
        x = torch.stack([bert, log, ts, qf], dim=1)  # (B,4,256)
        x = x.transpose(0, 1)                       # (4,B,256)
        x = self.transformer(x)
        return self.fc(x.mean(dim=0))               # (B,256)

class GateComDiffPretrainModel(nn.Module):
    def __init__(self, emb_dim=FUSED_DIM, n_label=9, cross_model=None, weight=0.5):
        super().__init__()
        self.n_label = n_label
        self.weight = weight
        self.rootcause_cross_model = cross_model
        self.sigmoid = nn.Sigmoid()

        self.pred_label_cross_list = nn.ModuleList([nn.Linear(emb_dim, 1) for _ in range(n_label)])
        self.pred_opt_cross_list = nn.ModuleList([nn.Linear(emb_dim, 1) for _ in range(n_label)])
        self.gate_sql = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])
        self.gate_plan = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])
        self.gate_log = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])
        self.gate_metrics = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])

    def forward(self, sql_emb, plan_emb, log_emb, time_emb, common_emb):
        for i in range(self.n_label):
            sql_gate = self.sigmoid(self.gate_sql[i](sql_emb)) * sql_emb
            plan_gate = self.sigmoid(self.gate_plan[i](plan_emb)) * plan_emb
            log_gate = self.sigmoid(self.gate_log[i](log_emb)) * log_emb
            time_gate = self.sigmoid(self.gate_metrics[i](time_emb)) * time_emb

            emb = self.rootcause_cross_model(sql_gate, plan_gate, log_gate, time_gate)
            emb = (1 - self.weight) * common_emb + self.weight * emb

            pred_label = torch.sigmoid(self.pred_label_cross_list[i](emb))
            pred_opt = self.pred_opt_cross_list[i](emb)

            if i == 0:
                pred_label_output = pred_label
                pred_opt_output = pred_opt
            else:
                pred_label_output = torch.cat([pred_label_output, pred_label], dim=-1)
                pred_opt_output = torch.cat([pred_opt_output, pred_opt], dim=-1)

        return pred_label_output, pred_opt_output

# ==============================================================
# 2️⃣ Load Model
# ==============================================================
def load_trained_model():
    cross_model = FusionModel().to(DEVICE)
    model = GateComDiffPretrainModel(cross_model=cross_model).to(DEVICE)
    if os.path.exists(MODEL_PATH):
        state = torch.load(MODEL_PATH, map_location=DEVICE)
        model.load_state_dict(state, strict=False)
        print("[INFO] Model loaded successfully.")
    else:
        print("[WARN] Model file not found, using random weights.")
    model.eval(); cross_model.eval()
    return model, cross_model

model, cross_model = load_trained_model()

class_names = [
    "Outdated Statistical Information", "Under-optimized Join Order", "Inappropriate Distribution Keys",
    "Missing Indexes", "Redundant Indexes", "Repeatedly Executing Subqueries",
    "Complex Table Joins", "Updating an Entire Table", "Inserting Large Data"
]

# ==============================================================
# 3️⃣ Internal Feature Extraction
# ==============================================================

def extract_plan_features(explain_output):
    text = json.dumps(explain_output).lower()
    metrics = [
        text.count("join"),
        text.count("scan"),
        text.count("filter"),
        text.count("index"),
        text.count("rows"),
        text.count("cost"),
        text.count("nested loop"),
        text.count("hash"),
        len(text),
        text.count("->")
    ]
    x = torch.tensor(metrics, dtype=torch.float32)
    x = (x - x.mean()) / (x.std() + 1e-6)
    return x.unsqueeze(0)  # (1,10)

def extract_log_features(query: str):
    q = query.lower()
    features = [
        q.count("select"),
        q.count("join"),
        q.count("update"),
        q.count("delete"),
        q.count("insert"),
        int("where" in q),
        int("and" in q),
        int("or" in q),
        len(q),
        q.count("*"),
        q.count("group"),
        q.count("order"),
        q.count("(")
    ]
    x = torch.tensor(features, dtype=torch.float32)
    x = (x - x.mean()) / (x.std() + 1e-6)
    return x.unsqueeze(0)  # (1,13)

def extract_kpi_features(execution_time: float, rows: int):
    # 6 KPIs: [exec_time, rows, log(exec_time), log(rows+1), ratio, normalized]
    metrics = torch.tensor([
        execution_time,
        rows,
        torch.log(torch.tensor(execution_time + 1.0)),
        torch.log(torch.tensor(rows + 1.0)),
        execution_time / (rows + 1.0),
        (execution_time - 0.1) / 10.0
    ], dtype=torch.float32)
    x = (metrics - metrics.mean()) / (metrics.std() + 1e-6)
    return x.unsqueeze(0)  # (1,6)

# ==============================================================
# 4️⃣ Core Inference Logic
# ==============================================================

def analyze_root_causes(query: str):
    """
    Takes a SQL query, automatically:
    1. Runs EXPLAIN to get execution plan.
    2. Executes query & measures time (KPI).
    3. Generates plan/log/KPI embeddings.
    4. Passes all 4 embeddings (query/plan/log/kpi) to model.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # Step 1: Execution plan
    cursor.execute(f"EXPLAIN {query}")
    explain_output = cursor.fetchall()

    # Step 2: Measure execution KPIs
    start_time = time.time()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        row_count = len(rows)
    except Exception:
        row_count = 0
    end_time = time.time()
    exec_time = round(end_time - start_time, 3)

    conn.close()

    # Step 3: Extract multimodal features
    # Query → BERT (semantic)
    inputs = tokenizer(query, return_tensors="pt", padding=True, truncation=True, max_length=512).to(DEVICE)
    pooled = torch.randn(1, BERT_DIM)  # replace this with bert_model(**inputs)["pooled"]
    q_emb = proj_bert(pooled)

    # Plan → numerical stats (10-dim → 256)
    plan_feats = extract_plan_features(explain_output)
    plan_emb = proj_qf(F.pad(plan_feats, (0, PLAN_DIM - plan_feats.shape[1])))  # (1,256)

    # Log → from query pattern (13 → 32 → 256)
    log_feats = extract_log_features(query)
    log_32 = F.relu(nn.Linear(13, LOG_DIM)(log_feats))
    log_emb = proj_log(log_32)

    # KPI → simple derived stats (6 → 128 → 256)
    kpi_feats = extract_kpi_features(exec_time, row_count)
    kpi_128 = F.relu(nn.Linear(6, TS_DIM)(kpi_feats))
    kpi_emb = proj_ts(kpi_128)

    assert all(e.shape == (1, 256) for e in [q_emb, plan_emb, log_emb, kpi_emb])

    # Step 4: Fusion
    with torch.no_grad():
        common_emb = cross_model(q_emb, plan_emb, log_emb, kpi_emb)
        pred_label, pred_opt = model(q_emb, plan_emb, log_emb, kpi_emb, common_emb)
        score = torch.sigmoid(pred_opt.mean()).item()

    # Step 5: Interpret
    score = max(0.0, min(1.0, score))
    if score >= 0.75:
        status = "Slow"
        cause = class_names[int(score * len(class_names)) % len(class_names)]
    elif 0.51 <= score < 0.75:
        status = "Near Slow"
        cause = class_names[int(score * len(class_names)) % len(class_names)]
    else:
        status = "Normal"
        cause = ""

    return {
        "query": query,
        "execution_time": exec_time,
        "rows": row_count,
        "score": round(score, 4),
        "status": status,
        "root_cause": cause
    }

# # # ==============================================================
# # # 5️⃣ Example Run
# # # ==============================================================
# # if __name__ == "__main__":
# #     result = analyze_root_causes("SELECT * FROM employees WHERE salary > 50000;")
# #     print(json.dumps(result, indent=2))


# multimodal_backend_full.py
# import os
# import time
# import json
# import torch
# import torch.nn as nn
# import torch.nn.functional as F
# import mysql.connector
# import numpy as np
# import pandas as pd
# from transformers import BertTokenizer
# from tqdm import tqdm
# import ast
# from collections import deque
# import sys
# sys.path.append(".")

# # ==============================================================
# # 0️⃣ System Config
# # ==============================================================
# DEVICE = torch.device("cpu")

# DB_CONFIG = {
#     "host": "localhost",
#     "port": 3307,
#     "user": "root",
#     "password": "rootpassword",
#     "database": "mydb"
# }

# MODEL_PATH = os.path.join(os.path.dirname(__file__), "trained_model_final1.pth")

# FUSED_DIM = 256
# BERT_DIM = 768
# PLAN_DIM = 256
# LOG_DIM = 32
# TS_DIM = 128

# proj_bert = nn.Linear(BERT_DIM, FUSED_DIM).to(DEVICE)
# proj_qf   = nn.Linear(PLAN_DIM, FUSED_DIM).to(DEVICE)
# proj_log  = nn.Linear(LOG_DIM, FUSED_DIM).to(DEVICE)
# proj_ts   = nn.Linear(TS_DIM, FUSED_DIM).to(DEVICE)

# tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# # ==============================================================
# # 1️⃣ Helper utilities + Plan node2feature (as in training)
# # ==============================================================
# def node2feature(node, encoding, hist_file, table_sample):
#     num_filter = len(node.filterDict.get('colId', []))
#     pad = np.zeros((2, 20 - num_filter))
#     filts = np.array(list(node.filterDict.values())) if isinstance(node.filterDict, dict) else np.zeros((2,20))
#     # if filts shape mismatch, try robust handling
#     try:
#         filts = np.concatenate((filts, pad), axis=1).flatten()
#     except Exception:
#         filts = np.zeros(60)
#     mask = np.zeros(20)
#     mask[:num_filter] = 1
#     type_join = np.array([node.typeId, node.join])
#     table = np.array([getattr(node, "table_id", 0)])
#     sample = np.zeros(1000)
#     global_plan_cost = np.array([
#         float(getattr(node, "start_up_cost", 0.0)),
#         float(getattr(node, "total_cost", 0.0)),
#         float(getattr(node, "plan_rows", 0.0)),
#         float(getattr(node, "plan_width", 0.0))
#     ])
#     return np.concatenate((type_join, filts, mask, table, sample, global_plan_cost), dtype=np.float64)

# def f(s):
#     if '    ' in s and '\n' in s:
#         return s.split('    ')[1].split('\n')[0]
#     else:
#         return s

# class Encoding:
#     """
#     Minimal encoding used at inference to map strings -> ids.
#     If you have the original Encoding class from training (vocab maps)
#     load/replace that here to preserve exact ids.
#     """
#     def __init__(self, table_map=None, default_dict=None):
#         self.table_map = {} if table_map is None else table_map
#         self.default_dict = {'NA': 0} if default_dict is None else default_dict
#     def encode_type(self, s): return abs(hash(str(s))) % 1500
#     def encode_join(self, s): return abs(hash(str(s))) % 1500
#     def encode_table(self, s): return abs(hash(str(s))) % 1500
#     def encode_filters(self, filters, alias): 
#         # training code encoded filters to a (2 x 20) like array; here we keep a minimal placeholder
#         # If you have the real encode_filters function from training, use that for fidelity
#         if isinstance(filters, dict):
#             # expect filters to have lists for colId/opId/val
#             return {
#                 'colId': filters.get('colId', [0]),
#                 'opId': filters.get('opId', [0]),
#                 'val': filters.get('val', [0])
#             }
#         return {'colId': [], 'opId': [], 'val': []}

# # padding helpers (mirrors training collator behavior)
# def pad_2d_unsqueeze(x, max_node):
#     x = np.array(x)
#     pad_rows = max_node - x.shape[0]
#     if pad_rows < 0:
#         x = x[:max_node]
#         pad_rows = 0
#     padded = np.pad(x, ((0, pad_rows), (0, 0)), mode='constant')
#     return torch.tensor(padded, dtype=torch.float32).unsqueeze(0)

# def pad_1d_unsqueeze(x, max_node):
#     x = np.array(x)
#     pad = np.pad(x, (0, max_node - len(x)), mode='constant')
#     return torch.tensor(pad, dtype=torch.long).unsqueeze(0)

# def pad_attn_bias_unsqueeze(attn_bias, max_node):
#     pad = torch.zeros((max_node + 1, max_node + 1), dtype=torch.float32)
#     h, w = attn_bias.shape
#     pad[:h, :w] = attn_bias
#     return pad.unsqueeze(0)

# def pad_rel_pos_unsqueeze(rel_pos, max_node):
#     pad = torch.zeros((max_node, max_node), dtype=torch.long)
#     h, w = rel_pos.shape
#     pad[:h, :w] = rel_pos
#     return pad.unsqueeze(0)

# def floyd_warshall_rewrite(adj):
#     n = adj.shape[0]
#     dist = np.where(adj, 1.0, np.inf)
#     np.fill_diagonal(dist, 0.0)
#     for k in range(n):
#         for i in range(n):
#             for j in range(n):
#                 if dist[i, j] > dist[i, k] + dist[k, j]:
#                     dist[i, j] = dist[i, k] + dist[k, j]
#     return dist

# # ==============================================================
# # 2️⃣ PlanEncoder & TreeNode (copied and adapted from your training file)
# # ==============================================================
# class TreeNode:
#     def __init__(self, nodeType, typeId, filters, card, joinId, join, filters_encoded,
#                  start_up_cost, total_cost, plan_rows, plan_width):
#         self.nodeType = nodeType
#         self.typeId = typeId
#         self.filterDict = filters_encoded if filters_encoded is not None else {'colId': [], 'opId': [], 'val': []}
#         self.join = joinId
#         self.children = []
#         self.table_id = 0
#         self.start_up_cost = start_up_cost
#         self.total_cost = total_cost
#         self.plan_rows = plan_rows
#         self.plan_width = plan_width
#         self.query_id = None
#     def addChild(self, node): self.children.append(node)

# class PlanEncoder:
#     """
#     Build the plan tensor dict exactly like training's PlanEncoder.
#     Input: plan_json (nested dict) with 'Node Type' and optionally 'Plans' keys.
#     Output: a dict with keys 'x','attn_bias','rel_pos','heights' - shapes match training collator.
#     """
#     def __init__(self, plan_json, encoding):
#         self.encoding = encoding
#         # Expect plan_json to be a dict representing the root plan node
#         root_node = self._normalize_plan(plan_json)
#         treeNode = self.traversePlan(root_node, 0, self.encoding)
#         _dict = self.node2dict(treeNode)
#         self.data = self.pre_collate(_dict)

#     def _normalize_plan(self, plan):
#         # If plan is a list (like some EXPLAIN outputs), take first element
#         if isinstance(plan, list) and len(plan) > 0:
#             return plan[0]
#         return plan

#     def pre_collate(self, the_dict, max_node=500, rel_pos_max=20):
#         x = pad_2d_unsqueeze(the_dict['features'].numpy(), max_node) if isinstance(the_dict['features'], torch.Tensor) else pad_2d_unsqueeze(the_dict['features'], max_node)
#         N = int(the_dict['features'].shape[0])
#         attn_bias = torch.zeros([N + 1, N + 1], dtype=torch.float32)
#         edge_index = the_dict['adjacency_list'].t() if the_dict['adjacency_list'].numel() > 0 else torch.tensor([])
#         if edge_index.numel() == 0:
#             rel_pos = torch.tensor([[0]], dtype=torch.long)
#         else:
#             adj = torch.zeros([N, N], dtype=torch.bool)
#             edge_index_np = edge_index.numpy()
#             adj[edge_index_np[0, :], edge_index_np[1, :]] = True
#             rel_pos_np = floyd_warshall_rewrite(adj.numpy())
#             rel_pos = torch.from_numpy(rel_pos_np).long()
#         attn_bias[1:, 1:][rel_pos >= rel_pos_max] = float('-inf')
#         attn_bias = pad_attn_bias_unsqueeze(attn_bias, max_node + 1)
#         rel_pos = pad_rel_pos_unsqueeze(rel_pos, max_node)
#         heights = pad_1d_unsqueeze(the_dict['heights'].numpy() if isinstance(the_dict['heights'], torch.Tensor) else the_dict['heights'], max_node)
#         return {'x': x, 'attn_bias': attn_bias, 'rel_pos': rel_pos, 'heights': heights}

#     def node2dict(self, treeNode):
#         adj_list, num_child, features = self.topo_sort(treeNode)
#         heights = self.calculate_height(adj_list, len(features))
#         return {
#             'features': torch.tensor(features, dtype=torch.float32),
#             'heights': torch.LongTensor(heights),
#             'adjacency_list': torch.LongTensor(np.array(adj_list)) if len(adj_list) else torch.LongTensor(np.zeros((0,2),dtype=int))
#         }

#     def topo_sort(self, root_node):
#         adj_list = []
#         features = []
#         toVisit = deque()
#         toVisit.append((0, root_node))
#         next_id = 1
#         while toVisit:
#             idx, node = toVisit.popleft()
#             features.append(node.feature)
#             for child in node.children:
#                 toVisit.append((next_id, child))
#                 adj_list.append((idx, next_id))
#                 next_id += 1
#         return adj_list, len(features), features

#     def traversePlan(self, plan, idx, encoding):
#         # plan expected to be dict with fields like 'Node Type','Startup Cost','Total Cost','Plan Rows','Plan Width','Relation Name','Plans'
#         nodeType = plan.get('Node Type', plan.get('node_type', 'Unknown'))
#         typeId = encoding.encode_type(nodeType)
#         # try extracting filters/alias using heuristics; best to supply same format used in training
#         filters = {}
#         alias = None
#         join = ""  # representation string for join
#         joinId = encoding.encode_join(join)
#         filters_encoded = encoding.encode_filters(filters, alias)
#         root = TreeNode(nodeType, typeId, filters, None, joinId, join, filters_encoded,
#                         plan.get("Startup Cost", 0.0), plan.get("Total Cost", 0.0),
#                         plan.get("Plan Rows", 0.0), plan.get("Plan Width", 0.0))
#         if 'Relation Name' in plan:
#             root.table = plan['Relation Name']
#             root.table_id = encoding.encode_table(plan['Relation Name'])
#         root.query_id = idx
#         # compute feature vector
#         root.feature = node2feature(root, encoding, None, None)
#         # recursively traverse
#         if 'Plans' in plan and isinstance(plan['Plans'], list):
#             for subplan in plan['Plans']:
#                 subnode = self.traversePlan(subplan, idx, encoding)
#                 subnode.parent = root
#                 root.addChild(subnode)
#         return root

#     def calculate_height(self, adj_list, tree_size):
#         if tree_size == 1:
#             return np.array([0])
#         adj_list = np.array(adj_list)
#         node_ids = np.arange(tree_size, dtype=int)
#         node_order = np.zeros(tree_size, dtype=int)
#         uneval_nodes = np.ones(tree_size, dtype=bool)
#         parent_nodes = adj_list[:,0]
#         child_nodes = adj_list[:,1]
#         n = 0
#         while uneval_nodes.any():
#             uneval_mask = uneval_nodes[child_nodes]
#             unready_parents = parent_nodes[uneval_mask]
#             node2eval = uneval_nodes & ~np.isin(node_ids, unready_parents)
#             node_order[node2eval] = n
#             uneval_nodes[node2eval] = False
#             n += 1
#         return node_order

# # ==============================================================
# # 3️⃣ BERT (custom lightweight) + QueryFormer (full) + Log + TS
# #    (QueryFormer code adapted from your uploaded training file)
# # ==============================================================

# # --- BERT ---
# class MultiHeadAttentionBlockB(nn.Module):
#     def __init__(self, hidden_size, num_heads):
#         super().__init__()
#         assert hidden_size % num_heads == 0
#         self.num_heads = num_heads
#         self.head_dim = hidden_size // num_heads
#         self.q_proj = nn.Linear(hidden_size, hidden_size)
#         self.k_proj = nn.Linear(hidden_size, hidden_size)
#         self.v_proj = nn.Linear(hidden_size, hidden_size)
#         self.out_proj = nn.Linear(hidden_size, hidden_size)
#         self.ln = nn.LayerNorm(hidden_size)
#         self.dropout = nn.Dropout(0.1)
#     def forward(self, x, mask=None):
#         B, T, H = x.shape
#         Q = self.q_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1,2)
#         K = self.k_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1,2)
#         V = self.v_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1,2)
#         attn_scores = torch.matmul(Q, K.transpose(-1, -2)) / (self.head_dim ** 0.5)
#         attn_weights = torch.softmax(attn_scores, dim=-1)
#         attn_output = torch.matmul(attn_weights, V)
#         attn_output = attn_output.transpose(1, 2).contiguous().view(B, T, H)
#         return self.ln(x + self.dropout(self.out_proj(attn_output)))

# class FeedForwardBlockB(nn.Module):
#     def __init__(self, hidden_size):
#         super().__init__()
#         self.linear1 = nn.Linear(hidden_size, hidden_size * 4)
#         self.linear2 = nn.Linear(4 * hidden_size, hidden_size)
#         self.gelu = nn.GELU()
#         self.ln = nn.LayerNorm(hidden_size)
#         self.dropout = nn.Dropout(0.1)
#     def forward(self, x):
#         ff = self.linear2(self.gelu(self.linear1(x)))
#         return self.ln(x + self.dropout(ff))

# class BertModelCustom(nn.Module):
#     def __init__(self, vocab_size=30522, hidden_size=768, num_heads=12, num_layers=6, max_length=512, pad_token_id=0):
#         super().__init__()
#         self.word_embeddings = nn.Embedding(vocab_size, hidden_size, padding_idx=pad_token_id)
#         self.position_embeddings = nn.Embedding(max_length, hidden_size)
#         self.layer_norm = nn.LayerNorm(hidden_size)
#         self.dropout = nn.Dropout(0.1)
#         self.attn_layers = nn.ModuleList([MultiHeadAttentionBlockB(hidden_size, num_heads) for _ in range(num_layers)])
#         self.ff_layers = nn.ModuleList([FeedForwardBlockB(hidden_size) for _ in range(num_layers)])
#         self.final_ln = nn.LayerNorm(hidden_size)
#         self.pad_token_id = pad_token_id
#     def forward(self, input_ids, attention_mask=None):
#         B, T = input_ids.size()
#         position_ids = torch.arange(T, dtype=torch.long, device=input_ids.device).unsqueeze(0).expand(B, T)
#         if attention_mask is None:
#             attention_mask = (input_ids != self.pad_token_id).long()
#         x = self.word_embeddings(input_ids) + self.position_embeddings(position_ids)
#         x = self.layer_norm(x)
#         x = self.dropout(x)
#         for attn, ff in zip(self.attn_layers, self.ff_layers):
#             x = attn(x, attention_mask)
#             x = ff(x)
#         hidden_states = self.final_ln(x)
#         mask = attention_mask.unsqueeze(-1).float()
#         pooled = (hidden_states * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
#         return {"pooled": pooled}

# bert_model = BertModelCustom(vocab_size=tokenizer.vocab_size, hidden_size=BERT_DIM, num_heads=8, num_layers=6).to(DEVICE)

# # --- QueryFormer and submodules (adapted from your training file) ---
# # We reuse EncoderLayer, MultiHeadAttention, FeedForwardNetwork and QueryFormer
# class FeedForwardNetwork(nn.Module):
#     def __init__(self, hidden_size, ffn_size, dropout_rate):
#         super().__init__()
#         self.layer1 = nn.Linear(hidden_size, ffn_size)
#         self.gelu = nn.GELU()
#         self.layer2 = nn.Linear(ffn_size, hidden_size)
#     def forward(self, x):
#         x = self.layer1(x)
#         x = self.gelu(x)
#         x = self.layer2(x)
#         return x

# class MultiHeadAttention(nn.Module):
#     def __init__(self, hidden_size, attention_dropout_rate, head_size):
#         super().__init__()
#         self.head_size = head_size
#         self.att_size = hidden_size // head_size
#         self.scale = self.att_size ** -0.5
#         self.linear_q = nn.Linear(hidden_size, head_size * self.att_size)
#         self.linear_k = nn.Linear(hidden_size, head_size * self.att_size)
#         self.linear_v = nn.Linear(hidden_size, head_size * self.att_size)
#         self.att_dropout = nn.Dropout(attention_dropout_rate)
#         self.output_layer = nn.Linear(head_size * self.att_size, hidden_size)
#     def forward(self, q, k, v, attn_bias=None):
#         batch_size = q.size(0)
#         Q = self.linear_q(q).view(batch_size, -1, self.head_size, self.att_size).transpose(1,2)
#         K = self.linear_k(k).view(batch_size, -1, self.head_size, self.att_size).transpose(1,2)
#         V = self.linear_v(v).view(batch_size, -1, self.head_size, self.att_size).transpose(1,2)
#         Q = Q * self.scale
#         x = torch.matmul(Q, K.transpose(-1, -2))
#         if attn_bias is not None:
#             x = x + attn_bias
#         x = torch.softmax(x, dim=3)
#         x = self.att_dropout(x)
#         x = x.matmul(V)
#         x = x.transpose(1, 2).contiguous().view(batch_size, -1, self.head_size * self.att_size)
#         x = self.output_layer(x)
#         return x

# class EncoderLayer(nn.Module):
#     def __init__(self, hidden_size, ffn_size, dropout_rate, attention_dropout_rate, head_size):
#         super().__init__()
#         self.self_attention_norm = nn.LayerNorm(hidden_size)
#         self.self_attention = MultiHeadAttention(hidden_size, attention_dropout_rate, head_size)
#         self.self_attention_dropout = nn.Dropout(dropout_rate)
#         self.ffn_norm = nn.LayerNorm(hidden_size)
#         self.ffn = FeedForwardNetwork(hidden_size, ffn_size, dropout_rate)
#         self.ffn_dropout = nn.Dropout(dropout_rate)
#     def forward(self, x, attn_bias=None):
#         y = self.self_attention_norm(x)
#         y = self.self_attention(y, y, y, attn_bias)
#         y = self.self_attention_dropout(y)
#         x = x + y
#         y = self.ffn_norm(x)
#         y = self.ffn(y)
#         y = self.ffn_dropout(y)
#         x = x + y
#         return x

# class QueryFormer(nn.Module):
#     def __init__(self, emb_size=32, ffn_dim=32, head_size=8, dropout=0.1, attention_dropout_rate=0.1, n_layers=8, use_sample=True, use_hist=False, bin_number=50, pred_hid=256, input_size=1067):
#         super().__init__()
#         use_hist = False
#         hidden_dim = emb_size*4 + emb_size//8 + 4
#         self.hidden_dim = hidden_dim
#         self.head_size = head_size
#         self.input_size = input_size
#         self.rel_pos_encoder = nn.Embedding(64, head_size, padding_idx=0)
#         self.height_encoder = nn.Embedding(64, hidden_dim, padding_idx=0)
#         self.input_dropout = nn.Dropout(dropout)
#         encoders = [EncoderLayer(hidden_dim, ffn_dim, dropout, attention_dropout_rate, head_size) for _ in range(n_layers)]
#         self.layers = nn.ModuleList(encoders)
#         self.final_ln = nn.LayerNorm(hidden_dim)
#         self.super_token = nn.Embedding(1, hidden_dim)
#         self.super_token_virtual_distance = nn.Embedding(1, head_size)
#         # FeatureEmbed from training (reduced here to a linear project for simplicity)
#         # but we keep the idea: project input features to hidden_dim
#         self.project = nn.Linear(input_size, hidden_dim)
#         self.pred = nn.Linear(hidden_dim, pred_hid)
#         self.pred_ln = nn.LayerNorm(pred_hid)
#     def forward(self, batched_data):
#         # batched_data: dict with 'x','attn_bias','rel_pos','heights' each (batch, seq_len, ...)
#         x = batched_data["x"]          # (batch, seq_len, feat_dim)
#         rel_pos = batched_data["rel_pos"]
#         attn_bias = batched_data["attn_bias"]
#         heights = batched_data["heights"]
#         n_batch, n_node, feat_dim = x.size()
#         # project features to hidden dim
#         node_feature = self.project(x.view(n_batch, n_node, feat_dim))
#         node_feature = node_feature + self.height_encoder(heights)
#         super_token_feature = self.super_token.weight.unsqueeze(0).repeat(n_batch, 1, 1)
#         super_node_feature = torch.cat([super_token_feature, node_feature], dim=1)
#         output = self.input_dropout(super_node_feature)
#         # Prepare attn_bias shape: (batch, n_head, seq_len, seq_len)
#         tree_attn_bias = attn_bias.clone().unsqueeze(1).repeat(1, self.head_size, 1, 1)
#         # add relative pos bias
#         rel_pos_bias = self.rel_pos_encoder(rel_pos).permute(0, 3, 1, 2)
#         tree_attn_bias[:, :, 1:, 1:] = tree_attn_bias[:, :, 1:, 1:] + rel_pos_bias
#         t = self.super_token_virtual_distance.weight.view(1, self.head_size, 1)
#         tree_attn_bias[:, :, 1:, 0] = tree_attn_bias[:, :, 1:, 0] + t
#         tree_attn_bias[:, :, 0, :] = tree_attn_bias[:, :, 0, :] + t
#         for enc_layer in self.layers:
#             output = enc_layer(output, tree_attn_bias)
#         output = self.final_ln(output)
#         output = self.pred(output)
#         output = self.pred_ln(output)
#         return output

# # instantiate a QueryFormer with hidden dims matching projection expected by proj_qf
# queryformer_model = QueryFormer(emb_size=32, ffn_dim=32, head_size=8, n_layers=6, pred_hid=256, input_size=1067).to(DEVICE)

# # --- LogModel ---
# class LogModel(nn.Module):
#     def __init__(self, input_dim=13, hidden_dim=64, output_dim=32):
#         super().__init__()
#         self.ll_1 = nn.Linear(input_dim, hidden_dim)
#         self.ll_2 = nn.Linear(hidden_dim, hidden_dim)
#         self.cls = nn.Linear(hidden_dim, output_dim)
#         for p in self.parameters():
#             if p.dim() > 1:
#                 nn.init.xavier_uniform_(p)
#     def forward(self, input_ids):
#         x = F.relu(self.ll_1(input_ids))
#         x = F.relu(self.ll_2(x))
#         return self.cls(x)

# log_model = LogModel().to(DEVICE)

# # --- Timeseries model (autoencoder encoder) ---
# class CustomConvAutoencoder(nn.Module):
#     def __init__(self):
#         super(CustomConvAutoencoder, self).__init__()
#         self.encoder = nn.Sequential(
#             nn.Conv2d(1, 16, kernel_size=3, stride=2, padding=0),
#             nn.ReLU(True),
#             nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=0),
#             nn.ReLU(True),
#             nn.Conv2d(32, 32, kernel_size=(1, 2), stride=1, padding=0),
#         )
#     def forward(self, x):
#         return self.encoder(x)

# ts_model = CustomConvAutoencoder().to(DEVICE)

# # ==============================================================
# # 4️⃣ Fusion + Gate (same architecture as training)
# # ==============================================================

# class FusionModel(nn.Module):
#     def __init__(self, fused_dim=FUSED_DIM, nhead=4, num_layers=2):
#         super().__init__()
#         encoder_layer = nn.TransformerEncoderLayer(d_model=fused_dim, nhead=nhead)
#         self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
#         self.fc = nn.Linear(fused_dim, fused_dim)
#     def forward(self, bert, log, ts, qf):
#         x = torch.stack([bert, log, ts, qf], dim=1)  # (B,4,fused_dim)
#         x = x.transpose(0,1)                         # (4,B,fused_dim)
#         x = self.transformer(x)
#         return self.fc(x.mean(dim=0))

# class GateComDiffPretrainModel(nn.Module):
#     def __init__(self, emb_dim=FUSED_DIM, n_label=9, cross_model=None, weight=0.5):
#         super().__init__()
#         self.n_label = n_label
#         self.weight = weight
#         self.rootcause_cross_model = cross_model
#         self.sigmoid = nn.Sigmoid()
#         self.pred_label_cross_list = nn.ModuleList([nn.Linear(emb_dim, 1) for _ in range(n_label)])
#         self.pred_opt_cross_list = nn.ModuleList([nn.Linear(emb_dim, 1) for _ in range(n_label)])
#         self.gate_sql = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])
#         self.gate_plan = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])
#         self.gate_log = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])
#         self.gate_metrics = nn.ModuleList([nn.Linear(emb_dim, emb_dim) for _ in range(n_label)])
#     def forward(self, sql_emb, plan_emb, log_emb, time_emb, common_emb):
#         for i in range(self.n_label):
#             sql_gate = self.sigmoid(self.gate_sql[i](sql_emb)) * sql_emb
#             plan_gate = self.sigmoid(self.gate_plan[i](plan_emb)) * plan_emb
#             log_gate = self.sigmoid(self.gate_log[i](log_emb)) * log_emb
#             time_gate = self.sigmoid(self.gate_metrics[i](time_emb)) * time_emb
#             emb = self.rootcause_cross_model(sql_gate, plan_gate, log_gate, time_gate)
#             emb = (1 - self.weight) * common_emb + self.weight * emb
#             pred_label = torch.sigmoid(self.pred_label_cross_list[i](emb))
#             pred_opt = self.pred_opt_cross_list[i](emb)
#             if i == 0:
#                 pred_label_output = pred_label
#                 pred_opt_output = pred_opt
#             else:
#                 pred_label_output = torch.cat([pred_label_output, pred_label], dim=-1)
#                 pred_opt_output = torch.cat([pred_opt_output, pred_opt], dim=-1)
#         return pred_label_output, pred_opt_output

# def load_trained_model():
#     cross_model = FusionModel().to(DEVICE)
#     model = GateComDiffPretrainModel(cross_model=cross_model).to(DEVICE)
#     if os.path.exists(MODEL_PATH):
#         state = torch.load(MODEL_PATH, map_location=DEVICE)
#         model.load_state_dict(state, strict=False)
#         print("[INFO] Model loaded successfully from", MODEL_PATH)
#     else:
#         print("[WARN] Model file not found at", MODEL_PATH, " — using random weights.")
#     model.eval(); cross_model.eval()
#     return model, cross_model

# model, cross_model = load_trained_model()

# class_names = [
#     "Bad Join Order", "Missing Index", "Complex Joins",
#     "Table-wide Updates", "Bulk Inserts", "Skewed Data",
#     "High Contention", "Too Many Connections", "Suboptimal UDF"
# ]

# # ==============================================================
# # 5️⃣ Inference pipeline using all four real encoders
# # ==============================================================

# def explain_to_planjson_from_mysql_rows(explain_rows):
#     """
#     Convert DB-specific EXPLAIN rows (list of dicts) into a nested plan dict.
#     This function is necessarily heuristic because different DBs return different shapes.
#     If your DB returns JSON of a Plan directly (e.g. Postgres EXPLAIN (FORMAT JSON)), just load it.
#     """
#     if not explain_rows:
#         return {"Node Type": "Unknown", "Plans": []}
#     # Some MySQL variants return rows where each row has a 'select_type' or 'table' etc.
#     # We attempt to create a single-node plan using available keys.
#     row0 = explain_rows[0]
#     # best-effort mapping:
#     plan = {}
#     plan["Node Type"] = row0.get("select_type", row0.get("Extra", "Unknown"))
#     plan["Startup Cost"] = float(row0.get("cost", 0.0)) if "cost" in row0 else 0.0
#     plan["Total Cost"] = float(row0.get("cost", 0.0)) if "cost" in row0 else 0.0
#     plan["Plan Rows"] = float(row0.get("rows", 0)) if "rows" in row0 else 0.0
#     plan["Plan Width"] = float(row0.get("width", 0)) if "width" in row0 else 0.0
#     # no nested 'Plans' from simple explain -> empty list
#     plan["Plans"] = []
#     return plan

# def extract_log_vector_from_query(query: str):
#     q = query.lower()
#     features = [
#         q.count("select"),
#         q.count("join"),
#         q.count("update"),
#         q.count("delete"),
#         q.count("insert"),
#         int("where" in q),
#         int("and" in q),
#         int("or" in q),
#         len(q),
#         q.count("*"),
#         q.count("group"),
#         q.count("order"),
#         q.count("(")
#     ]
#     x = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
#     # normalize with stable stats (if you have training mean/std store and use those)
#     x = (x - x.mean()) / (x.std() + 1e-6)
#     return x

# def analyze_root_causes(query: str):
#     conn = mysql.connector.connect(**DB_CONFIG)
#     cursor = conn.cursor(dictionary=True)

#     # Step 1: EXPLAIN
#     try:
#         cursor.execute(f"EXPLAIN {query}")
#         explain_rows = cursor.fetchall()
#     except Exception as e:
#         explain_rows = []
#     plan_json = explain_to_planjson_from_mysql_rows(explain_rows)

#     encoding = Encoding()
#     plan_enc = PlanEncoder(plan_json, encoding)
#     plan_tensor = plan_enc.data  # dict with 'x','attn_bias','rel_pos','heights'
#     # squeeze batch-dim to match QueryFormer expected shapes
#     plan_data = {
#         "x": plan_tensor["x"].squeeze(0).to(DEVICE),            # (seq_len, feat_dim)
#         "attn_bias": plan_tensor["attn_bias"].squeeze(0).to(DEVICE), # (seq_len+1, seq_len+1)
#         "rel_pos": plan_tensor["rel_pos"].squeeze(0).to(DEVICE), # (seq_len, seq_len)
#         "heights": plan_tensor["heights"].squeeze(0).to(DEVICE)  # (seq_len,)
#     }
#     # Add batch dim where QueryFormer expects batch
#     plan_for_model = {
#         "x": plan_data["x"].unsqueeze(0),          # (1, seq_len, feat_dim)
#         "attn_bias": plan_data["attn_bias"].unsqueeze(0),
#         "rel_pos": plan_data["rel_pos"].unsqueeze(0),
#         "heights": plan_data["heights"].unsqueeze(0)
#     }

#     # Step 2: Execute query to measure KPI
#     start_time = time.time()
#     try:
#         cursor.execute(query)
#         rows = cursor.fetchall()
#         row_count = len(rows)
#     except Exception:
#         row_count = 0
#     end_time = time.time()
#     exec_time = round(end_time - start_time, 3)
#     conn.close()

#     # Step 3: Query embedding via BERT
#     inputs = tokenizer(query, return_tensors="pt", padding=True, truncation=True, max_length=512).to(DEVICE)
#     with torch.no_grad():
#         bert_out = bert_model(inputs["input_ids"].to(DEVICE), attention_mask=inputs.get("attention_mask", None))
#         q_pooled = bert_out["pooled"]  # (1, BERT_DIM)
#     q_emb = proj_bert(q_pooled)  # (1, FUSED_DIM)

#     # Step 4: Plan embedding via QueryFormer
#     with torch.no_grad():
#         plan_out = queryformer_model(plan_for_model)         # (1, seq_len+1, pred_hid)
#         # in training they used plan_embed = plan_out[:, 0, :]  # super-token embedding
#         plan_embed = plan_out[:, 0, :]                       # (1, pred_hid)
#     # Project plan_embed to fused dim (training had proj_qf)
#     plan_emb = proj_qf(plan_embed)  # (1, FUSED_DIM)

#     # Step 5: Log embedding
#     log_vec = extract_log_vector_from_query(query).to(DEVICE)  # (1,13)
#     with torch.no_grad():
#         log_32 = log_model(log_vec)     # (1, LOG_DIM)
#     log_emb = proj_log(log_32)          # (1, FUSED_DIM)

#     # Step 6: KPI / timeseries embedding
#     # Build timeseries-like input: shape expected by ts_model encoder e.g. (B, 1, H, W)
#     metrics = torch.tensor([[exec_time, row_count, np.log(exec_time + 1.0), np.log(row_count + 1.0),
#                              exec_time / (row_count + 1.0), (exec_time - 0.1) / 10.0]], dtype=torch.float32).to(DEVICE)
#     # reshape into "image" expected by ts_model. Training used time.unsqueeze(1) then ts_model(time) where ts_model was conv2d expecting (B,1,H,W)
#     # We make H=1 W=6 or H=6 W=1 depending on conv kernel choices. We'll use (B,1,2,3) unlikely; but keep it consistent
#     ts_input = metrics.unsqueeze(1).unsqueeze(-1)  # shape (1,1,6,1)
#     with torch.no_grad():
#         ts_enc = ts_model(ts_input)   # some conv output
#     ts_flat = ts_enc.view(ts_enc.size(0), -1)  # flatten
#     ts_emb = proj_ts(ts_flat)                  # (1, FUSED_DIM)

#     # Step 7: Fusion + Gate prediction
#     with torch.no_grad():
#         common_emb = cross_model(q_emb, log_emb, ts_emb, plan_emb)
#         pred_label, pred_opt = model(q_emb, log_emb, ts_emb, plan_emb, common_emb)
#         score = torch.sigmoid(pred_opt.mean()).item()

#     score = float(max(0.0, min(1.0, score)))
#     if score >= 0.75:
#         status = "Slow"
#         cause = class_names[int(score * len(class_names)) % len(class_names)]
#     elif 0.51 <= score < 0.75:
#         status = "Near Slow"
#         cause = class_names[int(score * len(class_names)) % len(class_names)]
#     else:
#         status = "Normal"
#         cause = ""

#     return {
#         "query": query,
#         "execution_time": exec_time,
#         "rows": row_count,
#         "score": round(score, 4),
#         "status": status,
#         "root_cause": cause
#     }

# # Example usage:
# # if __name__ == "__main__":
# #     out = analyze_root_causes("SELECT * FROM employees WHERE salary > 50000;")
# #     print(json.dumps(out, indent=2))
