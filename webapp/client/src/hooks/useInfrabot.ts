import { useEffect, useState } from "react";
import { infrabotApi, CreateComponentResponse } from "@/lib/api";
import { useProject } from "@/context/ProjectContext";

// Shared state for component output
let sharedComponentOutput: CreateComponentResponse | null = null;
const listeners: Set<(output: CreateComponentResponse | null) => void> = new Set();

export function useInfrabot() {
  const [isLoading, setIsLoading] = useState(false);
  const [componentOutput, setComponentOutput] = useState<CreateComponentResponse | null>(sharedComponentOutput);
  const { currentProject } = useProject();

  // Subscribe to shared state changes
  useEffect(() => {
    const listener = (output: CreateComponentResponse | null) => {
      setComponentOutput(output);
    };
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  }, []);

  const createComponent = async (prompt: string) => {
    try {
      setIsLoading(true);

      if (!currentProject) {
        throw new Error("No project selected");
      }

      const response = await infrabotApi.createComponent({
        prompt,
        workdir: currentProject,
        self_healing: true, // Enable self-healing by default
      });

      // Update shared state
      sharedComponentOutput = response;
      // Notify all listeners
      listeners.forEach(listener => listener(response));

      return response;
    } catch (error) {
      console.error("Error creating component:", error);
      // Update shared state with error
      const errorResponse: CreateComponentResponse = {
        success: false,
        error_message: error instanceof Error ? error.message : 'An unexpected error occurred',
        component_name: '',
        terraform_code: '',
        plan_summary: '',
        outputs: {}
      };
      sharedComponentOutput = errorResponse;
      listeners.forEach(listener => listener(errorResponse));
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    componentOutput,
    createComponent,
  };
}
