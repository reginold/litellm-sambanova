"""SambaNova Agentic App - Main Agent with Tools and Memory."""

import logging
import json
from typing import Dict, List, Any, Optional

from client import SambaNovaClient
from tools import ToolRegistry
from memory import Memory
from config import Config, default_config, TOOL_CALL_START, TOOL_CALL_END, MEMORY_COMMANDS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Agent:
    """An agentic app with tools and memory."""
    
    SYSTEM_PROMPT = """You are a helpful AI assistant with access to tools.
When you need to use a tool, respond in this format:

<tool_call>
{{
  "tool": "tool_name",
  "parameters": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}
</tool_call>

After getting the result, continue with your response.

You also have access to persistent memory:
- To remember something: say "remember: key = value"
- To recall something: say "recall: key" or "search: query"

Available tools: {tool_list}"""
    
    def __init__(
        self,
        client: Optional[SambaNovaClient] = None,
        use_memory: bool = True,
        config: Optional[Config] = None
    ):
        self.client = client or SambaNovaClient()
        self.tools = ToolRegistry()
        self.config = config or default_config
        self.memory = Memory(use_persistent=use_memory) if use_memory else None
        self.conversation_history: List[Dict[str, str]] = []
    
    def _build_system_prompt(self) -> str:
        tool_list = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools.list_tools()])
        return self.SYSTEM_PROMPT.format(tool_list=tool_list)
    
    def _parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """Parse tool calls from the model's response."""
        tool_calls = []
        
        start_marker = TOOL_CALL_START
        end_marker = TOOL_CALL_END
        
        if start_marker in text and end_marker in text:
            start = text.find(start_marker) + len(start_marker)
            end = text.find(end_marker)
            try:
                tool_data = json.loads(text[start:end].strip())
                tool_calls.append(tool_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse tool call: {e}")
        
        return tool_calls
    
    def _parse_memory_commands(self, text: str) -> List[Dict[str, Any]]:
        """Parse memory commands from the model's response."""
        commands = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check for remember command
            if line.startswith(MEMORY_COMMANDS["REMEMBER"]):
                content = line[len(MEMORY_COMMANDS["REMEMBER"]):].strip()
                if '=' in content:
                    key, value = content.split('=', 1)
                    commands.append({"type": "remember", "key": key.strip(), "value": value.strip()})
            
            # Check for recall command
            elif line.startswith(MEMORY_COMMANDS["RECALL"]):
                key = line[len(MEMORY_COMMANDS["RECALL"]):].strip()
                commands.append({"type": "recall", "key": key})
            
            # Check for search command
            elif line.startswith(MEMORY_COMMANDS["SEARCH"]):
                query = line[len(MEMORY_COMMANDS["SEARCH"]):].strip()
                commands.append({"type": "search", "query": query})
        
        return commands
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool and return the result."""
        logger.info(f"Executing tool: {tool_name}")
        result = self.tools.execute_tool(tool_name, **parameters)
        return result
    
    def process_input(self, user_input: str) -> str:
        """Process user input and return the agent's response."""
        logger.info(f"Processing input: {user_input[:50]}...")
        
        # Add user message to memory
        if self.memory:
            self.memory.add_message("user", user_input)
        
        # Build conversation context
        messages: List[Dict[str, str]] = [{"role": "system", "content": self._build_system_prompt()}]
        
        # Add memory context
        if self.memory:
            context = self.memory.get_context(max_tokens=self.config.max_context_tokens)
            messages.extend(context)
        
        # Add current user message
        messages.append({"role": "user", "content": user_input})
        
        # Get model response
        try:
            response = self.client.chat(messages)
        except Exception as e:
            logger.error(f"Initial API call failed: {e}", exc_info=True)
            return f"Error: Failed to get response from API: {e}"

        # Process any tool calls
        tool_calls = self._parse_tool_calls(response)
        max_iterations = 5  # Prevent infinite loops
        iterations = 0

        while tool_calls and iterations < max_iterations:
            iterations += 1
            for call in tool_calls:
                tool_name = call.get("tool")
                params = call.get("parameters", {})

                try:
                    tool_result = self._execute_tool(tool_name, params)
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}", exc_info=True)
                    tool_result = f"Error executing tool: {str(e)}"

                # Add tool result to conversation
                messages.append({"role": "user", "content": f"Tool result for {tool_name}: {tool_result}"})

            # Get next response
            try:
                response = self.client.chat(messages)
            except Exception as e:
                logger.error(f"API call failed during tool loop: {e}", exc_info=True)
                return f"Error: Failed to get response from API during tool execution: {e}"
            tool_calls = self._parse_tool_calls(response)
        
        if iterations >= max_iterations:
            logger.warning("Reached maximum tool call iterations")
        
        # Process memory commands
        memory_commands = self._parse_memory_commands(response)
        for cmd in memory_commands:
            if cmd["type"] == "remember" and self.memory:
                result = self.memory.remember(cmd["key"], cmd["value"])
                response += f"\n\n{result}"
            elif cmd["type"] == "recall" and self.memory:
                result = self.memory.recall(key=cmd["key"])
                response += f"\n\nRecall: {result}"
            elif cmd["type"] == "search" and self.memory:
                result = self.memory.recall(query=cmd["query"])
                response += f"\n\nSearch results: {result}"
        
        # Add assistant response to memory
        if self.memory:
            self.memory.add_message("assistant", response)
        
        return response
    
    def run(self, user_input: str) -> str:
        """Run the agent with user input."""
        return self.process_input(user_input)
    
    def new_conversation(self, name: Optional[str] = None) -> str:
        """Start a new conversation."""
        if self.memory:
            return self.memory.new_conversation(name)
        self.conversation_history = []
        return "Started new conversation"
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        if self.memory:
            return self.memory.get_messages()
        return []
    
    def list_tools(self) -> List[Dict[str, str]]:
        """List available tools."""
        return self.tools.list_tools()
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations."""
        if self.memory:
            return self.memory.list_conversations()
        return []


def main():
    import argparse
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    parser = argparse.ArgumentParser(description="SambaNova Agentic App")
    parser.add_argument("task", nargs="?", help="Task to execute")
    parser.add_argument("--model", default="MiniMax-M2.5", help="Model to use")
    parser.add_argument("--no-memory", action="store_true", help="Disable persistent memory")
    parser.add_argument("--list-tools", action="store_true", help="List available tools")
    parser.add_argument("--list-conversations", action="store_true", help="List conversations")
    parser.add_argument("--new", nargs="?", help="Start new conversation")
    
    args = parser.parse_args()
    
    client = SambaNovaClient()
    client.set_model(args.model)
    agent = Agent(client, use_memory=not args.no_memory)
    
    if args.list_tools:
        print("\n=== Available Tools ===")
        for tool in agent.list_tools():
            print(f"- {tool['name']}: {tool['description']}")
    elif args.list_conversations:
        print("\n=== Conversations ===")
        for conv in agent.list_conversations():
            print(f"{conv['id']}: {conv['name']} (created: {conv['created_at']})")
    elif args.new is not None:
        print(agent.new_conversation(args.new))
    elif args.task:
        result = agent.run(args.task)
        print(result)
    else:
        print("Usage: agent.py 'task' [--model MODEL] [--no-memory]")
        print("       agent.py --list-tools")
        print("       agent.py --list-conversations")
        print("       agent.py --new [name]")


if __name__ == "__main__":
    main()
