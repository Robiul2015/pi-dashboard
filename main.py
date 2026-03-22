import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from ui.dashboard_app import DashboardApp

if __name__ == "__main__":
    app = DashboardApp()
    app.run()
