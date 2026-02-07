import { ModeToggle } from "@/components/apx/mode-toggle";
import Logo from "@/components/apx/logo";
import { ReactNode } from "react";

interface NavbarProps {
  leftContent?: ReactNode;
  rightContent?: ReactNode;
}

export function Navbar({ leftContent, rightContent }: NavbarProps) {
  return (
    <header className="z-50 bg-background/85 backdrop-blur-md border-b transition-colors duration-200">
      <div className="h-16 flex items-center justify-between px-4 md:px-6">
        {leftContent || <Logo />}
        <div className="flex-1" />
        {rightContent || <ModeToggle />}
      </div>
    </header>
  );
}

export default Navbar;
