

variable "aws_az1" {
  type        = string
  description = "AWS AZ"
}
variable "aws_az2" {
  type        = string
  description = "AWS AZ"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR for the VPC"
}

variable "public_subnet1_cidr" {
  type        = string
  description = "CIDR for the public subnet"
}

variable "public_subnet2_cidr" {
  type        = string
  description = "CIDR for the public subnet"
}

resource "aws_vpc" "vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name                          = "${lower(var.app_name)}-vpc"
    "${upper(var.app_cost_code)}" = "vpc"
    cost_code                     = var.app_cost_code
  }
}


resource "aws_subnet" "public-subnet" {
  vpc_id = aws_vpc.vpc.id

  cidr_block              = var.public_subnet1_cidr
  map_public_ip_on_launch = "true"
  availability_zone       = var.aws_az1

  tags = {
    Name                          = "${lower(var.app_name)}-public-subnet"
    "${upper(var.app_cost_code)}" = "subnet"
    cost_code                     = var.app_cost_code
  }
}


resource "aws_subnet" "public-subnet2" {
  vpc_id = aws_vpc.vpc.id

  cidr_block              = var.public_subnet2_cidr
  map_public_ip_on_launch = "true" //it makes this a public subnet
  availability_zone       = var.aws_az2

  tags = {
    Name                          = "${lower(var.app_name)}-public-subnet2"
    "${upper(var.app_cost_code)}" = "subnet"
    cost_code                     = var.app_cost_code
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id

  tags = {
    Name                          = "${lower(var.app_name)}-igw"
    "${upper(var.app_cost_code)}" = "igw"
    cost_code                     = var.app_cost_code
  }
}

resource "aws_route_table" "public-rt" {
  vpc_id = aws_vpc.vpc.id
  route {
    cidr_block = "0.0.0.0/0"                 //associated subnet can reach everywhere
    gateway_id = aws_internet_gateway.igw.id //CRT uses this IGW to reach internet
  }

  tags = {
    Name                          = "${lower(var.app_name)}-rt"
    "${upper(var.app_cost_code)}" = "rt"
    cost_code                     = var.app_cost_code
  }
}

resource "aws_route_table_association" "public-rt-association" {
  for_each       = { subnet1 = aws_subnet.public-subnet.id, subnet2 = aws_subnet.public-subnet2.id }
  subnet_id      = each.value
  route_table_id = aws_route_table.public-rt.id
}


resource "aws_route53_zone" "private" {
  name = var.app_internal_domain

  vpc {
    vpc_id = aws_vpc.vpc.id
  }
}
