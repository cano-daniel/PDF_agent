from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime

# Initialize Flask application
# Flask is a lightweight web framework that makes it easy to create web applications
app = Flask(__name__)

# Enable CORS (Cross-Origin Resource Sharing)
# This allows your frontend to communicate with the backend even if they're on different ports
CORS(app)

# Store chat messages in memory (resets when container restarts)
# In a production app, you'd use a database like PostgreSQL or MongoDB
chat_history = []


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
    
    # Create bot response (echoing the same message)
    bot_msg = {
        'type': 'bot',
        'content': user_message,  # Simply echo back what was sent
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


if __name__ == '__main__':
    # Run the Flask development server
    # host='0.0.0.0' makes it accessible from outside the container
    # port=5000 is the standard Flask port
    # debug=True enables hot reloading and better error messages
    app.run(host='0.0.0.0', port=5000, debug=True)