class Shop:
    def __init__(self, database, player, items, verbose=False):
        self.database = database
        self.player = player
        self.items = items  # json
        self.verbose = verbose

    def buy_item(self, item, amount):
        try:
            amount = int(amount)
        except ValueError:
            response = {"success": False,
                        "reason": "not numeric",
                        "message": f"{amount} is not numeric"}
            return response

        if item not in self.items:
            response = {"success": False,
                        "reason": "not found",
                        "message": f"{item} not found"}
        else:
            expense = self.items[item]["price"] * amount
            if self.player.money >= expense:
                self.player.update_value(money_change=-expense)
                response = {"success": True,
                            "player": self.player.get_all_data(),
                            "amount": amount,
                            "message": f"Bought {item} successfully"}
            else:
                response = {"success": False,
                            "reason": "money",
                            "message": f"Bought {item} failed"}
        return response

    def buy_fuel(self, expense):
        try:
            expense = int(expense)
        except ValueError:
            response = {"success": False,
                        "reason": "not numeric",
                        "message": f"{expense} is not numeric"}
            return response

        if self.player.money >= expense:
            amount = expense / self.items["fuel"]["price"]
            self.player.update_value(fuel_change=amount, money_change=-expense)
            message = "[ok] buy: fuel"
            response = {"success": True,
                        "amount": amount,
                        "player": self.player.get_all_data(),
                        "message": message}
        else:
            message = "Sorry, you don't have enough money"
            response = {"success": False,
                        "reason": "money",
                        "message": message}
        return response

    def buy_airport(self):
        if self.player.location != self.player.home:
            message = "[fail] buy: airport how do you buy airport when you are not at home?"
            response = {"success": False,
                        "reason": "hack",
                        "message": message}
            return response

        expense = self.items["airport"]["price"]
        if self.player.money >= expense:
            self.player.update_value(money_change=-expense)
            message = "[ok] buy: airport"
            response = {"success": True,
                        "player": self.player.get_all_data(),
                        "message": message}
            self.player.update_state(finish=True)
        else:
            message = "[fail] buy: airport"
            response = {"success": False,
                        "reason": "money",
                        "message": message}
        return response
