# Создать виртуальное окружение
python3 -m venv venv

# Активировать его
source venv/bin/activate

# Установить библиотеку
pip install psycopg2-binary

# Запустить дневник
python3 dery.py

# Когда закончите — деактивировать
deactivate
 
