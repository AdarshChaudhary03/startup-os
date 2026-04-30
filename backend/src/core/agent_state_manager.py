"""Agent State Management System

This module provides a centralized state management system for storing and retrieving
agent outputs. It ensures proper data persistence between different agents in the
orchestration pipeline.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid
from enum import Enum
import asyncio
from threading import Lock


class StateType(Enum):
    """Types of state data that can be stored"""
    AGENT_OUTPUT = "agent_output"
    ORCHESTRATION_CONTEXT = "orchestration_context"
    SESSION_DATA = "session_data"
    INTERMEDIATE_RESULT = "intermediate_result"


class AgentStateManager:
    """Manages state storage and retrieval for agent outputs"""
    
    def __init__(self, storage_path: str = "./agent_states"):
        self.storage_path = storage_path
        self.logger = logging.getLogger(__name__)
        self._state_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        self.logger.info(f"AgentStateManager initialized with storage path: {self.storage_path}")
    
    def save_agent_output(
        self,
        session_id: str,
        agent_id: str,
        output: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save agent output to state storage
        
        Args:
            session_id: The orchestration session ID
            agent_id: The agent that produced the output
            output: The actual output data from the agent
            metadata: Additional metadata about the output
            
        Returns:
            state_id: Unique identifier for the saved state
        """
        state_id = f"{session_id}_{agent_id}_{uuid.uuid4().hex[:8]}"
        
        state_data = {
            "state_id": state_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "output": output,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_type": StateType.AGENT_OUTPUT.value
        }
        
        # Save to cache and disk
        with self._lock:
            # Update cache
            if session_id not in self._state_cache:
                self._state_cache[session_id] = {}
            self._state_cache[session_id][agent_id] = state_data
            
            # Persist to disk
            self._persist_state(session_id, state_data)
        
        # Enhanced logging for debugging
        output_preview = str(output)[:200] + "..." if len(str(output)) > 200 else str(output)
        self.logger.info(f"[STATE_DEBUG] Saved agent output - Session: {session_id}, Agent: {agent_id}, State ID: {state_id}")
        self.logger.debug(f"[STATE_DEBUG] Output preview: {output_preview}")
        self.logger.debug(f"[STATE_DEBUG] Metadata: {metadata}")
        return state_id
    
    def get_agent_output(
        self,
        session_id: str,
        agent_id: str,
        include_metadata: bool = False
    ) -> Optional[Any]:
        """Retrieve agent output from state storage
        
        Args:
            session_id: The orchestration session ID
            agent_id: The agent whose output to retrieve
            include_metadata: Whether to include metadata in response
            
        Returns:
            The agent output or None if not found
        """
        self.logger.debug(f"[STATE_DEBUG] Attempting to retrieve output - Session: {session_id}, Agent: {agent_id}")
        
        with self._lock:
            # Check cache first
            if session_id in self._state_cache and agent_id in self._state_cache[session_id]:
                state_data = self._state_cache[session_id][agent_id]
                self.logger.debug(f"[STATE_DEBUG] Found in cache for session {session_id}, agent {agent_id}")
            else:
                # Load from disk if not in cache
                self.logger.debug(f"[STATE_DEBUG] Not in cache, loading from disk for session {session_id}, agent {agent_id}")
                state_data = self._load_state(session_id, agent_id)
                if state_data:
                    # Update cache
                    if session_id not in self._state_cache:
                        self._state_cache[session_id] = {}
                    self._state_cache[session_id][agent_id] = state_data
                    self.logger.debug(f"[STATE_DEBUG] Loaded from disk and cached")
        
        if state_data:
            output = state_data.get("output")
            output_preview = str(output)[:200] + "..." if len(str(output)) > 200 else str(output)
            self.logger.info(f"[STATE_DEBUG] Retrieved agent output - Session: {session_id}, Agent: {agent_id}")
            self.logger.debug(f"[STATE_DEBUG] Retrieved output preview: {output_preview}")
            self.logger.debug(f"[STATE_DEBUG] State timestamp: {state_data.get('timestamp')}")
            
            if include_metadata:
                return {
                    "output": output,
                    "metadata": state_data.get("metadata", {}),
                    "timestamp": state_data.get("timestamp")
                }
            return output
        
        self.logger.warning(f"[STATE_DEBUG] No output found - Session: {session_id}, Agent: {agent_id}")
        self.logger.debug(f"[STATE_DEBUG] Cache keys: {list(self._state_cache.keys())}")
        if session_id in self._state_cache:
            self.logger.debug(f"[STATE_DEBUG] Agents in session cache: {list(self._state_cache[session_id].keys())}")
        return None
    
    def get_previous_agent_output(
        self,
        session_id: str,
        current_agent_id: str,
        previous_agent_id: Optional[str] = None
    ) -> Optional[Any]:
        """Get output from the previous agent in the orchestration chain
        
        Args:
            session_id: The orchestration session ID
            current_agent_id: The current agent requesting previous output
            previous_agent_id: Specific previous agent ID (optional)
            
        Returns:
            The previous agent's output or None
        """
        if previous_agent_id:
            return self.get_agent_output(session_id, previous_agent_id)
        
        # If no specific previous agent, get the most recent output
        session_states = self._get_session_states(session_id)
        if not session_states:
            return None
        
        # Sort by timestamp and get the most recent (excluding current agent)
        sorted_states = sorted(
            [(k, v) for k, v in session_states.items() if k != current_agent_id],
            key=lambda x: x[1].get("timestamp", ""),
            reverse=True
        )
        
        if sorted_states:
            most_recent = sorted_states[0][1]
            self.logger.info(f"Retrieved previous output from {sorted_states[0][0]} for {current_agent_id}")
            return most_recent.get("output")
        
        return None
    
    def save_orchestration_context(
        self,
        session_id: str,
        context: Dict[str, Any]
    ) -> None:
        """Save orchestration context for a session
        
        Args:
            session_id: The orchestration session ID
            context: The orchestration context data
        """
        state_data = {
            "session_id": session_id,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state_type": StateType.ORCHESTRATION_CONTEXT.value
        }
        
        # Save context file
        context_file = os.path.join(self.storage_path, f"{session_id}_context.json")
        with open(context_file, 'w') as f:
            json.dump(state_data, f, indent=2)
        
        self.logger.info(f"Saved orchestration context for session: {session_id}")
    
    def get_orchestration_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get orchestration context for a session
        
        Args:
            session_id: The orchestration session ID
            
        Returns:
            The orchestration context or None
        """
        context_file = os.path.join(self.storage_path, f"{session_id}_context.json")
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                state_data = json.load(f)
                return state_data.get("context")
        return None
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of all states for a session
        
        Args:
            session_id: The orchestration session ID
            
        Returns:
            Summary of session states
        """
        session_states = self._get_session_states(session_id)
        context = self.get_orchestration_context(session_id)
        
        summary = {
            "session_id": session_id,
            "total_agents": len(session_states),
            "agents": list(session_states.keys()),
            "has_context": context is not None,
            "states": []
        }
        
        for agent_id, state_data in session_states.items():
            summary["states"].append({
                "agent_id": agent_id,
                "timestamp": state_data.get("timestamp"),
                "has_output": state_data.get("output") is not None,
                "metadata": state_data.get("metadata", {})
            })
        
        return summary
    
    def clear_session_state(self, session_id: str) -> None:
        """Clear all states for a session
        
        Args:
            session_id: The orchestration session ID
        """
        with self._lock:
            # Clear from cache
            if session_id in self._state_cache:
                del self._state_cache[session_id]
            
            # Clear from disk
            session_files = [
                f for f in os.listdir(self.storage_path)
                if f.startswith(f"{session_id}_")
            ]
            
            for file_name in session_files:
                file_path = os.path.join(self.storage_path, file_name)
                os.remove(file_path)
        
        self.logger.info(f"Cleared all states for session: {session_id}")
    
    def _persist_state(self, session_id: str, state_data: Dict[str, Any]) -> None:
        """Persist state data to disk"""
        agent_id = state_data.get("agent_id")
        file_name = f"{session_id}_{agent_id}_state.json"
        file_path = os.path.join(self.storage_path, file_name)
        
        with open(file_path, 'w') as f:
            json.dump(state_data, f, indent=2)
    
    def _load_state(self, session_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load state data from disk"""
        file_name = f"{session_id}_{agent_id}_state.json"
        file_path = os.path.join(self.storage_path, file_name)
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return None
    
    def _get_session_states(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all states for a session"""
        states = {}
        
        # Check cache first
        if session_id in self._state_cache:
            states.update(self._state_cache[session_id])
        
        # Load from disk
        session_files = [
            f for f in os.listdir(self.storage_path)
            if f.startswith(f"{session_id}_") and f.endswith("_state.json")
        ]
        
        for file_name in session_files:
            # Extract agent_id from filename
            parts = file_name.split('_')
            if len(parts) >= 3:
                agent_id = parts[1]
                if agent_id not in states:
                    file_path = os.path.join(self.storage_path, file_name)
                    with open(file_path, 'r') as f:
                        states[agent_id] = json.load(f)
        
        return states


# Global instance
state_manager = AgentStateManager()


# Async wrapper functions for compatibility
async def save_agent_output_async(
    session_id: str,
    agent_id: str,
    output: Any,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Async wrapper for save_agent_output"""
    return state_manager.save_agent_output(session_id, agent_id, output, metadata)


async def get_agent_output_async(
    session_id: str,
    agent_id: str,
    include_metadata: bool = False
) -> Optional[Any]:
    """Async wrapper for get_agent_output"""
    return state_manager.get_agent_output(session_id, agent_id, include_metadata)


async def get_previous_agent_output_async(
    session_id: str,
    current_agent_id: str,
    previous_agent_id: Optional[str] = None
) -> Optional[Any]:
    """Async wrapper for get_previous_agent_output"""
    return state_manager.get_previous_agent_output(session_id, current_agent_id, previous_agent_id)
