import { ReactNode } from "react";

interface AppLayoutProps {
  sidebar: ReactNode;
  header: ReactNode;
  chatArea: ReactNode;
  inputArea: ReactNode;
  rightPanel: ReactNode;
  isSidebarOpen: boolean;
  setIsSidebarOpen: (open: boolean) => void;
}

export function AppLayout({
  sidebar,
  header,
  chatArea,
  inputArea,
  rightPanel,
  isSidebarOpen,
  setIsSidebarOpen
}: AppLayoutProps) {
  return (
    <div className="fixed inset-0 flex h-full w-full bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-sans overflow-hidden">
      
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity duration-300"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar */}
      <div className="shrink-0 h-full z-50 md:z-auto md:relative absolute transition-all duration-300">
        {sidebar}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full relative bg-slate-50/50 dark:bg-slate-900 transition-all duration-300">
        
        {/* Header */}
        <div className="shrink-0 z-20 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-700">
            {header}
        </div>

        {/* Content Container (Chat + Right Panel) */}
        <div className="flex-1 flex flex-row min-h-0 relative"> 
            
            {/* Chat Column */}
            <div className="flex-1 flex flex-col h-full relative min-w-0">
                
                {/* Scrollable Messages Area */}
                <div className="flex-1 overflow-y-auto scroll-smooth min-h-0">
                    <div className="w-full max-w-3xl xl:max-w-4xl 2xl:max-w-5xl mx-auto px-4 sm:px-6 py-6 transition-all duration-300">
                        {chatArea}
                    </div>
                </div>

                {/* Input Area - Standard Flex Item (Not Floating) */}
                <div className="shrink-0 z-20 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 p-4">
                    <div className="w-full max-w-3xl xl:max-w-4xl 2xl:max-w-5xl mx-auto px-4 sm:px-6 transition-all duration-300">
                        {inputArea}
                    </div>
                </div>

            </div>

            {/* Right Panel (Knowledge) - Overlay/Drawer Mode */}
            <div className="absolute right-0 top-0 bottom-0 z-30 pointer-events-none">
                 {/* The panel content itself handles the slide-in/out and pointer-events */}
                 {rightPanel}
            </div>

        </div>
      </div>
    </div>
  );
}
