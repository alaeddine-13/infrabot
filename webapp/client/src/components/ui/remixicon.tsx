import React from "react";

export type IconName =
  | "cloud-line"
  | "arrow-left-s-line"
  | "arrow-right-s-line"
  | "save-line"
  | "refresh-line"
  | "add-line"
  | "folder-line"
  | "folder-open-line"
  | "settings-4-line"
  | "question-line"
  | "download-line"
  | "robot-line"
  | "send-plane-fill"
  | "information-line"
  | "close-line"
  | "more-2-fill"
  | "user-line"
  | "checkbox-circle-line"
  | "error-warning-line"
  | "alert-line";

interface IconProps {
  name: IconName;
  className?: string;
}

export const RemixIcon: React.FC<IconProps> = ({ name, className = "" }) => {
  // We're not using an SVG sprite but adding the classname that loads the icon from the CDN
  const iconClass = `ri-${name} ${className}`;
  return <i className={iconClass}></i>;
};

export default RemixIcon;
