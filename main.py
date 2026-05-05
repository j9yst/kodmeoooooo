import json
import os
from enum import Enum
from collections import deque
from typing import List, Optional, Dict, Any, Tuple
from copy import deepcopy

# ==================== Модель данных (Model) ====================

class Priority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    
    @classmethod
    def from_string(cls, value: str) -> 'Priority':
        if not value:
            return cls.MEDIUM
        for priority in cls:
            if priority.value.lower() == value.lower():
                return priority
        raise ValueError(f"Некорректный приоритет: {value}")
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        return [p.value for p in cls]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value.lower() in [p.value.lower() for p in cls]


class Status(Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    
    @classmethod
    def from_string(cls, value: str) -> 'Status':
        if not value:
            return cls.TODO
        for status in cls:
            if status.value.lower() == value.lower():
                return status
        raise ValueError(f"Некорректный статус: {value}")
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        return [s.value for s in cls]
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value.lower() in [s.value.lower() for s in cls]


class Task:
    """Класс задачи с использованием инкапсуляции"""
    def __init__(self, task_id: int, title: str, description: str, 
                 priority: Priority, status: Status):
        self._id = task_id
        self._title = title
        self._description = description
        self._priority = priority
        self._status = status
    
    # Геттеры
    @property
    def id(self) -> int:
        return self._id
    
    @property
    def title(self) -> str:
        return self._title
    
    @title.setter
    def title(self, value: str):
        if not value or not value.strip():
            raise ValueError("Название не может быть пустым")
        self._title = value.strip()
    
    @property
    def description(self) -> str:
        return self._description
    
    @description.setter
    def description(self, value: str):
        self._description = value.strip() if value else ""
    
    @property
    def priority(self) -> Priority:
        return self._priority
    
    @priority.setter
    def priority(self, value: Priority):
        if not isinstance(value, Priority):
            raise ValueError("Некорректный тип приоритета")
        self._priority = value
    
    @property
    def status(self) -> Status:
        return self._status
    
    @status.setter
    def status(self, value: Status):
        if not isinstance(value, Status):
            raise ValueError("Некорректный тип статуса")
        self._status = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь для JSON"""
        return {
            "id": self._id,
            "title": self._title,
            "description": self._description,
            "priority": self._priority.value,
            "status": self._status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Десериализация из словаря"""
        return cls(
            task_id=data["id"],
            title=data["title"],
            description=data["description"],
            priority=Priority.from_string(data["priority"]),
            status=Status.from_string(data["status"])
        )
    
    def __str__(self) -> str:
        priority_icon = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
        status_icon = {"To Do": "⭕", "In Progress": "🔄", "Done": "✅"}
        return (f"[{self._id}] {self._title}\n"
                f" Описание: {self._description}\n"
                f" Приоритет: {priority_icon.get(self._priority.value, '')} {self._priority.value}\n"
                f" Статус: {status_icon.get(self._status.value, '')} {self._status.value}")


class UndoStack:
    """Стек для отмены последних действий"""
    def __init__(self, max_size: int = 50):
        self._stack: List[Dict[str, Any]] = []
        self._max_size = max_size
    
    def push(self, action_type: str, data: Any):
        """Добавить действие в стек"""
        self._stack.append({
            "type": action_type,
            "data": deepcopy(data), # Глубокое копирование для сохранения состояния
            "timestamp": len(self._stack)
        })
        if len(self._stack) > self._max_size:
            self._stack.pop(0)
    
    def pop(self) -> Optional[Dict[str, Any]]:
        """Извлечь последнее действие"""
        if self._stack:
            return self._stack.pop()
        return None
    
    def peek(self) -> Optional[Dict[str, Any]]:
        """Посмотреть последнее действие без извлечения"""
        if self._stack:
            return self._stack[-1]
        return None
    
    def is_empty(self) -> bool:
        return len(self._stack) == 0
    
    def clear(self):
        self._stack.clear()
    
    def size(self) -> int:
        return len(self._stack)


class TaskManager:
    """Управление задачами с использованием очереди по приоритету"""
    def __init__(self):
        self._tasks: Dict[int, Task] = {}
        self._next_id: int = 1
        self._priority_queue: deque = deque() # Очередь задач по приоритету
        self._undo_stack = UndoStack()
    
    def _save_state_for_undo(self, action_type: str, task_id: int = None, old_state: Dict = None):
        """Сохранить состояние для отмены действия"""
        if action_type == "add" and task_id:
            # При добавлении сохраняем ID добавленной задачи
            self._undo_stack.push("add", {"id": task_id})
        elif action_type == "delete" and task_id:
            # При удалении сохраняем полные данные задачи
            task = self.get_task(task_id)
            if task:
                self._undo_stack.push("delete", task.to_dict())
        elif action_type == "update" and old_state:
            # При обновлении сохраняем старое состояние
            self._undo_stack.push("update", old_state)
    
    def add_task(self, title: str, description: str, priority: Priority, status: Status) -> Task:
        """Добавить новую задачу"""
        # Валидация входных данных
        if not title or not title.strip():
            raise ValueError("Название задачи не может быть пустым")
        
        task = Task(self._next_id, title, description, priority, status)
        self._tasks[task.id] = task
        self._add_to_priority_queue(task)
        self._next_id += 1
        
        # Сохраняем состояние для отмены
        self._save_state_for_undo("add", task.id)
        return task
    
    def _add_to_priority_queue(self, task: Task):
        """Добавить задачу в очередь по приоритету"""
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        self._priority_queue.append((priority_order[task.priority.value], task.id))
        # Сортируем очередь по приоритету
        self._priority_queue = deque(sorted(self._priority_queue, key=lambda x: x[0]))
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Получить задачу по ID"""
        return self._tasks.get(task_id)
    
    def update_task(self, task_id: int, title: str = None, description: str = None,
                   priority: Priority = None, status: Status = None) -> bool:
        """Обновить задачу"""
        task = self.get_task(task_id)
        if not task:
            return False
        
        # Сохраняем старое состояние для отмены
        old_state = {
            "id": task_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "status": task.status.value
        }
        
        # Обновляем поля с валидацией
        try:
            if title is not None:
                task.title = title
            if description is not None:
                task.description = description
            if priority is not None:
                task.priority = priority
            if status is not None:
                task.status = status
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
            return False
        
        self._save_state_for_undo("update", old_state=old_state)
        
        # Обновляем очередь приоритетов если изменился приоритет
        if priority is not None:
            self._update_priority_queue(task)
        
        return True
    
    def _update_priority_queue(self, task: Task):
        """Обновить позицию задачи в очереди приоритетов"""
        # Удаляем старую запись
        self._priority_queue = deque([item for item in self._priority_queue if item[1] != task.id])
        # Добавляем новую
        self._add_to_priority_queue(task)
    
    def delete_task(self, task_id: int) -> bool:
        """Удалить задачу"""
        task = self.get_task(task_id)
        if not task:
            return False
        
        # Сохраняем задачу для отмены
        self._save_state_for_undo("delete", task_id)
        
        # Удаляем из очереди
        self._priority_queue = deque([item for item in self._priority_queue if item[1] != task_id])
        
        # Удаляем задачу
        del self._tasks[task_id]
        return True
    
    def undo_last_action(self) -> bool:
        """Отменить последнее действие"""
        action = self._undo_stack.pop()
        if not action:
            return False
        
        action_type = action["type"]
        data = action["data"]
        
        try:
            if action_type == "add":
                # Удаляем добавленную задачу
                return self.delete_task(data["id"])
            elif action_type == "delete":
                # Восстанавливаем удаленную задачу
                task_data = data
                # Проверяем, не существует ли уже задача с таким ID
                if task_data["id"] in self._tasks:
                    # Если существует, создаем с новым ID
                    task_data["id"] = self._next_id
                    self._next_id += 1
                
                task = Task.from_dict(task_data)
                self._tasks[task.id] = task
                self._add_to_priority_queue(task)
                if task.id >= self._next_id:
                    self._next_id = task.id + 1
                return True
            elif action_type == "update":
                # Восстанавливаем старое состояние
                task = self.get_task(data["id"])
                if task:
                    task.title = data["title"]
                    task.description = data["description"]
                    task.priority = Priority.from_string(data["priority"])
                    task.status = Status.from_string(data["status"])
                    self._update_priority_queue(task)
                    return True
        except Exception as e:
            print(f"Ошибка при отмене действия: {e}")
            return False
        
        return False
    
    def get_all_tasks(self) -> List[Task]:
        """Получить все задачи"""
        return list(self._tasks.values())
    
    def filter_by_status(self, status: Status) -> List[Task]:
        """Фильтрация по статусу"""
        if not isinstance(status, Status):
            raise ValueError("Некорректный статус")
        return [task for task in self._tasks.values() if task.status == status]
    
    def filter_by_priority(self, priority: Priority) -> List[Task]:
        """Фильтрация по приоритету"""
        if not isinstance(priority, Priority):
            raise ValueError("Некорректный приоритет")
        return [task for task in self._tasks.values() if task.priority == priority]
    
    def get_tasks_by_priority_order(self) -> List[Task]:
        """Получить задачи в порядке приоритета (из очереди)"""
        tasks_by_priority = []
        for _, task_id in self._priority_queue:
            task = self.get_task(task_id)
            if task:
                tasks_by_priority.append(task)
        return tasks_by_priority
    
    def save_to_file(self, filename: str = "tasks.json"):
        """Сохранить задачи в JSON файл"""
        try:
            data = {
                "next_id": self._next_id,
                "tasks": [task.to_dict() for task in self._tasks.values()]
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False
    
    def load_from_file(self, filename: str = "tasks.json") -> bool:
        """Загрузить задачи из JSON файла"""
        if not os.path.exists(filename):
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Очищаем текущие данные
            self._tasks.clear()
            self._priority_queue.clear()
            self._undo_stack.clear()
            
            self._next_id = data.get("next_id", 1)
            for task_data in data.get("tasks", []):
                task = Task.from_dict(task_data)
                self._tasks[task.id] = task
                self._add_to_priority_queue(task)
            return True
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Ошибка загрузки файла: {e}")
            return False


# ==================== Представление (View) ====================

class ConsoleView:
    """Консольное представление для взаимодействия с пользователем"""
    
    @staticmethod
    def display_menu():
        """Отобразить главное меню"""
        print("\n" + "="*50)
        print(" МЕНЕДЖЕР ЗАДАЧ")
        print("="*50)
        print("1. 📋 Показать все задачи")
        print("2. ➕ Добавить задачу")
        print("3. ✏️ Редактировать задачу")
        print("4. ❌ Удалить задачу")
        print("5. 🔍 Фильтрация задач")
        print("6. 📊 Показать задачи по приоритету")
        print("7. ↩️ Отменить последнее действие")
        print("8. 💾 Сохранить в файл")
        print("9. 📂 Загрузить из файла")
        print("0. 🚪 Выход")
        print("-"*50)
    
    @staticmethod
    def display_tasks(tasks: List[Task], title: str = "Задачи"):
        """Отобразить список задач"""
        if not tasks:
            print(f"\n{title} не найдены.")
            return
        
        print(f"\n{title}:")
        print("-" * 50)
        for i, task in enumerate(tasks, 1):
            print(task)
            if i < len(tasks):
                print("-" * 30)
    
    @staticmethod
    def get_task_input() -> Tuple[str, str, Priority, Status]:
        """Получить данные новой задачи от пользователя"""
        while True:
            title = input("Введите название задачи: ").strip()
            if title:
                break
            print("❌ Ошибка: Название не может быть пустым!")
        
        description = input("Введите описание задачи: ").strip()
        
        print("\nДоступные приоритеты:")
        for p in Priority.get_all_values():
            print(f" - {p}")
        
        while True:
            priority_input = input("Выберите приоритет (Low/Medium/High): ").strip()
            try:
                priority = Priority.from_string(priority_input)
                break
            except ValueError:
                print("❌ Ошибка: Некорректный приоритет! Используйте Low, Medium или High")
        
        print("\nДоступные статусы:")
        for s in Status.get_all_values():
            print(f" - {s}")
        
        while True:
            status_input = input("Выберите статус (To Do/In Progress/Done): ").strip()
            try:
                status = Status.from_string(status_input)
                break
            except ValueError:
                print("❌ Ошибка: Некорректный статус! Используйте To Do, In Progress или Done")
        
        return title, description, priority, status
    
    @staticmethod
    def get_task_id(prompt: str = "Введите ID задачи") -> Optional[int]:
        """Получить ID задачи от пользователя"""
        try:
            task_id = int(input(f"{prompt}: ").strip())
            if task_id <= 0:
                print("❌ Ошибка: ID должен быть положительным числом!")
                return None
            return task_id
        except ValueError:
            print("❌ Ошибка: Введите корректное число!")
            return None
    
    @staticmethod
    def get_filter_criteria() -> Tuple[Optional[str], Optional[any]]:
        """Получить критерии фильтрации"""
        print("\nФильтровать по:")
        print("1. Статусу")
        print("2. Приоритету")
        
        choice = input("Выберите опцию: ").strip()
        
        if choice == "1":
            print("\nДоступные статусы:")
            for s in Status.get_all_values():
                print(f" - {s}")
            
            while True:
                status_input = input("Выберите статус: ").strip()
                try:
                    status = Status.from_string(status_input)
                    return "status", status
                except ValueError:
                    print("❌ Ошибка: Некорректный статус!")
                    
        elif choice == "2":
            print("\nДоступные приоритеты:")
            for p in Priority.get_all_values():
                print(f" - {p}")
            
            while True:
                priority_input = input("Выберите приоритет: ").strip()
                try:
                    priority = Priority.from_string(priority_input)
                    return "priority", priority
                except ValueError:
                    print("❌ Ошибка: Некорректный приоритет!")
        else:
            print("❌ Неверный выбор!")
        
        return None, None
    
    @staticmethod
    def display_message(message: str, is_error: bool = False):
        """Отобразить сообщение"""
        prefix = "❌" if is_error else "✅"
        print(f"{prefix} {message}")
    
    @staticmethod
    def get_edit_input(task: Task) -> Tuple[str, str, str, str]:
        """Получить данные для редактирования задачи"""
        print(f"\nРедактирование задачи #{task.id}")
        print(f"Текущее название: {task.title}")
        new_title = input("Новое название (Enter для сохранения): ").strip()
        
        print(f"Текущее описание: {task.description}")
        new_description = input("Новое описание (Enter для сохранения): ").strip()
        
        print(f"Текущий приоритет: {task.priority.value}")
        print("Доступные приоритеты: Low, Medium, High")
        new_priority_input = input("Новый приоритет (Enter для сохранения): ").strip()
        
        print(f"Текущий статус: {task.status.value}")
        print("Доступные статусы: To Do, In Progress, Done")
        new_status_input = input("Новый статус (Enter для сохранения): ").strip()
        
        return new_title, new_description, new_priority_input, new_status_input
    
    @staticmethod
    def show_welcome():
        """Показать приветственное сообщение"""
        print("\n" + "="*50)
        print(" Добро пожаловать в Task Manager!")
        print(" Управляйте своими задачами легко и удобно")
        print("="*50)


# ==================== Контроллер (Controller) ====================

class MenuController:
    """Контроллер для обработки команд пользователя"""
    
    def __init__(self, task_manager: TaskManager, view: ConsoleView):
        self.task_manager = task_manager
        self.view = view
        self.running = True
    
    def run(self):
        """Запустить главный цикл приложения"""
        self.view.show_welcome()
        
        # Автоматическая загрузка при старте
        if self.task_manager.load_from_file():
            self.view.display_message("Данные загружены из файла")
        else:
            self.view.display_message("Файл с данными не найден, создан новый список задач")
        
        while self.running:
            self.view.display_menu()
            choice = input("\nВыберите действие: ").strip()
            self.handle_choice(choice)
    
    def handle_choice(self, choice: str):
        """Обработать выбор пользователя"""
        actions = {
            "1": self.show_all_tasks,
            "2": self.add_task,
            "3": self.edit_task,
            "4": self.delete_task,
            "5": self.filter_tasks,
            "6": self.show_by_priority,
            "7": self.undo_action,
            "8": self.save_tasks,
            "9": self.load_tasks,
            "0": self.exit_app
        }
        
        action = actions.get(choice)
        if action:
            action()
        else:
            self.view.display_message("Неверный выбор! Попробуйте снова.", is_error=True)
    
    def show_all_tasks(self):
        """Показать все задачи"""
        tasks = self.task_manager.get_all_tasks()
        if not tasks:
            self.view.display_message("Нет задач для отображения")
        else:
            self.view.display_tasks(tasks, "Все задачи")
    
    def add_task(self):
        """Добавить новую задачу"""
        try:
            title, description, priority, status = self.view.get_task_input()
            task = self.task_manager.add_task(title, description, priority, status)
            self.view.display_message(f"Задача '{task.title}' успешно добавлена с ID {task.id}")
        except ValueError as e:
            self.view.display_message(str(e), is_error=True)
    
    def edit_task(self):
        """Редактировать задачу"""
        task_id = self.view.get_task_id("Введите ID задачи для редактирования")
        if task_id is None:
            return
        
        task = self.task_manager.get_task(task_id)
        if not task:
            self.view.display_message(f"Задача с ID {task_id} не найдена", is_error=True)
            return
        
        self.view.display_tasks([task], "Редактируемая задача")
        
        new_title, new_description, new_priority_input, new_status_input = self.view.get_edit_input(task)
        
        # Подготавливаем обновления
        title = new_title if new_title else None
        description = new_description if new_description else None
        
        priority = None
        if new_priority_input:
            try:
                priority = Priority.from_string(new_priority_input)
            except ValueError:
                self.view.display_message("Некорректный приоритет, оставляем текущий", is_error=True)
        
        status = None
        if new_status_input:
            try:
                status = Status.from_string(new_status_input)
            except ValueError:
                self.view.display_message("Некорректный статус, оставляем текущий", is_error=True)
        
        if self.task_manager.update_task(task_id, title, description, priority, status):
            self.view.display_message("Задача успешно обновлена")
        else:
            self.view.display_message("Ошибка при обновлении задачи", is_error=True)
    
    def delete_task(self):
        """Удалить задачу"""
        task_id = self.view.get_task_id("Введите ID задачи для удаления")
        if task_id is None:
            return
        
        task = self.task_manager.get_task(task_id)
        if not task:
            self.view.display_message(f"Задача с ID {task_id} не найдена", is_error=True)
            return
        
        self.view.display_tasks([task], "Удаляемая задача")
        confirm = input("Вы уверены, что хотите удалить эту задачу? (y/n): ").strip().lower()
        
        if confirm == 'y' or confirm == 'yes':
            if self.task_manager.delete_task(task_id):
                self.view.display_message("Задача успешно удалена")
            else:
                self.view.display_message("Ошибка при удалении задачи", is_error=True)
        else:
            self.view.display_message("Удаление отменено")
    
    def filter_tasks(self):
        """Фильтрация задач"""
        filter_type, value = self.view.get_filter_criteria()
        
        if filter_type == "status":
            tasks = self.task_manager.filter_by_status(value)
            self.view.display_tasks(tasks, f"Задачи со статусом '{value.value}'")
        elif filter_type == "priority":
            tasks = self.task_manager.filter_by_priority(value)
            self.view.display_tasks(tasks, f"Задачи с приоритетом '{value.value}'")
        else:
            self.view.display_message("Фильтрация отменена", is_error=True)
    
    def show_by_priority(self):
        """Показать задачи в порядке приоритета"""
        tasks = self.task_manager.get_tasks_by_priority_order()
        if not tasks:
            self.view.display_message("Нет задач для отображения")
        else:
            self.view.display_tasks(tasks, "Задачи по приоритету (High → Medium → Low)")
    
    def undo_action(self):
        """Отменить последнее действие"""
        if self.task_manager.undo_last_action():
            self.view.display_message("Последнее действие успешно отменено")
        else:
            self.view.display_message("Нет действий для отмены", is_error=True)
    
    def save_tasks(self):
        """Сохранить задачи в файл"""
        if self.task_manager.save_to_file():
            self.view.display_message("Задачи успешно сохранены в файл 'tasks.json'")
        else:
            self.view.display_message("Ошибка при сохранении задач", is_error=True)
    
    def load_tasks(self):
        """Загрузить задачи из файла"""
        if self.task_manager.load_from_file():
            self.view.display_message("Задачи успешно загружены из файла 'tasks.json'")
        else:
            self.view.display_message("Ошибка при загрузке задач или файл не найден", is_error=True)
    
    def exit_app(self):
        """Выйти из приложения"""
        save_choice = input("Сохранить изменения перед выходом? (y/n): ").strip().lower()
        if save_choice == 'y' or save_choice == 'yes':
            self.save_tasks()
        self.view.display_message("До свидания!")
        self.running = False


# ==================== Юнит-тесты ====================

import unittest

class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.manager = TaskManager()
    
    def test_add_task(self):
        task = self.manager.add_task("Test Task", "Description", Priority.HIGH, Status.TODO)
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.priority, Priority.HIGH)
        self.assertEqual(len(self.manager.get_all_tasks()), 1)
    
    def test_add_task_empty_title(self):
        with self.assertRaises(ValueError):
            self.manager.add_task("", "Description", Priority.MEDIUM, Status.TODO)
    
    def test_update_task(self):
        task = self.manager.add_task("Old Title", "Old Desc", Priority.LOW, Status.TODO)
        self.manager.update_task(task.id, title="New Title", status=Status.IN_PROGRESS)
        updated = self.manager.get_task(task.id)
        self.assertEqual(updated.title, "New Title")
        self.assertEqual(updated.status, Status.IN_PROGRESS)
    
    def test_delete_task(self):
        task = self.manager.add_task("To Delete", "Desc", Priority.MEDIUM, Status.TODO)
        self.manager.delete_task(task.id)
        self.assertIsNone(self.manager.get_task(task.id))
    
    def test_undo_add(self):
        task = self.manager.add_task("Undo Test", "Desc", Priority.HIGH, Status.TODO)
        self.assertEqual(len(self.manager.get_all_tasks()), 1)
        self.manager.undo_last_action()
        self.assertEqual(len(self.manager.get_all_tasks()), 0)
    
    def test_filter_by_status(self):
        self.manager.add_task("Task 1", "Desc", Priority.LOW, Status.TODO)
        self.manager.add_task("Task 2", "Desc", Priority.MEDIUM, Status.DONE)
        self.manager.add_task("Task 3", "Desc", Priority.HIGH, Status.TODO)
        
        todo_tasks = self.manager.filter_by_status(Status.TODO)
        self.assertEqual(len(todo_tasks), 2)
    
    def test_filter_by_priority(self):
        self.manager.add_task("Task 1", "Desc", Priority.HIGH, Status.TODO)
        self.manager.add_task("Task 2", "Desc", Priority.LOW, Status.DONE)
        self.manager.add_task("Task 3", "Desc", Priority.HIGH, Status.TODO)
        
        high_tasks = self.manager.filter_by_priority(Priority.HIGH)
        self.assertEqual(len(high_tasks), 2)
    
    def test_priority_order(self):
        self.manager.add_task("Low", "Desc", Priority.LOW, Status.TODO)
        self.manager.add_task("High", "Desc", Priority.HIGH, Status.TODO)
        self.manager.add_task("Medium", "Desc", Priority.MEDIUM, Status.TODO)
        
        ordered = self.manager.get_tasks_by_priority_order()
        priorities = [task.priority.value for task in ordered]
        self.assertEqual(priorities, ["High", "Medium", "Low"])
    
    def test_save_load(self):
        self.manager.add_task("Save Test", "Desc", Priority.MEDIUM, Status.TODO)
        self.manager.save_to_file("test_tasks.json")
        
        new_manager = TaskManager()
        new_manager.load_from_file("test_tasks.json")
        self.assertEqual(len(new_manager.get_all_tasks()), 1)
        
        # Cleanup
        if os.path.exists("test_tasks.json"):
            os.remove("test_tasks.json")


# ==================== Точка входа ====================

def run_tests():
    """Запустить тесты"""
    print("\n" + "="*50)
    print("ЗАПУСК ТЕСТОВ")
    print("="*50)
    unittest.main(argv=[''], verbosity=2, exit=False)


def main():
    """Точка входа в приложение"""
    task_manager = TaskManager()
    view = ConsoleView()
    controller = MenuController(task_manager, view)
    controller.run()


if __name__ == "__main__":
    import sys
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
    else:
        main()
