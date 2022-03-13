from ccqt.core.core import core

import pandas as pd
import datetime
import tqdm

class backtest(core):
    def __init__(self, name):
        super().__init__(name)
        self.m_curtime = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
        self.m_ticker2ohlcv_min = {}
        self.m_ticker2ohlcv_hour = {}
        self.m_timeframe = 'day'
        self.m_balance = {}

        df_columns = [
            'asset_as_krw',
            'is_bull',
            'profit(%)',
            'cagr(%)_all',
            'cagr(%)_3month',
            'cagr(%)_month',
            'cagr(%)_week(7d)',
            'stdev(%)_all',
            'mdd(%)',
            'recovery_days',
            'ration_win(%)',
            'mean_profit(%)',
            'mean_loss(%)',
            'max_profit(%)',
            'max_loss(%)',
            'count_trade',
            'count_all',
        ]
        self.m_result_df = pd.DataFrame(
            columns=df_columns,
            index=pd.to_datetime([], utc=True))

    def load_config(self, filename):
        super().load_config(filename)
        self.m_balance['KRW'] = self.m_config_budget_krw

    def get_current_time(self) -> datetime.datetime:
        return self.m_curtime

    def get_current_price(self, ticker):
        tmp = self.m_ticker2ohlcv_min[ticker]['open']
        tmp = tmp.fillna(method='ffill')
        tmp = tmp[ tmp.index <= self.m_curtime]
        # upbit의 경우 minute candle csv 뽑으면 없는 분봉 있기도 함
        return tmp[-1]

    def get_current_balance(self, ticker) -> float:
        if ticker not in self.m_balance:
            return 0
        return self.m_balance[ticker]

    def inc_balance(self, ticker, amount):
        if ticker not in self.m_balance:
            self.m_balance[ticker] = 0
        self.m_balance[ticker] += amount

    def dec_balance(self, ticker, amount):
        if ticker not in self.m_balance:
            self.m_balance[ticker] = 0
        self.m_balance[ticker] -= amount

    def get_current_ohlcv_hour(self, ticker):
        df = self.m_ticker2ohlcv_hour[ticker]
        # 현재 시간을 시작하는 데이터도 포함하도록 하자
        df_p = df[ df.index <= self.m_curtime]
        return df_p

    def get_current_asset_as_krw(self):
        krw = 0
        for asset in self.m_balance:
            if asset == 'KRW':
                krw += self.m_balance[asset]
            else:
                krw += self.m_balance[asset] * self.get_current_price(asset)
        return krw

    def report_end_of_day(self, day=None):
        if day is None:
            day = self.m_curtime.date()

        self.m_result_df.loc[day] = {
            'asset_as_krw': self.get_current_asset_as_krw(),
        }



    def standby_short(self):
        if self.m_timeframe == 'minute':
            td = datetime.timedelta(minutes=1)
        elif self.m_timeframe == 'hour':
            td = datetime.timedelta(hours=1)
        else:
            td = datetime.timedelta(days=1)
        self.m_curtime += td

    def standby_until(self, target):
        self.m_curtime = target
        self.logerror(f'standby_until, {target=}')

    def order_buy_market_wo_fee(self, ticker, krw_wo_fee):
        '''
        upbit 처럼 구현한다.
        계좌에 krw_wo_fee 외에 수수료도 있어야 한다
        '''
        # upbit : 매수할 때는 수수료 고려한 금액을 넣어줘야한다.
        # upbit : 매도할 때는 암호화폐 총량만 넣어주면 됨 (매도 후 금액에서 수수료 공제되서 들어옴)
        self.loginfo(f'{krw_wo_fee=}, {ticker=}')
        self.loginfo(f'(before) {self.get_current_balance(ticker)=}')
        self.inc_balance(ticker, krw_wo_fee / self.get_current_price(ticker))
        self.loginfo(f'(after) {self.get_current_balance(ticker)=}')

    def order_buy_market_including_fee(self, ticker, krw):
        if krw > self.get_current_balance('KRW'):
            krw = self.get_current_balance('KRW')
        self.dec_balance('KRW', krw)
        krw_wo_fee = krw / (1 + self.m_config_fee_rate_percent / 100)
        self.order_buy_market_wo_fee(ticker, krw_wo_fee)

    def order_sell_market(self, ticker, amount):
        self.loginfo(f'order_sell {ticker=}, {amount=})')
        if self.m_balance[ticker] < amount:
            amount = self.m_balance[ticker]
        self.loginfo(f"(before) order_sell m_balance : {self.m_balance=}")
        self.m_balance[ticker] -= amount
        self.m_balance['KRW'] += \
            self.get_current_price(ticker) * amount * (1 - self.m_config_fee_rate_percent / 100)
        self.loginfo(f"(after) order_sell m_balance : {self.m_balance=}")
        # Backtest 상에서는 언제나 성공함
        return True


    def set_timeframe(self, timeframe: str):
        self.m_timeframe = timeframe

    def load_ohlcv_min(self, ticker: str, filename: str):
        dt_parser = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S%z")
        df = pd.read_csv(
            filename,
            index_col = 0,
            parse_dates = True,
            date_parser = dt_parser)
        self.m_ticker2ohlcv_min[ticker] = df
        self.m_ticker2ohlcv_hour[ticker] = df.resample('1H').agg({
            'open': 'first', #lambda df: None if df.empty else df[0],
            'close': 'last', #lambda df: None if df.empty else df,
            'high': 'max',
            'low': 'min',
            'volume': 'sum',
            'value': 'sum',
        })

    def infer_starttime_from_ohlcv(self):
        times = []
        for df in self.m_ticker2ohlcv_min.values():
            times += [df.index[0].to_pydatetime()]
        self.m_curtime = min(times)
        self.loginfo(f'{self.m_curtime=}')

    def set_curtime(self, curtime):
        self.m_curtime = curtime




