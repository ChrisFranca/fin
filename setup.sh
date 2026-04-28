#!/bin/bash

# FinHome - Script de Instalação Automática (Linux/macOS)
echo "======================================================"
echo "   FinHome - Script de Instalacao Automatica"
echo "======================================================"

# 1. Verificar Python
if ! command -v python3 &> /dev/null
then
    echo "[ERRO] Python 3 nao encontrado."
    exit
fi

# 2. Criar venv
echo "[+] Criando ambiente virtual..."
python3 -m venv venv

# 3. Instalar dependências
echo "[+] Instalando dependencias..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 4. Banco de Dados
echo "[+] Migrando banco de dados..."
./venv/bin/python manage.py makemigrations financas
./venv/bin/python manage.py migrate

# 5. Criar superusuário
read -p "Deseja criar um usuario agora? (s/n): " choice
if [ "$choice" == "s" ]; then
    ./venv/bin/python manage.py createsuperuser
fi

echo "======================================================"
echo "   INSTALACAO CONCLUIDA!"
echo "   Para rodar: ./venv/bin/python manage.py runserver"
echo "======================================================"

read -p "Deseja rodar o sistema agora? (s/n): " run
if [ "$run" == "s" ]; then
    ./venv/bin/python manage.py runserver
fi
