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
              apt-get install -y python3-pip git nginx
              
              # Налаштування простого веб-сервера
              systemctl start nginx
              systemctl enable nginx
              
              # Створюємо тестову сторінку
              echo "Server is running. Instance type: ${var.target_server_instance_type}" > /var/www/html/index.html
              
              # Клонуємо репозиторій зі скриптами
              cd /home/ubuntu
              git clone ${var.github_repo} scripts
              cd scripts
              
              # Встановлюємо залежності
              apt-get install -y python3-psutil
              
              chown -R ubuntu:ubuntu /home/ubuntu/scripts
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
              apt-get install -y python3-pip nginx
              systemctl start nginx
              systemctl enable nginx
              
              echo "Comparison server - Type: ${var.instance_types[count.index]}" > /var/www/html/index.html
              
              pip3 install flask psutil boto3
              EOF

  tags = {
    Name         = "${var.project_name}-comparison-${var.instance_types[count.index]}"
    Role         = "comparison"
    InstanceType = var.instance_types[count.index]
  }

  monitoring = true
}