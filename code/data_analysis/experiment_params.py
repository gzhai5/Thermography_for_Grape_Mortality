class ExperimentParameter:
    def __init__(self):
        self.fps = 30
        self.start_experiment_time = 0
        self.start_heating_time = 1
        self.end_heating_time = 10
        self.end_experiment_time = 20

        self.interested_points_num = 1000
        self.selected_points = []
        self.threshold = 9400
        self.selected_point_radius = 3