variable "public_key_path" {
  description = "Path to the public SSH key"
  type        = string
}
variable "private_key_path" {
  description = "Path to the private SSH key"
  type        = string
}

variable "app_name" {
  description = "The name of the application"
  type        = string
  default     = "mpm"
}

variable "aws_region" {
  description = "region"
  type        = string
  default     = "us-east-1"
}

variable "aws_public_bucket_name" {
  description = "cdr bucket name"
  type        = string
  default     = "public.cdr.land"
}



variable "app_cost_code" {
  description = "The cost code for the application"
  type        = string
}


variable "mpm-api_server_spec" {
  type = object({
    instance_type = string
    volume_size   = number
  })
  description = "mpm-api server"
}


variable "app_internal_domain" {
  description = "The name of the application"
  type        = string
  default     = "mpm_internal"
}


locals {
  ec2_user_data = file("init.sh")

  ec2_env_tags = {
    app_name            = "${lower(var.app_name)}"
    env_internal_domain = "${lower(var.app_internal_domain)}"
  }
}



