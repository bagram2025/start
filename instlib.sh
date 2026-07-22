# 1. Установить pip для Python, если ещё нет
sudo apt-get install -y python3-pip

# 2. Установить psycopg2
pip3 install psycopg2-binary

# 3. Проверить, что установилось
python3 -c "import psycopg2; print('OK')"
