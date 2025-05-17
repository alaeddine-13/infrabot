provider "aws" {
  region = var.aws_region
}

provider "random" {}

variable "aws_region" {
  default = null
}
