# FileFlows Integration for Home Assistant

A custom integration for Home Assistant to monitor and manage [FileFlows](https://fileflows.com) instances.

## Features

- Monitor FileFlows server status
- Track processing queues and statistics
- View active and completed flow executions
- Monitor system resources

## Configuration

1. Install the integration through HACS
2. Restart Home Assistant
3. Go to Settings > Devices & Services
4. Click "Add Integration" and search for "FileFlows"
5. Enter your FileFlows server details:
   - **Host**: Your FileFlows server IP/hostname
   - **Port**: FileFlows API port (default: 19200)
   - **API Key**: Generate in FileFlows Settings > Security

## Requirements

- FileFlows server version 1.0.0 or higher
- Home Assistant 2023.1.0 or higher

## Support

If you encounter issues, please report them on the [GitHub repository](https://github.com/wildenrou/home-assistant-fileflows/issues).
