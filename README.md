# 🚗 EcoGranite: Fuel Efficiency Coach

Turning Raw OBD-II Data into AI-Driven Eco-Driving Coaching

Author: Ines El Asri (ines.elasri.23@ucl.ac.uk)
UCL Final Year Project

Project Status Document (with Weekly & Monthly updates) : https://docs.google.com/document/d/1i2nGMdczQketJoSdZ07nO4apT52TPrFoXufwxPKZxLE/edit?tab=t.0

# 🌱 Why EcoGranite?

Modern vehicles generate huge amounts of telemetry data through OBD-II sensors — speed, RPM, airflow, throttle position, and more.
However, this data is rarely transformed into actionable feedback for drivers.
EcoGranite aims to bridge this gap by converting raw driving data into clear, personalised eco-driving coaching, helping drivers reduce fuel consumption and improve driving efficiency.

# 🔧 Project Overview
EcoGranite: Fuel Efficiency Coach is an AI-assisted system that:
- Analyzes OBD-II trip data
- Detects inefficient driving patterns
- Scores driving behaviour
- Generates natural-language coaching feedback using IBM Granite
<img width="1440" height="709" alt="Screenshot 2026-01-25 at 16 56 48" src="https://github.com/user-attachments/assets/99ee5e3e-0bd1-4ffe-930a-a142b2c852cc" />

This project is developed as a solo UCL Final Year Project, combining data engineering, applied ML, and human-centred AI feedback.

# 📊 Dataset & Features
- Dataset: KIT Automotive OBD-II Dataset
- Source: Karlsruhe Institute of Technology (KIT)

Each trip includes:
- Vehicle speed
- Engine RPM
- Mass Air Flow (MAF)
- Throttle position
- Intake air temperature
- Coolant temperature

From this, EcoGranite derives higher-level features such as:
- Estimated fuel consumption (L/100km)
- High RPM at low speed
- Long idling periods
- Frequent acceleration–braking cycles

# From Data to Coaching: The Pipeline

At a high level, the system works as follows:
1. CSV Upload
Raw OBD-II trip files are uploaded into the system.
3. Feature Engineering
Trip-level statistics and behavioural indicators are computed.
4. Driving Pattern Detection
Inefficiencies such as excessive idling or aggressive acceleration are flagged.
5. Trip Scoring
Each trip receives a composite efficiency score.
6. AI Feedback Generation (IBM Granite)
Structured trip summaries are passed to the Granite model, which generates:
- A trip overview
- Bullet-point coaching suggestions
- A concise takeaway message

# 🖥️ The Dashboard Experience
A lightweight Streamlit dashboard brings everything together:
- 📁 CSV Upload
<img width="329" height="528" alt="Screenshot 2026-01-25 at 16 59 45" src="https://github.com/user-attachments/assets/7d50eba2-41a7-4a69-b2dc-e530ccdcba28" />

- 🎯 Overall Driver Score (designed like a real car dashboard)
<img width="502" height="581" alt="Screenshot 2026-01-25 at 16 57 10" src="https://github.com/user-attachments/assets/e5fbfffb-3ea5-43be-bec5-fcec4c544b03" />
<img width="1015" height="628" alt="Screenshot 2026-01-25 at 16 57 22" src="https://github.com/user-attachments/assets/7feaada9-4530-40aa-88c8-0db2500e65a5" />

- 🔍 Trip Filters (High RPM, High idling, High fuel consumption)
<img width="319" height="448" alt="Screenshot 2026-01-25 at 16 58 35" src="https://github.com/user-attachments/assets/0947691a-0bef-41c4-ab96-abf058707b84" />

- 📈 Trace Visualisations (Speed over time, RPM over time, Fuel consumption trace)
<img width="961" height="494" alt="Screenshot 2026-01-25 at 16 57 33" src="https://github.com/user-attachments/assets/d2aa0f30-f720-4220-8337-65c540b30dd8" />
<img width="973" height="477" alt="Screenshot 2026-01-25 at 16 57 42" src="https://github.com/user-attachments/assets/dc8a0257-e552-436c-8b8f-9a90e08a8124" />
<img width="982" height="461" alt="Screenshot 2026-01-25 at 16 57 50" src="https://github.com/user-attachments/assets/d542321a-c20f-417c-9a1b-07948456f88a" />

- 🤖 Granite-Generated Coaching Feedback :
<img width="1440" height="706" alt="Screenshot 2026-01-25 at 17 02 52" src="https://github.com/user-attachments/assets/baa86dc5-1e6e-44ee-9071-19c8582cb349" />
 
The goal is to make technical driving data intuitive, visual, and motivating, rather than overwhelming.

# ✅ Current Progress
So far, EcoGranite supports:
- End-to-end data processing from CSV to feedback
- Trip-level efficiency scoring
- Multiple driving pattern detectors
- AI-generated coaching text
- Interactive dashboard with filters and traces

The system is now fully functional for trip analysis.

# 🔮 What’s Next
Upcoming work focuses on:
- Preparing final report and demo material


# 💬 Final Thoughts
EcoGranite explores how AI can translate low-level sensor data into meaningful behavioural feedback : not just predictions, but explanations and guidance.
If you’re interested in eco-driving, human-centred AI, or applied ML in mobility, feedback and discussion are very welcome (ines.elasri.23@ucl.ac.uk).
