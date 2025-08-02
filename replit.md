# Overview

This is a Flask web application that provides a Telegram bot for searching and sharing content from Pixabay (images, videos, music, and GIFs). The application features a web-based admin panel for bot management, user statistics, and channel administration. The bot includes mandatory channel subscription functionality and tracks user activity and search history.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Web Framework
- **Flask**: Lightweight Python web framework serving as the main application server
- **Templates**: Jinja2 templating with Bootstrap for responsive UI
- **Static Assets**: CSS styling with Arabic RTL support and dark theme integration

## Bot Integration
- **Telegram Bot Handler**: Custom bot handler managing user interactions and commands
- **Webhook Architecture**: Flask routes handle incoming Telegram webhook requests
- **Message Processing**: Structured command handling for search, admin, and subscription management

## Database Layer
- **SQLite**: Local file-based database for simplicity and deployment ease
- **Schema Design**: 
  - Users table with activity tracking and ban management
  - Mandatory channels table for subscription enforcement
  - Search history for analytics and user behavior tracking
- **Database Class**: Centralized database operations with error handling

## External API Integration
- **Pixabay API**: Primary content source with multiple endpoints
  - Image search with configurable parameters
  - Video search functionality
  - Music and audio content support
- **Rate Limiting**: Built-in request management for API quota compliance

## Admin Panel Features
- **User Management**: View, ban/unban users, track activity
- **Channel Administration**: Add/remove mandatory subscription channels
- **Analytics Dashboard**: Real-time statistics and search history
- **Bot Control**: Start/stop functionality and status monitoring

## Deployment Architecture
- **Render.com Optimized**: Configuration for cloud platform deployment
- **Environment Variables**: Secure API key and configuration management
- **Logging**: Comprehensive logging system for debugging and monitoring
- **Error Handling**: Graceful degradation with fallback responses

# External Dependencies

## Third-Party APIs
- **Pixabay API**: Content search and retrieval service
- **Telegram Bot API**: Bot communication and webhook handling

## Python Libraries
- **Flask**: Web framework and routing
- **Requests**: HTTP client for external API calls
- **SQLite3**: Database connectivity (built-in Python module)

## Frontend Dependencies
- **Bootstrap**: UI framework with dark theme support
- **Feather Icons**: Icon library for consistent UI elements
- **Custom CSS**: Arabic RTL layout and bot-specific styling

## Deployment Services
- **Render.com**: Cloud hosting platform
- **Environment Configuration**: Secure credential management through platform environment variables