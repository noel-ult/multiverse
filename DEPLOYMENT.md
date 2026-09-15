# Production deployment: EC2 + private RDS

Multiverse is deployed in `ap-south-1` as an Amazon Linux 2023 EC2 application server behind Nginx and Gunicorn, connected over private VPC traffic to an RDS MySQL 8.4 database. RDS must remain non-public. This document intentionally uses placeholders and never contains production secrets.

## EC2 bootstrap

```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip git nginx gcc mariadb105
git clone https://github.com/noel-ult/multiverse.git /home/ec2-user/multiverse
cd /home/ec2-user/multiverse
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

## Runtime configuration

Create `/home/ec2-user/multiverse/.env` with mode `600`, owned by `ec2-user`:

```dotenv
FLASK_ENV=production
SECRET_KEY=<generated-random-secret>
DATABASE_URL=mysql+pymysql://<app-user>:<encoded-password>@<rds-endpoint>:3306/multiverse
SESSION_COOKIE_SECURE=false
```

Set `SESSION_COOKIE_SECURE=true` only after HTTPS and a domain are configured. Run migrations with the environment loaded:

```bash
cd /home/ec2-user/multiverse
set -a; source .env; set +a
.venv/bin/flask --app wsgi:app db upgrade
.venv/bin/flask --app wsgi:app db current
```

## systemd

Create `/etc/systemd/system/multiverse.service`:

```ini
[Unit]
Description=Multiverse Flask Application
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/multiverse
EnvironmentFile=/home/ec2-user/multiverse/.env
ExecStart=/home/ec2-user/multiverse/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now multiverse
sudo systemctl status multiverse
```

## Nginx

Create `/etc/nginx/conf.d/multiverse.conf`:

```nginx
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo nginx -t
sudo systemctl enable --now nginx
curl -I http://127.0.0.1/
```

## Network policy

- EC2 security group: SSH from the operator IPv4 `/32`; HTTP/HTTPS from the internet.
- RDS security group: MySQL 3306 from the Multiverse EC2 security group only.
- RDS: private subnets, `PubliclyAccessible=false`, encrypted storage, backups, deletion protection.

## Operations

```bash
sudo journalctl -u multiverse -n 100 --no-pager
sudo systemctl restart multiverse
sudo systemctl restart nginx
```

After a reboot, confirm both services are active and test the public EC2 URL. Do not run demo/reset scripts against production.
