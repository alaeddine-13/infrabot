import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";

export async function registerRoutes(app: Express): Promise<Server> {
  // prefix all routes with /api
  const apiPrefix = "/api";

  // Initialize a project
  app.post(`${apiPrefix}/init`, async (req, res) => {
    try {
      const { workdir, verbose, local } = req.body;

      // Validation
      if (!workdir) {
        return res.status(400).json({
          success: false,
          message: "workdir is required"
        });
      }

      // Here we would normally call the InfraBot service
      // For now, we'll simulate the response

      return res.json({
        success: true,
        message: "Project initialized successfully",
        workdir
      });
    } catch (error) {
      console.error("Error initializing project:", error);
      return res.status(500).json({
        success: false,
        message: "Failed to initialize project"
      });
    }
  });

  // Create an infrastructure component
  app.post(`${apiPrefix}/component/create`, async (req, res) => {
    try {
      const {
        prompt,
        name = "main",
        model = "gpt-4o",
        self_healing = false,
        max_attempts = 3,
        keep_on_failure = false,
        langfuse_session_id = null,
        workdir
      } = req.body;

      // Validation
      if (!prompt) {
        return res.status(400).json({
          success: false,
          error_message: "prompt is required"
        });
      }

      if (!workdir) {
        return res.status(400).json({
          success: false,
          error_message: "workdir is required"
        });
      }

      // Here we would normally call the InfraBot service
      // For now, we'll simulate a response based on the prompt

      let response;
      if (prompt.toLowerCase().includes("s3") || prompt.toLowerCase().includes("bucket")) {
        response = {
          success: true,
          error_message: "",
          component_name: name || "s3-bucket",
          terraform_code: 'resource "aws_s3_bucket" "example" {\n  bucket = "my-example-bucket"\n  tags = {\n    Name = "My bucket"\n    Environment = "Dev"\n  }\n}\n\nresource "aws_s3_bucket_versioning" "versioning" {\n  bucket = aws_s3_bucket.example.id\n  versioning_configuration {\n    status = "Enabled"\n  }\n}',
          tfvars_code: 'bucket_name = "my-example-bucket"',
          plan_summary: "2 resources to add, 0 to change, 0 to destroy",
          outputs: {
            bucket_name: "my-example-bucket",
            bucket_arn: "arn:aws:s3:::my-example-bucket"
          },
          self_healing_attempts: 0,
          fixed_errors: []
        };
      } else if (prompt.toLowerCase().includes("ec2") || prompt.toLowerCase().includes("instance")) {
        response = {
          success: true,
          error_message: "",
          component_name: name || "ec2-instance",
          terraform_code: 'resource "aws_instance" "web" {\n  ami           = "ami-0c55b159cbfafe1f0"\n  instance_type = "t2.micro"\n  tags = {\n    Name = "WebServer"\n  }\n}\n\nresource "aws_security_group" "web" {\n  name        = "web-sg"\n  description = "Allow web and SSH traffic"\n\n  ingress {\n    from_port   = 80\n    to_port     = 80\n    protocol    = "tcp"\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n\n  ingress {\n    from_port   = 22\n    to_port     = 22\n    protocol    = "tcp"\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n\n  egress {\n    from_port   = 0\n    to_port     = 0\n    protocol    = "-1"\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n}',
          tfvars_code: 'instance_type = "t2.micro"\nami_id = "ami-0c55b159cbfafe1f0"',
          plan_summary: "2 resources to add, 0 to change, 0 to destroy",
          outputs: {
            instance_id: "i-0123456789abcdef0",
            public_ip: "54.12.34.56"
          },
          self_healing_attempts: 0,
          fixed_errors: []
        };
      } else {
        response = {
          success: true,
          error_message: "",
          component_name: name,
          terraform_code: `# Terraform configuration for: ${prompt}\n# This is a placeholder, replace with actual implementation`,
          tfvars_code: "",
          plan_summary: "Resources to be determined",
          outputs: {
            status: "Component placeholder created"
          },
          self_healing_attempts: 0,
          fixed_errors: []
        };
      }

      return res.json(response);
    } catch (error) {
      console.error("Error creating component:", error);
      return res.status(500).json({
        success: false,
        error_message: "Failed to create component"
      });
    }
  });

  // List projects
  app.get(`${apiPrefix}/projects`, async (req, res) => {
    try {
      const parentDir = req.query.parent_dir as string || ".";

      // Here we would normally call the InfraBot service
      // For now, we'll simulate a response with some mock projects

      const mockProjects = [
        `${parentDir}/production-infra`,
        `${parentDir}/staging-infra`,
        `${parentDir}/development-infra`
      ];

      return res.json({
        success: true,
        message: `Found ${mockProjects.length} InfraBot projects`,
        projects: mockProjects
      });
    } catch (error) {
      console.error("Error listing projects:", error);
      return res.status(500).json({
        success: false,
        message: "Failed to list projects"
      });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
