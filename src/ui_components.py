from nicegui import ui

from .utils import get_slot_time_str


class TimetableGrid:
    def __init__(self):
        self.cells = {}  # Map (Day, Slot) -> ui.element
        self.header_cells = []  # Store header cells for theme updates
        self.day_cells = []  # Store day label cells for theme updates
        self.lunch_cell = None
        self.lunch_dividers = []
        self.grid_container = None
        self.dark_mode = False

    def render(self):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        # Grid Definition
        grid_style = "grid-template-columns: 70px repeat(3, 1fr) 60px repeat(3, 1fr);"

        self.grid_container = ui.element("div").classes(
            "grid w-full gap-0 border").style(grid_style)

        with self.grid_container:
            # --- HEADER ROW ---
            day_header = ui.label("Day").classes(
                "font-bold p-2 border flex items-center justify-center text-xs"
            )
            self.header_cells.append(day_header)

            for i in range(1, 4):
                time_str = get_slot_time_str(i)
                header = ui.label(time_str).classes(
                    "font-bold p-1 border text-center text-xs flex items-center justify-center"
                )
                self.header_cells.append(header)

            self.lunch_cell = ui.column().classes(
                "border items-center justify-center overflow-hidden"
            )
            with self.lunch_cell:
                ui.label("LUNCH").classes(
                    "text-[9px] font-bold whitespace-nowrap tracking-widest text-gray-500"
                )

            for i in range(4, 7):
                time_str = get_slot_time_str(i)
                header = ui.label(time_str).classes(
                    "font-bold p-1 border text-center text-xs flex items-center justify-center"
                )
                self.header_cells.append(header)

            # --- DATA ROWS ---
            for day in days:
                day_label = ui.label(day).classes(
                    "font-bold p-2 border flex items-center justify-center"
                )
                self.day_cells.append(day_label)

                for slot in range(1, 4):
                    with ui.column().classes(
                        "p-1 border min-h-[80px] text-xs relative group"
                    ) as cell:
                        self.cells[(day, slot)] = cell

                divider = ui.element("div").classes("border")
                self.lunch_dividers.append(divider)

                for slot in range(4, 7):
                    with ui.column().classes(
                        "p-1 border min-h-[80px] text-xs relative group"
                    ) as cell:
                        self.cells[(day, slot)] = cell

    def set_theme(self, dark_mode):
        """Update grid colors based on theme"""
        self.dark_mode = dark_mode

        if self.grid_container:
            self.grid_container.classes(
                'border-gray-700' if dark_mode else 'border-gray-300',
                remove='border-gray-700 border-gray-300'
            )

        # Update header cells
        for header in self.header_cells:
            header.classes(
                'border-gray-700 bg-gray-700' if dark_mode else 'border-gray-200 bg-gray-100',
                remove='border-gray-700 bg-gray-700 border-gray-200 bg-gray-100'
            )

        # Update lunch cell
        if self.lunch_cell:
            self.lunch_cell.classes(
                'border-gray-700 bg-gray-700' if dark_mode else 'border-gray-200 bg-gray-100',
                remove='border-gray-700 bg-gray-700 border-gray-200 bg-gray-100'
            )

        # Update day cells
        for day_label in self.day_cells:
            day_label.classes(
                'border-gray-700 bg-gray-800' if dark_mode else 'border-gray-200 bg-gray-50',
                remove='border-gray-700 bg-gray-800 border-gray-200 bg-gray-50'
            )

        # Update lunch dividers
        for divider in self.lunch_dividers:
            divider.classes(
                'border-gray-700 bg-gray-700' if dark_mode else 'border-gray-200 bg-gray-100',
                remove='border-gray-700 bg-gray-700 border-gray-200 bg-gray-100'
            )

        # Update all data cells
        for cell in self.cells.values():
            cell.classes(
                'border-gray-700 bg-gray-800' if dark_mode else 'border-gray-200 bg-white',
                remove='border-gray-700 bg-gray-800 border-gray-200 bg-white'
            )

    def update(self, selected_courses):
        for cell in self.cells.values():
            cell.clear()

        for course in selected_courses:
            day, slot = course["day"], course["slot"]

            if (day, slot) in self.cells:
                with self.cells[(day, slot)]:
                    if self.dark_mode:
                        color = (
                            "bg-blue-700 text-blue-100"
                            if course["half"] == "BOTH"
                            else (
                                "bg-green-700 text-green-100"
                                if course["half"] == "H1"
                                else "bg-purple-700 text-purple-100"
                            )
                        )
                    else:
                        color = (
                            "bg-blue-100 text-blue-900"
                            if course["half"] == "BOTH"
                            else (
                                "bg-green-100 text-green-900"
                                if course["half"] == "H1"
                                else "bg-purple-100 text-purple-900"
                            )
                        )

                    with ui.card().classes(f"w-full p-1 {color} shadow-sm mb-1"):
                        ui.label(course["name"]).classes(
                            "font-medium leading-tight")
                        if course["half"] != "BOTH":
                            half_text_color = "text-gray-300" if self.dark_mode else "text-gray-600"
                            ui.label(course["half"]).classes(
                                f"text-[10px] {half_text_color}"
                            )
