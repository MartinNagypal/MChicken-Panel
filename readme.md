# MChicken Panel

MChicken Panel is a web-based dashboard for managing Docker-based Minecraft servers.

The panel allows users to monitor server status and statistics, execute Minecraft console commands, view live server logs, and manage users and permissions.

![MChicken Panel](Frontend/assets/showCaseIndex.png)

## Features

- Minecraft server overview
- Server status monitoring:
  - Online
  - Starting
  - Offline
  - Error
- Server information:
  - Server name
  - Minecraft version
  - Server IP
- Live server statistics:
  - Current player count
  - Maximum player count
  - CPU usage
  - Memory usage
  - Server uptime
- Start and stop the server
- Restart the server
- Minecraft RCON console
- Live server logs via WebSockets
- User registration and login
- Session management using HTTP-only cookies
- Logout from all active sessions
- User management
- Create and delete users
- Change user roles
- Role-based permissions
- SSH configuration through the web interface
- Encrypted SSH password storage
- Argon2 password hashing
- Responsive web interface
- SQLite database for user, session, and server configuration

## Roles and Permissions

The panel supports three user roles.

| Feature | Admin | Mod | User |
|---|:---:|:---:|:---:|
| Start/stop server | Yes | Yes | No |
| View server statistics | Yes | Yes | Yes |
| Manage backups | Yes | Yes | No |
| View backups | Yes | Yes | Yes |
| View console | Yes | Yes | Yes |
| Send commands | Yes | Yes | No |
| Configure SSH | Yes | No | No |
| Configure RCON | Yes | No | No |
| Manage users | Yes | No | No |
| View users | Yes | Yes | No |
| Modify users | Yes | No | No |

The first registered user is automatically assigned the `admin` role. Additional users can only register if registration is enabled or if an administrator creates them through the user management interface.

## Architecture

The project consists of two main components:

```text
MChicken Panel
├── Backend
│   └── FastAPI API
└── Frontend
    └── HTML, CSS and JavaScript