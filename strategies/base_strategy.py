# strategies/base_strategy.py

class BaseStrategy:
    def __init__(self):
        pass

    def fetch_initial_data(self):
        raise NotImplementedError

    def update_data(self):
        raise NotImplementedError

    def analyze_market(self):
        raise NotImplementedError

    def execute_order(self, order_type, entry_price, level):
        raise NotImplementedError
