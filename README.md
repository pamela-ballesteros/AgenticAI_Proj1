# Agentic AI Travel Planner

**Intelligent Multi-City Travel Planning Using LangChain Agents + Real-Time APIs**

## 📌 Project Overview ## 

This project implements an Agentic AI-based travel planning system that autonomously gathers, synthesizes, and analyzes real-time data to generate personalized travel recommendations.

Using LangChain’s agent framework, the system orchestrates multiple external APIs to provide:

 📍 **Location geocoding**
- 🌦 **Weather forecasting**
- 🌫 **Air quality monitoring (AQI)**
- 🗺 **Tourist attraction discovery**
- 👕 **Clothing recommendations**
- ☂ **Umbrella and face mask advisories**
  
The solution demonstrates how AI agents can coordinate tool-based workflows to produce structured, real-world decision support outputs.

## 🎯 Business Problem

**Travelers planning multi-city trips often rely on fragmented sources for:**

- Weather conditions  
- Environmental air quality  
- Attractions and points of interest  
- Packing and preparation decisions 

This project addresses that fragmentation by building an autonomous AI planning assistant that:

Collects information from multiple data providers

- Applies domain logic

- Produces a consolidated travel plan

- Reduces manual research effort

## 🧠 Agent Architecture

The system follows a tool-driven agent architecture:

User Input (Cities)
        ↓
LangChain Agent (LLM Orchestrator)
        ↓
---------------------------------
| Geocoding API                 |
| Weather API (Google/OpenWeather) |
| Air Quality API               |
| Places API (Attractions)      |
---------------------------------
        ↓
Decision Logic Layer
(Clothing, Umbrella, Mask Rules)
        ↓
Structured Travel Plan Output

| File               | Purpose                                         |
| ------------------ | ----------------------------------------------- |
| `main.py`          | Entry point and multi-city execution logic      |
| `agent.py`         | LangChain agent creation and tool orchestration |
| `tools.py`         | API integrations and helper functions           |
| `config.py`        | Environment variable configuration              |
| `streamlit_app.py` | Web UI interface (optional)                     |
| `requirements.txt` | Python dependencies                             |

## 🛠 Technology Stack

**Python 3.10+

**LangChain (Agent Framework)

**OpenAI GPT-4o-mini

**Google Maps API

**Google Air Quality API

**Google Places API

**OpenWeatherMap API (fallback)

**Streamlit (UI Layer)

**Requests, dotenv

## ⚙ Features

✔ Autonomous tool selection and execution
✔ Real-time weather forecasting
✔ Dynamic AQI categorization
✔ Packing recommendations
✔ Attraction discovery by proximity
✔ Multi-city batch processing
✔ API fallback logic
✔ Error-handling resilience

## 🚀 How To Run Locally

### 1️⃣ Clone Repository

```git clone https://github.com/YOUR_USERNAME/AgenticAI_Proj1.git
cd AgenticAI_Proj1```

### 2️⃣ Create Virtual Environment
```
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows
```

### 3️⃣ Install Dependencies
```
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a .env file:

OPENAI_API_KEY=your_openai_key
GOOGLE_MAPS_API_KEY=your_google_maps_key
OPENWEATHER_API_KEY=your_openweather_key


⚠️ .env is ignored from GitHub for security.

### 5️⃣ Run Agent From Terminal

Single or multi-city input:
```
python main.py Paris Tokyo Toronto
```

Or interactive mode:
```
python main.py
```

## 🌐 Streamlit Web Interface (Optional)

Launch web UI:
```
streamlit run streamlit_app.py
```

Then open:

**http://localhost:8501**

## 📊 Example Output

For each city the agent returns:

## Coordinates & formatted address

- 3-day weather forecast

- AQI value and health category

- Top nearby attractions

- Clothing advice

- Umbrella recommendation

- Mask advisory

## 🔐 Security & Best Practices

✔ API keys stored using environment variables
✔ .env excluded from repository
✔ Modular architecture
✔ Tool fallback logic
✔ Error handling and graceful degradation

## 📈 Learning Outcomes

- This project demonstrates:

- Agent-based AI orchestration

- Tool-driven reasoning pipelines

- Real-world API integration

- Prompt engineering for tool enforcement

- Modular software architecture

- Production-style environment management

## 📚 Future Enhancements

Deployment on Streamlit Cloud

User preference profiles

Travel budget optimization

Multi-language output support

Interactive map visualization

##Recommendation ranking

## 👤 Author

Pamela Ballesteros
Master of Business Analytics Candidate
Saint Mary’s University — Sobey School of Business

Specializing in:

**Applied AI Systems

**Business Analytics

**Risk & Compliance Analytics

**Data-Driven Decision Support

Give the repo a ⭐ and feel free to fork or contribute!


