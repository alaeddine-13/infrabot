import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import RemixIcon from "../ui/remixicon";
import { useProject } from "@/context/ProjectContext";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";

interface LeftSidebarProps {
  onCollapse: () => void;
}

export default function LeftSidebar({ onCollapse }: LeftSidebarProps) {
  const [newProjectName, setNewProjectName] = useState("");
  const { toast } = useToast();

  const {
    parentDir,
    setParentDir,
    projects,
    isLoading,
    fetchProjects,
    initProject,
    setCurrentProject,
    currentProject,
  } = useProject();

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) {
      toast({
        title: "Please enter a project name",
        variant: "destructive"
      });
      return;
    }

    try {
      await initProject(newProjectName);
      setNewProjectName("");
    } catch (error) {
      console.error("Error creating project:", error);
    }
  };

  const handleUpdateParentDir = async () => {
    if (!parentDir.trim()) {
      toast({
        title: "Please enter a valid directory path",
        variant: "destructive"
      });
      return;
    }

    setParentDir(parentDir);
    await fetchProjects();
    toast({
      title: "Parent directory updated",
      description: `Directory set to: ${parentDir}`
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleCreateProject();
    }
  };

  return (
    <>
      <div className="p-4 border-b border-neutral-200 flex justify-between items-center">
        <h1 className="text-lg font-semibold text-primary-700 flex items-center">
          <RemixIcon name="cloud-line" className="mr-2" />
          InfraBot
        </h1>
        <Button
          variant="ghost"
          size="icon"
          onClick={onCollapse}
          className="text-neutral-500 hover:text-primary-500"
        >
          <RemixIcon name="arrow-left-s-line" />
        </Button>
      </div>

      {/* Parent path configuration */}
      <div className="p-4 border-b border-neutral-200">
        <h2 className="text-sm font-medium text-neutral-800 mb-2">Parent Directory</h2>
        <div className="flex">
          <Input
            value={parentDir}
            onChange={(e) => setParentDir(e.target.value)}
            placeholder="Directory path"
            className="rounded-r-none"
          />
          <Button
            onClick={handleUpdateParentDir}
            className="rounded-l-none"
            variant="default"
          >
            <RemixIcon name="save-line" />
          </Button>
        </div>
      </div>

      {/* Projects section */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-sm font-medium text-neutral-800">Projects</h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={fetchProjects}
              className="text-primary-500 hover:text-primary-700 transition-colors"
              title="Refresh projects"
            >
              <RemixIcon name="refresh-line" />
            </Button>
          </div>

          {/* Projects list */}
          <div className="space-y-2 mb-6">
            {isLoading ? (
              <div className="animate-pulse space-y-2 py-1">
                <div className="h-4 bg-neutral-200 rounded w-3/4"></div>
                <div className="h-4 bg-neutral-200 rounded w-full"></div>
                <div className="h-4 bg-neutral-200 rounded w-5/6"></div>
              </div>
            ) : projects.length === 0 ? (
              <p className="text-sm text-neutral-500 italic">No projects found. Create a new one to get started.</p>
            ) : (
              projects.map((project) => {
                const projectName = project.split("/").pop() || "";
                const isActive = currentProject === project;

                return (
                  <div
                    key={project}
                    className={`cursor-pointer border rounded-md p-2 transition-colors ${
                      isActive
                        ? "bg-primary-50 border-primary-100"
                        : "border-neutral-200 hover:bg-neutral-50"
                    }`}
                    onClick={() => setCurrentProject(project)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <RemixIcon
                          name={isActive ? "folder-open-line" : "folder-line"}
                          className={`mr-2 ${isActive ? "text-primary-500" : "text-neutral-500"}`}
                        />
                        <span className={`text-sm font-medium ${
                          isActive ? "text-primary-600" : "text-neutral-700"
                        }`}>
                          {projectName}
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-neutral-500 mt-1 truncate" key={project}>
                      
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <Separator className="my-4" />

          {/* Create new project */}
          <div className="mt-4">
            <h3 className="text-xs font-medium text-neutral-600 mb-2">
              Create New Project
            </h3>
            <div className="flex flex-col space-y-2">
              <Input
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Project name"
              />
              <Button
                onClick={handleCreateProject}
                className="w-full"
              >
                <RemixIcon name="add-line" className="mr-1" /> Create Project
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Left sidebar footer */}
      <div className="p-3 border-t border-neutral-200 bg-neutral-50">
        <div className="flex items-center text-xs text-neutral-500">
          <RemixIcon name="information-line" className="mr-1" />
          <span>
            {isLoading
              ? "Loading projects..."
              : `${projects.length} project${projects.length !== 1 ? "s" : ""} found`}
          </span>
        </div>
      </div>
    </>
  );
}
