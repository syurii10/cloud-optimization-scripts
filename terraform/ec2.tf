# AMI для Ubuntu
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Сервер-мішень (приймає навантаження)
resource "aws_instance" "target_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.target_server_instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.servers.id]
  key_name               = aws_key_pair.main.key_name

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y python3-pip git python3-psutil

              # Клонуємо репозиторій зі скриптами
              cd /home/ubuntu
              git clone ${var.github_repo} scripts
              cd scripts

              chown -R ubuntu:ubuntu /home/ubuntu/scripts

              # Запускаємо CPU-intensive сервер як systemd service
              cat > /etc/systemd/system/cpu-server.service <<'SERVICE'
[Unit]
Description=CPU-Intensive HTTP Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/scripts
ExecStart=/usr/bin/python3 /home/ubuntu/scripts/scripts/cpu_intensive_server.py 80
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

              # Запускаємо сервіс
              systemctl daemon-reload
              systemctl enable cpu-server
              systemctl start cpu-server
              EOF

  tags = {
    Name = "${var.project_name}-target-server"
    Role = "target"
    InstanceType = var.target_server_instance_type
  }

  monitoring = true
}

# Клієнтські сервери для тестування
resource "aws_instance" "client_servers" {
  count = var.client_server_count

  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.servers.id]
  key_name               = aws_key_pair.main.key_name

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y python3-pip git python3-aiohttp
              
              # Клонуємо репозиторій зі скриптами
              cd /home/ubuntu
              git clone ${var.github_repo} scripts
              cd scripts
              
              # Зберігаємо IP цільового сервера
              echo "${aws_instance.target_server.private_ip}" > /home/ubuntu/target_ip.txt
              
              chown -R ubuntu:ubuntu /home/ubuntu
              EOF

  tags = {
    Name = "${var.project_name}-client-${count.index + 1}"
    Role = "client"
  }

  depends_on = [aws_instance.target_server]
}

# Додаткові інстанси для порівняння різних типів
resource "aws_instance" "comparison_servers" {
  count = length(var.instance_types)

  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.comparison_server_instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.servers.id]
  key_name               = aws_key_pair.main.key_name

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y python3-pip git python3-psutil

              # Клонуємо репозиторій зі скриптами
              cd /home/ubuntu
              git clone ${var.github_repo} scripts
              cd scripts

              chown -R ubuntu:ubuntu /home/ubuntu/scripts

              # Запускаємо CPU-intensive сервер як systemd service
              cat > /etc/systemd/system/cpu-server.service <<'SERVICE'
[Unit]
Description=CPU-Intensive HTTP Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/scripts
ExecStart=/usr/bin/python3 /home/ubuntu/scripts/scripts/cpu_intensive_server.py 80
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

              # Запускаємо сервіс
              systemctl daemon-reload
              systemctl enable cpu-server
              systemctl start cpu-server
              EOF

  tags = {
    Name         = "${var.project_name}-comparison-${var.instance_types[count.index]}"
    Role         = "comparison"
    InstanceType = var.instance_types[count.index]
  }

  monitoring = true
}