import { useState } from "react";
import { infrabotApi, CreateComponentResponse } from "@/lib/api";
import { useProject } from "@/context/ProjectContext";

export function useInfrabot() {
  const [isLoading, setIsLoading] = useState(false);
  const [componentOutput, setComponentOutput] = useState<CreateComponentResponse | null>(null);
  const { currentProject } = useProject();

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

      setComponentOutput(response);
      return response;
    } catch (error) {
      console.error("Error creating component:", error);
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
