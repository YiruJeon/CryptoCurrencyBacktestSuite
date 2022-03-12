from ccqt.core.core import core

import pause

class trade(core):

    def get_current_time(self):
        pass

    def get_current_price(self):
        pass

    def standby_short(self):
        pass

    def standby_until(self, dt):
        pause.until(dt)
