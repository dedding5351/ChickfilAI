import pandas as pd

customer_data = pd.read_csv("Chick-Fil-A Kiosk - Customer.csv")

menu_data = pd.read_csv("Chick-Fil-A Kiosk - Menu.csv")

customerArray = []

menuArray = []


class Person:
  def __init__(self, ID, first_name, last_name, last_order, description, order_price, url):
    self.id = ID
    self.first_name = first_name
    self.last_name = last_name
    self.last_order = last_order
    self.order_price = order_price
    self.description = description
    self.url = url

class Menu:
  def __init__(self, ID, name, description, order_price, url):
    self.id = ID
    self.name = name
    self.description = description
    self.order_price = order_price
    self.url = url


for i in range(len(customer_data)):
    customerArray.append(Person(customer_data.values[i][0], customer_data.values[i][1], customer_data.values[i][2], customer_data.values[i][3], customer_data.values[i][4], customer_data.values[i][5], customer_data.values[i][6]))

for i in range(len(menu_data)):
    menuArray.append(Menu(menu_data.values[i][0], menu_data.values[i][1], menu_data.values[i][2], menu_data.values[i][3], menu_data.values[i][4]))

