import json
import os


class ScheduleManager:
    def __init__(self, path):
        self.path = path
        if not os.path.isfile(self.path):
            self.data = {}
        else:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def write_data(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def check_user(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {"table": [[""] * 8 for i in range(7)]}
            self.write_data()

    def set_lesson(self, user_id, day, number, new_lesson):
        user_id = str(user_id)
        self.check_user(user_id)
        self.data[user_id]["table"][day][number] = new_lesson
        self.write_data()

    def set_day_schedule(self, user_id, day, lessons):
        user_id = str(user_id)
        self.check_user(user_id)
        self.data[user_id]["table"][day] = lessons
        self.write_data()

    def get_day_schedule(self, user_id, day):
        user_id = str(user_id)
        self.check_user(user_id)
        return self.data[user_id]["table"][int(day)]
