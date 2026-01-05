# 🚀 Setup Instructions for Doffair Python Backend

## ✅ Step 1: Activate Virtual Environment

### On Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

### If you get execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### On Windows CMD:
```cmd
.\venv\Scripts\activate.bat
```

### On Linux/Mac:
```bash
source venv/bin/activate
```

**You'll know it's activated when you see `(venv)` at the start of your prompt.**

---

## ✅ Step 2: Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## ✅ Step 3: Configure Environment Variables

Create a `.env` file (it might already exist):

```env
# MongoDB Connection
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=doffair

# JWT Secret (change this!)
SECRET_KEY=your-secret-key-here-change-in-production

# Azure Storage (for image uploads)
AZURE_STORAGE_CONNECTION_STRING=your-azure-connection-string
AZURE_STORAGE_CONTAINER_NAME=vendor-images

# Environment
ENVIRONMENT=development
```

---

## ✅ Step 4: Run the Server

```powershell
uvicorn main:app --reload
```

### Alternative ways to run:
```powershell
# With specific host and port
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python -m uvicorn main:app --reload
```

---

## ✅ Step 5: Access the API

- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **API Base URL**: http://localhost:8000

---

## 🔧 Troubleshooting

### Issue: `uvicorn` not found
**Solution**: Make sure virtual environment is activated
```powershell
.\venv\Scripts\Activate.ps1
pip install uvicorn
```

### Issue: MongoDB connection error
**Solution**: Make sure MongoDB is running
```powershell
# Check if MongoDB service is running
Get-Service -Name MongoDB

# Or start MongoDB manually
mongod --dbpath C:\data\db
```

### Issue: Import errors
**Solution**: Reinstall dependencies
```powershell
pip install -r requirements.txt --upgrade
```

### Issue: Port already in use
**Solution**: Use a different port
```powershell
uvicorn main:app --reload --port 8001
```

---

## 🐳 Optional: Run with Docker

If you prefer Docker:

```dockerfile
# Create Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```powershell
# Build and run
docker build -t doffair-backend .
docker run -p 8000:8000 doffair-backend
```

---

## 📦 Quick Command Reference

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload

# Deactivate venv (when done)
deactivate
```

---

## ✨ You're all set! Access http://localhost:8000/docs to start testing.
