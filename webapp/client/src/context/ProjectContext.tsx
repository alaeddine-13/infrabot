import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { infrabotApi } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface ProjectContextProps {
  parentDir: string;
  setParentDir: (dir: string) => void;
  projects: string[];
  isLoading: boolean;
  currentProject: string | null;
  setCurrentProject: (project: string) => void;
  fetchProjects: () => Promise<void>;
  initProject: (name: string) => Promise<void>;
  isInitialized: boolean;
}

const ProjectContext = createContext<ProjectContextProps | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [parentDir, setParentDir] = useState<string>("./");
  const [projects, setProjects] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [currentProject, setCurrentProject] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState<boolean>(false);
  const { toast } = useToast();

  // Fetch projects on initial load and when parentDir changes
  useEffect(() => {
    fetchProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchProjects = async () => {
    try {
      setIsLoading(true);
      const response = await infrabotApi.listProjects(parentDir);
      setProjects(response.projects);
      setIsInitialized(true);
    } catch (error) {
      console.error("Error fetching projects:", error);
      toast({
        title: "Failed to fetch projects",
        description: "Please check the parent directory and try again",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const initProject = async (name: string) => {
    try {
      setIsLoading(true);
      const response = await infrabotApi.initProject(name, parentDir);

      toast({
        title: "Project created",
        description: `${name} has been initialized successfully`,
      });

      // Refresh project list
      await fetchProjects();

      // Set as current project
      setCurrentProject(response.workdir);

      return response;
    } catch (error) {
      console.error("Error initializing project:", error);
      toast({
        title: "Failed to create project",
        description: "Please try again with a different name",
        variant: "destructive",
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ProjectContext.Provider
      value={{
        parentDir,
        setParentDir,
        projects,
        isLoading,
        currentProject,
        setCurrentProject,
        fetchProjects,
        initProject,
        isInitialized,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error("useProject must be used within a ProjectProvider");
  }
  return context;
}
