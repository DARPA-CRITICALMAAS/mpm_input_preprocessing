# Application Definition
app_name            = "mpm"
app_cost_code       = "USGS"
app_internal_domain = "mpm_internal"

# Key Pair
public_key_path = "~/.ssh/id_mpm_rsa.pub"
private_key_path = "~/.ssh/id_mpm_rsa"

# AWS
aws_region = "us-east-1"

mpm-api_server_spec = {
  instance_type = "t3.large"
  volume_size = 128
}