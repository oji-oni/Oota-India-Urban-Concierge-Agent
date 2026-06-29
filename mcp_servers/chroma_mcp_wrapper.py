"""
Wrapper around chroma-mcp that redirects any startup prints to stderr
so they don't corrupt the stdio JSON-RPC transport.
"""
import sys
import os

# Redirect stdout → stderr BEFORE importing chroma_mcp so that any
# print() calls during initialization go to stderr, not the JSON-RPC pipe.
_real_stdout = sys.stdout
sys.stdout = sys.stderr

from chroma_mcp.server import get_chroma_client, mcp, create_parser

# Parse args and initialise the client (all prints go to stderr here)
parser = create_parser()
args = parser.parse_args()

from dotenv import load_dotenv
load_dotenv(dotenv_path=args.dotenv_path)

try:
    get_chroma_client(args)
    print("Successfully initialized Chroma client", file=sys.stderr)
except Exception as e:
    print(f"Failed to initialize Chroma client: {str(e)}", file=sys.stderr)
    raise

# Restore real stdout BEFORE starting the MCP server so it can use JSON-RPC
sys.stdout = _real_stdout
print("Starting MCP server", file=sys.stderr)
mcp.run(transport='stdio')
