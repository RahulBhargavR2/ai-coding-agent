from app.tools.base import Tool
from app.core.exceptions import ToolAlreadyExists

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str,Tool] = {}
    
    def register(self, tool:Tool) -> None:
        if tool.name in self._tools:
            raise ToolAlreadyExists(
                f"Tool '{tool.name}' is already registered."
            )
        
        self._tools[tool.name] = tool
    
    def get(self, name:str) -> Tool:
        try:
            return self._tools[name]
        except KeyError:
            raise KeyError(
                f"Tool '{name}' is not registered."
            )
    
    def list_tools(self)-> list[Tool]:
        return list(self._tools.values())