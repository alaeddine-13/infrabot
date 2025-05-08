import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import RemixIcon from "../ui/remixicon";
import { useProject } from "@/context/ProjectContext";
import { useToast } from "@/hooks/use-toast";
import { useInfrabot } from "@/hooks/useInfrabot";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

interface RightSidebarProps {
  onCollapse: () => void;
}

interface Message {
  id: string;
  content: string;
  sender: "user" | "agent";
  timestamp: Date;
}

// Utility to render output values nicely
function renderOutputValue(value: any): string {
  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean" ||
    value === null
  ) {
    return String(value);
  }
  // Pretty-print objects/arrays as JSON
  return `<pre style=\"margin:0;\">${JSON.stringify(value, null, 2)}</pre>`;
}

export default function RightSidebar({ onCollapse }: RightSidebarProps) {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      content: `Hi there! I'm your InfraBot assistant. I can help you create AWS infrastructure using natural language. Just tell me what you want to build, and I'll generate the Terraform code for you.

      Example: "Create an S3 bucket with versioning enabled" or "Set up an EC2 instance with a security group"`,
      sender: "agent",
      timestamp: new Date(),
    },
  ]);

  const { toast } = useToast();
  const { currentProject, isInitialized } = useProject();
  const { createComponent, isLoading } = useInfrabot();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim()) {
      toast({
        title: "Please enter a message",
        variant: "destructive",
      });
      return;
    }

    if (!currentProject) {
      toast({
        title: "Please select a project first",
        description: "Choose a project from the left sidebar",
        variant: "destructive",
      });
      return;
    }

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setMessage("");

    try {
      // Create component
      const result = await createComponent(message);

      // Format agent response
      let responseContent = `<p class="font-medium">Component created: ${result.component_name}</p>`;

      if (result.plan_summary) {
        responseContent += `<p class="mt-2">${result.plan_summary}</p>`;
      }

      if (result.outputs) {
        responseContent += '<p class="mt-2 font-medium">Outputs:</p>';
        responseContent += '<ul class="mt-1 space-y-1">';

        for (const [key, value] of Object.entries(result.outputs)) {
          responseContent += `<li><span class="font-medium">${key}:</span> ${renderOutputValue(value)}</li>`;
        }

        responseContent += '</ul>';
      }

      // Add agent response
      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: responseContent,
        sender: "agent",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, agentMessage]);

    } catch (error) {
      console.error("Error creating component:", error);

      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `<p class="text-destructive">Error: Failed to create component</p>`,
        sender: "agent",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);

      toast({
        title: "Error creating component",
        description: "Please try again with a different description",
        variant: "destructive",
      });
    }
  };

  // Auto-resize textarea as user types
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);

    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  };

  return (
    <>
      <div className="p-4 border-b border-neutral-200 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-primary-700 flex items-center">
          <RemixIcon name="robot-line" className="mr-2" />
          AI Agent
        </h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={onCollapse}
          className="text-neutral-500 hover:text-primary-500"
        >
          <RemixIcon name="arrow-right-s-line" />
        </Button>
      </div>

      {/* Chat messages area */}
      <ScrollArea className="flex-1">
        <ScrollBar orientation="horizontal" />
        <div className="space-y-4 p-4">
          {messages.map((msg) => (
            <div key={msg.id} className="flex items-start space-x-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.sender === "agent"
                    ? "bg-primary-100 text-primary-600"
                    : "bg-secondary-100 text-secondary-600"
                }`}
              >
                <RemixIcon name={msg.sender === "agent" ? "robot-line" : "user-line"} />
              </div>
              <div
                className={`rounded-lg p-3 text-sm overflow-x-auto whitespace-pre-wrap break-words ${
                  msg.sender === "agent" ? "bg-neutral-100" : "bg-primary-50"
                }`}
                style={{ minWidth: 0, maxWidth: 'calc(100% - 2rem)' }}
                dangerouslySetInnerHTML={{ __html: msg.content }}
              ></div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Chat input area */}
      <div className="p-3 border-t border-neutral-200">
        <form onSubmit={handleSendMessage} className="flex flex-col space-y-2">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            placeholder="Describe the infrastructure you want to create..."
            className="min-h-[80px] resize-none"
            rows={3}
          />
          <div className="flex justify-between items-center">
            <div className="flex items-center text-xs text-neutral-500">
              <RemixIcon name="information-line" className="mr-1" />
              <span>{isLoading ? "Processing..." : "Ready"}</span>
            </div>
            <Button
              type="submit"
              disabled={isLoading || !currentProject || !message.trim()}
              className="flex items-center"
            >
              <RemixIcon name="send-plane-fill" className="mr-1" /> Send
            </Button>
          </div>
        </form>
      </div>
    </>
  );
}
