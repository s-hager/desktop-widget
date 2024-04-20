import unittest

import calendar

def find_first_day_after_gap(dates_list):
  result_days = []
  length = len(dates_list)
  for index, date in enumerate(dates_list):
    _, days_in_month = calendar.monthrange(date[2], date[1])
    if index + 1 <= length - 1:  # if index + 1 is still valid list index
      if date[0] == days_in_month and dates_list[index + 1][0] == 1:
        continue
      elif date[0] != dates_list[index + 1][0] - 1:  # if date day n does not equal date day n+1 - 1
        first_day_after_gap = dates_list[index + 1]
        result_days.append(first_day_after_gap)
  # print(days)
  return result_days


class testFunction(unittest.TestCase):
    def tc_1(self):
        dates_list = [
            (29, 8, 2023),
            (30, 8, 2023),
            (31, 8, 2023),
            (1, 9, 2023),
            (5, 9, 2023),
            (6, 9, 2023),
            (7, 9, 2023),
            (8, 9, 2023),
            (11, 9, 2023),
            (12, 9, 2023),
            (13, 9, 2023),
            (14, 9, 2023),
            (15, 9, 2023),
            (18, 9, 2023),
            (19, 9, 2023),
            (20, 9, 2023),
            (21, 9, 2023),
            (22, 9, 2023),
            (25, 9, 2023),
        ]
        result = find_first_day_after_gap(dates_list)
        expected = [(5, 9, 2023), (11, 9, 2023), (18, 9, 2023), (25, 9, 2023)]
        self.assertEqual(result, expected)

    def tc_2(self):
        dates_list = [
            (29, 12, 2023),
            (30, 12, 2023),
            (3, 1, 2024),
            (4, 1, 2024),
            (5, 1, 2024),
        ]
        result = find_first_day_after_gap(dates_list)
        expected = [(3, 1, 2024)]
        self.assertEqual(result, expected)

    def tc_3(self):
        dates_list = [
            (1, 12, 2023),
            (4, 12, 2023),
            (5, 12, 2023),
            (6, 12, 2023),
            (7, 12, 2023),
            (8, 12, 2023),
            (11, 12, 2023),
            (12, 12, 2023),
            (13, 12, 2023),
            (14, 12, 2023),
            (15, 12, 2023),
            (18, 12, 2023),
            (19, 12, 2023),
            (20, 12, 2023),
            (21, 12, 2023),
            (22, 12, 2023),
            (26, 12, 2023),
            (27, 12, 2023),
            (28, 12, 2023),
            (29, 12, 2023),
            (3, 1, 2024),
            (4, 1, 2024),
            (5, 1, 2024),
            (6, 1, 2024),
            (9, 1, 2024),
            (10, 1, 2024),
        ]
        result = find_first_day_after_gap(dates_list)
        expected = [
            (4, 12, 2023),
            (11, 12, 2023),
            (18, 12, 2023),
            (26, 12, 2023),
            (3, 1, 2024),
            (9, 1, 2024)
            ]
        self.assertEqual(result, expected)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(testFunction("tc_1"))
    suite.addTest(testFunction("tc_2"))
    suite.addTest(testFunction("tc_3"))
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    suite = test_suite()
    runner.run(suite)
