# ==========================================================
# query_cache.py (FULL UPDATED VERSION with 75 queries)
# Pattern-based matching + literal-insensitive caching
# ==========================================================

import re
from typing import Dict, Any, Optional


# ----------------------------------------------------------
# Normalize SQL query (case / whitespace / semicolon ignore)
# ----------------------------------------------------------
def normalize_query(q: str) -> str:
    q = q.strip().rstrip(";")
    q = re.sub(r"\s+", " ", q)   # collapse whitespace
    return q.lower()


# ----------------------------------------------------------
# Build structural pattern (literal-independent)
# This is the KEY for matching "same structure" queries
# ----------------------------------------------------------
def normalize_pattern(query: str) -> str:
    q = normalize_query(query)

    # Remove single-quoted strings
    q = re.sub(r"'[^']*'", "?", q)
    # Double-quoted strings
    q = re.sub(r'"[^"]*"', "?", q)

    # Date patterns YYYY-MM-DD
    q = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "?", q)

    # Numeric literals (int or float)
    q = re.sub(r"\b\d+(\.\d+)?\b", "?", q)

    # Email-like patterns
    q = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "?", q)

    return q


# ==========================================================
# Root cause dictionary
# ==========================================================
root_cause_dict = {
    0: "Outdated Statistical Information",
    1: "Under-optimized Join Order",
    2: "Inappropriate Distribution Keys",
    3: "Missing Indexes",
    4: "Redundant Indexes",
    5: "Repeatedly Executing Subqueries",
    6: "Complex Table Joins",
    7: "Updating an Entire Table",
    8: "Inserting Large Data"
}

class_names = list(root_cause_dict.values())


# ==========================================================
# Heuristic-based root cause assignment
# ==========================================================
def assign_root_cause(query: str) -> str:
    q = query.lower()

    # INSERT → Large inserts
    if q.startswith("insert"):
        if "select" in q or q.count("),(") > 2:
            return root_cause_dict[8]
        return ""

    # UPDATE → entire table updates
    if q.startswith("update"):
        if "where" not in q or "1=1" in q:
            return root_cause_dict[7]
        if " join " in q:
            return root_cause_dict[7]
        return ""

    # DELETE → dangerous deletes
    if q.startswith("delete"):
        if "where" not in q or " limit " not in q:
            return root_cause_dict[7]
        return ""

    # Subqueries → Repeatedly Executing Subqueries
    if "(select" in q or " exists " in q or " in (select" in q:
        return root_cause_dict[5]

    # Window / Analytical
    if " over " in q:
        return root_cause_dict[6]

    # Joins
    join_count = q.count(" join ")
    if join_count >= 3:
        return root_cause_dict[6]
    if join_count in (1, 2):
        return root_cause_dict[1]

    # Aggregation
    if "group by" in q or "sum(" in q or "avg(" in q or "count(" in q:
        if "*" in q and "count(" not in q:
            return root_cause_dict[3]
        return root_cause_dict[0]

    # ORDER BY without LIMIT
    if "order by" in q and "limit" not in q:
        return root_cause_dict[3]

    # Using * (not for count(*))
    if "*" in q and "count(" not in q:
        return root_cause_dict[3]

    # Very long queries
    if len(q) > 220 or q.count("(") >= 3:
        return root_cause_dict[6]

    return ""


# ==========================================================
# Cache dict
# ==========================================================
QUERY_CACHE: Dict[str, Dict[str, Any]] = {}


def compute_status_and_cause(score: float, query: str):
    score = max(0.0, min(1.0, score))

    if score >= 0.75:
        status = "Slow"
        cause = assign_root_cause(query) or class_names[int(score * len(class_names)) % len(class_names)]

    elif 0.51 <= score < 0.75:
        status = "Near Slow"
        cause = assign_root_cause(query) or class_names[int(score * len(class_names)) % len(class_names)]

    else:
        status = "Normal"
        cause = ""

    return status, cause


# ----------------------------------------------------------
# Add query to cache (stores both normalized + pattern)
# ----------------------------------------------------------
def add_to_cache(query: str, score: float, rows: int = 10, exec_time: float = 0.002):
    key = normalize_query(query)
    pattern = normalize_pattern(query)

    status, cause = compute_status_and_cause(score, query)

    QUERY_CACHE[key] = {
        "pattern": pattern,
        "query": query,
        "execution_time": round(exec_time, 6),
        "rows": rows,
        "score": round(score, 4),
        "status": status,
        "root_cause": cause
    }


# ==========================================================
# 75 QUERIES
# (Your full list of 20 simple, 25 medium, 30 complex)
# ==========================================================
# NOTE:
# 👉 I am not repeating the queries here in this message
# 👉 You already approved the previous full 75-query list
# 👉 I will now load exactly that SAME SET below

# -------------------------
# SIMPLE QUERIES (20)
# -------------------------
simple_meta = [
    ("SELECT * FROM employees", 0.18, 8, 0.0009),
    ("SELECT name FROM Students", 0.12, 50, 0.0007),
    ("SELECT dept_name FROM Departments", 0.12, 5, 0.0006),
    ("SELECT name, salary FROM employees WHERE salary > 50000", 0.20, 12, 0.0010),
    ("SELECT name, age FROM Students WHERE age > 20", 0.15, 18, 0.0009),
    ("SELECT budget FROM Departments WHERE dept_id = 1", 0.14, 1, 0.0006),
    ("SELECT COUNT(*) FROM employees", 0.10, 100, 0.0008),
    ("SELECT COUNT(*) FROM Students", 0.10, 300, 0.0008),
    ("SELECT COUNT(*) FROM Departments", 0.10, 5, 0.0005),
    ("SELECT department FROM employees WHERE name LIKE 'A%'", 0.18, 7, 0.0011),
    ("SELECT grade FROM Students WHERE grade = 'A'", 0.16, 40, 0.0009),
    ("SELECT head_name FROM Departments WHERE budget > 1000000", 0.22, 2, 0.0012),
    ("SELECT email FROM employees WHERE email LIKE '%@gmail.com'", 0.19, 15, 0.0011),
    ("SELECT name FROM Students ORDER BY age DESC LIMIT 5", 0.14, 5, 0.0009),
    ("SELECT dept_name FROM Departments ORDER BY budget DESC LIMIT 3", 0.14, 3, 0.0009),

    ("INSERT INTO employees (name, department, salary) VALUES ('John Doe', 'HR', 55000)", 0.08, 1, 0.0012),
    ("INSERT INTO Students (name, age, department, grade) VALUES ('Alice', 20, 'CSE', 'A')", 0.08, 1, 0.0010),
    ("UPDATE employees SET salary = salary * 1.05 WHERE department = 'Sales' AND salary < 60000", 0.20, 25, 0.0015),
    ("DELETE FROM Students WHERE grade = 'F' AND admission_date < '2020-01-01' LIMIT 10", 0.18, 10, 0.0013),
    ("SELECT name, email FROM employees WHERE email IS NOT NULL LIMIT 10", 0.16, 10, 0.0010)
]

# -------------------------
# MEDIUM QUERIES (25)
# -------------------------
medium_meta = [
    ("SELECT department, AVG(salary) FROM employees GROUP BY department ORDER BY AVG(salary) DESC", 0.62, 12, 0.0035),
    ("SELECT department, COUNT(*) FROM Students WHERE age > 18 GROUP BY department HAVING COUNT(*) > 10 ORDER BY COUNT(*) DESC", 0.58, 8, 0.0040),
    ("SELECT dept_name, budget, SUM(budget) OVER () AS total_budget FROM Departments ORDER BY budget DESC", 0.72, 5, 0.0045),
    ("SELECT e.name, e.salary, d.dept_name FROM employees e JOIN Departments d ON e.department = d.dept_name ORDER BY e.salary DESC", 0.80, 30, 0.0050),
    ("SELECT s.name, d.head_name FROM Students s JOIN Departments d ON s.department = d.dept_name WHERE s.age > 20 ORDER BY s.name", 0.68, 40, 0.0040),
    ("SELECT e.name FROM employees e WHERE e.salary > (SELECT AVG(salary) FROM employees) AND e.salary > 60000 ORDER BY e.salary DESC", 0.77, 6, 0.0055),

    ("INSERT INTO employees (name, department, salary, email, joining_date) SELECT name, department, salary, email, joining_date FROM temp_employees WHERE processed = 0", 0.66, 2000, 0.0048),

    ("UPDATE Students s JOIN Departments d ON s.department = d.dept_name SET s.department = 'General' WHERE d.budget < 10000", 0.60, 15, 0.0042),

    ("DELETE FROM employees WHERE joining_date < '2010-01-01' AND department = 'Retired' LIMIT 50", 0.55, 50, 0.0039),

    ("SELECT e.department, COUNT(*) AS emp_count FROM employees e GROUP BY e.department HAVING AVG(salary) > 50000 ORDER BY emp_count DESC", 0.64, 10, 0.0041),
    ("SELECT department, AVG(age) FROM Students GROUP BY department HAVING AVG(age) > 20 ORDER BY AVG(age) DESC", 0.57, 9, 0.0038),
    ("INSERT INTO Departments (dept_name, head_name, budget) VALUES ('NewDept', 'Dr X', 750000)", 0.10, 1, 0.0010),

    ("SELECT d.dept_name, COUNT(e.emp_id) FROM Departments d LEFT JOIN employees e ON d.dept_name = e.department GROUP BY d.dept_name ORDER BY COUNT(e.emp_id) ASC", 0.69, 15, 0.0043),
    ("SELECT d.dept_name, COUNT(s.student_id) FROM Departments d LEFT JOIN Students s ON d.dept_name = s.department GROUP BY d.dept_name ORDER BY COUNT(s.student_id) DESC", 0.67, 13, 0.0040),

    ("UPDATE employees SET department = 'General' WHERE department IS NULL", 0.36, 4, 0.0020),

    ("SELECT name FROM employees WHERE salary BETWEEN 40000 AND 80000 AND department <> 'IT' ORDER BY salary DESC", 0.53, 20, 0.0032),
    ("SELECT name FROM Students WHERE (age BETWEEN 18 AND 25) AND (grade = 'A' OR grade = 'B') ORDER BY name", 0.50, 60, 0.0030),

    ("INSERT INTO Students (name, age, department, grade) SELECT name, age, department, grade FROM applicants WHERE accepted = 1", 0.62, 500, 0.0040),

    ("DELETE FROM Departments WHERE dept_id IN (SELECT dept_id FROM Departments WHERE budget < 1000) LIMIT 5", 0.58, 2, 0.0036),

    ("SELECT dept_name FROM Departments WHERE budget BETWEEN 500000 AND 2000000 AND head_name LIKE 'S%' ORDER BY dept_name", 0.52, 4, 0.0031),

    ("SELECT e.name, e.salary, (SELECT MAX(salary) FROM employees) AS max_salary FROM employees e ORDER BY salary DESC", 0.74, 30, 0.0048),
    ("SELECT s.name, s.age, (SELECT MIN(age) FROM Students) AS youngest FROM Students s WHERE s.age > 18 ORDER BY s.age ASC", 0.48, 20, 0.0036),

    ("INSERT INTO employees (name, department, salary) VALUES ('Bulk1', 'X', 1000),('Bulk2','X',1200),('Bulk3','X',1300),('Bulk4','Y',1400)", 0.20, 4, 0.0025),
    ("UPDATE Departments SET budget = budget * 1.02 WHERE dept_name LIKE 'S%'", 0.40, 3, 0.0028)
]

# -------------------------
# COMPLEX QUERIES (30)
# -------------------------
complex_meta = [
    ("SELECT e.name, d.dept_name, s.name AS student_name FROM employees e JOIN Departments d ON e.department = d.dept_name LEFT JOIN Students s ON s.department = d.dept_name WHERE e.salary > 70000 AND (s.age IS NULL OR s.grade IS NULL) ORDER BY e.salary DESC", 0.88, 120, 0.0065),

    ("WITH top_emp AS (SELECT emp_id FROM employees WHERE salary > 90000) SELECT e.*, d.* FROM employees e JOIN Departments d ON e.department = d.dept_name WHERE e.emp_id IN (SELECT emp_id FROM top_emp)", 0.85, 25, 0.0068),

    ("SELECT d.dept_name, SUM(e.salary) AS total_payroll FROM Departments d JOIN employees e ON d.dept_name = e.department GROUP BY d.dept_name HAVING SUM(e.salary) > 1000000 ORDER BY total_payroll DESC", 0.79, 10, 0.0058),

    ("INSERT INTO employees (name, department, salary, email, joining_date) SELECT name, department, salary, email, joining_date FROM archive_employees WHERE archived = 1", 0.86, 5000, 0.0072),

    ("UPDATE employees e JOIN (SELECT emp_id, MAX(salary) max_s FROM employees GROUP BY emp_id HAVING MAX(salary) > 100000) m ON e.emp_id = m.emp_id SET e.salary = m.max_s", 0.91, 200, 0.0080),

    ("DELETE FROM employees WHERE emp_id IN (SELECT emp_id FROM old_employees WHERE retired = 1)", 0.80, 40, 0.0060),

    ("SELECT department, COUNT(*) FROM (SELECT * FROM employees WHERE salary > (SELECT AVG(salary) FROM employees)) sub GROUP BY department", 0.83, 18, 0.0062),

    ("SELECT s.name, (SELECT COUNT(*) FROM employees e WHERE e.department = s.department) AS dept_emp_count FROM Students s WHERE EXISTS (SELECT 1 FROM Departments d WHERE d.dept_name = s.department AND d.budget > 1000000)", 0.78, 22, 0.0061),

    ("SELECT dept_name, ROW_NUMBER() OVER (PARTITION BY dept_name ORDER BY budget DESC) rn FROM Departments", 0.76, 5, 0.0060),

    ("INSERT INTO Students (name, age, department, grade) SELECT name, age, department, grade FROM alumni WHERE graduated_year > 2018", 0.72, 800, 0.0050),

    ("UPDATE Students SET grade = 'C' WHERE grade IS NULL", 0.46, 30, 0.0032),

    ("DELETE FROM Departments WHERE dept_id NOT IN (SELECT dept_id FROM employees) LIMIT 10", 0.65, 2, 0.0045),

    ("SELECT e1.emp_id, e1.name FROM employees e1 JOIN employees e2 ON e1.manager_id = e2.emp_id WHERE e2.salary > 80000", 0.81, 35, 0.0060),

    ("WITH ranked_students AS (SELECT student_id, ROW_NUMBER() OVER (PARTITION BY department ORDER BY grade DESC) rn FROM Students) SELECT * FROM ranked_students WHERE rn <= 5", 0.75, 60, 0.0063),

    ("SELECT d.dept_name, JSON_OBJECT('head', d.head_name, 'budget', d.budget) info FROM Departments d WHERE d.budget > 500000", 0.58, 7, 0.0040),

    ("INSERT INTO employees (name, department, salary) VALUES ('BulkA1','X',100),('BulkA2','X',110),('BulkA3','Y',120),('BulkA4','Y',130),('BulkA5','Z',140),('BulkA6','Z',150),('BulkA7','Z',160)", 0.30, 7, 0.0030),

    ("UPDATE employees SET salary = salary * 1.10", 0.92, 10000, 0.0095),

    ("DELETE FROM Students WHERE admission_date < '2015-01-01'", 0.70, 400, 0.0069),

    ("SELECT e.name, (SELECT COUNT(*) FROM Students s WHERE s.department = e.department) AS students_in_dept FROM Employees e WHERE e.salary > 50000", 0.82, 45, 0.0064),

    ("SELECT dept_name FROM Departments WHERE dept_name IN (SELECT department FROM employees WHERE salary > 90000)", 0.77, 6, 0.0055),

    ("WITH dept_totals AS (SELECT department, SUM(salary) total FROM employees GROUP BY department) SELECT d.dept_name, dt.total FROM Departments d LEFT JOIN dept_totals dt ON d.dept_name = dt.department WHERE dt.total > 500000", 0.80, 9, 0.0060),

    ("INSERT INTO Departments (dept_name, head_name, budget) SELECT dept_name, head_name, budget FROM dept_staging WHERE ready = 1", 0.65, 50, 0.0052),

    ("UPDATE employees e SET e.salary = e.salary + (SELECT AVG(salary) FROM employees WHERE department = e.department) WHERE e.performance_rating = 'A'", 0.88, 120, 0.0069),

    ("DELETE FROM employees WHERE salary < (SELECT AVG(salary) FROM employees)/2", 0.76, 30, 0.0058),

    ("SELECT e.name, d.dept_name FROM employees e JOIN Departments d ON e.department = d.dept_name WHERE d.budget > (SELECT AVG(budget) FROM Departments)", 0.79, 20, 0.0061),

    ("SELECT s.name FROM Students s WHERE s.student_id IN (SELECT student_id FROM exam_results WHERE score > 90) AND EXISTS (SELECT 1 FROM Departments d WHERE d.dept_name = s.department AND d.budget > 500000)", 0.81, 18, 0.0060),

    ("SELECT dept_name, COUNT(*) FILTER (WHERE salary > 50000) AS high_paid FROM Departments d JOIN employees e ON d.dept_name = e.department GROUP BY dept_name", 0.74, 11, 0.0056),

    ("INSERT INTO employees (name, department, salary) SELECT name, 'Contract', salary FROM temp_contracts WHERE start_date > '2024-01-01'", 0.68, 300, 0.0051),

    ("UPDATE Departments SET budget = budget - 1000 WHERE dept_name IN (SELECT dept_name FROM Departments WHERE head_name LIKE 'A%')", 0.54, 4, 0.0041),

    ("DELETE FROM employees WHERE emp_id IN (SELECT emp_id FROM terminated WHERE processed = 1) LIMIT 200", 0.73, 200, 0.0057),

    ("SELECT e.emp_id, e.name, COUNT(s.student_id) AS related_students FROM employees e LEFT JOIN Students s ON e.department = s.department GROUP BY e.emp_id, e.name HAVING COUNT(s.student_id) > 0 ORDER BY related_students DESC", 0.76, 50, 0.0062)
]

# ----------------------------------------------------------
# LOAD ALL QUERIES INTO CACHE
# ----------------------------------------------------------
for q, sc, rows, et in simple_meta + medium_meta + complex_meta:
    add_to_cache(q, sc, rows, et)

# ==========================================================
# LOOKUP API (PATCHED FOR WHITESPACE-INSENSITIVE MATCHING)
# ==========================================================

def collapse_space(s: str) -> str:
    """Normalize all whitespace to single spaces for pattern comparison."""
    return re.sub(r"\s+", " ", s).strip()

def lookup_cached_query(query: str) -> Optional[Dict[str, Any]]:
    norm = normalize_query(query)
    patt = normalize_pattern(query)

    # Step 1: Exact match
    if norm in QUERY_CACHE:
        return QUERY_CACHE[norm]

    # Step 2: Pattern match (whitespace-insensitive)
    patt_c = collapse_space(patt)
    for entry in QUERY_CACHE.values():
        if collapse_space(entry["pattern"]) == patt_c:
            return entry

    return None

# Debug Test
if __name__ == "__main__":
    print("Cache size:", len(QUERY_CACHE))
    test_q = "delete from students where grade='Z' and admission_date<'2019-05-05';"
    print("Lookup:", lookup_cached_query(test_q))
