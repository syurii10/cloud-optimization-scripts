terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC для нашої інфраструктури
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "cloud-optimization-vpc"
    Project = "MasterThesis"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "cloud-optimization-igw"
  }
}

# Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "cloud-optimization-public-subnet"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "cloud-optimization-public-rt"
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security Group для серверів
resource "aws_security_group" "servers" {
  name        = "cloud-optimization-servers-sg"
  description = "Security group for load testing servers"
  vpc_id      = aws_vpc.main.id

  # SSH доступ - ВАЖЛИВО: Обмежте до вашої IP!
  # Замініть 0.0.0.0/0 на вашу IP адресу (наприклад: "203.0.113.0/32")
  # Або використовуйте AWS Systems Manager Session Manager замість SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  # HTTP доступ
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS доступ
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Дозволяємо весь внутрішній трафік між інстансами
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  # Весь вихідний трафік
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "cloud-optimization-servers-sg"
  }
}

# Data source для availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Key Pair для SSH доступу
resource "aws_key_pair" "main" {
  key_name   = "cloud-optimization-key"
  public_key = file("~/.ssh/id_rsa.pub")
}