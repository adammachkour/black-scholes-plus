from math import *
from scipy.stats import norm
from datetime import datetime
import yfinance as yf
import statistics as stat
import csv


def get_spot_price(ticker):
    ticker_df = yf.Ticker(ticker)
    data = ticker_df.history()
    # Get last quote
    spot_price = (data.tail(1)['Close'].iloc[0])
    # Round price
    return round(spot_price, 2)


def get_standard_deviation(ticker,
                           period):
    # Set yahoo finance
    ticker_df = yf.Ticker(ticker)
    # Get period data
    data = ticker_df.history(period=period)
    # Get closing price
    data_close = data['Close']
    # Get % change ( day_1 / day_0 ) - 1
    per_change = (data_close / data_close.shift(1)) - 1
    # Delete first datum (NaN)
    per_change = per_change.iloc[1:]
    # Standard deviation
    standard_deviation = stat.stdev(per_change)
    # Annualized standard dev
    annual_standard_deviation = standard_deviation * (252 ** 0.5)
    return annual_standard_deviation


def get_time_to_expiry(maturity):
    # Today's date
    day_0 = datetime.today()
    # Maturity date
    date_format = "%Y-%m-%d"
    day_exp = datetime.strptime(maturity, date_format)
    # Delta date: i.e. 1 day, 0:00:00
    date_to_exp = day_exp - day_0
    # Delta days: i.e. 1 day
    days_to_exp = date_to_exp.days
    return days_to_exp


def bsm_calculation(flag_call_put,
                    spot,
                    strike,
                    time_to_exp,
                    vol,
                    rfr,
                    div_yield):
    # Convert time to expiration from years to day
    time_to_exp = time_to_exp / 365
    # Partial Diff Equ -BSM
    d1 = (log(float(spot) / strike) + ((rfr - div_yield) + vol * vol / 2.) * time_to_exp) / (vol * sqrt(time_to_exp))
    d2 = d1 - vol * sqrt(time_to_exp)
    # Calculate euro call price
    bsm_call = spot * exp(-div_yield * time_to_exp) * norm.cdf(d1) - strike * exp(-rfr * time_to_exp) * norm.cdf(d2)
    bsm_call_string = 'BSM call price {}'.format(round(bsm_call, 2))
    # Calculate euro put price
    bsm_put = strike * exp(-rfr * time_to_exp) * norm.cdf(-d2) - spot * exp(-div_yield * time_to_exp) * norm.cdf(-d1)
    bsm_put_string = 'BSM put price {}'.format(round(bsm_put, 2))
    # Check if call or put calculation and return value
    if flag_call_put == 'C':
        # If call
        return round(bsm_call, 2)
    elif flag_call_put == 'P':
        # If put
        return round(bsm_put, 2)
    else:
        # else both
        return bsm_call_string, bsm_put_string


def get_option_market_data(ticker, maturity, put_or_call_flag, strike):
    ticker_df = yf.Ticker(ticker)
    # Fetch option chain @ specified maturity
    option_chain = ticker_df.option_chain(maturity)
    # Fetch call or put
    if put_or_call_flag == 'C':
        option_chain_call = option_chain.calls
        # Select strike row
        option_row = option_chain_call.loc[option_chain_call['strike'] == strike]
        return option_row[['contractSymbol', 'strike', 'lastPrice', 'bid', 'ask', 'openInterest', 'impliedVolatility']]
    elif put_or_call_flag == 'P':
        option_chain_put = option_chain.puts
        # Select strike row
        option_row = option_chain_put.loc[option_chain_put['strike'] == strike]
        return option_row[['contractSymbol', 'strike', 'lastPrice', 'bid', 'ask', 'openInterest', 'impliedVolatility']]
    else:
        exit(1)


def main(ticker, put_or_call_flag, standard_deviation_period, strike_price, expiration_date, rfr, div_yield):
    # Set risk free rate type into float
    risk_free_rate = float(rfr)                               # Will define a method for this later
    # Set dividend yield type into float
    returned_get_dividend_yield = float(div_yield)            # Will define a method for this later
    # Set strike price into float
    strike = float(strike_price)
    # Derive option prices
    bsm_price = bsm_calculation(put_or_call_flag,                                           # Call or put flag
                                get_spot_price(ticker),                                     # Spot price
                                strike,                                                     # Strike price
                                get_time_to_expiry(expiration_date),                        # Days to expiration
                                get_standard_deviation(ticker, standard_deviation_period),  # Volatility
                                risk_free_rate,                                             # Risk free rate
                                returned_get_dividend_yield)                                # Dividend yield
    # Fetch market price
    option_market_data = get_option_market_data(ticker,                                     # Ticker
                                                expiration_date,                            # Expiration date
                                                put_or_call_flag,                           # Call or put flag
                                                strike)                                     # Strike Price
    # Print ticker and spot to console
    '''
    print('{} $ {} USD'.format(ticker.upper(), get_spot_price(ticker)))
    print('Volatility over {} sample'.format(standard_deviation_period))
    print('Annualized volatility {}'.format(get_standard_deviation(ticker, standard_deviation_period)))
    # Print BSM price to console
    if put_or_call_flag == 'C':
        bsm_call_string = 'BSM call price {}'.format(round(bsm_price, 2))
        print(bsm_call_string)
    elif put_or_call_flag == 'P':
        bsm_put_string = 'BSM put price {}'.format(round(bsm_price, 2))
        print(bsm_put_string)
    else:
        print('{} not a valid flag'.format(put_or_call_flag))
    # Print option data to console
    '''
    print('------------------------------------- Option chain -------------------------------------')
    print(option_market_data.to_string())


### BULK OPTION PRICING: using a CSV file - located in the same directory as this script - with the following fields for every row:
# ticker  # put_or_call_flag  # standard_deviation_period  # strike  # expiration_date  # rfr  # div_yield
# Importing csv file containing option parameters and passing them into our list
'''
with open('file.csv') as f:
    reader = csv.reader(f)
    optionParamList = list(reader)
# print(optionParamList)
for optionParam in optionParamList:
    # Unpacking option data and passing to main
    main(*optionParam)
'''


### INDIVIDUAL OPTION PRICING: edit the following parameters and pass to main().
# ticker  # put_or_call_flag  # standard_deviation_period  # strike  # expiration_date  # rfr  # div_yield
main('fb', 'P', '6mo', '245', '2021-06-18', '0', '0')
