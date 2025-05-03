import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import fetch from 'node-fetch';

// InfraBot API URL
const INFRABOT_API_URL = process.env.INFRABOT_API_URL || "http://localhost:8000";

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

      try {
        // Call the InfraBot API to initialize a project
        const response = await fetch(`${INFRABOT_API_URL}/init`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            workdir,
            verbose: verbose || false,
            local: local || false
          }),
        });

        if (!response.ok) {
          throw new Error(`InfraBot API returned status: ${response.status}`);
        }

        const data = await response.json();
        return res.json(data);
      } catch (error: unknown) {
        const apiError = error as Error;
        console.error("Error calling InfraBot API:", apiError);
        return res.status(502).json({
          success: false,
          message: "Failed to initialize project via InfraBot API",
          error: apiError.message
        });
      }
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
        model = "perplexity/sonar-pro",
        self_healing = false,
        max_attempts = 3,
        keep_on_failure = true,
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

      try {
        // Call the InfraBot API to create a component
        const response = await fetch(`${INFRABOT_API_URL}/component/create`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            prompt,
            name,
            model,
            self_healing,
            max_attempts,
            keep_on_failure,
            langfuse_session_id,
            workdir
          }),
        });

        if (!response.ok) {
          throw new Error(`InfraBot API returned status: ${response.status}`);
        }

        const data = await response.json();
        return res.json(data);
      } catch (error: unknown) {
        const apiError = error as Error;
        console.error("Error calling InfraBot API:", apiError);
        return res.status(502).json({
          success: false,
          message: "Failed to create component via InfraBot API",
          error: apiError.message
        });
      }
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

      try {
        // Call the InfraBot API to list projects
        const response = await fetch(`${INFRABOT_API_URL}/projects?parent_dir=${encodeURIComponent(parentDir)}`);

        if (!response.ok) {
          throw new Error(`InfraBot API returned status: ${response.status}`);
        }

        const data = await response.json();
        return res.json(data);
      } catch (error: unknown) {
        const apiError = error as Error;
        console.error("Error calling InfraBot API:", apiError);
        return res.status(502).json({
          success: false,
          message: "Failed to retrieve projects from InfraBot API",
          error: apiError.message
        });
      }
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
