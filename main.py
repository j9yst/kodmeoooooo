import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg') # Для работы без GUI
import numpy as np

# ==================== Модели данных ====================

class Category:
    """Категории расходов"""
    FOOD = "Еда"
    TRANSPORT = "Транспорт"
    ENTERTAINMENT = "Развлечения"
    SHOPPING = "Покупки"
    UTILITIES = "Коммунальные услуги"
    HEALTH = "Здоровье"
    EDUCATION = "Образование"
    OTHER = "Другое"
    
    @classmethod
    def get_all(cls) -> List[str]:
        return [cls.FOOD, cls.TRANSPORT, cls.ENTERTAINMENT, 
                cls.SHOPPING, cls.UTILITIES, cls.HEALTH, 
                cls.EDUCATION, cls.OTHER]
    
    @classmethod
    def is_valid(cls, category: str) -> bool:
        return category in cls.get_all()


class Expense:
    """Базовый класс расхода (инкапсуляция)"""
    def __init__(self, expense_id: int, amount: float, category: str, date: str, description: str = ""):
        self._id = expense_id
        self._amount = amount
        self._category = category
        self._date = date
        self._description = description
    
    # Геттеры
    @property
    def id(self) -> int:
        return self._id
    
    @property
    def amount(self) -> float:
        return self._amount
    
    @amount.setter
    def amount(self, value: float):
        if value <= 0:
            raise ValueError("Сумма расхода должна быть положительной")
        self._amount = value
    
    @property
    def category(self) -> str:
        return self._category
    
    @category.setter
    def category(self, value: str):
        if not Category.is_valid(value):
            raise ValueError(f"Некорректная категория: {value}")
        self._category = value
    
    @property
    def date(self) -> str:
        return self._date
    
    @date.setter
    def date(self, value: str):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            self._date = value
        except ValueError:
            raise ValueError("Неверный формат даты. Используйте ГГГГ-ММ-ДД")
    
    @property
    def description(self) -> str:
        return self._description
    
    @description.setter
    def description(self, value: str):
        self._description = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в JSON"""
        return {
            "id": self._id,
            "amount": self._amount,
            "category": self._category,
            "date": self._date,
            "description": self._description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Expense':
        """Десериализация из JSON"""
        return cls(
            expense_id=data["id"],
            amount=data["amount"],
            category=data["category"],
            date=data["date"],
            description=data.get("description", "")
        )
    
    def __str__(self) -> str:
        return (f"[{self._id}] {self._date} | {self._category}: "
                f"{self._amount:,.2f} ₽\n {self._description}")


class EssentialExpense(Expense):
    """Подкласс для обязательных расходов (наследование)"""
    def __init__(self, expense_id: int, amount: float, category: str, date: str, 
                 description: str = "", is_essential: bool = True):
        super().__init__(expense_id, amount, category, date, description)
        self._is_essential = is_essential
    
    @property
    def is_essential(self) -> bool:
        return self._is_essential
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["type"] = "essential"
        data["is_essential"] = self._is_essential
        return data
    
    def __str__(self) -> str:
        essential_mark = " (Обязательный)" if self._is_essential else ""
        return super().__str__() + essential_mark


class LeisureExpense(Expense):
    """Подкласс для расходов на досуг (наследование)"""
    def __init__(self, expense_id: int, amount: float, category: str, date: str,
                 description: str = "", fun_level: int = 5):
        super().__init__(expense_id, amount, category, date, description)
        self._fun_level = max(1, min(10, fun_level)) # Уровень удовольствия 1-10
    
    @property
    def fun_level(self) -> int:
        return self._fun_level
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["type"] = "leisure"
        data["fun_level"] = self._fun_level
        return data
    
    def __str__(self) -> str:
        stars = "★" * (self._fun_level // 2) + "☆" * (5 - self._fun_level // 2)
        return super().__str__() + f"\n Уровень удовольствия: {stars}"


# ==================== Менеджер расходов ====================

class ExpenseManager:
    """Управление расходами"""
    def __init__(self):
        self._expenses: Dict[int, Expense] = {}
        self._next_id: int = 1
    
    def add_expense(self, amount: float, category: str, date: str, 
                    description: str = "", expense_type: str = "basic",
                    **kwargs) -> Optional[Expense]:
        """Добавить расход"""
        try:
            # Валидация даты
            datetime.strptime(date, "%Y-%m-%d")
            
            # Создание расхода в зависимости от типа
            if expense_type == "essential":
                is_essential = kwargs.get("is_essential", True)
                expense = EssentialExpense(self._next_id, amount, category, date, 
                                          description, is_essential)
            elif expense_type == "leisure":
                fun_level = kwargs.get("fun_level", 5)
                expense = LeisureExpense(self._next_id, amount, category, date,
                                        description, fun_level)
            else:
                expense = Expense(self._next_id, amount, category, date, description)
            
            self._expenses[expense.id] = expense
            self._next_id += 1
            return expense
        except ValueError as e:
            print(f"❌ Ошибка: {e}")
            return None
    
    def get_expense(self, expense_id: int) -> Optional[Expense]:
        """Получить расход по ID"""
        return self._expenses.get(expense_id)
    
    def delete_expense(self, expense_id: int) -> bool:
        """Удалить расход"""
        if expense_id in self._expenses:
            del self._expenses[expense_id]
            return True
        return False
    
    def get_all_expenses(self) -> List[Expense]:
        """Получить все расходы"""
        return list(self._expenses.values())
    
    def filter_by_category(self, category: str) -> List[Expense]:
        """Фильтрация по категории"""
        return [e for e in self._expenses.values() if e.category == category]
    
    def filter_by_period(self, start_date: str, end_date: str) -> List[Expense]:
        """Фильтрация по периоду"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            filtered = []
            for expense in self._expenses.values():
                expense_date = datetime.strptime(expense.date, "%Y-%m-%d")
                if start <= expense_date <= end:
                    filtered.append(expense)
            return filtered
        except ValueError:
            print("❌ Ошибка: Неверный формат даты")
            return []
    
    def get_total_by_period(self, start_date: str, end_date: str) -> float:
        """Подсчёт суммы расходов за период"""
        expenses = self.filter_by_period(start_date, end_date)
        return sum(e.amount for e in expenses)
    
    def get_expenses_by_category(self, start_date: str = None, end_date: str = None) -> Dict[str, float]:
        """Получить расходы по категориям за период"""
        if start_date and end_date:
            expenses = self.filter_by_period(start_date, end_date)
        else:
            expenses = self.get_all_expenses()
        
        category_totals = defaultdict(float)
        for expense in expenses:
            category_totals[expense.category] += expense.amount
        return dict(category_totals)
    
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, float]:
        """Получить сводку за месяц"""
        start_date = f"{year}-{month:02d}-01"
        # Определяем последний день месяца
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        # Вычитаем один день
        end = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=1)
        end_date = end.strftime("%Y-%m-%d")
        
        return self.get_expenses_by_category(start_date, end_date)
    
    def save_to_file(self, filename: str = "expenses.json"):
        """Сохранить данные в JSON"""
        try:
            data = {
                "next_id": self._next_id,
                "expenses": []
            }
            for expense in self._expenses.values():
                data["expenses"].append(expense.to_dict())
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False
    
    def load_from_file(self, filename: str = "expenses.json") -> bool:
        """Загрузить данные из JSON"""
        if not os.path.exists(filename):
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._expenses.clear()
            self._next_id = data.get("next_id", 1)
            
            for expense_data in data.get("expenses", []):
                expense_type = expense_data.get("type", "basic")
                
                if expense_type == "essential":
                    expense = EssentialExpense(
                        expense_id=expense_data["id"],
                        amount=expense_data["amount"],
                        category=expense_data["category"],
                        date=expense_data["date"],
                        description=expense_data.get("description", ""),
                        is_essential=expense_data.get("is_essential", True)
                    )
                elif expense_type == "leisure":
                    expense = LeisureExpense(
                        expense_id=expense_data["id"],
                        amount=expense_data["amount"],
                        category=expense_data["category"],
                        date=expense_data["date"],
                        description=expense_data.get("description", ""),
                        fun_level=expense_data.get("fun_level", 5)
                    )
                else:
                    expense = Expense.from_dict(expense_data)
                
                self._expenses[expense.id] = expense
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False


# ==================== Построитель графиков ====================

class ChartBuilder:
    """Класс для построения графиков"""
    
    @staticmethod
    def plot_expenses_by_category(expenses_by_category: Dict[str, float], 
                                  title: str = "Расходы по категориям"):
        """Построить круговую диаграмму расходов по категориям"""
        if not expenses_by_category:
            print("❌ Нет данных для построения графика")
            return
        
        # Подготовка данных
        categories = list(expenses_by_category.keys())
        amounts = list(expenses_by_category.values())
        
        # Создание графика
        plt.figure(figsize=(12, 6))
        
        # Круговая диаграмма
        plt.subplot(1, 2, 1)
        colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
        wedges, texts, autotexts = plt.pie(amounts, labels=categories, autopct='%1.1f%%',
                                            colors=colors, startangle=90)
        plt.title(title, fontsize=14, fontweight='bold')
        
        # Столбчатая диаграмма
        plt.subplot(1, 2, 2)
        bars = plt.bar(categories, amounts, color=colors)
        plt.xlabel('Категории', fontsize=12)
        plt.ylabel('Сумма (₽)', fontsize=12)
        plt.title('Расходы по категориям (сравнение)', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        
        # Добавление значений на столбцы
        for bar, amount in zip(bars, amounts):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{amount:,.0f}₽', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_monthly_trend(expenses: List[Expense], year: int):
        """Построить график тренда расходов по месяцам"""
        monthly_totals = defaultdict(float)
        
        for expense in expenses:
            expense_date = datetime.strptime(expense.date, "%Y-%m-%d")
            if expense_date.year == year:
                month_key = expense_date.strftime("%B")
                monthly_totals[month_key] += expense.amount
        
        if not monthly_totals:
            print(f"❌ Нет данных за {year} год")
            return
        
        # Сортировка по месяцам
        months_order = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        
        months_ru = {
            'January': 'Январь', 'February': 'Февраль', 'March': 'Март',
            'April': 'Апрель', 'May': 'Май', 'June': 'Июнь',
            'July': 'Июль', 'August': 'Август', 'September': 'Сентябрь',
            'October': 'Октябрь', 'November': 'Ноябрь', 'December': 'Декабрь'
        }
        
        months = [m for m in months_order if m in monthly_totals]
        totals = [monthly_totals[m] for m in months]
        months_ru_labels = [months_ru[m] for m in months]
        
        plt.figure(figsize=(12, 6))
        plt.plot(months_ru_labels, totals, marker='o', linewidth=2, markersize=8)
        plt.xlabel('Месяц', fontsize=12)
        plt.ylabel('Сумма расходов (₽)', fontsize=12)
        plt.title(f'Тренд расходов за {year} год', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # Добавление значений
        for i, (month, total) in enumerate(zip(months_ru_labels, totals)):
            plt.text(i, total, f'{total:,.0f}₽', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()


# ==================== Консольное представление ====================

class ConsoleView:
    """Консольный интерфейс"""
    
    @staticmethod
    def clear_screen():
        """Очистка экрана"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def display_menu():
        """Отобразить главное меню"""
        print("\n" + "="*60)
        print(" 📊 МЕНЕДЖЕР РАСХОДОВ 📊")
        print("="*60)
        print("1. 💰 Добавить расход")
        print("2. 📋 Просмотреть все расходы")
        print("3. 🗑️ Удалить расход")
        print("4. 🔍 Фильтрация расходов")
        print("5. 📈 Подсчёт суммы за период")
        print("6. 📊 Построить график расходов по категориям")
        print("7. 📉 Построить график тренда по месяцам")
        print("8. 💾 Сохранить данные")
        print("9. 📂 Загрузить данные")
        print("0. 🚪 Выход")
        print("-"*60)
    
    @staticmethod
    def display_expenses(expenses: List[Expense], title: str = "Расходы"):
        """Отобразить список расходов"""
        if not expenses:
            print(f"\n❌ {title} не найдены")
            return
        
        print(f"\n📋 {title}:")
        print("-" * 50)
        total = 0
        for i, expense in enumerate(expenses, 1):
            print(f"{i}. {expense}")
            total += expense.amount
            if i < len(expenses):
                print()
        print("-" * 50)
        print(f"💰 ИТОГО: {total:,.2f} ₽")
    
    @staticmethod
    def get_expense_input() -> tuple:
        """Получить данные о расходе"""
        # Ввод суммы
        while True:
            try:
                amount = float(input("💰 Сумма расхода (₽): "))
                if amount <= 0:
                    print("❌ Сумма должна быть положительной!")
                    continue
                break
            except ValueError:
                print("❌ Введите корректное число!")
        
        # Выбор категории
        print("\n📁 Доступные категории:")
        categories = Category.get_all()
        for i, cat in enumerate(categories, 1):
            print(f" {i}. {cat}")
        
        while True:
            try:
                cat_choice = int(input("Выберите категорию (1-8): "))
                if 1 <= cat_choice <= len(categories):
                    category = categories[cat_choice - 1]
                    break
                print("❌ Неверный номер категории!")
            except ValueError:
                print("❌ Введите число!")
        
        # Ввод даты
        while True:
            date_str = input("📅 Дата (ГГГГ-ММ-ДД): ")
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                break
            except ValueError:
                print("❌ Неверный формат! Используйте ГГГГ-ММ-ДД")
        
        # Ввод описания
        description = input("📝 Описание (необязательно): ").strip()
        
        # Выбор типа расхода
        print("\n📌 Тип расхода:")
        print(" 1. Обычный")
        print(" 2. Обязательный")
        print(" 3. На досуг")
        
        expense_type = "basic"
        extra_params = {}
        
        type_choice = input("Выберите тип (1-3): ").strip()
        if type_choice == "2":
            expense_type = "essential"
            is_essential = input("Это обязательный расход? (y/n): ").lower() == 'y'
            extra_params["is_essential"] = is_essential
        elif type_choice == "3":
            expense_type = "leisure"
            try:
                fun_level = int(input("Уровень удовольствия (1-10): "))
                extra_params["fun_level"] = max(1, min(10, fun_level))
            except ValueError:
                extra_params["fun_level"] = 5
        
        return amount, category, date_str, description, expense_type, extra_params
    
    @staticmethod
    def get_period_input() -> tuple:
        """Получить период для фильтрации"""
        print("\n📅 Введите период:")
        while True:
            start_date = input("Начальная дата (ГГГГ-ММ-ДД): ")
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                break
            except ValueError:
                print("❌ Неверный формат!")
        
        while True:
            end_date = input("Конечная дата (ГГГГ-ММ-ДД): ")
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
                if datetime.strptime(end_date, "%Y-%m-%d") >= datetime.strptime(start_date, "%Y-%m-%d"):
                    break
                print("❌ Конечная дата должна быть позже начальной!")
            except ValueError:
                print("❌ Неверный формат!")
        
        return start_date, end_date
    
    @staticmethod
    def display_message(message: str, is_error: bool = False):
        """Отобразить сообщение"""
        prefix = "❌" if is_error else "✅"
        print(f"{prefix} {message}")


# ==================== Контроллер ====================

class ExpenseController:
    """Контроллер приложения"""
    
    def __init__(self):
        self.manager = ExpenseManager()
        self.view = ConsoleView()
        self.running = True
    
    def run(self):
        """Запуск приложения"""
        self.view.clear_screen()
        print("\n" + "="*60)
        print(" Добро пожаловать в Expense Chart!")
        print(" Отслеживайте и анализируйте свои расходы")
        print("="*60)
        
        # Автоматическая загрузка
        if self.manager.load_from_file():
            self.view.display_message("Данные загружены из файла")
        else:
            self.view.display_message("Новый файл данных будет создан при сохранении")
        
        while self.running:
            self.view.display_menu()
            choice = input("\n🔧 Выберите действие: ").strip()
            self.handle_choice(choice)
    
    def handle_choice(self, choice: str):
        """Обработка выбора пользователя"""
        actions = {
            "1": self.add_expense,
            "2": self.view_all_expenses,
            "3": self.delete_expense,
            "4": self.filter_expenses,
            "5": self.show_total_by_period,
            "6": self.show_category_chart,
            "7": self.show_monthly_trend,
            "8": self.save_data,
            "9": self.load_data,
            "0": self.exit_app
        }
        
        action = actions.get(choice)
        if action:
            action()
        else:
            self.view.display_message("Неверный выбор!", is_error=True)
    
    def add_expense(self):
        """Добавление расхода"""
        amount, category, date_str, description, expense_type, extra_params = self.view.get_expense_input()
        
        expense = self.manager.add_expense(amount, category, date_str, 
                                           description, expense_type, **extra_params)
        if expense:
            self.view.display_message(f"Расход добавлен с ID {expense.id}")
    
    def view_all_expenses(self):
        """Просмотр всех расходов"""
        expenses = self.manager.get_all_expenses()
        if expenses:
            # Сортировка по дате
            expenses.sort(key=lambda x: x.date, reverse=True)
            self.view.display_expenses(expenses, "Все расходы")
        else:
            self.view.display_message("Нет добавленных расходов", is_error=True)
    
    def delete_expense(self):
        """Удаление расхода"""
        try:
            expense_id = int(input("Введите ID расхода для удаления: "))
            if self.manager.delete_expense(expense_id):
                self.view.display_message("Расход удалён")
            else:
                self.view.display_message("Расход не найден", is_error=True)
        except ValueError:
            self.view.display_message("Неверный ID!", is_error=True)
    
    def filter_expenses(self):
        """Фильтрация расходов"""
        print("\n🔍 Фильтрация:")
        print("1. По категории")
        print("2. По периоду")
        
        choice = input("Выберите опцию: ").strip()
        
        if choice == "1":
            print("\n📁 Категории:")
            for cat in Category.get_all():
                print(f" - {cat}")
            category = input("Введите категорию: ").strip()
            
            if Category.is_valid(category):
                expenses = self.manager.filter_by_category(category)
                self.view.display_expenses(expenses, f"Расходы по категории '{category}'")
            else:
                self.view.display_message("Неверная категория!", is_error=True)
        
        elif choice == "2":
            start_date, end_date = self.view.get_period_input()
            expenses = self.manager.filter_by_period(start_date, end_date)
            self.view.display_expenses(expenses, f"Расходы за период {start_date} - {end_date}")
        
        else:
            self.view.display_message("Неверный выбор!", is_error=True)
    
    def show_total_by_period(self):
        """Подсчёт суммы за период"""
        start_date, end_date = self.view.get_period_input()
        total = self.manager.get_total_by_period(start_date, end_date)
        
        print("\n" + "="*50)
        print(f"📊 Сумма расходов за период {start_date} - {end_date}")
        print("="*50)
        print(f"💰 ИТОГО: {total:,.2f} ₽")
        
        # Показать детали по категориям
        category_totals = self.manager.get_expenses_by_category(start_date, end_date)
        if category_totals:
            print("\n📁 По категориям:")
            for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / total * 100) if total > 0 else 0
                print(f" {category}: {amount:,.2f} ₽ ({percentage:.1f}%)")
    
    def show_category_chart(self):
        """Показать график расходов по категориям"""
        print("\n📊 Построение графика расходов по категориям")
        use_period = input("Использовать период? (y/n): ").lower() == 'y'
        
        if use_period:
            start_date, end_date = self.view.get_period_input()
            expenses_by_category = self.manager.get_expenses_by_category(start_date, end_date)
            title = f"Расходы по категориям ({start_date} - {end_date})"
        else:
            expenses_by_category = self.manager.get_expenses_by_category()
            title = "Расходы по категориям (все время)"
        
        if expenses_by_category:
            ChartBuilder.plot_expenses_by_category(expenses_by_category, title)
        else:
            self.view.display_message("Нет данных для построения графика", is_error=True)
    
    def show_monthly_trend(self):
        """Показать график тренда по месяцам"""
        try:
            year = int(input("Введите год (например, 2024): "))
            expenses = self.manager.get_all_expenses()
            ChartBuilder.plot_monthly_trend(expenses, year)
        except ValueError:
            self.view.display_message("Неверный год!", is_error=True)
    
    def save_data(self):
        """Сохранение данных"""
        if self.manager.save_to_file():
            self.view.display_message("Данные сохранены в 'expenses.json'")
        else:
            self.view.display_message("Ошибка при сохранении", is_error=True)
    
    def load_data(self):
        """Загрузка данных"""
        if self.manager.load_from_file():
            self.view.display_message("Данные загружены из 'expenses.json'")
        else:
            self.view.display_message("Ошибка при загрузке или файл не найден", is_error=True)
    
    def exit_app(self):
        """Выход из приложения"""
        save_choice = input("Сохранить изменения перед выходом? (y/n): ").lower()
        if save_choice == 'y':
            self.save_data()
        self.view.display_message("До свидания!")
        self.running = False


# ==================== Точка входа ====================

def main():
    """Главная функция"""
    try:
        controller = ExpenseController()
        controller.run()
    except KeyboardInterrupt:
        print("\n\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
