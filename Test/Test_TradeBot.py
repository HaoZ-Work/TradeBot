import unittest
from unittest.mock import patch
from SwingTrading import TradeBot

class TestTradeBot(unittest.TestCase):

    def setUp(self):
        # Mock the ccxt library used in TradeBot
        self.patcher = patch('SwingTrading.ccxt')
        self.mock_ccxt = self.patcher.start()

        # Setup mock for the exchange and its methods
        self.mock_exchange = self.mock_ccxt.coinbase.return_value
        self.mock_exchange.fetch_balance.return_value = {'total': {'BTC': 1, 'USDC': 10000}}
        self.mock_exchange.fetch_ticker.return_value = {'last': 57000}
        self.mock_exchange.create_limit_buy_order.return_value = {'id': '123', 'amount': 0.5}
        self.mock_exchange.create_limit_sell_order.return_value = {'id': '456', 'amount': 0.5}
        self.mock_exchange.fetch_order.return_value = {'status': 'closed'}
        self.mock_exchange.fetch_open_orders.return_value = []
        self.mock_exchange.cancel_order.return_value = True

        # Initialize TradeBot instance for testing
        self.bot = TradeBot('coinbase', '../secret.json')

    def tearDown(self):
        self.patcher.stop()

    def test_fetch_balance(self):
        balance = self.bot.fetch_balance()
        self.assertEqual(balance, {'total': {'BTC': 1, 'USDC': 10000}})

    def test_fetch_current_price(self):
        price = self.bot.fetch_current_price('BTC/USDC')
        self.assertEqual(price, 57000)

    def test_create_order_buy(self):
        order = self.bot.create_order('BTC/USDC', 'buy', 'limit', 0.5, 57000)
        self.assertEqual(order['id'], '123')
        self.assertEqual(order['amount'], 0.5)

    def test_create_order_sell(self):
        order = self.bot.create_order('BTC/USDC', 'sell', 'limit', 0.5, 60000)
        self.assertEqual(order['id'], '456')
        self.assertEqual(order['amount'], 0.5)

    def test_cancel_order(self):
        result = self.bot.cancel_order('123')
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()