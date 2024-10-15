

data "aws_subnet" "default_subnet" {
  default_for_az = true  
}


data "aws_ami" "ubuntu-linux-2204-amd64" {
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



resource "aws_iam_role" "ec2_basic_role" {
  name = "${lower(var.app_name)}-ec2-basic-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

  tags = {
    Name       = "${lower(var.app_name)}-ec2-basic-role"
    cost_code  = var.app_cost_code
  }
}


resource "aws_iam_instance_profile" "ec2_basic_profile" {
  name = "${lower(var.app_name)}-ec2-basic-profile"
  role = aws_iam_role.ec2_basic_role.name
}


resource "aws_key_pair" "public_key_pair" {
  key_name   = "${lower(var.app_name)}-deployment-key"
  public_key = "${file(var.public_key_path)}"
}


# Create EC2 Instance
resource "aws_instance" "mpm-api_server" {

  ami                         = data.aws_ami.ubuntu-linux-2204-amd64.id
  instance_type               = var.mpm-api_server_spec.instance_type
  subnet_id                   = data.aws_subnet.default_subnet.id
  iam_instance_profile        = aws_iam_instance_profile.ec2_basic_profile.name
  vpc_security_group_ids      = [aws_security_group.sg-ssh-only.id]
  source_dest_check           = false
  key_name                    = aws_key_pair.public_key_pair.key_name

  user_data                   = format("%s\n%s\n", local.ec2_user_data, "sudo hostnamectl set-hostname mpm-api.${lower(var.app_internal_domain)}")

  # root disk
  root_block_device {
    volume_size           =  var.mpm-api_server_spec.volume_size
    # volume_type           = var.linux_root_volume_type
    delete_on_termination = true
    encrypted             = true
  }

  tags = merge(tomap({
    Name = "${lower(var.app_name)}-mpm-api-server"
    "${upper(var.app_cost_code)}" = "server"
    dns = "mpm-api.${lower(var.app_internal_domain)}"
    inventory = "mpm-api"
  }), local.ec2_env_tags)

  volume_tags = {
    Name = "${lower(var.app_name)}-mpm-api-server-vol"
    "${upper(var.app_cost_code)}" = "volume"
    cost_code = var.app_cost_code
  }

  lifecycle {
    ignore_changes = [
      ami,
    ]
  }
}

