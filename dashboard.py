import flet as ft
from ui.boards import BoardSidebar, BoardView


class DashboardView(ft.Container):
    """Dashboard view with boards functionality"""
    
    def __init__(self, page: ft.Page, user, on_logout, is_guest=False):
        super().__init__()
        self.app_page = page
        self.user = user
        self.on_logout = on_logout
        self.current_board = None
        self.is_guest = is_guest
        
        # Create header
        self.header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "Tusday.com",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Container(expand=True),  # Spacer
                    ft.Text(
                        f"👤 {user.username}" + (" (Guest)" if is_guest else ""),
                        size=16,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Container(width=20),
                    ft.ElevatedButton(
                        content=ft.Text("Logout" if not is_guest else "Exit Guest"),
                        bgcolor=ft.Colors.RED_700,
                        color=ft.Colors.WHITE,
                        on_click=lambda e: self.on_logout(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=20,
            bgcolor=ft.Colors.BLUE_700,
        )
        
        # Create board view (initially empty)
        self.board_view = BoardView(page, None)
        
        # Create sidebar with guest mode support
        self.sidebar = BoardSidebar(
            page,
            user,
            on_board_select=self.handle_board_select,
            on_refresh=self.refresh_board_view,
            is_guest=is_guest,
        )
        
        # Build main layout with sidebar and content
        self.content = ft.Column(
            [
                self.header,
                ft.Container(
                    content=ft.Row(
                        [
                            self.sidebar,
                            self.board_view,
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )
        
        self.expand = True
    
    def handle_board_select(self, board):
        """Handle board selection from sidebar"""
        self.current_board = board
        self.refresh_board_view()
    
    def refresh_board_view(self):
        """Refresh the board view content"""
        # Find the row containing sidebar and board view
        main_row = self.content.controls[1].content
        
        # Replace board view with is_guest parameter
        self.board_view = BoardView(self.app_page, self.current_board, is_guest=self.is_guest)
        main_row.controls[1] = self.board_view
        
        self.app_page.update()
