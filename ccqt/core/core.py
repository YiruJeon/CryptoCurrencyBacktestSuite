import configparser
import logging
import slack_sdk

class core:
    def __init__(self, bot_name, level=logging.WARNING):
        self.m_name = bot_name

        # logger = logging.getLogger(__file__)
        self.m_logger = logging.getLogger(bot_name)

        self.m_logger.setLevel(level)
        # create console handler and set level to debug
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(level)
        # create formatter
        formatter = logging.Formatter('[%(asctime)s][%(filename)s][%(levelname)s] %(message)s')
        # add formatter to consoleHandler
        consoleHandler.setFormatter(formatter)
        # add consoleHandler to logger
        self.m_logger.addHandler(consoleHandler)

    def logdebug(self, msg):
        self.m_logger.debug(msg)

    def loginfo(self, msg):
        self.m_logger.info(msg)

    def logwarn(self, msg)
        self.m_logger.warning(msg)

    def logerror(self, msg):
        self.m_logger.error(msg)

    def logcritical(self, msg):
        self.m_logger.critical(msg)


    def print_slack_msg(self, text):
        '''
        슬랙 postMessage API는 1초에 1번 이하임에 주의
        '''
        self.m_slack_webcli.chat_postMessage(channel=self.m_slack_channel_name, text=text)
        self.m_logger.info('_SLACK_'+text)


    def load_config(self, configFileName):
        self.m_config = configparser.ConfigParser()
        self.m_config.read(configFileName, encoding='UTF-8')
        self.m_config_open_time_hour = int(self.m_config['common']['open_time_hour'])
        self.m_config_open_time_min = int(self.m_config['common']['open_time_min'])
        self.m_config_fee_rate_percent = float(self.m_config['upbit']['fee_rate_percent'])
        self.m_config_budget_krw = int(self.m_config['common']['budget_krw'])
        self.m_budget_krw = self.m_config_budget_krw
        self.m_config_upbit_acc_key = self.m_config['upbit']['upbit_acc_key']
        self.m_config_upbit_sec_key = self.m_config['upbit']['upbit_sec_key']
        self.m_config_slack_bot_token = self.m_config['slack']['slack_bot_token']


        # 기본적인 입력값 체크
        self.loginfo(f'{self.m_config_open_time_hour=}')
        self.loginfo(f'{self.m_config_open_time_min=}')
        self.loginfo(f'{self.m_config_fee_rate_percent=}')
        self.loginfo(f'{self.m_config_budget_krw=}')
        self.loginfo(f'{len(self.m_config_upbit_acc_key)=}')
        self.loginfo(f'{len(self.m_config_upbit_sec_key)=}')
        self.loginfo(f'{len(self.m_config_slack_bot_token)=}')

        if not 0 <= self.m_config_open_time_hour < 24:
            self.m_logger.error("config_open_time_hour")
            raise ValueError("config_open_time_hour")

        if not 0 <= self.m_config_open_time_min < 60:
            self.m_logger.error("m_config_open_time_min")
            raise ValueError("m_config_open_time_min")


    def prepare_slack(self, channel_name):
        self.m_slack_webcli = slack_sdk.WebClient(self.m_config_slack_bot_token)
        self.m_slack_channel_name = channel_name
        self.loginfo(f'{self.m_slack_channel_name=}')

    def check_slack(self):
        self.print_slack_msg("Test Message for slack bot:" + self.m_name)


    def get_current_time(self):
        pass

    def get_current_price(self):
        pass

    def standby_short(self):
        pass

    def standby_until(self):
        pass