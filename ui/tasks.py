import flet as ft
from database import get_session
from models import BoardColumn, Task, TaskCell
from datetime import datetime


# Status options with colors
STATUS_OPTIONS = {
    "Done": ft.Colors.GREEN_600,
    "Working On It": ft.Colors.AMBER_600,
    "Stuck": ft.Colors.RED_600,
    "": ft.Colors.GREY_400,  # Empty/not set
}


def show_snackbar(page: ft.Page, message: str, is_error: bool = False):
    """Helper function to show snackbar notifications"""
    snackbar = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700,
    )
    snackbar.open = True
    page.overlay.append(snackbar)
    page.update()


class TaskTableView(ft.Container):
    """Task table with columns and rows"""
    
    def __init__(self, page: ft.Page, board, is_guest=False, on_refresh=None):
        super().__init__()
        self.app_page = page
        self.board = board
        self.is_guest = is_guest
        self.on_refresh = on_refresh
        
        # In-memory storage for guest mode
        self.guest_columns = []
        self.guest_tasks = []
        self.guest_cells = {}  # {task_id: {column_id: value}}
        self.guest_column_counter = 0
        self.guest_task_counter = 0
        
        # Initialize with default columns for new boards
        if is_guest and not self.guest_columns:
            self._create_default_columns_guest()
        elif not is_guest:
            self._ensure_default_columns()
        
        # Table header and content
        self.table_header = ft.Row(scroll=ft.ScrollMode.AUTO)
        self.table_content = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0)
        
        # Build UI
        self.content = ft.Column(
            [
                # Action buttons
                ft.Container(
                    content=ft.Row(
                        [
                            ft.ElevatedButton(
                                content=ft.Text("+ Add Task"),
                                bgcolor=ft.Colors.BLUE_700,
                                color=ft.Colors.WHITE,
                                on_click=self.add_task,
                            ),
                            ft.ElevatedButton(
                                content=ft.Text("+ Add Column"),
                                bgcolor=ft.Colors.GREEN_700,
                                color=ft.Colors.WHITE,
                                on_click=self.show_add_column_dialog,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=15,
                ),
                ft.Divider(height=1),
                # Table header
                ft.Container(
                    content=self.table_header,
                    bgcolor=ft.Colors.BLUE_GREY_50,
                    padding=10,
                ),
                # Table content
                ft.Container(
                    content=self.table_content,
                    expand=True,
                    padding=10,
                ),
            ],
            expand=True,
        )
        
        self.expand = True
        self.bgcolor = ft.Colors.WHITE
        
        # Load data
        self.refresh_table()
    
    def _create_default_columns_guest(self):
        """Create default columns for guest mode"""
        self.guest_column_counter += 1
        self.guest_columns.append(type('GuestColumn', (), {
            'id': self.guest_column_counter,
            'name': 'Status',
            'column_type': 'status',
            'position': 0
        })())
        
        self.guest_column_counter += 1
        self.guest_columns.append(type('GuestColumn', (), {
            'id': self.guest_column_counter,
            'name': 'Notes',
            'column_type': 'text',
            'position': 1
        })())
        
        self.guest_column_counter += 1
        self.guest_columns.append(type('GuestColumn', (), {
            'id': self.guest_column_counter,
            'name': 'Due Date',
            'column_type': 'date',
            'position': 2
        })())
    
    def _ensure_default_columns(self):
        """Ensure board has default columns"""
        session = get_session()
        try:
            existing_columns = session.query(BoardColumn).filter_by(board_id=self.board.id).count()
            if existing_columns == 0:
                # Add default columns
                columns = [
                    BoardColumn(board_id=self.board.id, name="Status", column_type="status", position=0),
                    BoardColumn(board_id=self.board.id, name="Notes", column_type="text", position=1),
                    BoardColumn(board_id=self.board.id, name="Due Date", column_type="date", position=2),
                ]
                for col in columns:
                    session.add(col)
                session.commit()
        except Exception as ex:
            session.rollback()
            show_snackbar(self.app_page, f"Error creating columns: {str(ex)}", is_error=True)
        finally:
            session.close()
    
    def refresh_table(self):
        """Refresh the entire table"""
        self.table_header.controls.clear()
        self.table_content.controls.clear()
        
        # Get columns
        if self.is_guest:
            columns = sorted(self.guest_columns, key=lambda c: c.position)
        else:
            session = get_session()
            try:
                columns = session.query(BoardColumn).filter_by(board_id=self.board.id).order_by(BoardColumn.position).all()
            finally:
                session.close()
        
        # Build header
        self.table_header.controls.append(
            ft.Container(
                content=ft.Text("Task Name", weight=ft.FontWeight.BOLD, size=14),
                width=200,
                padding=10,
            )
        )
        
        for col in columns:
            self.table_header.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(col.name, weight=ft.FontWeight.BOLD, size=14, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_size=16,
                                tooltip="Delete column",
                                on_click=lambda e, c=col: self.delete_column(c),
                            ),
                        ],
                    ),
                    width=200,
                    padding=10,
                )
            )
        
        # Get tasks
        if self.is_guest:
            tasks = sorted(self.guest_tasks, key=lambda t: t.position)
        else:
            session = get_session()
            try:
                tasks = session.query(Task).filter_by(board_id=self.board.id).order_by(Task.position).all()
            finally:
                session.close()
        
        # Build rows
        for task in tasks:
            self.table_content.controls.append(self.create_task_row(task, columns))
        
        if not tasks:
            self.table_content.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No tasks yet. Click '+ Add Task' to get started!",
                        color=ft.Colors.GREY_500,
                        italic=True,
                    ),
                    padding=20,
                )
            )
        
        self.app_page.update()
    
    def create_task_row(self, task, columns):
        """Create a task row with cells"""
        row_controls = []
        
        # Task name cell (editable)
        task_name_field = ft.TextField(
            value=task.name,
            border=ft.InputBorder.NONE,
            on_submit=lambda e, t=task: self.update_task_name(t, e.control.value),
            on_blur=lambda e, t=task: self.update_task_name(t, e.control.value),
        )
        
        row_controls.append(
            ft.Container(
                content=ft.Row(
                    [
                        task_name_field,
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_size=16,
                            tooltip="Delete task",
                            on_click=lambda e, t=task: self.delete_task(t),
                        ),
                    ],
                ),
                width=200,
                padding=5,
                border=ft.border.all(1, ft.Colors.GREY_300),
            )
        )
        
        # Column cells
        for col in columns:
            cell_value = self.get_cell_value(task, col)
            row_controls.append(self.create_cell(task, col, cell_value))
        
        return ft.Row(row_controls, spacing=0)
    
    def get_cell_value(self, task, column):
        """Get cell value for task and column"""
        if self.is_guest:
            return self.guest_cells.get(task.id, {}).get(column.id, "")
        else:
            session = get_session()
            try:
                cell = session.query(TaskCell).filter_by(task_id=task.id, column_id=column.id).first()
                return cell.value if cell else ""
            finally:
                session.close()
    
    def create_cell(self, task, column, value):
        """Create a cell based on column type"""
        if column.column_type == "status":
            return self.create_status_cell(task, column, value)
        elif column.column_type == "date":
            return self.create_date_cell(task, column, value)
        else:  # text
            return self.create_text_cell(task, column, value)
    
    def create_status_cell(self, task, column, value):
        """Create status cell with color"""
        status_value = value or ""
        status_color = STATUS_OPTIONS.get(status_value, ft.Colors.GREY_400)
        
        return ft.Container(
            content=ft.Container(
                content=ft.Text(
                    status_value or "Not set",
                    color=ft.Colors.WHITE if status_value else ft.Colors.GREY_600,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=status_color,
                padding=ft.padding.symmetric(horizontal=15, vertical=8),
                border_radius=15,
                on_click=lambda e, t=task, c=column: self.cycle_status(t, c),
            ),
            width=200,
            padding=5,
            border=ft.border.all(1, ft.Colors.GREY_300),
            alignment=ft.Alignment(-1, 0),  # center_left
        )
    
    def create_text_cell(self, task, column, value):
        """Create text input cell"""
        text_field = ft.TextField(
            value=value or "",
            border=ft.InputBorder.NONE,
            on_submit=lambda e, t=task, c=column: self.update_cell(t, c, e.control.value),
            on_blur=lambda e, t=task, c=column: self.update_cell(t, c, e.control.value),
            multiline=False,
        )
        
        return ft.Container(
            content=text_field,
            width=200,
            padding=5,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )
    
    def create_date_cell(self, task, column, value):
        """Create date input cell"""
        date_field = ft.TextField(
            value=value or "",
            border=ft.InputBorder.NONE,
            hint_text="YYYY-MM-DD",
            on_submit=lambda e, t=task, c=column: self.update_cell(t, c, e.control.value),
            on_blur=lambda e, t=task, c=column: self.update_cell(t, c, e.control.value),
        )
        
        return ft.Container(
            content=date_field,
            width=200,
            padding=5,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )
    
    def cycle_status(self, task, column):
        """Cycle through status values"""
        current_value = self.get_cell_value(task, column)
        status_list = list(STATUS_OPTIONS.keys())
        
        try:
            current_index = status_list.index(current_value)
            next_index = (current_index + 1) % len(status_list)
        except ValueError:
            next_index = 0
        
        new_value = status_list[next_index]
        self.update_cell(task, column, new_value)
    
    def update_task_name(self, task, new_name):
        """Update task name"""
        if not new_name.strip():
            return
        
        if self.is_guest:
            for guest_task in self.guest_tasks:
                if guest_task.id == task.id:
                    guest_task.name = new_name
                    break
        else:
            session = get_session()
            try:
                db_task = session.query(Task).filter_by(id=task.id).first()
                if db_task:
                    db_task.name = new_name
                    session.commit()
            except Exception as ex:
                session.rollback()
                show_snackbar(self.app_page, f"Error updating task: {str(ex)}", is_error=True)
            finally:
                session.close()
        
        self.refresh_table()
    
    def update_cell(self, task, column, value):
        """Update cell value"""
        if self.is_guest:
            if task.id not in self.guest_cells:
                self.guest_cells[task.id] = {}
            self.guest_cells[task.id][column.id] = value
        else:
            session = get_session()
            try:
                cell = session.query(TaskCell).filter_by(task_id=task.id, column_id=column.id).first()
                if cell:
                    cell.value = value
                else:
                    cell = TaskCell(task_id=task.id, column_id=column.id, value=value)
                    session.add(cell)
                session.commit()
            except Exception as ex:
                session.rollback()
                show_snackbar(self.app_page, f"Error updating cell: {str(ex)}", is_error=True)
            finally:
                session.close()
        
        self.refresh_table()
    
    def add_task(self, e):
        """Add a new task"""
        if self.is_guest:
            self.guest_task_counter += 1
            new_task = type('GuestTask', (), {
                'id': self.guest_task_counter,
                'name': f'New Task {self.guest_task_counter}',
                'position': len(self.guest_tasks),
                'board_id': self.board.id
            })()
            self.guest_tasks.append(new_task)
            show_snackbar(self.app_page, "Task added! (Guest mode - not saved)")
        else:
            session = get_session()
            try:
                task_count = session.query(Task).filter_by(board_id=self.board.id).count()
                new_task = Task(
                    board_id=self.board.id,
                    name=f"New Task {task_count + 1}",
                    position=task_count
                )
                session.add(new_task)
                session.commit()
                show_snackbar(self.app_page, "Task added!")
            except Exception as ex:
                session.rollback()
                show_snackbar(self.app_page, f"Error adding task: {str(ex)}", is_error=True)
            finally:
                session.close()
        
        self.refresh_table()
    
    def delete_task(self, task):
        """Delete a task"""
        if self.is_guest:
            self.guest_tasks = [t for t in self.guest_tasks if t.id != task.id]
            if task.id in self.guest_cells:
                del self.guest_cells[task.id]
            show_snackbar(self.app_page, "Task deleted")
        else:
            session = get_session()
            try:
                db_task = session.query(Task).filter_by(id=task.id).first()
                if db_task:
                    session.delete(db_task)
                    session.commit()
                    show_snackbar(self.app_page, "Task deleted")
            except Exception as ex:
                session.rollback()
                show_snackbar(self.app_page, f"Error deleting task: {str(ex)}", is_error=True)
            finally:
                session.close()
        
        self.refresh_table()
    
    def show_add_column_dialog(self, e):
        """Show dialog to add new column"""
        column_name_field = ft.TextField(label="Column Name", autofocus=True, width=300)
        column_type_dropdown = ft.Dropdown(
            label="Column Type",
            width=300,
            options=[
                ft.dropdown.Option("text", "Text"),
                ft.dropdown.Option("status", "Status"),
                ft.dropdown.Option("date", "Date"),
            ],
            value="text"
        )
        
        def close_dialog(e):
            dialog.open = False
            self.app_page.update()
        
        def create_column(e):
            name = column_name_field.value
            col_type = column_type_dropdown.value
            
            if not name:
                show_snackbar(self.app_page, "Column name is required", is_error=True)
                return
            
            if self.is_guest:
                self.guest_column_counter += 1
                new_column = type('GuestColumn', (), {
                    'id': self.guest_column_counter,
                    'name': name,
                    'column_type': col_type,
                    'position': len(self.guest_columns)
                })()
                self.guest_columns.append(new_column)
                show_snackbar(self.app_page, f"Column '{name}' added! (Guest mode)")
            else:
                session = get_session()
                try:
                    col_count = session.query(BoardColumn).filter_by(board_id=self.board.id).count()
                    new_column = BoardColumn(
                        board_id=self.board.id,
                        name=name,
                        column_type=col_type,
                        position=col_count
                    )
                    session.add(new_column)
                    session.commit()
                    show_snackbar(self.app_page, f"Column '{name}' added!")
                except Exception as ex:
                    session.rollback()
                    show_snackbar(self.app_page, f"Error adding column: {str(ex)}", is_error=True)
                finally:
                    session.close()
            
            close_dialog(e)
            self.refresh_table()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Add New Column"),
            content=ft.Column([column_name_field, column_type_dropdown], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Add", on_click=create_column),
            ],
        )
        
        self.app_page.overlay.append(dialog)
        dialog.open = True
        self.app_page.update()
    
    def delete_column(self, column):
        """Delete a column"""
        if self.is_guest:
            self.guest_columns = [c for c in self.guest_columns if c.id != column.id]
            # Remove cells for this column
            for task_cells in self.guest_cells.values():
                if column.id in task_cells:
                    del task_cells[column.id]
            show_snackbar(self.app_page, f"Column '{column.name}' deleted")
        else:
            session = get_session()
            try:
                db_column = session.query(BoardColumn).filter_by(id=column.id).first()
                if db_column:
                    session.delete(db_column)
                    session.commit()
                    show_snackbar(self.app_page, f"Column '{column.name}' deleted")
            except Exception as ex:
                session.rollback()
                show_snackbar(self.app_page, f"Error deleting column: {str(ex)}", is_error=True)
            finally:
                session.close()
        
        self.refresh_table()
