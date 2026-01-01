"""
auth.py - Authentication UI Views

This module contains the Login and Signup screens for the Monday.com-style app.
Built with Flet for pure Python desktop UI.
Now includes real database authentication.
"""

import flet as ft
from database import get_session
from models import User
from sqlalchemy.exc import IntegrityError


def show_snackbar(page: ft.Page, message: str, is_error: bool = False):
    """Helper function to show snackbar notifications"""
    snackbar = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700,
    )
    snackbar.open = True
    page.overlay.append(snackbar)
    page.update()


def show_snackbar(page: ft.Page, message: str, is_error: bool = False):
    """Helper function to show snackbars"""
    snackbar = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700,
    )
    page.overlay.append(snackbar)
    snackbar.open = True
    page.update()


class LoginView(ft.Container):
    """Login screen with username and password fields"""
    
    def __init__(self, page: ft.Page, on_switch_to_signup, on_login_success, on_guest_mode=None):
        super().__init__()
        self.app_page = page
        self.on_switch_to_signup = on_switch_to_signup
        self.on_login_success = on_login_success
        self.on_guest_mode = on_guest_mode
        
        # Username input field
        self.username_field = ft.TextField(
            label="Username",
            width=300,
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_700,
        )
        
        # Password input field
        self.password_field = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=300,
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_700,
        )
        
        # Login button
        self.login_button = ft.ElevatedButton(
            content=ft.Text("Login"),
            width=300,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            on_click=self.handle_login,
        )
        
        # Switch to signup button
        self.signup_link = ft.TextButton(
            content=ft.Text("Don't have an account? Sign up"),
            on_click=lambda e: self.on_switch_to_signup(),
        )
        
        # Guest mode button (if callback provided)
        self.guest_button = None
        if on_guest_mode:
            self.guest_button = ft.TextButton(
                content=ft.Text("Continue as Guest"),
                on_click=lambda e: self.on_guest_mode(),
            )
        
        # Build column items
        column_items = [
            ft.Text(
                "Welcome Back",
                size=32,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_700,
            ),
            ft.Text(
                "Login to your account",
                size=16,
                color=ft.Colors.GREY_700,
            ),
            ft.Container(height=20),  # Spacer
            self.username_field,
            ft.Container(height=10),
            self.password_field,
            ft.Container(height=20),
            self.login_button,
            ft.Container(height=10),
            self.signup_link,
        ]
        
        # Add guest button if available
        if self.guest_button:
            column_items.extend([
                ft.Container(height=5),
                self.guest_button,
            ])
        
        # Build the login card
        self.content = ft.Container(
            content=ft.Column(
                column_items,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLUE_GREY_100,
                offset=ft.Offset(0, 0),
            ),
        )
        
        # Configure container properties
        self.alignment = ft.Alignment.CENTER
        self.expand = True
        self.bgcolor = ft.Colors.BLUE_50
    
    def handle_login(self, e):
        """Handle login button click with real database authentication"""
        username = self.username_field.value
        password = self.password_field.value
        
        # Validate input
        if not username or not password:
            show_snackbar(self.app_page, "Please fill in all fields", is_error=True)
            return
        
        # Authenticate user
        session = get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            
            if user and user.check_password(password):
                # Login successful
                show_snackbar(self.app_page, f"Welcome back, {username}!")
                # Call success callback with user object
                if self.on_login_success:
                    self.on_login_success(user)
            else:
                # Invalid credentials
                show_snackbar(self.app_page, "Invalid username or password", is_error=True)
        except Exception as ex:
            show_snackbar(self.app_page, f"Login error: {str(ex)}", is_error=True)
        finally:
            session.close()


class SignupView(ft.Container):
    """Signup screen with username, email, and password fields"""
    
    def __init__(self, page: ft.Page, on_switch_to_login):
        super().__init__()
        self.app_page = page
        self.on_switch_to_login = on_switch_to_login
        
        # Username input field
        self.username_field = ft.TextField(
            label="Username",
            width=300,
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_700,
        )
        
        # Email input field
        self.email_field = ft.TextField(
            label="Email",
            width=300,
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_700,
        )
        
        # Password input field
        self.password_field = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=300,
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_700,
        )
        
        # Confirm password input field
        self.confirm_password_field = ft.TextField(
            label="Confirm Password",
            password=True,
            can_reveal_password=True,
            width=300,
            border_color=ft.Colors.BLUE_400,
            focused_border_color=ft.Colors.BLUE_700,
        )
        
        # Signup button
        self.signup_button = ft.ElevatedButton(
            content=ft.Text("Sign Up"),
            width=300,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            on_click=self.handle_signup,
        )
        
        # Switch to login button
        self.login_link = ft.TextButton(
            content=ft.Text("Already have an account? Login"),
            on_click=lambda e: self.on_switch_to_login(),
        )
        
        # Build the signup card
        self.content = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Create Account",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_700,
                    ),
                    ft.Text(
                        "Sign up to get started",
                        size=16,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Container(height=20),  # Spacer
                    self.username_field,
                    ft.Container(height=10),
                    self.email_field,
                    ft.Container(height=10),
                    self.password_field,
                    ft.Container(height=10),
                    self.confirm_password_field,
                    ft.Container(height=20),
                    self.signup_button,
                    ft.Container(height=10),
                    self.login_link,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLUE_GREY_100,
                offset=ft.Offset(0, 0),
            ),
        )
        
        # Configure container properties
        self.alignment = ft.Alignment.CENTER
        self.expand = True
        self.bgcolor = ft.Colors.BLUE_50
    
    def handle_signup(self, e):
        """Handle signup button click with real database storage"""
        username = self.username_field.value
        email = self.email_field.value
        password = self.password_field.value
        confirm_password = self.confirm_password_field.value
        
        # Validate input
        if not all([username, email, password, confirm_password]):
            show_snackbar(self.app_page, "Please fill in all fields", is_error=True)
            return
        
        # Check password match
        if password != confirm_password:
            show_snackbar(self.app_page, "Passwords do not match", is_error=True)
            return
        
        # Validate password strength (minimum 6 characters)
        if len(password) < 6:
            show_snackbar(self.app_page, "Password must be at least 6 characters", is_error=True)
            return
        
        # Create new user in database
        session = get_session()
        try:
            # Check if username or email already exists
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    show_snackbar(self.app_page, "Username already exists", is_error=True)
                else:
                    show_snackbar(self.app_page, "Email already exists", is_error=True)
                return
            
            # Create new user
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            
            session.add(new_user)
            session.commit()
            
            # Success - show message and switch to login
            show_snackbar(self.app_page, "Account created successfully! Please login.")
            
            # Clear fields
            self.username_field.value = ""
            self.email_field.value = ""
            self.password_field.value = ""
            self.confirm_password_field.value = ""
            self.app_page.update()
            
            # Switch to login screen after a brief moment
            self.on_switch_to_login()
            
        except IntegrityError:
            session.rollback()
            show_snackbar(self.app_page, "Username or email already exists", is_error=True)
        except Exception as ex:
            session.rollback()
            show_snackbar(self.app_page, f"Signup error: {str(ex)}", is_error=True)
        finally:
            session.close()
