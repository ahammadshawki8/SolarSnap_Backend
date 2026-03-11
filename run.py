import os
from app import create_app, db
from app.models import User, Site, Panel, Inspection, UploadQueue

# Create app with environment-specific configuration
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Site': Site,
        'Panel': Panel,
        'Inspection': Inspection,
        'UploadQueue': UploadQueue
    }

if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
