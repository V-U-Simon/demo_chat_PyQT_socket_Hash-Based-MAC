# from common.errors_user import ReqFieldMissingError, ServerError
# import unittest
# from common.variables import *
# from client import create_presence, process_response_ans
# import sys

# sys.path.append("../")


# # Класс с тестами
# class TestClass(unittest.TestCase):
#     # тест коректного запроса
#     def test_def_presense(self):
#         test = create_presence("Guest")
#         # время необходимо приравнять принудительно иначе тест никогда не будет пройден
#         test[TIME] = 1.1
#         self.assertEqual(
#             test, {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: "Guest"}}
#         )

#     # тест корректтного разбора ответа 200
#     def test_200_ans(self):
#         self.assertEqual(process_response_ans({RESPONSE: 200}), "200 : OK")

#     # тест корректного разбора 400
#     def test_400_ans(self):
#         self.assertRaises(
#             ServerError, process_response_ans, {RESPONSE: 400, ERROR: "Bad Request"}
#         )

#     # тест исключения без поля RESPONSE
#     def test_no_response(self):
#         self.assertRaises(
#             ReqFieldMissingError, process_response_ans, {ERROR: "Bad Request"}
#         )


# if __name__ == "__main__":
#     unittest.main()
