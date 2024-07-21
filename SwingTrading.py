import ccxt
import json
import time
import os
import logging
from tgLogger import TelegramBotHandler
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
load_dotenv()


class TradeBot:
    '''
    Base class for trading bot
    '''
    def __init__(self, exchange_name, json_file_path):
        with open(json_file_path, 'r') as f:
            secrets = json.load(f)

        self.exchange = getattr(ccxt, exchange_name)({
            'apiKey': secrets[exchange_name]['dev_key']['key'],
            'secret': secrets[exchange_name]['dev_key']['secret']
        })

    def fetch_balance(self):
        return self.exchange.fetch_balance()

    def fetch_current_price(self, symbol):
        ticker = self.exchange.fetch_ticker(symbol)
        return ticker['last']  # 'last' is the price of the last trade

    def list_open_orders(self):
        orders = self.exchange.fetch_open_orders()
        orders_dict = {order['id']: order for order in orders}
        return orders_dict

    def create_order(self, symbol, side, order_type, amount_btc, price, amount_currency=None):
        if amount_currency is None:
            if side == 'buy':
                order = self.exchange.create_limit_buy_order(symbol, amount_btc, price)
            elif side == 'sell':
                order = self.exchange.create_limit_sell_order(symbol, amount_btc, price)
        else:
            amount_btc = amount_currency / price
            if side == 'buy':
                order = self.exchange.create_limit_buy_order(symbol, amount_btc, price)
            elif side == 'sell':
                order = self.exchange.create_limit_sell_order(symbol, amount_btc, price)

        return order

    def cancel_order(self, order_id):
        return self.exchange.cancel_order(order_id)

    def monitor_order(self, order_id):
        order = self.exchange.fetch_order(order_id)
        return order['status']

    def cancel_all_orders(self):
        orders = self.list_open_orders()
        for order_id in orders.keys():
            self.cancel_order(order_id)

    def swing_trade(self, symbol, entry_price, exit_price, amount_currency, check_interval=3):
        open_orders = self.list_open_orders()

        entry_order = next(
            (order for order in open_orders.values() if
             order['symbol'] == symbol and order['price'] == entry_price and order['side'] == 'buy'),
            None
        )
        exit_order = next(
            (order for order in open_orders.values() if
             order['symbol'] == symbol and order['price'] == exit_price and order['side'] == 'sell'),
            None
        )

        if exit_order:
            logging.info('---EXIT order already exists---')
            logging.info('waiting for EXIT order to be filled')

            order_id = exit_order['id']

            while True:
                order_status = self.monitor_order(order_id)
                if order_status == 'closed':
                    logging.info('---EXIT order filled!---')
                    break
                time.sleep(check_interval)

        if entry_order:
            logging.info('---ENTRY order already exists---')
            order_id = entry_order['id']
            amount = open_orders[order_id]['amount']
            logging.info('waiting for ENTRY order to be filled')

            while True:
                order_status = self.monitor_order(order_id)
                if order_status == 'closed':
                    logging.info('---ENTRY order filled!---')
                    break
                time.sleep(check_interval)

            while True:
                current_price = self.fetch_current_price(symbol)
                if abs((current_price - exit_price) / exit_price) <= 0.05:
                    order = self.create_order(symbol, 'sell', 'limit', amount, exit_price)
                    logging.info("EXIT order created.")
                    order_id = order['id']
                    break
                time.sleep(check_interval)

            while True:
                order_status = self.monitor_order(order_id)
                logging.info('waiting for EXIT order to be filled')

                if order_status == 'closed':
                    logging.info('---EXIT order filled!---')
                    break
                time.sleep(check_interval)

        if not entry_order:
            current_price = self.fetch_current_price(symbol)

            amount = amount_currency / current_price
            while True:
                if abs((current_price - entry_price) / entry_price) <= 0.05:
                    order = self.create_order(symbol, 'buy', 'limit', amount, entry_price)
                    logging.info("entry order created.")
                    new_order_id = order['id']
                    break
                time.sleep(check_interval)

            logging.info('waiting for ENTRY order to be filled')
            while True:
                order_status = self.monitor_order(new_order_id)
                if order_status == 'closed':
                    logging.info('---ENTRY order filled!---')
                    break
                time.sleep(check_interval)

            while True:
                current_price = self.fetch_current_price(symbol)
                if abs((current_price - exit_price) / exit_price) <= 0.05:
                    order = self.create_order(symbol, 'sell', 'limit', amount, exit_price)
                    logging.info("EXIT order created.")
                    order_id = order['id']
                    break
                time.sleep(check_interval)

            logging.info('waiting for EXIT order to be filled')
            while True:
                order_status = self.monitor_order(order_id)
                if order_status == 'closed':
                    logging.info('---EXIT order filled!---')
                    break
                time.sleep(check_interval)

def main():
    try:
        BUY_PRICE = int(os.environ['BUY_PRICE'].strip())
        SELL_PRICE = int(os.environ['SELL_PRICE'].strip())
        AMOUNT_CURRENCY = int(os.environ['AMOUNT_CURRENCY'].strip())

        bot = TradeBot('coinbase', 'secret.json')
        bot.swing_trade('BTC/USDC', BUY_PRICE, SELL_PRICE, AMOUNT_CURRENCY)
    except KeyError as e:
        logging.error(f"Error: Missing required environment variable: {e}")
        exit(1)
    except ValueError as e:
        logging.error(f"Error: Invalid value for environment variable: {e}")
        exit(1)

if __name__ == '__main__':
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    logging.basicConfig(
        handlers=[
            RotatingFileHandler('tradebot.log', maxBytes=1000000, backupCount=3),
            TelegramBotHandler(bot_token=bot_token, chat_id=chat_id)
        ],
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

    main()
