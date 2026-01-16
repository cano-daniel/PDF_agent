# === web handler ===
from flask import Flask, render_template, request, jsonify # for web requests
from flask_cors import CORS # for cross-origin resource sharing

# === utilities ===
from datetime import datetime # for timestamps
import requests # for http requests
from dotenv import load_dotenv # for environment variables

# === system ===
import os # for environment variables
import io # for file handling
import logging # for logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Agent Service Configuration
AGENT_SERVICE_HOST = os.getenv('AGENT_SERVICE_HOST')
AGENT_SERVICE_PORT = os.getenv('AGENT_SERVICE_PORT')
AGENT_SERVICE_URL = f"http://{AGENT_SERVICE_HOST}:{AGENT_SERVICE_PORT}/search" # Agent Service URL

# Initialize Flask application
app = Flask(__name__)

# Enable CORS (Cross-Origin Resource Sharing)
CORS(app)

# Store chat messages in memory (resets when container restarts)
chat_history = [] # non production ready


@app.route('/')
def index():
    """
    Serves the main HTML page when someone visits the root URL
    This is the entry point of our web application
    """
    return render_template('index.html')


@app.route('/api/send', methods=['POST'])
def send_message():
    """
    API endpoint that receives messages from the user
    It echoes back the same message, simulating a chat bot
    
    The POST method is used because we're sending data to the server
    """
    # Extract the JSON data from the request
    data = request.get_json()
    user_message = data.get('message', '')
    
    # Validate that we actually received a message
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Get current timestamp for the message
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # Create user message object
    user_msg = {
        'type': 'user',
        'content': user_message,
        'timestamp': timestamp
    }

    # Inside another container on the same network:
    payload = {
        "text": user_message,
        "User_id": 'user' # no user id for now
    }

    try:
        # communicate with agent service
        response = requests.post(AGENT_SERVICE_URL, json=payload)
        response.raise_for_status()
        
        agent_data = response.json()
        # check if the response has a message field and saves the message
        bot_response_text = agent_data.get('message', 'Something is wrong with the agent')
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection to Agent Failed: {e}")
        bot_response_text = "System Error: Agent is unreachable."
    
    bot_msg = {
        'type': 'bot',
        'content': bot_response_text,  # Simply echo back what was sent
        'timestamp': timestamp
    }
    
    # Add both messages to our chat history
    chat_history.append(user_msg)
    chat_history.append(bot_msg)
    
    # Return the bot's response as JSON
    return jsonify({
        'success': True,
        'response': bot_msg
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    """
    API endpoint to retrieve all previous chat messages
    Useful when the page reloads or a new user joins
    """
    return jsonify({
        'success': True,
        'messages': chat_history
    })


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """
    API endpoint to clear all chat history
    Demonstrates how to modify global state in Flask
    """
    global chat_history
    chat_history = []
    return jsonify({
        'success': True,
        'message': 'Chat history cleared'
    })

@app.route('/api/get-pdf/<filename>')
def get_pdf_from_agent(filename):
    """
    Tries to fetch a PDF from the agent service and save it locally in static/
    """
    # 1. clean the extension to avoid duplicates like .pdf.pdf
    filename = filename.split('#')[0]
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    
    # 2. configure the pdf service route
    AGENT_PDF_URL = f"http://{AGENT_SERVICE_HOST}:{AGENT_SERVICE_PORT}/get-pdf"
    
    try:
        logger.info(f"Requesting {filename} from agent container at {AGENT_PDF_URL}...")
        
        # 3. request to the pdf service
        response = requests.get(AGENT_PDF_URL, params={'file_name': filename}, timeout=10)
        
        if response.status_code == 200:
            # 4. prepare the path and folder
            # os.path.join ensures the path is valid in Linux (Docker)
            static_folder = os.path.join(app.root_path, 'static')
            target_path = os.path.join(static_folder, filename)
            
            # 5. create the folder if it doesn't exist
            # This avoids the "No such file or directory" error
            os.makedirs(static_folder, exist_ok=True)
            
            # 6. write the file
            # 'wb' is for writing bytes (Binary)
            with open(target_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Success! {filename} saved to {target_path}")
            return jsonify({'success': True, 'path': f'/static/{filename}'})
        
        else:
            logger.error(f"Agent returned error {response.status_code} for file {filename}")
            return jsonify({'success': False, 'error': 'PDF not found on agent'}), 404
            
    except Exception as e:
        # catch connection or write permissions errors
        logger.error(f"Critical Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Run the Flask development server
    # host='0.0.0.0' makes it accessible from outside the container
    # port=5000 is the standard Flask port
    # debug=True enables hot reloading and better error messages
    app.run(host='0.0.0.0', port=5000, debug=True)