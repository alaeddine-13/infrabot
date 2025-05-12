import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import RemixIcon from "../ui/remixicon";
import { useInfrabot } from "@/hooks/useInfrabot";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useProject } from "@/context/ProjectContext";
import { ErrorDisplay } from "@/components/ErrorDisplay";
import { useState } from "react";

export default function MainContent() {
  const { componentOutput } = useInfrabot();
  const { currentProject } = useProject();
  const [error, setError] = useState<Error | null>(null);

  // Empty state when no project is selected or no component has been created
  if (!currentProject || !componentOutput) {
    return (
      <div className="flex-1 overflow-auto p-4 bg-neutral-50">
        {error && <ErrorDisplay error={error} onDismiss={() => setError(null)} />}
        <div className="h-full flex flex-col items-center justify-center text-neutral-400">
          <div className="w-20 h-20 mb-4">
            <RemixIcon name="cloud-line" className="text-6xl" />
          </div>
          <h3 className="text-lg font-medium mb-2">
            No Infrastructure Visualized
          </h3>
          <p className="text-sm text-center max-w-md">
            {!currentProject
              ? "Select a project from the sidebar to get started."
              : "Use the chat to create infrastructure components."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-4 bg-neutral-50">
      {error && <ErrorDisplay error={error} onDismiss={() => setError(null)} />}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-medium text-neutral-800">
            Infrastructure Components
          </h2>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              className="flex items-center text-neutral-700"
              onClick={() => {
                try {
                  // Add refresh logic here
                } catch (err) {
                  setError(err instanceof Error ? err : new Error('Failed to refresh'));
                }
              }}
            >
              <RemixIcon name="refresh-line" className="mr-1" /> Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex items-center text-neutral-700"
              onClick={() => {
                try {
                  // Add export logic here
                } catch (err) {
                  setError(err instanceof Error ? err : new Error('Failed to export'));
                }
              }}
            >
              <RemixIcon name="download-line" className="mr-1" /> Export
            </Button>
          </div>
        </div>

        <Card>
          <Tabs defaultValue="output">
            <div className="border-b px-4">
              <TabsList className="border-0">
                <TabsTrigger value="output">Output</TabsTrigger>
                <TabsTrigger value="terraform">Terraform Code</TabsTrigger>
                <TabsTrigger value="diagram">Diagram</TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="output" className="p-4">
              {renderComponentOutput()}
            </TabsContent>

            <TabsContent value="terraform" className="p-4">
              {componentOutput?.terraform_code ? (
                <div className="bg-neutral-50 rounded-md p-4 border border-neutral-200 font-mono text-sm text-neutral-800 max-h-[500px] overflow-y-auto">
                  <pre className="whitespace-pre-wrap">{componentOutput.terraform_code}</pre>
                </div>
              ) : (
                <Alert>
                  <AlertDescription>No Terraform code available.</AlertDescription>
                </Alert>
              )}
            </TabsContent>

            <TabsContent value="diagram" className="p-4">
              {componentOutput?.diagram ? (
                <div className="flex justify-center items-center">
                  <img 
                    src={`data:image/jpeg;base64,${componentOutput.diagram}`}
                    alt="Infrastructure Diagram"
                    className="max-w-full h-auto rounded-lg shadow-lg"
                  />
                </div>
              ) : (
                <Alert>
                  <AlertDescription>No infrastructure diagram available.</AlertDescription>
                </Alert>
              )}
            </TabsContent>
          </Tabs>
        </Card>
      </div>
    </div>
  );

  function renderComponentOutput() {
    if (!componentOutput) {
      return (
        <Alert>
          <AlertDescription>
            No output available. Use the agent to create infrastructure components.
          </AlertDescription>
        </Alert>
      );
    }

    return (
      <div className="bg-neutral-50 rounded-md p-4 border border-neutral-200 font-mono text-sm text-neutral-800 max-h-[500px] overflow-y-auto">
        <h3 className="text-sm font-medium mb-3">
          Component: {componentOutput.component_name}
        </h3>

        {componentOutput.error_message && (
          <div className="mb-4 p-2 bg-red-50 border border-red-100 rounded text-red-700 text-xs">
            <strong>Error:</strong> {componentOutput.error_message}
          </div>
        )}

        {componentOutput.plan_summary && (
          <div className="mb-4 p-2 bg-blue-50 border border-blue-100 rounded text-blue-700 text-xs">
            <strong>Plan Summary:</strong> {componentOutput.plan_summary}
          </div>
        )}

        {componentOutput.formatted_outputs && (
          <div className="mb-4 p-2 bg-green-50 border border-green-100 rounded text-green-700 text-xs">
            <strong>Formatted Outputs:</strong>
            <div className="mt-1 whitespace-pre-wrap">{componentOutput.formatted_outputs}</div>
          </div>
        )}

        {componentOutput.outputs && Object.keys(componentOutput.outputs).length > 0 && (
          <div className="w-full overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-neutral-100">
                  <th className="text-left py-2 px-3 border border-neutral-200">Output</th>
                  <th className="text-left py-2 px-3 border border-neutral-200">Value</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(componentOutput.outputs).map(([key, value]) => (
                  <tr key={key} className="border-b border-neutral-200">
                    <td className="py-2 px-3 border border-neutral-200 font-medium">{key}</td>
                    <td className="py-2 px-3 border border-neutral-200 font-mono">{renderOutputValue(value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  }

  // Utility to render output values nicely
  function renderOutputValue(value: any): JSX.Element | string {
    if (
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean" ||
      value === null
    ) {
      return String(value);
    }
    // Pretty-print objects/arrays as JSON
    return <pre style={{ margin: 0 }}>{JSON.stringify(value, null, 2)}</pre>;
  }
}
