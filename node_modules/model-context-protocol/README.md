# Model Context Protocol - Dad Jokes MCP Server

An npm package that provides an interface for implementing an MCP server with authentication and extensible resources.

## Overview

This MCP Server is designed to provide a fun and interactive way to get dad jokes. It leverages the Model Context Protocol (MCP) to expose tools and prompts for generating dad jokes on various topics.

## Features

- **Dad Joke Generator**: Generate dad jokes based on a given topic.
- **Dynamic Prompts**: Use prompts to guide the joke generation process.
- **Extensible Resources**: Easily add more resources and tools as needed.

## Installation

To install the package, run:

```bash
npm install
```

## Usage

To start the MCP server, run:

```bash
npm run start:mcp
```

The server will start and listen for incoming requests.

## Example

To add this MCP server to your MCP client, follow these steps:

1. Ensure that your MCP client is set up and configured correctly.
2. Obtain the IP address and port number where the MCP server is running.
3. In your MCP client configuration, add a new server entry with the obtained IP address and port number.
4. Save the configuration and restart your MCP client if necessary.
5. Connect to the newly added server from your MCP client.

Make sure that the server and client versions are compatible to avoid any connection issues.

## License

This project is licensed under the MIT License.
