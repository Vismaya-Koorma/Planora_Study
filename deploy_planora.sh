#!/bin/bash
# deploy_planora.sh - Automated Deployment Script for Planora on AWS EC2 (Ubuntu 24.04)

# Exit on any error
set -e

# Variables
PROJECT_NAME="Planora_Study"
REPO_URL="https://github.com/Vismaya-Koorma/Planora_Study.git"
CLONE_DIR="/home/ubuntu/$PROJECT_NAME"
VENV_DIR="$CLONE_DIR/venv"
DOMAIN="YOUR_DOMAIN_OR_IP" # Replace with actual IP/domain

echo "======================================"
echo "Starting Deployment for $PROJECT_NAME"
echo "======================================"

echo "[1/8] Updating system packages..."
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev libmysqlclient-dev mysql-server nginx pkg-config git

echo "[2/8] Setting up project directory..."
if [ ! -d "$CLONE_DIR" ]; then
    git clone $REPO_URL $CLONE_DIR
else
    echo "Directory exists. Pulling latest changes..."
    cd $CLONE_DIR
    git pull origin main
fi
cd $CLONE_DIR

echo "[3/8] Setting up virtual environment..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip install -r requirements.txt

echo "[4/8] Setting up .env file..."
if [ ! -f "$CLONE_DIR/.env" ]; then
    echo "Creating a template .env file..."
    cat <<EOF > $CLONE_DIR/.env
SECRET_KEY='$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")'
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,127.0.0.1,localhost
DB_NAME=studytracker_db
DB_USER=planora_user
DB_PASSWORD=SecurePassword123!
DB_HOST=127.0.0.1
DB_PORT=3306
EOF
    echo "Created .env file."
fi

echo "[5/8] Setting up MySQL Database..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS studytracker_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'planora_user'@'localhost' IDENTIFIED BY 'SecurePassword123!';"
sudo mysql -e "GRANT ALL PRIVILEGES ON studytracker_db.* TO 'planora_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

echo "[6/8] Running Django Tasks (migrations & collectstatic)..."
python manage.py migrate
python manage.py collectstatic --noinput

echo "[7/8] Configuring Gunicorn systemd service..."
sudo bash -c "cat <<EOF > /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon for $PROJECT_NAME
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=$CLONE_DIR
EnvironmentFile=$CLONE_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn --access-logfile - --workers 3 --bind unix:$CLONE_DIR/studytracker.sock studytracker.wsgi:application

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl enable gunicorn

echo "[8/8] Configuring Nginx..."
sudo bash -c "cat <<EOF > /etc/nginx/sites-available/$PROJECT_NAME
server {
    listen 80;
    server_name $DOMAIN;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $CLONE_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$CLONE_DIR/studytracker.sock;
    }
}
EOF"

sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "======================================"
echo "Deployment Complete!"
echo "Your app should now be running."
echo "======================================"
