import time
import datetime
import pandas as pd
import numpy as np
import pprint
import pause
import configparser
import slack_sdk
import logging
import pyupbit

#import cryptocompare
#import tqdm
#import plotly.express as px
#import os
#import shutil
#import itertools

################################################################################

logger = logging.getLogger(__file__)
# logger = logging.getLogger("LEVB-BOT")

logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('[%(asctime)s][%(filename)s][%(levelname)s] %(message)s')
# add formatter to consoleHandler
consoleHandler.setFormatter(formatter)
# add consoleHandler to logger
logger.addHandler(consoleHandler)

################################################################################

bot_name = 'Larry Williams Volatility Breakout with Volatility Control and Noise Tech. for Upbit-BTC-KRW Only'

# 설정변수 가져오기
config = configparser.ConfigParser()
config.read('test.ini', encoding='UTF-8')
config_open_time_hour = int(config['common']['open_time_hour'])
config_open_time_min = int(config['common']['open_time_min'])
config_budget_krw = int(config['common']['budget_krw'])
budget_krw = config_budget_krw
config_upbit_acc_key = config['upbit']['upbit_acc_key']
config_upbit_sec_key = config['upbit']['upbit_sec_key']
config_slack_bot_token = config['slack']['slack_bot_token']

slack_webcli = slack_sdk.WebClient(config_slack_bot_token)
slack_channel_name = '#lwvb-vn'

upbit = pyupbit.Upbit(config_upbit_acc_key, config_upbit_sec_key)

# 기본적인 입력값 체크
logger.info(f'{config_open_time_hour=}')
logger.info(f'{config_open_time_min=}')
logger.info(f'{config_budget_krw=}')
logger.info(f'{slack_channel_name=}')

logger.info(f'{len(config_upbit_acc_key)=}')
logger.info(f'{len(config_upbit_sec_key)=}')
logger.info(f'{len(config_slack_bot_token)=}')

if not 0 <= config_open_time_hour < 24:
    logger.error("config_open_time_hour")
    exit(0)

if not 0 <= config_open_time_min < 60:
    logger.error("config_open_time_hour")
    exit(0)

if config_budget_krw > upbit.get_balance("KRW") :
    logger.error("config_budget_krw > KRW in my account")
    exit(0)
logger.info("current Upbit account has enough KRW than budget_krw")

# upbit 호출하면서 key validity 체크 완료

def print_slack_msg(text):
    slack_webcli.chat_postMessage(channel=slack_channel_name, text=text)
    logger.info('_SLACK_'+text)

# slack 봇도 작동 테스트
print_slack_msg("BOT STARTED:" + bot_name)
time.sleep(1)


################################################################################

# 처음 틀었을때: 다음 첫 개장할때까지 기다리기
# 오늘 개장시각 기준으로 다음첫개장시각 확인
now = datetime.datetime.now().astimezone(datetime.timezone.utc)
first_open_time = datetime.datetime(
    now.year, now.month, now.day,
    config_open_time_hour, config_open_time_min, 0).astimezone(datetime.timezone.utc)
if now < first_open_time:
    logger.info("Bot started before first open time {}".format(first_open_time))
else:
    logger.info("Bot started after {}".format(first_open_time))
    first_open_time += datetime.timedelta(days=1)
    logger.info("first open time would be {}".format(first_open_time))

# 다음첫개장할때까지 대기
logger.info("Before first trade, now, wait until {}".format(first_open_time))
pause.until(first_open_time)

print_slack_msg("now going to while loop...")


################################################################################

next_open_time = first_open_time
# 세팅모드 먼저 시작하도록 한다!


while True:
    # loop invariant:
    # 1. next_open_time = cur_open_time + 1day
    # (not now) 2. cur_open_time <= now < next_open_time
    # 3. cur_open_time < clear_time < next_open_time
    now = datetime.datetime.now().astimezone(datetime.timezone.utc)

    # 하루의 끝이자 시작. 세팅 모드
    if next_open_time <= now:
        print_slack_msg("투자일 시작/종료 시각 도달, LWVB 초기 세팅 시작")
        cur_open_time = next_open_time
        next_open_time = next_open_time + datetime.timedelta(days=1)
        clear_time = next_open_time - datetime.timedelta(minutes=10)
        is_buy_completed = False
        is_sold_completed = False

        # MT여부 확인
        df = pyupbit.get_ohlcv("KRW-BTC", "minute60", count=300)
        #pyupbit 리턴 결과가 UTC+9로 주어지므로 이걸 GMT로 바꿔준다
        df.index = df.index.tz_localize('Asia/Seoul').tz_convert('GMT')
        hist_day = df.resample('1D', offset=datetime.timedelta(
            hours=config_open_time_hour,
            minutes=config_open_time_min)).agg(
        {
            'open': 'first',
            'close': 'last',
            'high': 'max',
            'low': 'min',
            'volume': 'sum',
            'value': 'sum',
        })
        if cur_open_time not in hist_day.index:
            logger.error("cur_open_time not in hist_day.index")
            logger.error(f'{cur_open_time=}')
            logger.error(hist_day.index)

        hist_day['is_bull'] = True
        for open_dcount in [3, 5, 10]:
            colStr = 'maopen_{}'.format(open_dcount)
            hist_day[colStr] = hist_day['open'].shift(1).rolling(open_dcount).mean()
            hist_day['is_bull'] = hist_day['is_bull'] & (hist_day['open'].shift(1) > hist_day[colStr])

        print_slack_msg(str(hist_day[['open', 'high', 'low', 'close', 'is_bull']]))
        time.sleep(1)
        if not hist_day['is_bull'][-1]:
            print_slack_msg("MT 조건 만족 안함! 오늘 하루 쉼")
            pause.until(datetime.datetime.today() + datetime.timedelta(hour=23))

        # 기억하자:
          # hist_day 에서 마지막행은 오늘 데이터(시가만 유효)이고
          # 마지막 전 행이 어제 데이터다

        range_prev = hist_day['high'][-2] - hist_day['low'][-2]
        noise_prev = 1 - abs(hist_day['close'][-2] - hist_day['open'][-2]) / range_prev
        breakout_price = hist_day['open'][-1] + range_prev * noise_prev
        volatility = range_prev / hist_day['open'][-2]
        if volatility <= 0.05:
            invest_ratio = 1
        else:
            invest_ratio = 0.05 / volatility

        today_open = hist_day['open'][-1]
        print_slack_msg(f'{range_prev=}, {noise_prev=}, {breakout_price=}, {volatility=}, {invest_ratio=}, {today_open=}')



    # loop invariant:
    # 1. next_open_time = cur_open_time + 1day
    # 2. cur_open_time <= now < next_open_time
    # 3. cur_open_time < clear_time < next_open_time
    # now loop invariant 2. holds

    # 하루의 종료에 다다름 정리 모드
    # 모두 팔고, 수익실현, 수익률계산하고, 현재 관리예금 업데이트
    if clear_time <= now :
        if is_sold_completed:
            print_slack_msg('매도 이미 완료, 다음 개장 시간 까지 대기 ...')
            pause.until(next_open_time)
        else:
            logger.info("Starting Selling...")
            btc_amount = upbit.get_balance("BTC")
            sellResult = upbit.sell_market_order("KRW-BTC", btc_amount)
            is_sold_completed = True

            if sellResult is None:
                logger.error("critical error. sell order failed")
                print_slack_msg('매도 주문 실패' + f'{btc_amount=}')
            else:
                # check revenue_krw
                order_detail = upbit.get_order(sellResult['uuid'])
                revenue_krw = -float(order_detail['paid_fee'])
                for trade_detail in order_detail['trades']:
                    revenue_krw += float(trade_detail['funds'])
                revenue_krw = int(revenue_krw)
                budget_krw += revenue_krw
                print_slack_msg('매도 주문 완료' + f'{btc_amount=}, {revenue_krw=}, {budget_krw=}')

        # 루프 전 iteration 제거할 수 있을거같은데?
        #remaining_volume = float(sell_result['remaining_volume'])
        #while remaining_volume > 0:
        #    time.sleep(5)
        #    print_slack_msg('remaining_volume: {}'.format(float(sell_result['remaining_volume'])))
        #    sell_result = upbit.sell_market_order("KRW-BTC", cur_btc_amount)
        #    if sell_result is None:
        #        print_slack_msg('api failed. stop sell_all()')
        #        print_slack_msg('final_btc_asset is the previous reamining_volume')
        #        break
        #    print_slack_msg(f'{sell_result=}')


    # 거래 모드
    if now < clear_time:
        if is_buy_completed:
            print_slack_msg('매수 이미 완료, 정리 시간 까지 대기 ...')
            pause.until(clear_time)
        else:
            curPrice = pyupbit.get_current_price('KRW-BTC')
            if breakout_price <= curPrice:
                logger.info("Starting Buying...")
                buyResult = upbit.buy_market_order('KRW-BTC', budget_krw * invest_ratio)
                is_buy_completed = True
                if buyResult is None:
                    # 거래실패. 너무 낮은 금액으로 시도한 것일 수 있음
                    print_slack_msg('매수 주문 실패' + f'{budget_krw * invest_ratio=}')
                else:
                    # check cost krw
                    order_detail = upbit.get_order(buyResult['uuid'])
                    cost_krw = float(order_detail['paid_fee'])
                    for trade_detail in order_detail['trades']:
                        cost_krw += float(trade_detail['funds'])
                    cost_krw = int(cost_krw)
                    budget_krw -= cost_krw
                    print_slack_msg('매수 주문 완료' + f'{cost_krw=}, {budget_krw=}')

    time.sleep(1)  # 1초에 한번 정도 API로 체크하는건 전혀 문제 없음
    logger.info("bot is running well ... now:{}".format(str(datetime.datetime.now())))