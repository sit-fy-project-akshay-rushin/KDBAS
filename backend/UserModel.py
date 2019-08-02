import numpy as np
from scipy.spatial import distance
from scipy.special import expit

class UserModel:
    detector = "cityblock"
    min_samples = 3

    def __init__(self, db, email):
        self.db = db
        self.email = email
        
        # Device Properties
        self.device_info = {
            "isMobile": False,
            "type": 3,
            "pwdlength": 0,
            "pwdhash": ""
        }

        # Keystroke Dynamics
        self.char_codes = []
        self.seek_times = []
        self.press_times = []
        self.key_codes = []

        # Calculated Model
        self.madx = {}
        self.central_tendancy = {}
        self.threshold = 0

        self.fetch_data()

    @staticmethod
    def parse_keystroke_string (keystroke_str):
        typing_data = keystroke_str.split('|')
        keystroke_data = np.array([x.split(',') for x in typing_data[1:]]).astype(np.float).T
        
        device_info = typing_data[0].split(',')
        char_code = keystroke_data[0]
        seek_time = keystroke_data[1]
        seek_time[0] = np.mean(seek_time[1:])  #normalize time to first stroke
        press_time = keystroke_data[2]
        key_code = keystroke_data[3]

        return (device_info, char_code, seek_time, press_time, key_code)

    @staticmethod
    def parse_device_info(device_info):
        info = {
            "isMobile": device_info[0] == 1,
            "type": device_info[3],
            "pwdlength": device_info[4],
            "pwdhash": device_info[5]
        }

        return info

    @staticmethod
    def mad(data, axis=None):
        madx = np.mean(np.absolute(data - np.mean(data, axis)), axis)
        madx[madx == 0] = 1
        return madx

    @staticmethod
    def dist(central_tendency, samples, w=None):
        return distance.cdist(
            [central_tendency], samples, UserModel.detector, w=w, VI=None).flatten()
        
    @staticmethod
    def weighted_dist(char_code_dist, seek_time_dist, press_time_dist, key_code_dist):
        weights = np.array([1000, 1, 1, 10])

        distances = np.array([char_code_dist, seek_time_dist, press_time_dist, key_code_dist])
        weighted_distance = np.sum(distances * weights)

        return weighted_distance

    def fetch_data(self):
        db = self.db

        self.char_codes = []
        self.seek_times = []
        self.press_times = []
        self.key_codes = []

        cursor = db.cursor()
        cursor.execute(
            "SELECT id, signature FROM keystroke_data WHERE email = %s ORDER BY id DESC LIMIT 5", 
            (self.email,) )
        result = cursor.fetchall()

        for row in result:
            kstr = row[1]
            (device_info, char_code, seek_time, press_time, key_code) = UserModel.parse_keystroke_string(kstr)
            
            self.device_info = UserModel.parse_device_info(device_info)
            self.char_codes += [char_code]
            self.seek_times += [seek_time]
            self.press_times += [press_time]
            self.key_codes += [key_code]

        if self.count() > 0:
            self.calc_central_tendency()
            self.calc_threshold()

    def calc_central_tendency(self):
        self.madx['char_code'] = UserModel.mad(self.char_codes, axis=0)
        self.madx['seek_time'] = UserModel.mad(self.seek_times, axis=0)
        self.madx['press_time'] = UserModel.mad(self.press_times, axis=0)
        self.madx['key_code'] = UserModel.mad(self.key_codes, axis=0)

        self.central_tendancy['char_code'] = np.mean(self.char_codes, axis=0)
        self.central_tendancy['seek_time'] = np.mean(self.seek_times, axis=0)
        self.central_tendancy['press_time'] = np.mean(self.press_times, axis=0)
        self.central_tendancy['key_code'] = np.mean(self.key_codes, axis=0)

    def calc_threshold(self):
        char_code_dist = np.max(UserModel.dist(self.central_tendancy['char_code'], self.char_codes, w=1/self.madx['char_code']))
        seek_time_dist = np.max(UserModel.dist(self.central_tendancy['seek_time'], self.seek_times, w=1/self.madx['seek_time']))
        press_time_dist = np.max(UserModel.dist(self.central_tendancy['press_time'], self.press_times, w=1/self.madx['press_time']))
        key_code_dist = np.max(UserModel.dist(self.central_tendancy['key_code'], self.key_codes, w=1/self.madx['key_code']))
        
        weighted_distance = UserModel.weighted_dist(char_code_dist, seek_time_dist, press_time_dist, key_code_dist)
        
        threshold = 1.6 * weighted_distance
        threshold = min(1000, threshold)
        self.threshold = max(50, threshold)

    def validate_keystroke(self, keystroke_string):
        (device_info, char_code, seek_time, press_time, key_code) = self.parse_keystroke_string(keystroke_string)
        device_info = UserModel.parse_device_info(device_info)

        if (self.count() > 0) and (not self.device_info["pwdhash"] == device_info["pwdhash"]):
            print(self.count())
            print(self.device_info["pwdhash"] + " - " + device_info["pwdhash"])
            return 0

        if self.count() >= self.min_samples:
            char_code_distance = np.max(UserModel.dist(char_code, [self.central_tendancy['char_code']], w=1/self.madx['char_code']))
            seek_time_distance = np.max(UserModel.dist(seek_time, [self.central_tendancy['seek_time']], w=1/self.madx['seek_time']))
            press_time_distance = np.max(UserModel.dist(press_time, [self.central_tendancy['press_time']], w=1/self.madx['press_time']))
            key_code_distance = np.max(UserModel.dist(key_code, [self.central_tendancy['key_code']], w=1/self.madx['key_code']))

            weighted_distance = UserModel.weighted_dist(char_code_distance, seek_time_distance, 
                                            press_time_distance, key_code_distance)

            print("Threshold: " + str(round(self.threshold, 2)))
            diff = self.threshold - weighted_distance
            print("Debug Diff: " + str(round(diff, 2)))
            # acc = (self.threshold - weighted_distance)/self.threshold
            acc = expit((diff/self.threshold) * 2)
            # acc = (acc + 1) / 2
            print("Accuracy: " + str(round(acc, 5)))

            return acc
        
        return 1

    def add(self, keystroke_string):
        db = self.db

        insertcursor = db.cursor()
        insert_sql = "INSERT INTO keystroke_data (email, signature) VALUES (%s, %s)"
        val = (self.email, keystroke_string)
        insertcursor.execute(insert_sql, val)
        db.commit()

        self.fetch_data()


    def count(self):
        return len(self.press_times)
