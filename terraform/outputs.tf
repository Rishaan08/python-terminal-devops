output "instance_id" {
  value = aws_instance.jenkins_server.id
}

output "public_ip" {
  value = aws_eip.jenkins_eip.public_ip
}

output "jenkins_url" {
  value = "http://${aws_eip.jenkins_eip.public_ip}:8080"
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/jenkins_key ubuntu@${aws_eip.jenkins_eip.public_ip}"
}
