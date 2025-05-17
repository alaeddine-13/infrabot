import { apiRequest } from "./queryClient";

export interface InitProjectParams {
  workdir?: string;
  verbose?: boolean;
  local?: boolean;
}

export interface InitProjectResponse {
  success: boolean;
  message: string;
  workdir: string;
}

export interface CreateComponentParams {
  prompt: string;
  name?: string;
  model?: string;
  self_healing?: boolean;
  max_attempts?: number;
  keep_on_failure?: boolean;
  langfuse_session_id?: string | null;
  workdir?: string;
}

export interface CreateComponentResponse {
  success: boolean;
  error_message?: string;
  component_name: string;
  terraform_code: string;
  tfvars_code?: string;
  plan_summary: string;
  outputs: Record<string, string>;
  formatted_outputs?: string;
  self_healing_attempts?: number;
  fixed_errors?: string[];
  diagram?: string;
}

export interface ListProjectsResponse {
  success: boolean;
  message: string;
  projects: string[];
}

export const infrabotApi = {
  // Initialize a project
  async initProject(projectName: string, parentDir: string): Promise<InitProjectResponse> {
    const workdir = `${parentDir}/${projectName}`;
    const response = await apiRequest("POST", "/api/init", {
      workdir,
      verbose: true,
    });
    return response.json();
  },

  // Create a component
  async createComponent(params: CreateComponentParams): Promise<CreateComponentResponse> {
    const response = await apiRequest("POST", "/api/component/create", params);
    return response.json();
  },

  // List projects
  async listProjects(parentDir: string): Promise<ListProjectsResponse> {
    const url = `/api/projects?parent_dir=${encodeURIComponent(parentDir)}`;
    const response = await fetch(url, {
      credentials: "include",
    });
    
    if (!response.ok) {
      throw new Error(`Failed to list projects: ${response.statusText}`);
    }
    
    return response.json();
  },
};
