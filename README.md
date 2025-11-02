# UAV Log Viewer

![log seeking](preview.gif "Logo Title Text 1")

 This is a Javascript based log viewer for Mavlink telemetry and dataflash logs with an integrated AI chatbot for intelligent flight log analysis.
 [Live demo here](http://plot.ardupilot.org).

## 🚀 Quick Start

### Running the Application

#### 1. Start the Backend (AI Chatbot API)

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run the backend server
python main.py
```

The backend will be available at `http://localhost:8000`

#### 2. Start the Frontend (in a new terminal)

```bash
# Install dependencies (first time only)
npm install

# Set Cesium token (optional, for 3D map)
export VUE_APP_CESIUM_TOKEN=<your token>

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:8080`

#### 3. Use the Application

1. Open `http://localhost:8080` in your browser
2. Upload a `.bin` flight log file
3. Interact with the AI chatbot in the bottom-right corner
4. Ask questions like:
   - "What was the maximum altitude?"
   - "Are there any anomalies in this flight?"
   - "Show me all error messages"

### Using Startup Scripts

Alternatively, use the provided startup scripts:

```bash
# Terminal 1: Start backend
./start_backend.sh

# Terminal 2: Start frontend
./start_frontend.sh
```

## Build Setup

``` bash
# initialize submodules
git submodule update --init --recursive

# install dependencies
npm install

# enter Cesium token
export VUE_APP_CESIUM_TOKEN=<your token>

# serve with hot reload at localhost:8080
npm run dev

# build for production with minification
npm run build

# run unit tests
npm run unit

# run e2e tests
npm run e2e

# run all tests
npm test
```

# Docker

run the prebuilt docker image:

``` bash
docker run -p 8080:8080 -d ghcr.io/ardupilot/uavlogviewer:latest

```

or build the docker file locally:

``` bash

# Build Docker Image
docker build -t <your username>/uavlogviewer .

# Run Docker Image
docker run -e VUE_APP_CESIUM_TOKEN=<Your cesium ion token> -it -p 8080:8080 -v ${PWD}:/usr/src/app <your username>/uavlogviewer

# Navigate to localhost:8080 in your web browser

# changes should automatically be applied to the viewer

```
