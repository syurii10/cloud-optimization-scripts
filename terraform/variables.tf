variable "aws_region" {
  description = "AWS регіон для розгортання"
  type        = string
  default     = "eu-central-1"
}

variable "instance_types" {
  description = "Типи EC2 інстансів для порівняння"
  type        = list(string)
  default     = ["t3.micro"]
}

variable "target_server_instance_type" {
  description = "Тип інстансу для сервера-мішені"
  type        = string
  default     = "t3.small"
}

variable "comparison_server_instance_type" {
  description = "Тип інстансу для comparison сервера"
  type        = string
  default     = "t3.micro"
}

variable "client_server_count" {
  description = "Кількість клієнтських серверів"
  type        = number
  default     = 1
}

variable "project_name" {
  description = "Назва проекту"
  type        = string
  default     = "cloud-optimization"
}

variable "github_repo" {
  description = "GitHub репозиторій зі скриптами"
  type        = string
  default     = "https://github.com/syurii10/cloud-optimization-scripts.git"
}

variable "allowed_ssh_cidr" {
  description = "CIDR блок для SSH доступу (обмежте до вашої IP для безпеки!)"
  type        = string
  default     = "0.0.0.0/0"  # УВАГА: Змініть на вашу IP!
}