output "public_ip" {
  description = "Public IPv4 address of the k3s node."
  value       = aws_instance.node.public_ip
}

output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.node.id
}

output "instance_type" {
  description = "EC2 instance type."
  value       = aws_instance.node.instance_type
}

output "vpc_id" {
  description = "ID of the VPC."
  value       = aws_vpc.main.id
}

output "ssh_command" {
  description = "SSH into the node."
  value       = "ssh ubuntu@${aws_instance.node.public_ip}"
}

output "app_url" {
  description = "PantryPulse through the k3s Traefik ingress."
  value       = "http://${aws_instance.node.public_ip}/"
}
