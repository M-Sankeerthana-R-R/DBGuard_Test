# **Database Monitoring & Client-Server Management System**

---

# **Overview**
This project is a database monitoring and client-server management system developed using Python, MySQL, Docker, and Node.js.

The system supports:
- Database monitoring
- Client-server communication
- Backend API handling
- Real-time monitoring services
- MySQL container management
- Multi-client interaction

---

# **Tech Stack**
- Python
- MySQL
- Docker
- Node.js
- Flask / Backend APIs

---

# **Project Structure**

```bash
backend1/              # Python backend and socket programs
mysql-monitoring/      # Dockerized MySQL monitoring setup
```

---

# **Setup & Execution Steps**

## **1. Start Backend Application**

```bash
cd backend1
python app.py
```

---

## **2. Start Frontend / Node Application**

```bash
cd ..
npm start
```

---

## **3. Open MySQL Container**

```bash
cd mysql-monitoring
docker exec -it mysql mysql -u root -p
```

### **MySQL Password**
```bash
rootpassword
```

### **Use Database**
```sql
use mydb;
```

---

## **4. Start Docker Monitoring Services**

```bash
cd mysql-monitoring
docker-compose up -d
```

---

## **5. Start Python Server**

```bash
cd backend1
python server.py
```

---

## **6. Start Python Client**

```bash
cd backend1
python client.py
```

---

# **Features**
- Client-server communication
- Database activity monitoring
- Dockerized MySQL services
- Backend API integration
- Multi-client handling
- Real-time database interaction

---

# **Future Enhancements**
- GUI dashboard integration
- Advanced query analytics
- Role-based authentication
- AI-powered anomaly detection
- Real-time alerts and reporting

---

# **License**
This project is intended for educational and research purposes.
