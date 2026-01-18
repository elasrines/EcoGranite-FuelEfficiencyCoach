# 🚗 EcoGranite: Turning Raw OBD-II Data into AI-Driven Eco-Driving Coaching

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
2. Feature Engineering
Trip-level statistics and behavioural indicators are computed.
3. Driving Pattern Detection
Inefficiencies such as excessive idling or aggressive acceleration are flagged.
4. Trip Scoring
Each trip receives a composite efficiency score.
5. AI Feedback Generation (IBM Granite)
Structured trip summaries are passed to the Granite model, which generates:
- A trip overview
- Bullet-point coaching suggestions
- A concise takeaway message

# 🖥️ The Dashboard Experience
A lightweight Streamlit dashboard brings everything together:
- 📁 CSV Upload
- 🎯 Overall Driver Score (designed like a real car dashboard)
- 🔍 Trip Filters (High RPM, High idling, High fuel consumption)
- 📈 Trace Visualisations (Speed over time, RPM over time, Fuel consumption trace)
- 🤖 Granite-Generated Coaching Feedback : 
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
- Refining prompt design for more precise coaching
- UI polish and storytelling improvements
- Adding lightweight evaluation metrics (accuracy, usefulness, safety) + testing
- Preparing final report and demo material


# 💬 Final Thoughts
EcoGranite explores how AI can translate low-level sensor data into meaningful behavioural feedback : not just predictions, but explanations and guidance.
If you’re interested in eco-driving, human-centred AI, or applied ML in mobility, feedback and discussion are very welcome (ines.elasri.23@ucl.ac.uk).
