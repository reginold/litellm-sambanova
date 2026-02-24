"""Tools module for the agentic app."""

import os
import re
import json
import logging
import subprocess
import requests
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Configure module logger
logging.basicConfig(level=logging.INFO)


class Tool(ABC):
    """Abstract base class for tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        pass
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description
        }


class ReadFileTool(Tool):
    """Tool for reading file contents."""
    
    def __init__(self, allowed_dirs: Optional[List[str]] = None):
        super().__init__("read_file", "Read the contents of a file")
        self.allowed_dirs = allowed_dirs or []
    
    def execute(self, path: str, **kwargs) -> str:
        try:
            file_path = Path(path).expanduser().resolve()
            
            # Security check: ensure path is within allowed directories
            if self.allowed_dirs:
                allowed = False
                for allowed_dir in self.allowed_dirs:
                    allowed_dir_path = Path(allowed_dir).expanduser().resolve()
                    try:
                        file_path.relative_to(allowed_dir_path)
                        allowed = True
                        break
                    except ValueError:
                        continue
                
                if not allowed:
                    return f"Error: Path {path} is not in allowed directories"
            
            if not file_path.exists():
                return f"Error: File not found: {path}"
            
            if not file_path.is_file():
                return f"Error: Not a file: {path}"
            
            # Limit file size to 1MB
            if file_path.stat().st_size > 1024 * 1024:
                return f"Error: File too large (max 1MB): {path}"
            
            with open(file_path, "r") as f:
                content = f.read(1024 * 1024)  # Read max 1MB
            
            logger.info(f"Read file: {file_path}")
            return content
            
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return f"Error reading file: {str(e)}"


class WriteFileTool(Tool):
    """Tool for writing content to files."""
    
    def __init__(self, allowed_dirs: Optional[List[str]] = None):
        super().__init__("write_file", "Write content to a file")
        self.allowed_dirs = allowed_dirs or []
    
    def execute(self, path: str, content: str, **kwargs) -> str:
        try:
            file_path = Path(path).expanduser().resolve()
            
            # Security check: ensure path is within allowed directories
            if self.allowed_dirs:
                allowed = False
                for allowed_dir in self.allowed_dirs:
                    allowed_dir_path = Path(allowed_dir).expanduser().resolve()
                    try:
                        file_path.relative_to(allowed_dir_path)
                        allowed = True
                        break
                    except ValueError:
                        continue
                
                if not allowed:
                    return f"Error: Path {path} is not in allowed directories"
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w") as f:
                f.write(content)
            
            logger.info(f"Wrote file: {file_path}")
            return f"Successfully wrote to {path}"
            
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            return f"Error writing file: {str(e)}"


class ListDirectoryTool(Tool):
    """Tool for listing directory contents."""
    
    def __init__(self, allowed_dirs: Optional[List[str]] = None):
        super().__init__("list_directory", "List files in a directory")
        self.allowed_dirs = allowed_dirs or []
    
    def execute(self, path: str = ".", **kwargs) -> str:
        try:
            dir_path = Path(path).expanduser().resolve()
            
            # Security check
            if self.allowed_dirs:
                allowed = False
                for allowed_dir in self.allowed_dirs:
                    allowed_dir_path = Path(allowed_dir).expanduser().resolve()
                    try:
                        dir_path.relative_to(allowed_dir_path)
                        allowed = True
                        break
                    except ValueError:
                        continue
                
                if not allowed:
                    return f"Error: Path {path} is not in allowed directories"
            
            if not dir_path.exists():
                return f"Error: Directory not found: {path}"
            
            if not dir_path.is_dir():
                return f"Error: Not a directory: {path}"
            
            items = []
            for item in sorted(dir_path.iterdir()):
                if item.is_dir():
                    items.append(f"{item.name}/")
                else:
                    items.append(item.name)
            
            logger.info(f"Listed directory: {dir_path}")
            return "\n".join(items)
            
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            return f"Error listing directory: {str(e)}"


class ExecuteCodeTool(Tool):
    """Tool for executing Python code (sandboxed)."""
    
    def __init__(self, timeout: int = 30):
        super().__init__("execute_code", "Execute Python code and return the result")
        self.timeout = timeout
    
    def execute(self, code: str, **kwargs) -> str:
        try:
            # Create sandboxed environment
            sandbox = {
                "abs": abs,
                "min": min,
                "max": max,
                "pow": pow,
                "round": round,
                "sum": sum,
                "len": len,
                "sorted": sorted,
                "reversed": list,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": list(map),
                "filter": list(filter),
                "any": any,
                "all": all,
            }
            
            # Add math functions
            import math
            sandbox.update({
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
                "floor": math.floor,
                "ceil": math.ceil,
            })
            
            # Execute in restricted environment
            result = {}
            exec(code, {"__builtins__": {}}, result)
            
            # Filter out internal variables
            output = {k: v for k, v in result.items() if not k.startswith('_')}
            
            logger.info(f"Executed code successfully")
            return json.dumps(output, indent=2, default=str)
            
        except SyntaxError as e:
            return f"Syntax error: {str(e)}"
        except Exception as e:
            logger.error(f"Error executing code: {e}")
            return f"Error executing code: {str(e)}"


class RunCommandTool(Tool):
    """Tool for running shell commands (with restrictions)."""
    
    def __init__(
        self,
        timeout: int = 30,
        allowed_commands: Optional[List[str]] = None,
        blocked_commands: Optional[List[str]] = None
    ):
        super().__init__("run_command", "Run a shell command")
        self.timeout = timeout
        self.allowed_commands = allowed_commands  # None means all allowed
        self.blocked_commands = blocked_commands or [
            "rm -rf", "mkfs", "dd", ":(){:|:&};:",  # Destructive + fork bomb
            "curl", "wget", "nc", "netcat",  # Network ops
            "chmod 777", "chown",  # Permission changes
        ]
    
    def _is_command_allowed(self, command: str) -> tuple[bool, str]:
        """Check if command is allowed."""
        # Check blocked commands
        for blocked in self.blocked_commands:
            if blocked in command:
                return False, f"Command contains blocked pattern: {blocked}"
        
        # Check allowed list if specified
        if self.allowed_commands:
            for allowed in self.allowed_commands:
                if command.strip().startswith(allowed):
                    return True, ""
            return False, "Command not in allowed list"
        
        return True, ""
    
    def execute(self, command: str, cwd: Optional[str] = None, **kwargs) -> str:
        try:
            # Security check
            allowed, reason = self._is_command_allowed(command)
            if not allowed:
                logger.warning(f"Blocked command: {command} - {reason}")
                return f"Error: {reason}"
            
            # Use shell=False for better security when possible
            # Only use shell=True for complex commands
            use_shell = "&" in command or "|" in command or ";" in command
            
            result = subprocess.run(
                command,
                shell=use_shell,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = f"Exit code: {result.returncode}\n"
            if result.stdout:
                output += f"stdout: {result.stdout}\n"
            if result.stderr:
                output += f"stderr: {result.stderr}"
            
            logger.info(f"Executed command: {command[:50]}...")
            return output
            
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {self.timeout} seconds"
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return f"Error running command: {str(e)}"


class WebSearchTool(Tool):
    """Tool for web searching using DuckDuckGo."""
    
    def __init__(self):
        super().__init__("web_search", "Search the web for information")
    
    def execute(self, query: str, num_results: int = 5, **kwargs) -> str:
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if data.get("RelatedTopics"):
                for item in data["RelatedTopics"][:num_results]:
                    if "Text" in item:
                        results.append(f"- {item['Text']}")
            
            logger.info(f"Web search: {query}")
            return "\n".join(results) if results else "No results found"
            
        except requests.exceptions.Timeout:
            return "Error: Search request timed out"
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return f"Error searching web: {str(e)}"


class GetWeatherTool(Tool):
    """Tool for getting weather information."""
    
    def __init__(self):
        super().__init__("get_weather", "Get weather information for a location")
    
    def execute(self, location: str, **kwargs) -> str:
        try:
            # Validate location
            if not location or len(location) > 100:
                return "Error: Invalid location"
            
            # Sanitize location to prevent injection
            location = re.sub(r'[^a-zA-Z0-9\s\-\.\,]', '', location)
            
            response = requests.get(
                f"https://wttr.in/{location}?format=j1",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            current = data["current_condition"][0]
            result = f"Location: {location}\n"
            result += f"Temperature: {current['temp_C']}°C\n"
            result += f"Condition: {current['weatherDesc'][0]['value']}\n"
            result += f"Humidity: {current['humidity']}%\n"
            result += f"Wind: {current['windspeedKmph']} km/h"
            
            logger.info(f"Weather lookup: {location}")
            return result
            
        except requests.exceptions.Timeout:
            return "Error: Weather request timed out"
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return f"Error getting weather: {str(e)}"


class CalculatorTool(Tool):
    """Tool for safe mathematical calculations."""
    
    # Whitelist of allowed functions
    ALLOWED_FUNCTIONS = {
        "abs": abs,
        "min": min,
        "max": max,
        "pow": pow,
        "round": round,
        "sum": sum,
        "len": len,
    }
    
    # Math module functions
    MATH_FUNCTIONS = {
        "sqrt": __import__("math").sqrt,
        "sin": __import__("math").sin,
        "cos": __import__("math").cos,
        "tan": __import__("math").tan,
        "log": __import__("math").log,
        "log10": __import__("math").log10,
        "log2": __import__("math").log2,
        "exp": __import__("math").exp,
        "floor": __import__("math").floor,
        "ceil": __import__("math").ceil,
        "pi": __import__("math").pi,
        "e": __import__("math").e,
    }
    
    def __init__(self):
        super().__init__("calculator", "Perform mathematical calculations")
        self._allowed_names = {**self.ALLOWED_FUNCTIONS, **self.MATH_FUNCTIONS}
    
    def execute(self, expression: str, **kwargs) -> str:
        try:
            # Validate expression - only allow alphanumeric, operators, and parentheses
            if not re.match(r'^[0-9+\-*/%^().,\s]+$', expression):
                return "Error: Invalid characters in expression"
            
            # Replace common math notations
            expression = expression.replace('^', '**')
            
            # Evaluate in restricted environment
            result = eval(expression, {"__builtins__": {}}, self._allowed_names)
            
            logger.info(f"Calculated: {expression} = {result}")
            return str(result)
            
        except SyntaxError:
            return "Error: Invalid expression syntax"
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception as e:
            logger.error(f"Error calculating: {e}")
            return f"Error calculating: {str(e)}"


class ToolRegistry:
    """Registry for all available tools."""
    
    def __init__(self, tool_config: Optional[Dict[str, Any]] = None):
        self.tools: Dict[str, Tool] = {}
        self.tool_config = tool_config or {}
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register default tools."""
        # Get config values
        code_timeout = self.tool_config.get("execute_code_timeout", 30)
        cmd_timeout = self.tool_config.get("run_command_timeout", 30)
        allowed_dirs = self.tool_config.get("allowed_directories", [])
        allowed_cmds = self.tool_config.get("allowed_commands")
        
        tools = [
            ReadFileTool(allowed_dirs=allowed_dirs),
            WriteFileTool(allowed_dirs=allowed_dirs),
            ListDirectoryTool(allowed_dirs=allowed_dirs),
            ExecuteCodeTool(timeout=code_timeout),
            RunCommandTool(
                timeout=cmd_timeout,
                allowed_commands=allowed_cmds
            ),
            WebSearchTool(),
            GetWeatherTool(),
            CalculatorTool()
        ]
        
        for tool in tools:
            self.register(tool)
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, str]]:
        """List all available tools."""
        return [tool.to_dict() for tool in self.tools.values()]
    
    def execute_tool(self, name: str, **kwargs) -> str:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return f"Tool '{name}' not found"
        
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {e}")
            return f"Error: {str(e)}"


# Global registry instance
registry: Optional[ToolRegistry] = None


def get_registry(tool_config: Optional[Dict[str, Any]] = None) -> ToolRegistry:
    """Get or create the global tool registry."""
    global registry
    if registry is None:
        registry = ToolRegistry(tool_config)
    return registry
