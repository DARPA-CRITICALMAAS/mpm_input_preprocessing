
resource "aws_iam_instance_profile" "ec2_basic_profile" {
  name = "${lower(var.app_name)}-ec2-basic-profile"
  role = aws_iam_role.ec2_basic_role.name
}

resource "aws_iam_role" "ec2_basic_role" {
  name               = "${lower(var.app_name)}-ec2-basic-role"
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
    Name      = "${lower(var.app_name)}-ec2-basic-role"
    cost_code = var.app_cost_code
  }
}


# Attach the S3 read-only policy
resource "aws_iam_policy" "s3_readonly_policy" {
  name        = "${lower(var.app_name)}-s3-readonly-policy"
  description = "S3 read-only access for EC2 instances"
  policy      = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${var.aws_public_bucket_name}",        
        "arn:aws:s3:::${var.aws_public_bucket_name}/*" 
      ]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "attach_s3_readonly_policy" {
  role       = aws_iam_role.ec2_basic_role.name
  policy_arn = aws_iam_policy.s3_readonly_policy.arn
}
