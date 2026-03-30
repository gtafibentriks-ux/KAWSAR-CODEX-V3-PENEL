import eventlet
eventlet.monkey_patch()

from app import socketio, app

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 32382))
    socketio.run(app, host="0.0.0.0", port=port)
