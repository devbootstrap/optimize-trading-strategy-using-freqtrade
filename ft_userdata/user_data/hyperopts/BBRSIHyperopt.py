# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement

# --- Do not remove these libs ---
from functools import reduce
from typing import Any, Callable, Dict, List

import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from skopt.space import Categorical, Dimension, Integer, Real  # noqa

from freqtrade.optimize.hyperopt_interface import IHyperOpt

# --------------------------------
# Add your lib to import here
import talib.abstract as ta  # noqa
import freqtrade.vendor.qtpylib.indicators as qtpylib


class BBRSIHyperopt(IHyperOpt):
    """
    This is a Hyperopt template to get you started.

    More information in the documentation: https://www.freqtrade.io/en/latest/hyperopt/

    You should:
    - Add any lib you need to build your hyperopt.

    You must keep:
    - The prototypes for the methods: populate_indicators, indicator_space, buy_strategy_generator.

    The methods roi_space, generate_roi_table and stoploss_space are not required
    and are provided by default.
    However, you may override them if you need 'roi' and 'stoploss' spaces that
    differ from the defaults offered by Freqtrade.
    Sample implementation of these methods will be copied to `user_data/hyperopts` when
    creating the user-data directory using `freqtrade create-userdir --userdir user_data`,
    or is available online under the following URL:
    https://github.com/freqtrade/freqtrade/blob/develop/freqtrade/templates/sample_hyperopt_advanced.py.
    """
    @staticmethod
    def populate_indicators(dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi-buy'] = ta.RSI(dataframe)
        dataframe['rsi-sell'] = ta.RSI(dataframe)

        # Bollinger bands
        bollinger_1sd = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=1)
        dataframe['bb_lowerband_1sd'] = bollinger_1sd['lower']
        dataframe['bb_middleband_1sd'] = bollinger_1sd['mid']
        dataframe['bb_upperband_1sd'] = bollinger_1sd['upper']

        bollinger_2sd = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband_2sd'] = bollinger_2sd['lower']
        dataframe['bb_middleband_2sd'] = bollinger_2sd['mid']
        dataframe['bb_upperband_2sd'] = bollinger_2sd['upper']

        bollinger_3sd = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=3)
        dataframe['bb_lowerband_3sd'] = bollinger_3sd['lower']
        dataframe['bb_middleband_3sd'] = bollinger_3sd['mid']
        dataframe['bb_upperband_3sd'] = bollinger_3sd['upper']

        bollinger_4sd = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=4)
        dataframe['bb_lowerband_4sd'] = bollinger_4sd['lower']
        dataframe['bb_middleband_4sd'] = bollinger_4sd['mid']
        dataframe['bb_upperband_4sd'] = bollinger_4sd['upper']

        return dataframe

    @staticmethod
    def indicator_space() -> List[Dimension]:
        """
        Define your Hyperopt space for searching buy strategy parameters.
        """
        return [
            Integer(5, 50 , name='rsi-value'),
            Categorical([True, False], name='rsi-enabled'),
            Categorical(['tr_bb_lower_1sd', 'tr_bb_lower_2sd', 'tr_bb_lower_3sd', 'tr_bb_lower_4sd'], name='buy-trigger')
        ]

    @staticmethod
    def buy_strategy_generator(params: Dict[str, Any]) -> Callable:
        """
        Define the buy strategy parameters to be used by Hyperopt.
        """
        def populate_buy_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
            """
            Buy strategy Hyperopt will build and use.
            """
            conditions = []

            # GUARDS AND TRENDS
            if params.get('rsi-enabled'):
                conditions.append(dataframe['rsi-buy'] > params['rsi-value'])

            # TRIGGERS
            if 'buy-trigger' in params:
                if params['buy-trigger'] == 'tr_bb_lower_1sd':
                    conditions.append(dataframe['close'] < dataframe['bb_lowerband_1sd'])
                if params['buy-trigger'] == 'tr_bb_lower_2sd':
                    conditions.append(dataframe['close'] < dataframe['bb_lowerband_2sd'])
                if params['buy-trigger'] == 'tr_bb_lower_3sd':
                    conditions.append(dataframe['close'] < dataframe['bb_lowerband_3sd'])
                if params['buy-trigger'] == 'tr_bb_lower_4sd':
                    conditions.append(dataframe['close'] < dataframe['bb_lowerband_4sd'])

            # Check that the candle had volume
            conditions.append(dataframe['volume'] > 0)

            if conditions:
                dataframe.loc[
                    reduce(lambda x, y: x & y, conditions),
                    'buy'] = 1

            return dataframe

        return populate_buy_trend

    @staticmethod
    def sell_indicator_space() -> List[Dimension]:
        """
        Define your Hyperopt space for searching sell strategy parameters.
        """
        return [
            Integer(30, 100, name='sell-rsi-value'),
            Categorical([True, False], name='sell-rsi-enabled'),
            Categorical(['sell_tr_bb_lower_1sd',
                         'sell_tr_bb_mid_1sd',
                         'sell_tr_bb_upper_1sd'], name='sell-trigger')
        ]

    @staticmethod
    def sell_strategy_generator(params: Dict[str, Any]) -> Callable:
        """
        Define the sell strategy parameters to be used by Hyperopt.
        """
        def populate_sell_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
            """
            Sell strategy Hyperopt will build and use.
            """
            conditions = []

            # GUARDS AND TRENDS
            if params.get('sell-rsi-enabled'):
                conditions.append(dataframe['rsi-sell'] > params['sell-rsi-value'])

            # TRIGGERS
            if 'sell-trigger' in params:
                if params['sell-trigger'] == 'sell_tr_bb_lower_1sd':
                    conditions.append(dataframe['close'] > dataframe['bb_lowerband_1sd'])
                if params['sell-trigger'] == 'sell_tr_bb_mid_1sd':
                    conditions.append(dataframe['close'] > dataframe['bb_middleband_1sd'])
                if params['sell-trigger'] == 'sell_tr_bb_upper_1sd':
                    conditions.append(dataframe['close'] > dataframe['bb_upperband_1sd'])

            # Check that the candle had volume
            conditions.append(dataframe['volume'] > 0)

            if conditions:
                dataframe.loc[
                    reduce(lambda x, y: x & y, conditions),
                    'sell'] = 1

            return dataframe

        return populate_sell_trend
