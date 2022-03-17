from ccqt.core.core import core

import configparser
import datetime
import pause
import pyupbit
import slack_sdk
import time
import logging

'''
일단은 upbit 전용으로 구현했다. 다른 거래소까지 확장하는건 미래일
'''
class trade(core):
    def get_current_time(self):
        return datetime.datetime.now().astimezone(datetime.timezone.utc)

    def get_current_price(self):
        pass

    def get_current_ohlcv_hour(self, ticker):
        df = pyupbit.get_ohlcv("KRW-{ticker}", "minute60", count=300)
        #pyupbit 리턴 결과가 UTC+9로 주어지므로 이걸 GMT로 바꿔준다
        df.index = df.index.tz_localize('Asia/Seoul').tz_convert('UTC')
        return df

    def standby_short(self, seconds):
        time.sleep(seconds)

    def standby_until(self, dt):
        pause.until(dt)

    def prepare_upbit(self):
        self.m_upbit = pyupbit.Upbit(self.m_config_upbit_acc_key, self.m_config_upbit_sec_key)

    def check_upbit(self):
        if self.m_config_budget_krw > self.m_upbit.get_balance("KRW") :
            self.m_logger.error("config_budget_krw > KRW in my upbit account")
            raise ValueError("config_budget_krw > KRW in my upbitaccount")
        self.m_logger.info("current Upbit account has enough KRW than budget_krw")
        # upbit 호출하면서 key validity 체크 완료

    def check_loop(self):
        return True