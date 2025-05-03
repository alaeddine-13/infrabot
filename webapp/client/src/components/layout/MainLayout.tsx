import { useState } from "react";
import LeftSidebar from "./LeftSidebar";
import RightSidebar from "./RightSidebar";
import MainContent from "./MainContent";
import { Button } from "@/components/ui/button";
import RemixIcon from "@/components/ui/remixicon";
import HelpModal from "../ui/help-modal";
import { useProject } from "@/context/ProjectContext";

export default function MainLayout() {
  const [isLeftSidebarCollapsed, setIsLeftSidebarCollapsed] = useState(false);
  const [isRightSidebarCollapsed, setIsRightSidebarCollapsed] = useState(false);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);
  const { currentProject } = useProject();

  return (
    <div className="flex h-screen overflow-hidden bg-neutral-50">
      {/* Left sidebar */}
      <div
        className={`transition-all duration-300 ease-in-out border-r border-neutral-200 bg-white flex flex-col h-full ${
          isLeftSidebarCollapsed ? "w-0 overflow-hidden" : "w-64"
        }`}
      >
        <LeftSidebar onCollapse={() => setIsLeftSidebarCollapsed(true)} />
      </div>

      {/* Expand left sidebar button */}
      {isLeftSidebarCollapsed && (
        <div
          className="absolute left-0 top-1/2 transform -translate-y-1/2 bg-white border border-neutral-200 rounded-r-md p-2 shadow-sm cursor-pointer z-10"
          onClick={() => setIsLeftSidebarCollapsed(false)}
        >
          <RemixIcon
            name="arrow-right-s-line"
            className="text-neutral-500 hover:text-primary-500"
          />
        </div>
      )}

      {/* Main content area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Toolbar */}
        <div className="bg-white border-b border-neutral-200 p-3 flex justify-between items-center">
          <div className="flex items-center">
            <span className="text-sm font-medium text-neutral-600">
              <RemixIcon name="folder-line" className="mr-1" />
              {currentProject
                ? currentProject.split("/").pop()
                : "No project selected"}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="icon"
              className="text-neutral-500 hover:text-primary-500 rounded-full hover:bg-neutral-100"
            >
              <RemixIcon name="settings-4-line" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-neutral-500 hover:text-primary-500 rounded-full hover:bg-neutral-100"
              onClick={() => setIsHelpModalOpen(true)}
            >
              <RemixIcon name="question-line" />
            </Button>
          </div>
        </div>

        <MainContent />
      </div>

      {/* Right sidebar */}
      <div
        className={`transition-all duration-300 ease-in-out border-l border-neutral-200 bg-white flex flex-col h-full ${
          isRightSidebarCollapsed ? "w-0 overflow-hidden" : "w-80"
        }`}
      >
        <RightSidebar onCollapse={() => setIsRightSidebarCollapsed(true)} />
      </div>

      {/* Expand right sidebar button */}
      {isRightSidebarCollapsed && (
        <div
          className="absolute right-0 top-1/2 transform -translate-y-1/2 bg-white border border-neutral-200 rounded-l-md p-2 shadow-sm cursor-pointer z-10"
          onClick={() => setIsRightSidebarCollapsed(false)}
        >
          <RemixIcon
            name="arrow-left-s-line"
            className="text-neutral-500 hover:text-primary-500"
          />
        </div>
      )}

      {/* Help modal */}
      <HelpModal isOpen={isHelpModalOpen} onClose={() => setIsHelpModalOpen(false)} />
    </div>
  );
}
