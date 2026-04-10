# Summer Camp Application System

A web-based application system for managing summer camp applications built with Node.js, Express, and MongoDB.

## Overview

The Summer Camp Application System allows prospective campers to submit applications and administrators to manage and review applications. The system provides functionality for:

- **Applicants**: Submit applications with personal information, GPA, and background details
- **Review**: Check and update existing application status
- **Administrators**: Filter applicants by GPA and remove all applications

## Features

### For Applicants
- Submit summer camp applications with name, email, GPA, and background information
- Review and update existing applications

### For Administrators
- Filter applicants by minimum GPA threshold
- View applicant information in tabular format
- Remove all applications from the database

## Technology Stack

- **Backend**: Node.js with Express.js
- **Database**: MongoDB
- **Frontend**: EJS templating engine
- **Environment**: dotenv for configuration management

## Prerequisites

Before running this application, ensure you have the following installed:

- Node.js (v14 or higher)
- MongoDB
- npm (Node Package Manager)

## Installation

1. Clone or download the project files
2. Navigate to the SummerCamp directory:
   ```bash
   cd SummerCamp
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Create a `.env` file in the root directory with your MongoDB connection string:
   ```
   MONGO_CONNECTION_STRING=mongodb://localhost:27017
   ```
   Replace with your actual MongoDB connection string.

## Usage

1. Start the server with a port number:
   ```bash
   node summerCampServer.js 3000
   ```

2. Open your web browser and navigate to `http://localhost:3000`

3. Use the application:
   - **Home Page**: Choose between applicant and admin functions
   - **Apply**: Fill out the application form
   - **Review Application**: Enter email to view/update application
   - **Admin GPA**: Enter minimum GPA to filter applicants
   - **Admin Remove**: Remove all applications (use with caution)

4. To stop the server, type `stop` in the terminal

## Dependencies

- `express`: Web framework for Node.js
- `mongodb`: MongoDB driver for Node.js
- `ejs`: Templating engine
- `dotenv`: Environment variable management
- `body-parser`: Request body parsing middleware
- `nodemon`: Development tool for auto-restarting server

## Development

For development, you can use nodemon to automatically restart the server on file changes:

```bash
npx nodemon summerCampServer.js 3000
```
