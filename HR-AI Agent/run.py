import os
from main import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv('DEBUG_MODE'), host=os.getenv('HOST'), port=os.getenv('PORT'))