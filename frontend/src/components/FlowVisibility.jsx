import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useApiLogs, useAgentOutput, useCurrentSession, useAgentActions } from '../store/agentStore';
import { ChevronDown, ChevronRight, Activity, Send, CheckCircle, AlertCircle, Clock, Filter, Download, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

const FlowVisibility = ({ className = '' }) => {
  const [expandedLogs, setExpandedLogs] = useState(new Set());
  const [filter, setFilter] = useState('all');
  const [agentFilter, setAgentFilter] = useState('all');
  const scrollRef = useRef(null);
  
  const currentSession = useCurrentSession();
  const agentActions = useAgentActions();
  const logs = useApiLogs({ sessionId: currentSession });
  const sessionOutputs = agentActions.getCurrentSessionOutputs();
  
  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);
  
  const toggleLogExpansion = (logId) => {
    setExpandedLogs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(logId)) {
        newSet.delete(logId);
      } else {
        newSet.add(logId);
      }
      return newSet;
    });
  };
  
  const getStatusIcon = (log) => {
    if (log.type === 'request') {
      return <Send className="w-4 h-4 text-blue-500" />;
    }
    if (log.error) {
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
    return <CheckCircle className="w-4 h-4 text-green-500" />;
  };
  
  const getAgentFromUrl = (url) => {
    if (!url) return null;
    const match = url.match(/\/api\/agents\/([^/]+)/);
    return match ? match[1] : null;
  };
  
  const filteredLogs = logs.filter(log => {
    if (filter === 'errors' && !log.error) return false;
    if (filter === 'agents' && !log.url?.includes('/api/agents/')) return false;
    
    if (agentFilter !== 'all') {
      const agent = getAgentFromUrl(log.url);
      if (agent !== agentFilter) return false;
    }
    
    return true;
  });
  
  const exportLogs = () => {
    const exportData = {
      session: currentSession,
      timestamp: new Date().toISOString(),
      logs: filteredLogs,
      outputs: sessionOutputs,
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-flow-${currentSession}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  const clearLogs = () => {
    if (window.confirm('Are you sure you want to clear all logs?')) {
      agentActions.clearAllLogs();
    }
  };
  
  return (
    <Card className={`${className} h-full flex flex-col`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Flow Visibility Dashboard
            </CardTitle>
            <CardDescription>
              Real-time agent communication and data flow
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={exportLogs}
              className="flex items-center gap-1"
            >
              <Download className="w-4 h-4" />
              Export
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={clearLogs}
              className="flex items-center gap-1 text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-4 h-4" />
              Clear
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 p-0">
        <Tabs defaultValue="logs" className="h-full flex flex-col">
          <div className="px-4 pb-2">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="logs">API Logs</TabsTrigger>
              <TabsTrigger value="outputs">Agent Outputs</TabsTrigger>
              <TabsTrigger value="flow">Data Flow</TabsTrigger>
            </TabsList>
          </div>
          
          <TabsContent value="logs" className="flex-1 px-4 pb-4 mt-0">
            <div className="flex gap-2 mb-3">
              <Select value={filter} onValueChange={setFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Logs</SelectItem>
                  <SelectItem value="agents">Agent Calls</SelectItem>
                  <SelectItem value="errors">Errors Only</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={agentFilter} onValueChange={setAgentFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Agents</SelectItem>
                  <SelectItem value="content_writer">Content Writer</SelectItem>
                  <SelectItem value="social_publisher">Social Publisher</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <ScrollArea className="h-[400px]" ref={scrollRef}>
              <div className="space-y-2">
                <AnimatePresence>
                  {filteredLogs.map((log) => {
                    const isExpanded = expandedLogs.has(log.id);
                    const agent = getAgentFromUrl(log.url);
                    
                    return (
                      <motion.div
                        key={log.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="border rounded-lg p-3 bg-card hover:bg-accent/50 transition-colors cursor-pointer"
                        onClick={() => toggleLogExpansion(log.id)}
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5">
                            {getStatusIcon(log)}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-mono text-xs text-muted-foreground">
                                {log.method || 'RESPONSE'}
                              </span>
                              <span className="text-sm truncate">
                                {log.url || 'N/A'}
                              </span>
                              {agent && (
                                <Badge variant="secondary" className="text-xs">
                                  {agent}
                                </Badge>
                              )}
                              {log.duration && (
                                <Badge variant="outline" className="text-xs">
                                  <Clock className="w-3 h-3 mr-1" />
                                  {log.duration}ms
                                </Badge>
                              )}
                            </div>
                            
                            <div className="text-xs text-muted-foreground">
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </div>
                            
                            {isExpanded && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="mt-3 space-y-2"
                              >
                                {log.payload && (
                                  <div>
                                    <span className="text-xs font-semibold">Request Payload:</span>
                                    <pre className="text-xs mt-1 p-2 bg-muted rounded overflow-x-auto">
                                      {JSON.stringify(log.payload, null, 2)}
                                    </pre>
                                  </div>
                                )}
                                
                                {log.data && (
                                  <div>
                                    <span className="text-xs font-semibold">Response Data:</span>
                                    <pre className="text-xs mt-1 p-2 bg-muted rounded overflow-x-auto max-h-[200px] overflow-y-auto">
                                      {JSON.stringify(
                                        log.data.output ? 
                                          { ...log.data, output: log.data.output.substring(0, 200) + '...' } : 
                                          log.data, 
                                        null, 
                                        2
                                      )}
                                    </pre>
                                  </div>
                                )}
                                
                                {log.error && (
                                  <div>
                                    <span className="text-xs font-semibold text-red-600">Error:</span>
                                    <p className="text-xs mt-1 text-red-600">{log.error}</p>
                                  </div>
                                )}
                              </motion.div>
                            )}
                          </div>
                          
                          <div className="mt-0.5">
                            {isExpanded ? 
                              <ChevronDown className="w-4 h-4 text-muted-foreground" /> : 
                              <ChevronRight className="w-4 h-4 text-muted-foreground" />
                            }
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="outputs" className="flex-1 px-4 pb-4 mt-0">
            <ScrollArea className="h-[450px]">
              <div className="space-y-3">
                {Object.entries(sessionOutputs).map(([agentId, output]) => (
                  <Card key={agentId} className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-semibold capitalize">
                          {agentId.replace(/_/g, ' ')}
                        </h4>
                        <p className="text-xs text-muted-foreground">
                          {new Date(output.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <Badge variant="success">Stored</Badge>
                    </div>
                    
                    <div className="mt-3">
                      <p className="text-sm font-medium mb-1">Output Preview:</p>
                      <div className="p-3 bg-muted rounded-md">
                        <p className="text-sm whitespace-pre-wrap">
                          {typeof output.output === 'string' ? 
                            output.output.substring(0, 300) + '...' : 
                            JSON.stringify(output.output, null, 2).substring(0, 300) + '...'
                          }
                        </p>
                      </div>
                    </div>
                    
                    {output.metadata && Object.keys(output.metadata).length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium mb-1">Metadata:</p>
                        <pre className="text-xs p-2 bg-muted rounded overflow-x-auto">
                          {JSON.stringify(output.metadata, null, 2)}
                        </pre>
                      </div>
                    )}
                  </Card>
                ))}
                
                {Object.keys(sessionOutputs).length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No agent outputs captured yet</p>
                    <p className="text-sm mt-1">Execute agents to see their outputs here</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="flow" className="flex-1 px-4 pb-4 mt-0">
            <div className="space-y-4">
              <Card className="p-4">
                <h4 className="font-semibold mb-3">Data Flow Visualization</h4>
                <div className="space-y-3">
                  {Object.entries(sessionOutputs).map(([agentId, output], index) => {
                    const isContentWriter = agentId === 'content_writer';
                    const isSocialPublisher = agentId === 'social_publisher';
                    
                    return (
                      <React.Fragment key={agentId}>
                        <div className="flex items-center gap-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <Badge variant={isContentWriter ? 'default' : 'secondary'}>
                                {agentId.replace(/_/g, ' ')}
                              </Badge>
                              <span className="text-sm text-muted-foreground">
                                {new Date(output.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            
                            {isContentWriter && (
                              <p className="text-sm mt-1 text-muted-foreground">
                                Generated content: "{output.output?.substring(0, 50)}..."
                              </p>
                            )}
                            
                            {isSocialPublisher && (
                              <p className="text-sm mt-1 text-muted-foreground">
                                Posted to Instagram with content from Content Writer
                              </p>
                            )}
                          </div>
                        </div>
                        
                        {index < Object.keys(sessionOutputs).length - 1 && (
                          <div className="flex items-center justify-center">
                            <div className="w-0.5 h-8 bg-border" />
                            <ChevronDown className="w-4 h-4 text-muted-foreground -mt-2" />
                          </div>
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </Card>
              
              <Card className="p-4">
                <h4 className="font-semibold mb-3">Session Information</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Session ID:</span>
                    <span className="font-mono">{currentSession || 'No active session'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Total API Calls:</span>
                    <span>{logs.length}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Agent Outputs:</span>
                    <span>{Object.keys(sessionOutputs).length}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Errors:</span>
                    <span className="text-red-600">
                      {logs.filter(l => l.error).length}
                    </span>
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default FlowVisibility;