# Application Definition
app_name            = "mpm"
app_cost_code       = "USGS"
app_internal_domain = "mpm_internal"

# Key Pair
public_key_path  = "~/.ssh/id_mpm_rsa.pub"
private_key_path = "~/.ssh/id_mpm_rsa"

# AWS
aws_region = "us-east-1"
aws_az1    = "us-east-1f"
aws_az2    = "us-east-1c"

mpm-api_server_spec = {
  instance_type = "t3.large"
  volume_size   = 128
}
aws_public_bucket_name = "public.cdr.land"

vpc_cidr            = "172.31.0.0/16"
public_subnet1_cidr = "172.31.16.0/20"
public_subnet2_cidr = "172.31.32.0/20"


# Whitelist
sg_whitelist_cidr_blocks = [
  "0.0.0.0/0",
  # "96.231.60.6/32",
  # "100.15.187.165/32",
  # "72.83.146.52/32",
  # "136.49.32.28/32",
  # "100.15.212.73/32",
  # "69.243.55.136/32",
  # "3.209.210.243/32",
  # "74.110.220.37/32",
  # "85.145.65.113/32",
  # "159.235.8.204/32",
  # "108.31.73.15/32",
  # "44.213.72.188/32",
  # "35.172.124.179/32",
  # "173.73.216.40/32",
  # "141.142.146.0/24",
  # "70.106.251.216/32",
  # "130.11.41.115/32",
  # "192.5.18.7/32",
  # "107.140.126.166/32",
]

# Whitelist for IPv6 if any
sg_whitelist_cidr_blocks_v6 = [
  "::/0",
]
