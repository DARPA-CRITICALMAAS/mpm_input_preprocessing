

data "aws_vpc" "default" {
  default = true
}
# security group
resource "aws_security_group" "sg-ssh-only" {

  vpc_id = data.aws_vpc.default.id
  name = "${lower(var.app_name)}-ssh-only-sg"

  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${lower(var.app_name)}-ssh-only-sg"
    "${upper(var.app_cost_code)}" = "sg"
    cost_code = var.app_cost_code
  }
}

