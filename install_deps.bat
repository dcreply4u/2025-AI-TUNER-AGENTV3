@echo off
echo ========================================
echo Installing AI Tuner Agent Dependencies
echo ========================================
echo.

echo Installing core GUI dependencies...
pip install pyside6 pyqtgraph

echo.
echo Installing other dependencies...
pip install numpy pandas scikit-learn joblib requests

echo.
echo Installing optional dependencies (may fail, that's OK)...
pip install python-OBD racecapture SpeechRecognition pyttsx3 pyserial pynmea2 opencv-python psutil cantools python-can paho-mqtt cryptography

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo You can now run: python demo.py
echo.
pause

