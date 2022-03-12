from ccqt.core.core import core

import pandas as pd
import datetime

class backtest(core):
    _curtime = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    _ticker2ohlcv = {}
    _timeframe = 'day'

    def get_current_time(self):
        return self._curtime

    def get_current_price(self, ticker):
        pass

    def standby_short(self):
        if self._timeframe == 'minute':
            td = datetime.timedelta(minutes=1)
        elif self._timeframe == 'hour':
          td = datetime.timedelta(hours=1)
        else:
          td = datetime.timedelta(days=1)
        self._curtime += td

    def standby_until(self, target):
        self._curtime = target


    def set_curtime(self, curtime):
      self._curtime = curtime

    def set_timeframe(self, timeframe: str):
        self._timeframe = timeframe

    def load_ohlcv(self, ticker: str, filename: str):
        df = pd.read_csv(filename)
        self._ticker2ohlcv[str] = df




