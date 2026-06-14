@echo off
echo Starting Classroom Co-Pilot AI...
echo Opening http://localhost:8501
python -m streamlit run app.py --server.port 8501
pause
