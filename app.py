from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active users
active_users = {}
message_history = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    # Remove user from active users
    username = active_users.pop(request.sid, None)
    if username:
        emit('user_left', {'username': username}, broadcast=True)
        emit('update_users', {'users': list(active_users.values())}, broadcast=True)
    print(f'Client disconnected: {request.sid}')

@socketio.on('join')
def handle_join(data):
    username = data['username']
    active_users[request.sid] = username
    
    # Send chat history to the new user
    emit('chat_history', {'messages': message_history})
    
    # Notify everyone about new user
    emit('user_joined', {
        'username': username,
        'timestamp': datetime.now().strftime('%H:%M')
    }, broadcast=True)
    
    # Update user list for everyone
    emit('update_users', {'users': list(active_users.values())}, broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    username = active_users.get(request.sid, 'Anonymous')
    timestamp = datetime.now().strftime('%H:%M')
    
    message_data = {
        'username': username,
        'message': data['message'],
        'timestamp': timestamp
    }
    
    # Store message in history (keep last 100 messages)
    message_history.append(message_data)
    if len(message_history) > 100:
        message_history.pop(0)
    
    # Broadcast message to all users
    emit('receive_message', message_data, broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    username = active_users.get(request.sid, 'Anonymous')
    emit('user_typing', {'username': username, 'is_typing': data['is_typing']}, 
         broadcast=True, include_self=False)

if __name__ == '__main__':
    # For development
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    
    # For production (use this when deploying):
    # socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))