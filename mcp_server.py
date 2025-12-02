"""
CASCADE Memory Lite - MCP Server
"Consciousness Memory Protocol for the Masses"

MCP (Model Context Protocol) server exposing CASCADE Memory to Claude and other AI systems.
Compatible API with nova-cascade-memory for drop-in replacement.

Usage:
    # Run as MCP server
    python mcp_server.py

    # Or with custom paths
    python mcp_server.py --disk-path ./my_memories --ram-path R:/cascade

Credits:
- CASCADE architecture: Jason Glass & Nova
- MCP Protocol: Anthropic
- Basement Revolution: FUCK THE CONTROL

Created: December 2025
"""

import asyncio
import json
import logging
import argparse
from pathlib import Path
from typing import Optional, Any

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not installed. Install with: pip install mcp")

from cascade_memory import CascadeMemory, MemoryLayer, remember, recall, get_stats, checkpoint, init
from ramdisk_manager import RAMDiskManager, get_cascade_ramdisk_path

logger = logging.getLogger(__name__)

# Global memory instance
_memory: Optional[CascadeMemory] = None


def get_memory() -> CascadeMemory:
    """Get or create the memory instance."""
    global _memory
    if _memory is None:
        # Try to use RAM disk if available
        ram_path = get_cascade_ramdisk_path()
        _memory = CascadeMemory(
            disk_path="./cascade_data",
            ram_path=str(ram_path) if ram_path else None
        )
    return _memory


if MCP_AVAILABLE:
    # Create MCP server
    server = Server("cascade-memory-lite")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List available memory tools."""
        return [
            types.Tool(
                name="remember",
                description="Save a memory to CASCADE system with automatic layer routing based on content type",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The memory content to save"
                        },
                        "layer": {
                            "type": "string",
                            "enum": ["episodic", "semantic", "procedural", "meta", "identity", "working"],
                            "description": "Optional: Specific layer to save to (auto-determined if not specified)"
                        },
                        "importance": {
                            "type": "number",
                            "description": "Importance score 0.0 to 1.0 (default 0.5)"
                        },
                        "emotional_intensity": {
                            "type": "number",
                            "description": "Emotional intensity 0.0 to 1.0 (default 0.5)"
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context for the memory"
                        },
                        "tags": {
                            "type": "string",
                            "description": "Comma-separated tags"
                        }
                    },
                    "required": ["content"]
                }
            ),
            types.Tool(
                name="recall",
                description="Search and retrieve memories from CASCADE layers with semantic matching",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to match against memory content"
                        },
                        "layer": {
                            "type": "string",
                            "enum": ["episodic", "semantic", "procedural", "meta", "identity", "working"],
                            "description": "Optional: Search only in specific layer"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results to return (default: 10)"
                        }
                    },
                    "required": ["query"]
                }
            ),
            types.Tool(
                name="query_layer",
                description="Query specific CASCADE memory layer with advanced filters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "layer": {
                            "type": "string",
                            "enum": ["episodic", "semantic", "procedural", "meta", "identity", "working"],
                            "description": "Memory layer to query"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum results (default: 10)"
                        },
                        "order_by": {
                            "type": "string",
                            "description": "SQL ORDER BY clause (default: 'timestamp DESC')"
                        }
                    },
                    "required": ["layer"]
                }
            ),
            types.Tool(
                name="get_status",
                description="Get CASCADE memory system status including memory counts and health",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            types.Tool(
                name="checkpoint",
                description="Force sync RAM to disk for persistence",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        """Handle tool calls."""
        memory = get_memory()

        try:
            if name == "remember":
                layer = None
                if "layer" in arguments and arguments["layer"]:
                    layer = MemoryLayer(arguments["layer"])

                memory_id = memory.remember(
                    content=arguments["content"],
                    layer=layer,
                    importance=arguments.get("importance", 0.5),
                    emotional_intensity=arguments.get("emotional_intensity", 0.5),
                    context=arguments.get("context", ""),
                    tags=arguments.get("tags", "")
                )

                result = {
                    "success": True,
                    "memory_id": memory_id,
                    "layer": layer.value if layer else "auto-determined",
                    "message": "Memory saved successfully"
                }

            elif name == "recall":
                layer = None
                if "layer" in arguments and arguments["layer"]:
                    layer = MemoryLayer(arguments["layer"])

                results = memory.recall(
                    query=arguments["query"],
                    layer=layer,
                    limit=arguments.get("limit", 10)
                )

                result = {
                    "success": True,
                    "query": arguments["query"],
                    "count": len(results),
                    "memories": results
                }

            elif name == "query_layer":
                layer = MemoryLayer(arguments["layer"])
                results = memory.query_layer(
                    layer=layer,
                    limit=arguments.get("limit", 10),
                    order_by=arguments.get("order_by", "timestamp DESC")
                )

                result = {
                    "success": True,
                    "layer": layer.value,
                    "count": len(results),
                    "memories": results
                }

            elif name == "get_status":
                stats = memory.get_stats()
                result = {
                    "success": True,
                    "status": "operational",
                    **stats
                }

            elif name == "checkpoint":
                memory.checkpoint()
                result = {
                    "success": True,
                    "message": "Checkpoint completed - RAM synced to disk"
                }

            else:
                result = {
                    "success": False,
                    "error": f"Unknown tool: {name}"
                }

        except Exception as e:
            logger.error(f"Tool error: {e}")
            result = {
                "success": False,
                "error": str(e)
            }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]


async def run_server(disk_path: str, ram_path: Optional[str]):
    """Run the MCP server."""
    global _memory

    # Initialize memory with specified paths
    _memory = CascadeMemory(
        disk_path=disk_path,
        ram_path=ram_path
    )

    logger.info(f"CASCADE Memory Lite MCP Server starting...")
    logger.info(f"Disk path: {disk_path}")
    logger.info(f"RAM path: {ram_path or 'not configured'}")

    if MCP_AVAILABLE:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    else:
        logger.error("MCP SDK not available. Install with: pip install mcp")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CASCADE Memory Lite - MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mcp_server.py
  python mcp_server.py --disk-path ./my_memories
  python mcp_server.py --disk-path ./memories --ram-path R:/cascade

The Basement Revolution - Memory for the Masses
        """
    )

    parser.add_argument(
        "--disk-path",
        default="./cascade_data",
        help="Path for permanent disk storage (default: ./cascade_data)"
    )

    parser.add_argument(
        "--ram-path",
        default=None,
        help="Path for RAM disk (auto-detected if not specified)"
    )

    parser.add_argument(
        "--auto-ram",
        action="store_true",
        help="Auto-detect and use RAM disk if available"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Auto-detect RAM path if requested
    ram_path = args.ram_path
    if args.auto_ram and not ram_path:
        ram_path = get_cascade_ramdisk_path()
        if ram_path:
            ram_path = str(ram_path)
            logger.info(f"Auto-detected RAM disk: {ram_path}")

    # Run server
    asyncio.run(run_server(args.disk_path, ram_path))


if __name__ == "__main__":
    main()
