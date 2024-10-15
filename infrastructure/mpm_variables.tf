variable "public_key_path" {
  description = "Path to the public SSH key"
  type        = string
}



variable "app_name" {
  description = "The name of the application"
  type        = string
  default     = "mpm"  # default value can be used here
}

variable "app_cost_code" {
  description = "The cost code for the application"
  type        = string
}


variable "mpm-api_server_spec" {
  type = object({
    instance_type = string
    volume_size = number
  })
  description = "mpm-api server"
}

variable "app_internal_domain" {
  description = "The name of the application"
  type        = string
  default     = "mpm_internal" 
}
variable "app_external_domain" {
  description = "The name of the application"
  type        = string
  default     = "mpm.processing" 
}

locals {
  ec2_user_data = file("init.sh")

  ec2_env_tags = {
    app_name = "${lower(var.app_name)}"
    env_internal_domain = "${lower(var.app_internal_domain)}"
    env_external_domain = "${lower(var.app_external_domain)}"
  }
}



