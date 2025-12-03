output "target_server_public_ip" {
  description = "Публічний IP цільового сервера"
  value       = aws_instance.target_server.public_ip
}

output "target_server_private_ip" {
  description = "Приватний IP цільового сервера"
  value       = aws_instance.target_server.private_ip
}

output "client_servers_public_ips" {
  description = "Публічні IP клієнтських серверів"
  value       = aws_instance.client_servers[*].public_ip
}

output "comparison_servers_info" {
  description = "Інформація про сервери для порівняння"
  value = {
    for idx, instance in aws_instance.comparison_servers : 
    var.instance_types[idx] => {
      public_ip  = instance.public_ip
      private_ip = instance.private_ip
      instance_id = instance.id
    }
  }
}

output "vpc_id" {
  description = "ID VPC"
  value       = aws_vpc.main.id
}

output "ssh_connection_commands" {
  description = "Команди для SSH підключення"
  value = {
    target_server = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_instance.target_server.public_ip}"
    client_servers = [
      for ip in aws_instance.client_servers[*].public_ip : 
      "ssh -i ~/.ssh/id_rsa ubuntu@${ip}"
    ]
  }
}