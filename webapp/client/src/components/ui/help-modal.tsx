import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import RemixIcon from "./remixicon";

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function HelpModal({ isOpen, onClose }: HelpModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="text-lg font-semibold flex items-center">
            Help & Documentation
          </DialogTitle>
        </DialogHeader>

        <ScrollArea className="h-[60vh]">
          <div className="space-y-6 p-2">
            <div>
              <h3 className="text-md font-medium text-neutral-800 mb-2">
                Getting Started
              </h3>
              <p className="text-neutral-600 text-sm">
                InfraBot is an AI-powered tool that helps you create AWS infrastructure using natural language. Here's how to use it:
              </p>
            </div>

            <div>
              <h3 className="text-md font-medium text-neutral-800 mb-2">
                Managing Projects
              </h3>
              <ul className="list-disc pl-5 text-sm text-neutral-600 space-y-2">
                <li>Set the parent directory where your projects will be stored</li>
                <li>Create a new project by entering a name and clicking "Create Project"</li>
                <li>Select existing projects from the sidebar to work with them</li>
              </ul>
            </div>

            <div>
              <h3 className="text-md font-medium text-neutral-800 mb-2">
                Working with the AI Agent
              </h3>
              <ul className="list-disc pl-5 text-sm text-neutral-600 space-y-2">
                <li>Type your infrastructure request in natural language</li>
                <li>The agent will create the appropriate Terraform code based on your description</li>
                <li>Review the generated infrastructure in the main area</li>
              </ul>
            </div>

            <div>
              <h3 className="text-md font-medium text-neutral-800 mb-2">
                Example Prompts
              </h3>
              <div className="bg-neutral-50 p-3 rounded-md border border-neutral-200 space-y-2 text-sm">
                <p>"Create an S3 bucket with versioning enabled"</p>
                <p>"Set up an EC2 instance with a security group allowing SSH access"</p>
                <p>"Create a VPC with public and private subnets"</p>
                <p>"Deploy a Lambda function that processes S3 events"</p>
              </div>
            </div>
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button onClick={onClose}>Got it</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
