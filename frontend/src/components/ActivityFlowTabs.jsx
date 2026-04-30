import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Activity, Terminal } from 'lucide-react';
import TerminalFeed from './TerminalFeed';
import FlowVisibility from './FlowVisibility';

const ActivityFlowTabs = ({ logs, className = '' }) => {
  const [activeTab, setActiveTab] = useState('live');

  return (
    <div className={`h-full flex flex-col ${className}`}>
      <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
        <div className="px-4 pt-4 pb-2 border-b border-white/5">
          <TabsList className="grid w-full grid-cols-2 bg-black/20 border border-white/10">
            <TabsTrigger 
              value="live" 
              className="flex items-center gap-2 data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-300 data-[state=active]:border-cyan-500/50"
            >
              <Terminal className="w-4 h-4" />
              Live
            </TabsTrigger>
            <TabsTrigger 
              value="logs" 
              className="flex items-center gap-2 data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-300 data-[state=active]:border-cyan-500/50"
            >
              <Activity className="w-4 h-4" />
              Logs
            </TabsTrigger>
          </TabsList>
        </div>
        
        <TabsContent value="live" className="flex-1 mt-0 p-0">
          <TerminalFeed logs={logs} />
        </TabsContent>
        
        <TabsContent value="logs" className="flex-1 mt-0 p-0">
          <FlowVisibility className="h-full" />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ActivityFlowTabs;