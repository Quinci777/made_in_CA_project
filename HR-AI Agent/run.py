import os
from main import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host=os.getenv('HOST'), port=os.getenv('PORT'))