# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

terraform {
  required_version = ">= 1.5.0"
  backend "gcs" {
    bucket = "opsta-k8s-agent-15-tf"
    prefix = "terraform/cicd/state"
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.18.0"
    }
    github = {
      source  = "integrations/github"
      version = "6.5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.7.1"
    }
  }
}

provider "google" {
  alias                 = "staging_billing_override"
  billing_project       = var.staging_project_id
  region                = var.region
  user_project_override = true
}

provider "google" {
  alias                 = "prod_billing_override"
  billing_project       = var.prod_project_id
  region                = var.region
  user_project_override = true
}
