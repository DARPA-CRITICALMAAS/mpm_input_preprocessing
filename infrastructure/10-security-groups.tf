variable "sg_whitelist_cidr_blocks" {
  type        = list(string)
  description = "Whitelist cidrs ipv4"
}


variable "sg_whitelist_cidr_blocks_v6" {
  type        = list(string)
  description = "Whitelist cidrs v6 blocks"
}


resource "aws_key_pair" "public_key_pair" {
  key_name   = "${lower(var.app_name)}-deployment-key"
  public_key = file(var.public_key_path)
}


# security group
resource "aws_security_group" "sg-ssh-only" {

  vpc_id = aws_vpc.vpc.id
  name   = "${lower(var.app_name)}-ssh-only-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name                          = "${lower(var.app_name)}-ssh-only-sg"
    "${upper(var.app_cost_code)}" = "sg"
    cost_code                     = var.app_cost_code
  }
}

resource "aws_security_group" "sg-internal" {

  vpc_id = aws_vpc.vpc.id
  name   = "${lower(var.app_name)}-internal-sg"

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = -1
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  tags = {
    Name                          = "${lower(var.app_name)}-internal-sg"
    "${upper(var.app_cost_code)}" = "sg"
    cost_code                     = var.app_cost_code
  }

}


resource "aws_security_group" "sg-lb" {

  vpc_id = aws_vpc.vpc.id
  name   = "${lower(var.app_name)}-lb-sg"

  ingress {
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = var.sg_whitelist_cidr_blocks
    ipv6_cidr_blocks = var.sg_whitelist_cidr_blocks_v6
  }

  ingress {
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = var.sg_whitelist_cidr_blocks
    ipv6_cidr_blocks = var.sg_whitelist_cidr_blocks_v6
  }


  tags = {
    Name                          = "${lower(var.app_name)}-lb-sg"
    "${upper(var.app_cost_code)}" = "sg"
    cost_code                     = var.app_cost_code
  }
}

