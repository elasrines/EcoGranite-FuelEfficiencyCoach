# 🚗 EcoGranite: Fuel Efficiency Coach

Turning Raw OBD-II Data into Eco-Driving Coaching

EcoGranite Platform LIVE : https://ecogranite.streamlit.app/
Project Blog : https://project-blog-ecogranite.vercel.app

Author: Ines El Asri (ines.elasri.23@ucl.ac.uk)
UCL Final Year Project

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
<img width="1411" height="701" alt="Screenshot 2026-03-10 at 13 29 26" src="https://github.com/user-attachments/assets/8cb91e56-e144-4823-aa2a-6949fe92801d" />

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
<img width="1013" height="596" alt="Screenshot 2026-03-10 at 13 28 40" src="https://github.com/user-attachments/assets/83646d11-e349-4c64-a5a2-072c2f47f11d" />

- 🔍 Trip Filters (High RPM, High idling, High fuel consumption)
<img width="319" height="448" alt="Screenshot 2026-01-25 at 16 58 35" src="https://github.com/user-attachments/assets/0947691a-0bef-41c4-ab96-abf058707b84" />

- 📈 Trace Visualisations (Speed over time, RPM over time, Fuel consumption trace)
<img width="961" height="494" alt="Screenshot 2026-01-25 at 16 57 33" src="https://github.com/user-attachments/assets/d2aa0f30-f720-4220-8337-65c540b30dd8" />
<img width="973" height="477" alt="Screenshot 2026-01-25 at 16 57 42" src="https://github.com/user-attachments/assets/dc8a0257-e552-436c-8b8f-9a90e08a8124" />
<img width="982" height="461" alt="Screenshot 2026-01-25 at 16 57 50" src="https://github.com/user-attachments/assets/d542321a-c20f-417c-9a1b-07948456f88a" />

- 🤖 Granite-Generated Coaching Feedback :
<img width="1040" height="611" alt="Screenshot 2026-03-10 at 13 26 56" src="https://github.com/user-attachments/assets/db0ca063-897c-4fb8-9bdf-9fc9a4256b57" />

 
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
