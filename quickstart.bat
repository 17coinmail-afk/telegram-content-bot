@echo off
chcp 65001 >nul
echo.
echo  ============================================
echo    Telegram Content Bot - Быстрый старт
echo  ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  ⚠️ Python не найден. Скачай с python.org и установи.
    pause
    exit /b 1
)

echo  📦 Создаём виртуальное окружение...
python -m venv venv

echo  📦 Активируем окружение...
call venv\Scripts\activate.bat

echo  📦 Устанавливаем зависимости...
pip install -r requirements.txt

echo.
echo  ⚙️ Запускаем настройку...
python setup.py

echo.
echo  🚀 Для запуска бота выполни:
echo    venv\Scripts\activate.bat ^&^& python -m app.main
pause
