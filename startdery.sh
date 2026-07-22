# Создать виртуальное окружение
python3 -m venv venv

# Активировать его
source venv/bin/activate

# Установить библиотеку
pip install psycopg2-binary

# Запустить дневник
python3 diary.py

# Когда закончите — деактивировать
deactivate
