provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = null
}
