import flet as ft
from database import get_session
from models import Board
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from ui.tasks import TaskTableView


def show_snackbar(page: ft.Page, message: str, is_error: bool = False):
    """Helper function to show snackbar notifications"""
    snackbar = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700,
    )
    snackbar.open = True
    page.overlay.append(snackbar)
    page.update()


class BoardSidebar(ft.Container):
    """Sidebar showing list of boards - supports both guest and logged-in users"""
    
    def __init__(self, page: ft.Page, user, on_board_select, on_refresh, is_guest=False):
        super().__init__()
        self.app_page = page
        self.user = user
        self.on_board_select = on_board_select
        self.on_refresh = on_refresh
        self.selected_board_id = None
        self.is_guest = is_guest
        
        # In-memory storage for guest boards
        self.guest_boards = []
        self.guest_board_counter = 0
        
        # Add board button
        self.add_board_btn = ft.ElevatedButton(
            content=ft.Text("+ New Board"),
            width=200,
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            on_click=self.show_add_board_dialog,
        )
        
        # Boards list container
        self.boards_list = ft.Column(
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
        )
        
        # Build sidebar
        self.content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "My Boards",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Text(
                                    "👤 Guest Mode" if is_guest else "💾 Saved",
                                    size=11,
                                    color=ft.Colors.AMBER_400 if is_guest else ft.Colors.GREEN_400,
                                    italic=True,
                                ),
                            ],
                            spacing=2,
                        ),
                        padding=ft.padding.only(left=15, top=15, bottom=10),
                    ),
                    ft.Container(
                        content=self.add_board_btn,
                        padding=ft.padding.symmetric(horizontal=15),
                    ),
                    ft.Divider(color=ft.Colors.BLUE_GREY_700, height=20),
                    ft.Container(
                        content=self.boards_list,
                        padding=ft.padding.symmetric(horizontal=10),
                        expand=True,
                    ),
                ],
            ),
            width=250,
            bgcolor=ft.Colors.BLUE_GREY_900,
            padding=0,
        )
        
        # Load boards
        self.load_boards()
    
    def load_boards(self):
        """Load boards - from database for users, from memory for guests"""
        self.boards_list.controls.clear()
        
        if self.is_guest:
            # Load from in-memory storage for guests
            boards = self.guest_boards
            
            if not boards:
                self.boards_list.controls.append(
                    ft.Container(
                        content=ft.Text(
                            "No boards yet\nCreate one to get started!",
                            size=14,
                            color=ft.Colors.GREY_400,
                            italic=True,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        padding=10,
                    )
                )
            else:
                for board in boards:
                    board_item = self.create_board_item(board)
                    self.boards_list.controls.append(board_item)
        else:
            # Load from database for logged-in users
            session = get_session()
            try:
                boards = session.query(Board).filter_by(user_id=self.user.id).order_by(Board.updated_at.desc()).all()
                
                if not boards:
                    self.boards_list.controls.append(
                        ft.Container(
                            content=ft.Text(
                                "No boards yet\nCreate one to get started!",
                                size=14,
                                color=ft.Colors.GREY_400,
                                italic=True,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            padding=10,
                        )
                    )
                else:
                    for board in boards:
                        board_item = self.create_board_item(board)
                        self.boards_list.controls.append(board_item)
            except Exception as ex:
                show_snackbar(self.app_page, f"Error loading boards: {str(ex)}", is_error=True)
            finally:
                session.close()
        
        self.app_page.update()
    
    def create_board_item(self, board):
        """Create a board list item"""
        is_selected = self.selected_board_id == board.id
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.DASHBOARD,
                        size=20,
                        color=ft.Colors.WHITE if is_selected else ft.Colors.BLUE_GREY_400,
                    ),
                    ft.Text(
                        board.name,
                        size=14,
                        color=ft.Colors.WHITE if is_selected else ft.Colors.BLUE_GREY_300,
                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                        expand=True,
                    ),
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        icon_color=ft.Colors.WHITE if is_selected else ft.Colors.BLUE_GREY_400,
                        icon_size=18,
                        items=[
                            ft.PopupMenuItem(
                                content=ft.Text("Rename"),
                                icon=ft.Icons.EDIT,
                                on_click=lambda e, b=board: self.show_rename_dialog(b),
                            ),
                            ft.PopupMenuItem(
                                content=ft.Text("Delete"),
                                icon=ft.Icons.DELETE,
                                on_click=lambda e, b=board: self.show_delete_dialog(b),
                            ),
                        ],
                    ),
                ],
                spacing=10,
            ),
            padding=10,
            border_radius=5,
            bgcolor=ft.Colors.BLUE_700 if is_selected else None,
            on_click=lambda e, b=board: self.select_board(b),
            ink=True,
        )
    
    def select_board(self, board):
        """Handle board selection"""
        self.selected_board_id = board.id
        self.load_boards()  # Refresh to show selection
        if self.on_board_select:
            self.on_board_select(board)
    
    def show_add_board_dialog(self, e):
        """Show dialog to add new board"""
        board_name_field = ft.TextField(
            label="Board Name",
            autofocus=True,
            width=300,
        )
        
        def close_dialog(e):
            dialog.open = False
            self.app_page.update()
        
        def create_board(e):
            name = board_name_field.value
            if not name:
                show_snackbar(self.app_page, "Board name is required", is_error=True)
                return
            
            if self.is_guest:
                # Create in-memory board for guests
                self.guest_board_counter += 1
                new_board = type('GuestBoard', (), {
                    'id': self.guest_board_counter,
                    'name': name,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })()
                self.guest_boards.append(new_board)
                
                show_snackbar(self.app_page, f"Board '{name}' created! (Guest mode - not saved)")
                close_dialog(e)
                self.load_boards()
                if self.on_refresh:
                    self.on_refresh()
            else:
                # Save to database for logged-in users
                session = get_session()
                try:
                    new_board = Board(name=name, user_id=self.user.id)
                    session.add(new_board)
                    session.commit()
                    
                    show_snackbar(self.app_page, f"Board '{name}' created!")
                    close_dialog(e)
                    self.load_boards()
                    if self.on_refresh:
                        self.on_refresh()
                except Exception as ex:
                    session.rollback()
                    show_snackbar(self.app_page, f"Error creating board: {str(ex)}", is_error=True)
                finally:
                    session.close()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Create New Board"),
            content=board_name_field,
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Create", on_click=create_board),
            ],
        )
        
        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()
    
    def show_rename_dialog(self, board):
        """Show dialog to rename board"""
        board_name_field = ft.TextField(
            label="Board Name",
            value=board.name,
            autofocus=True,
            width=300,
        )
        
        def close_dialog(e):
            dialog.open = False
            self.app_page.update()
        
        def rename_board(e):
            new_name = board_name_field.value
            if not new_name:
                show_snackbar(self.app_page, "Board name is required", is_error=True)
                return
            
            if self.is_guest:
                # Update in-memory board for guests
                for guest_board in self.guest_boards:
                    if guest_board.id == board.id:
                        guest_board.name = new_name
                        guest_board.updated_at = datetime.now()
                        break
                
                show_snackbar(self.app_page, f"Board renamed to '{new_name}'")
                close_dialog(e)
                self.load_boards()
                if self.on_refresh:
                    self.on_refresh()
            else:
                # Update database for logged-in users
                session = get_session()
                try:
                    db_board = session.query(Board).filter_by(id=board.id).first()
                    if db_board:
                        db_board.name = new_name
                        session.commit()
                        
                        show_snackbar(self.app_page, f"Board renamed to '{new_name}'")
                        close_dialog(e)
                        self.load_boards()
                        if self.on_refresh:
                            self.on_refresh()
                except Exception as ex:
                    session.rollback()
                    show_snackbar(self.app_page, f"Error renaming board: {str(ex)}", is_error=True)
                finally:
                    session.close()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Rename Board"),
            content=board_name_field,
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Rename", on_click=rename_board),
            ],
        )
        
        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()
    
    def show_delete_dialog(self, board):
        """Show confirmation dialog to delete board"""
        def close_dialog(e):
            dialog.open = False
            self.app_page.update()
        
        def delete_board(e):
            if self.is_guest:
                # Delete from in-memory storage for guests
                self.guest_boards = [b for b in self.guest_boards if b.id != board.id]
                
                show_snackbar(self.app_page, f"Board '{board.name}' deleted")
                close_dialog(e)
                
                # Clear selection if deleted board was selected
                if self.selected_board_id == board.id:
                    self.selected_board_id = None
                
                self.load_boards()
                if self.on_refresh:
                    self.on_refresh()
            else:
                # Delete from database for logged-in users
                session = get_session()
                try:
                    db_board = session.query(Board).filter_by(id=board.id).first()
                    if db_board:
                        session.delete(db_board)
                        session.commit()
                        
                        show_snackbar(self.app_page, f"Board '{board.name}' deleted")
                        close_dialog(e)
                        
                        # Clear selection if deleted board was selected
                        if self.selected_board_id == board.id:
                            self.selected_board_id = None
                        
                        self.load_boards()
                        if self.on_refresh:
                            self.on_refresh()
                except Exception as ex:
                    session.rollback()
                    show_snackbar(self.app_page, f"Error deleting board: {str(ex)}", is_error=True)
                finally:
                    session.close()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Delete Board"),
            content=ft.Text(f"Are you sure you want to delete '{board.name}'? This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton(
                    "Delete",
                    bgcolor=ft.Colors.RED_700,
                    color=ft.Colors.WHITE,
                    on_click=delete_board
                ),
            ],
        )
        
        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()


class BoardView(ft.Container):
    """Main board view with task table"""
    
    def __init__(self, page: ft.Page, board=None, is_guest=False):
        super().__init__()
        self.app_page = page
        self.board = board
        self.is_guest = is_guest
        
        if board:
            # Board with task table
            self.content = ft.Column(
                [
                    # Board header
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.DASHBOARD, size=32, color=ft.Colors.BLUE_700),
                                ft.Text(
                                    board.name,
                                    size=28,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE_700,
                                ),
                            ],
                            spacing=15,
                        ),
                        padding=20,
                        bgcolor=ft.Colors.WHITE,
                    ),
                    ft.Divider(height=1),
                    # Task table
                    TaskTableView(page, board, is_guest=is_guest),
                ],
                expand=True,
                spacing=0,
            )
        else:
            # No board selected
            self.content = ft.Container(
                content=ft.Column(
                    [
                        ft.Container(height=100),
                        ft.Icon(
                            ft.Icons.DASHBOARD_OUTLINED,
                            size=100,
                            color=ft.Colors.GREY_300,
                        ),
                        ft.Container(height=20),
                        ft.Text(
                            "No Board Selected",
                            size=28,
                            color=ft.Colors.GREY_500,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Container(height=10),
                        ft.Text(
                            "Create a new board or select one from the sidebar",
                            size=16,
                            color=ft.Colors.GREY_400,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                expand=True,
                bgcolor=ft.Colors.BLUE_50,
            )
        
        self.expand = True
