import flet as ft
from auth import LoginView, SignupView
from dashboard import DashboardView
from database import init_database
from models import User
from datetime import datetime


def main(page: ft.Page):
    """Main application entry point"""
    
    # Initialize database on startup
    init_database()
    
    # Configure the app window
    page.title = "Tusday.com"
    page.window_width = 1000
    page.window_height = 700
    page.window_resizable = True
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Store current user
    current_user = None
    
    # Navigation functions
    def show_login():
        """Switch to login view"""
        page.controls.clear()
        page.add(LoginView(
            page, 
            on_switch_to_signup=show_signup,
            on_login_success=show_dashboard,
            on_guest_mode=show_guest_dashboard
        ))
        page.update()
    
    def show_signup():
        """Switch to signup view"""
        page.controls.clear()
        page.add(SignupView(page, on_switch_to_login=show_login))
        page.update()
    
    def show_dashboard(user):
        """Switch to dashboard view after successful login"""
        nonlocal current_user
        current_user = user
        page.controls.clear()
        page.add(DashboardView(page, user, on_logout=show_login))
        page.update()
    
    def show_guest_dashboard():
        """Switch to dashboard in guest mode"""
        # Create a temporary guest user object
        guest_user = type('GuestUser', (), {
            'username': 'Guest',
            'email': 'guest@example.com',
            'created_at': datetime.now(),
            'id': None  # No database ID for guest
        })()
        
        page.controls.clear()
        page.add(DashboardView(page, guest_user, on_logout=show_login, is_guest=True))
        page.update()
    
    # Start with login screen
    show_login()


if __name__ == "__main__":
    # Launch the Flet desktop app
    ft.run(main)

