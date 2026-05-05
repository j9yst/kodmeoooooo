import json
import os
from enum import Enum
from collections import deque

# ------------------- Model -------------------

class Priority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Status(Enum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"

class Task:
    def __init__(self, title: str, description: str = "", priority: Priority = Priority.MEDIUM, status: Status = Status.TO_DO):
        if not title:
            raise ValueError("Title cannot be empty.")
        self.title = title
        self.description = description
        self.priority = priority
        self.status = status

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value
        }

    @staticmethod
    def from_dict(data):
        try:
            priority = Priority(data["priority"])
        except ValueError:
            priority = Priority.MEDIUM # Default if invalid

        try:
            status = Status(data["status"])
        except ValueError:
            status = Status.TO_DO # Default if invalid

        return Task(
            title=data["title"],
            description=data.get("description", ""),
            priority=priority,
            status=status
        )

    def __str__(self):
        return f"[{self.status.value}/{self.priority.value}] {self.title}: {self.description}"

class TaskManagerModel:
    def __init__(self, filename="tasks.json"):
        self.tasks = []
        self.filename = filename
        self.history = deque() # Stack for undo functionality
        self.load_tasks()

    def add_task(self, task: Task):
        self.tasks.append(task)
        self._save_state(action="add", task_data=task.to_dict())
        self.save_tasks()

    def edit_task(self, index: int, new_dict(original_task_data.copy()) # Store a copy before modification

            self.tasks[index].title = new_task_data.get("title", self.tasks[index].title)
            self.tasks[index].description = new_task_data.get("description", self.tasks[index].description)
            self.tasks[index].priority = new_task_data.get("priority", self.tasks[index].priority)
            self.tasks[index].status = new_task_data.get("status", self.tasks[index].status)

            # Validate task after edit
            if not self.tasks[index].title:
                self.tasks[index] = old_task # Revert if title is empty
                raise ValueError("Title cannot be empty.")

            self._save_state(action="edit", old_task_data=original_task_data, new_task_data=self.tasks[index].to_dict())
            self.save_tasks()
        else:
            raise IndexError("Task index out of bounds.")

    def delete_task(self, index: int):
        if 0 <= index < len(self.tasks):
            deleted_task_data = self.tasks[index].to_dict()
            del self.tasks[index]
            self._save_state(action="delete", task_data=deleted_task_data)
            self.save_tasks()
        else:
            raise IndexError("Task index out of bounds.")

    def get_tasks(self):
        return self.tasks

    def get_task_by_index(self, index: int):
        if 0 <= index < len(self.tasks):
            return self.tasks[index]
        else:
            raise IndexError("Task index out of bounds.")

    def save_tasks(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([task.to_dict() for task in self.tasks], f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving tasks: {e}")

    def load_tasks(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(item) for item in data]
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading tasks: {e}") "edit":
            state["old_task_data"] = old_task_data
            state["new_task_data"] = new_task_data
        self.history.append(state)

    def undo_last_action(self):
        if not self.history:
            print("Nothing to undo.")
            return

        last_state = self.history.pop()
        action = last_state["action"]

        if action == "add":
            # Find and remove the last added task
            added_task_data = last_state["task_data"]
            for i in range(len(self.tasks) - 1 action == "delete":
            # Re-add the deleted task
            deleted_task_data = last_state["task_data"]
            self.tasks.insert(0, Task.from_dict(deleted_task_data)) # Insert at beginning for simplicity
            print("Undo: Last task deleted.")
        elif action == "edit":
            # Revert edited task to its previous state
            old_task_data = last_state["old_task_data"]
            new_task_data_current = last_state["new_task_data"]
            for i in range(len(self.tasks)):
                if self.tasks[i].to_dict() == new_task_data_current:
                    self.tasks[i] = Task.from_dict(old_task_data)
                    break
            print("Undo: Last edit reverted.")
        self.save_tasks()

    def get_tasks_by_priority_queue(self) -> list[Task]:
        # Sort tasks by priority (High > Medium > Low) and return them as a list
        # In a real "queue" scenario, you might process one by one from the highest priority
        tasks_sorted = sorted(self.tasks, key=lambda task: (
            task.priority.value == Priority.HIGH.value,
            task.priority.value == Priority.MEDIUM.value,
            task.priority.value == Priority.LOW.value
        ), reverse=True)
        return tasks_sorted

    def filter_tasks(self, status: Status = None, priority: Priority = None) -> list[Task]:
        filtered = self.tasks
        if status:
            filtered = [task for task in filtered if task.status == status]
        if priority:
            filtered = [task for task in filtered if task.priority == priority]
        return filtered

# ------------------- View -------------------

class TaskManagerView:
    def display_menu(self):
        print("\n--- Task Manager Menu ---")
        print("1. Add Task")
        print("2. View Tasks")
        print("3. Edit Task")
        print("4. Delete Task")
        print("5. Filter Tasks")
        print("6. Undo Last Action")
        print("7. View Tasks by Priority (Queue)")
        print("8. Exit")
        print("-------------------------")

    def get_user_input(self, prompt: str) -> str:
        return input(prompt).strip()

    def display_tasks(self, tasks: list[Task] = None):
        if tasks is None:
            print("\n--- All Tasks ---")
            tasks_to_display = self.model.get_tasks()
        else:
            print("\n--- Filtered/Prioritized Tasks ---")
            tasks_to_display = tasks

        if not tasks_to_display:
            print("No tasks found.")
            return

        for i, task in enumerate(tasks_to_display):
            print(f"{i}. {task}")

    def get_task_details(self) -> dict:
        title = ""
        while not title:
            title = self.get_user_input("Enter task title: ")
            if not title:
                print("Title cannot be empty.")

        description = self.get_user_input("Enter task description (optional): ")

        priority = self.get_priority_input()
        status = self.get_status_input()

        return {"title": title, "description": description, "priority": priority, "status": status}

    def get_priority_input(self) -> Priority:
        while True:
            priority_str = self.get_user_input(f"Enter priority ({', '.join([p.value for p in Priority])}): ").capitalize()
            try:
                return Priority(priority_str)
            except ValueError:
                print("Invalid priority. Please choose from the available options.")

    def get_status_input(self) -> Status:
        while True:
            status_str = self.get_user_input(f"Enter status ({', '.join([s.value for s in Status])}): ").title()
            try:
                return Status(status_str)
            except ValueError:
                print("Invalid status. Please choose from the available options.")

    def get_task_index_input(self, prompt: str) -> int:
        while True:
            try:
                index_str = self.get_user_input(prompt)
                index = int(index_str)
                return index
            except ValueError:
                print("Invalid input. Please enter a number.")

    def display_message(self, message: str):
        print(message)

    def display_error(self, error: str):
        print(f"Error: {error}")

    def set_model(self, model):
        self.model = model

# ------------------- Controller -------------------

class MenuController:
    def __init__(self, model: TaskManagerModel, view: TaskManagerView):
        self.model = model
        self.view = view
        self.view.set_model(model) # View needs access to model for getting tasks

    def run(self):
        while True:
            self.view.display_menu()
            choice = self.view.get_user_input("Enter your choice: ")

            if choice == '1': # Add Task
                self.add_task()
            elif choice == '2': # View Tasks
                self.view_tasks()
            elif choice == '3': # Edit Task
                self.edit_task()
            elif choice == '4': # Delete Task
                self.delete_task()
            elif choice == '5': # Filter Tasks
                self.filter_tasks()
            elif choice == '6': # Undo Last Action
                self.undo_action()
            elif choice == '7': # View Tasks by Priority (Queue)
                self.view_tasks_by_priority()
            elif choice == '8': # Exit
                self.view.display_message("Exiting Task Manager. Goodbye!")
                break
            else:
                self.view.display_message("Invalid choice. Please try again.")

    def add_task(self):
        try:
            task_data = self.view.get_task_details()
            new_task = Task(
                title=task_data["title"],
                description=task_data["description"],
                priority=task_data["priority"],
                status=task_data["status"]
            )
            self.model.add_task(new_task)
            self.view.display_message("Task added successfully!")
        except ValueError as e:
            self.view.display_error(str(e))
        except Exception as e:
            self.view.display_error(f"An unexpected error occurred: {e}")

    def view_tasks(self):
        self.view.display_tasks()

    def edit_task(self):
        current_tasks = self.model.get_tasks()
        if not current_tasks:
            self.view.display_message("No tasks to edit.")
            return

        self.view.display_tasks()
        try:
            index = self.view.get_task_index_input("Enter the number of the task to edit: ")
            if not (0 <= index < len(current_tasks)):
                self.view.display_error("Invalid task number.")
                return

            print(f"Editing task: {current_tasks[index]}")
            print("Enter new details (leave blank to keep current value):")

            new_title = self.view.get_user_input(f"Enter new title [{current_tasks[index].title}]: ")
            if not new_title:
                new_title = current_tasks[index].title # Keep original if empty

            new_description = self.view.get_user_input(f"Enter new description [{current_tasks[index].description}]: ")
            if not new_description and current_tasks[index].description is not None:
                new_description = current_tasks[index].description # Keep original if empty

            # Handle priority and status, allowing for empty input to signify no change
            current_priority = current_tasks[index].priority
            priority_input = self.view.get_user_input(f"Enter new priority ({', '.join([p.value for p in Priority])}) [{current_priority.value}]: ").capitalize()
            new_priority = current_priority
            if priority_input:
                try:
                    new_priority = Priority(priority_input)
                except ValueError:
                    self.view.display_error("Invalid priority input. Keeping current priority.")

            current_status = current_tasks[index].status
            status_input = self.view.get_user_input(f"Enter new status ({', '.join([s.value for s in Status])}) [{current_status.value}]: ").title()
            new_status = current_status
            if status_input:
                try:
                    new_status = Status(status_input)
                except ValueError:
                    self.view.display_error("Invalid status input. Keeping current status.")

            updated_data = {
                "title": new_title,
                "description": new_description,
                "priority": new_priority,
                "status": new_status
            }
            self.model.edit_task(index, updated_data)
            self.view.display_message("Task updated successfully!")
        except IndexError as e:
            self.view.display_error(str(e))
        except ValueError as e: # For title validation during edit
            self.view.display_error(str(e))
        except Exception as e:
            self.view.display_error(f"An unexpected error occurred: {e}")

    def delete_task(self):
        current_tasks = self.model.get_tasks()
        if not current_tasks:
            self.view.display_message("No tasks to delete.")
            return

        self.view.display_tasks()
        try:
            index = self.view.get_task_index_input("Enter the number of the task to delete: ")
            self.model.delete_task(index)
            self.view.display_message("Task deleted successfully!")
        except IndexError as e:
            self.view.display_error(str(e))
        except Exception as e:
            self.view.display_error(f"An unexpected error occurred: {e}")

    def filter_tasks(self):
        print("\n--- Filter Tasks ---")
        filter_status_str = self.view.get_user_input(f"Filter by status ({', '.join([s.value for s in Status])}, or leave blank for all): ").title()
        filter_priority_str = self.view.get_user_input(f"Filter by priority ({', '.join([p.value for p in Priority])}, or leave blank for all): ").capitalize()

        selected_status = None
        if filter_status_str:
            try:
                selected_status = Status(filter_status_str)
            except ValueError:
                self.view.display_error("Invalid status filter. Ignoring status filter.")

        selected_priority = None
        if filter_priority_str:
            try:
                selected_priority = Priority(filter_priority_str)
            except ValueError:
                self.view.display_error("Invalid priority filter. Ignoring priority filter.")

        filtered_tasks = self.model.filter_tasks(status=selected_status, priority=selected_priority)
        self.view.display_tasks(filtered_tasks)

    def undo_action(self):
        self.model.undo_last_action()
        self.view.display_message("Undo operation performed.")

    def view_tasks_by_priority(self):
        prioritized_tasks = self.model.get_tasks_by_priority_queue()
        self.view.display_tasks(prioritized_tasks)

# ------------------- Main Application -------------------

def main():
    model = TaskManagerModel()
    view = TaskManagerView()
    controller = MenuController(model, view)
    controller.run()

#ура победа
if __name__ == "__main__":
    main()
