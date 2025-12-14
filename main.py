import base64
import os
from datetime import date

from nicegui import ui

from src.generators import generate_ics_string, generate_pdf_bytes
from src.scheduler import Scheduler
from src.scraper import get_course_data
from src.ui_components import TimetableGrid

# --- Load Data ---
courses_data = get_course_data(
    json_path="courses.json", timetable_pdf="timetable.pdf", courses_pdf="courses.pdf"
)

if not courses_data:
    print("WARNING: No data found. Ensure PDF files are present.")


@ui.page("/")
def index():
    # --- Theme ---
    ui.colors(
        primary="#3B82F6", secondary="#64748B", positive="#22C55E", negative="#EF4444"
    )

    scheduler = Scheduler(courses_data)
    course_cards = {}

    # --- Header ---
    with ui.header().classes(
        "items-center justify-between bg-white text-gray-800 shadow-md px-4 py-3 md:px-6"
    ):
        ui.label("IIIT-H Timetable").classes("text-lg md:text-xl font-bold truncate")

        with ui.row().classes("items-center gap-2"):
            # Downloads
            async def dl_pdf():
                flat = scheduler.get_selected_courses_flat()
                if not flat:
                    return ui.notify("Select courses first!", type="warning")
                try:
                    b64 = base64.b64encode(generate_pdf_bytes(flat)).decode()
                    ui.download(f"data:application/pdf;base64,{b64}", "timetable.pdf")
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")

            async def dl_ics():
                flat = scheduler.get_selected_courses_flat()
                if not flat:
                    return ui.notify("Select courses first!", type="warning")
                try:
                    b64 = base64.b64encode(generate_ics_string(flat).encode()).decode()
                    ui.download(f"data:text/calendar;base64,{b64}", "schedule.ics")
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")

            ui.button("PDF", on_click=dl_pdf, icon="picture_as_pdf").props(
                "flat round dense"
            ).classes("text-sm")
            ui.button("ICS", on_click=dl_ics, icon="calendar_month").props(
                "flat round dense"
            ).classes("text-sm")

    # --- Content ---
    with ui.column().classes(
        "w-full max-w-[1400px] mx-auto p-2 md:p-4 gap-4 md:gap-6 mb-24"
    ):
        # 1. Preview
        with ui.card().classes("w-full p-2 md:p-4 shadow-sm border border-gray-200"):
            ui.label("Timetable Preview").classes("text-md md:text-lg font-bold mb-2")
            with ui.element("div").classes("w-full overflow-x-auto"):
                with ui.element("div").classes("min-w-[800px]"):
                    grid = TimetableGrid()
                    grid.render()

        ui.separator()

        # 2. Search Area
        with ui.row().classes("w-full gap-2 items-center"):
            # Input Field (grows to fill space)
            search_field = (
                ui.input(placeholder="Search courses...")
                .classes("flex-grow text-md")
                .props("outlined rounded-lg clearable dense")
            )
            # Decorate input with icon
            with search_field.add_slot("prepend"):
                ui.icon("search").classes("text-gray-400")

            # Discrete Manual Search Button
            search_btn = (
                ui.button("Search")
                .props("unelevated color=primary text-color=white")
                .classes("h-10 px-6 rounded-lg font-bold shadow-sm")
            )

        # 3. Lists (Responsive & Full Width)
        with ui.row().classes("w-full gap-4 md:gap-6 items-start wrap"):

            def list_col(title, icon, color):
                # LAYOUT FIX:
                # w-full: Full width on mobile (stacks vertically)
                # md:flex-1: Flex grow on desktop (shares width equally)
                # min-w-0: Prevents flex child from overflowing container
                with (
                    ui.expansion(title, icon=icon, value=True)
                    .classes(f"w-full md:flex-1 min-w-0 border rounded-lg {color}")
                    .props("header-class='font-bold text-md'") as exp
                ):
                    ui.separator().classes("mb-1")
                    with ui.scroll_area().classes("w-full h-[400px] md:h-[600px] p-2"):
                        content = ui.column().classes("w-full gap-2")
                return content, exp

            col_avail, exp_avail = list_col("Available", "list", "bg-gray-50")
            col_sel, exp_sel = list_col("Selected", "check_circle", "bg-blue-50")
            col_conf, exp_conf = list_col("Conflicting", "block", "bg-red-50")

    # --- Footer ---
    with ui.footer().classes("bg-white border-t border-gray-200 p-3 md:p-4 z-50"):
        with ui.column().classes("w-full items-center justify-center gap-1"):
            ui.label(f"© {date.today().year} Pranshul Shenoy, IIIT").classes(
                "text-xs md:text-sm text-gray-500 font-medium"
            )
            with ui.row().classes("gap-4 text-xs md:text-sm text-gray-400"):
                ui.link(
                    "Report Issue",
                    "https://github.com/pranshuul/timetable_generator/issues",
                ).classes("hover:text-primary transition-colors")
                ui.label("•")
                ui.link(
                    "GitHub", "https://github.com/pranshuul/timetable_generator"
                ).classes("hover:text-primary transition-colors")

    # --- Logic ---
    def refresh_ui():
        # Get flattened schedule for grid
        grid.update(scheduler.get_selected_courses_flat())

        sel_ids = scheduler.selected_ids
        conf_ids = scheduler.get_conflicting_ids()
        query = search_field.value.lower() if search_field.value else ""

        count_avail = 0
        count_sel = 0
        count_conf = 0

        sorted_ids = sorted(
            course_cards.keys(), key=lambda k: scheduler.all_courses[k]["name"]
        )

        for cid in sorted_ids:
            card = course_cards[cid]
            course = scheduler.all_courses[cid]

            if query and query not in course["name"].lower():
                card.set_visibility(False)
                continue
            card.set_visibility(True)

            if cid in sel_ids:
                card.move(col_sel)
                card.classes(
                    "bg-blue-100 border-blue-500 hover:bg-blue-200",
                    remove="bg-white bg-red-100 border-transparent border-red-300 opacity-60 hover:bg-gray-100 cursor-not-allowed",
                )
                count_sel += 1
            elif cid in conf_ids:
                card.move(col_conf)
                card.classes(
                    "bg-red-100 border-red-300 opacity-75 cursor-not-allowed",
                    remove="bg-white bg-blue-100 border-transparent border-blue-500 hover:bg-gray-100 hover:bg-blue-200",
                )
                count_conf += 1
            else:
                card.move(col_avail)
                card.classes(
                    "bg-white border-transparent hover:bg-gray-100 hover:shadow",
                    remove="bg-blue-100 bg-red-100 border-blue-500 border-red-300 opacity-60 opacity-75 cursor-not-allowed hover:bg-blue-200",
                )
                count_avail += 1

        exp_avail.text = f"Available ({count_avail})"
        exp_sel.text = f"Selected ({count_sel})"
        exp_conf.text = f"Conflicting ({count_conf})"

    def on_click(cid):
        if cid in scheduler.selected_ids or cid not in scheduler.get_conflicting_ids():
            scheduler.toggle_course(cid)
            refresh_ui()
        else:
            ui.notify("Conflict!", type="negative")

    # --- Build Cards ---
    for course in courses_data:
        cid = course["id"]
        with ui.card().classes(
            "w-full p-3 border cursor-pointer transition-all duration-300"
        ) as card:
            card.on("click", lambda e, c=cid: on_click(c))
            with ui.column().classes("gap-1"):
                ui.label(course["name"]).classes(
                    "text-sm font-semibold leading-tight text-gray-800"
                )

                if course["sessions"]:
                    with ui.row().classes("gap-2 items-center flex-wrap"):
                        day_map = {
                            "Mon": 0,
                            "Tue": 1,
                            "Wed": 2,
                            "Thu": 3,
                            "Fri": 4,
                            "Sat": 5,
                        }
                        sorted_sess = sorted(
                            course["sessions"],
                            key=lambda x: (day_map.get(x["day"], 9), x["slot"]),
                        )

                        for s in sorted_sess:
                            ui.label(f"{s['day']} S{s['slot']}").classes(
                                "text-[10px] bg-gray-600 text-white px-1.5 py-0.5 rounded"
                            )
                else:
                    ui.label("No slots found").classes("text-[9px] text-red-500 italic")

                if course["half"] != "BOTH":
                    clr = (
                        "bg-green-100 text-green-800"
                        if "H1" in course["half"]
                        else "bg-purple-100 text-purple-800"
                    )
                    ui.label(course["half"]).classes(
                        f"text-[10px] font-bold px-1.5 py-0.5 rounded {clr}"
                    )

        course_cards[cid] = card

    # Bind Events
    search_field.on_value_change(refresh_ui)
    search_btn.on_click(refresh_ui)  # Manual Trigger

    # Trigger initial load
    refresh_ui()


# --- Run for Deployment ---
ui.run(
    title="Timetable Generator",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    storage_secret="timetable-secret-key",
)
