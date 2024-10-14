# Application Definition
app_name            = "mpm"
app_cost_code       = "USGS"
app_internal_domain = "?"
app_external_domain = "?"

# Key Pair
public_key_path = "~/.ssh/_.pub"
private_key_path = "~/.ssh/_"

# AWS
aws_region = "us-east-1"

mpm-api_server_spec = {
  instance_type = "t3.large"
  volume_size = 128
}