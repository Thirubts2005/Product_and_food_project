# 🛒 GroceryMind — AI Grocery Assistant
### 100% Free · Offline · No API Key · Powered by Ollama 🦙

## ⚡ Quick Start (3 steps)

### Step 1 — Install Ollama (free)
Download: https://ollama.com/download

### Step 2 — Pull a free AI model (pick one)
```bash
ollama pull llama3    # Best quality  ~4 GB  ← RECOMMENDED
ollama pull mistral   # Fast + smart  ~4 GB
ollama pull phi3      # Lightweight   ~2 GB  ← for low-RAM PCs
```

### Step 3 — Run the app
```bash
pip install -r requirements.txt
ollama serve          # keep running in one terminal
streamlit run app.py  # open new terminal for this
```
Open: http://localhost:8501

---

## 📁 Files
```
AI_Grocery_Agent/
├── app.py            ← Main Streamlit app (6 pages)
├── inventory.py      ← SQLite inventory
├── ai_logic.py       ← Ollama AI (FREE, local)
├── price_checker.py  ← Price comparison
├── automation.py     ← Cart simulation
├── utils/helpers.py
└── requirements.txt  ← 4 packages, all free
```

## 💰 Total Cost: ₹0/month

## 🖥️ RAM Requirements
- 8 GB RAM  → use phi3
- 16 GB RAM → use llama3 or mistral
- 32 GB RAM → use gemma2
