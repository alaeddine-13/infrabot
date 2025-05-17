import { useEffect } from "react";
import MainLayout from "@/components/layout/MainLayout";
import { Helmet } from "react-helmet";
import { ProjectProvider } from "@/context/ProjectContext";

export default function Home() {
  // Add CDNs for Remix icons
  useEffect(() => {
    const link = document.createElement("link");
    link.href = "https://cdn.jsdelivr.net/npm/remixicon@2.5.0/fonts/remixicon.css";
    link.rel = "stylesheet";
    document.head.appendChild(link);

    return () => {
      document.head.removeChild(link);
    };
  }, []);

  return (
    <>
      <Helmet>
        <title>InfraBot - AI-powered Infrastructure Management</title>
        <meta name="description" content="Create, manage, and visualize AWS infrastructure using AI" />
      </Helmet>
      <ProjectProvider>
        <MainLayout />
      </ProjectProvider>
    </>
  );
}
