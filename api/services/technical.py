from __future__ import annotations
from typing import Dict, Optional
import pandas as pd
import numpy as np

from ..sources.prices_yfinance import get_price_history

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict:
    """Calculate Bollinger Bands"""
    sma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    current_price = prices.iloc[-1]
    bb_position = (current_price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1])
    
    return {
        'upper': upper.iloc[-1],
        'middle': sma.iloc[-1], 
        'lower': lower.iloc[-1],
        'position': bb_position,  # 0 = at lower band, 1 = at upper band
        'squeeze': (upper.iloc[-1] - lower.iloc[-1]) / sma.iloc[-1] < 0.1  # Tight bands
    }

def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict:
    """Calculate Stochastic Oscillator"""
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(d_period).mean()
    
    return {
        'k': k_percent.iloc[-1],
        'd': d_percent.iloc[-1]
    }

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """Calculate Williams %R"""
    highest_high = high.rolling(period).max()
    lowest_low = low.rolling(period).min()
    wr = -100 * ((highest_high - close) / (highest_high - lowest_low))
    return wr.iloc[-1]

def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> float:
    """Calculate Commodity Channel Index"""
    tp = (high + low + close) / 3  # Typical Price
    sma_tp = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: abs(x - x.mean()).mean())  # Mean Absolute Deviation
    cci = (tp - sma_tp) / (0.015 * mad)
    return cci.iloc[-1]

def get_support_resistance(prices: pd.Series, window: int = 20) -> Dict:
    """Calculate support and resistance levels"""
    highs = prices.rolling(window).max()
    lows = prices.rolling(window).min()
    
    # Find recent pivot points
    recent_high = highs.iloc[-window:].max()
    recent_low = lows.iloc[-window:].min()
    
    return {
        'resistance': recent_high,
        'support': recent_low,
        'current_price': prices.iloc[-1]
    }
    """Calculate MACD indicator"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line.iloc[-1],
        'signal': signal_line.iloc[-1],
        'histogram': histogram.iloc[-1]
    }

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """Calculate MACD indicator"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line.iloc[-1],
        'signal': signal_line.iloc[-1],
        'histogram': histogram.iloc[-1]
    }

def get_comprehensive_technical_analysis(ticker: str, period: str = "6mo") -> Dict:
    """Generate comprehensive technical analysis with multiple indicators"""
    try:
        df = get_price_history(ticker, period=period)
        if df.empty:
            return {"error": "No price data"}
        
        # Handle MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        current_price = float(close.iloc[-1])
        
        # Basic price metrics
        price_change_1d = ((current_price - float(close.iloc[-2])) / float(close.iloc[-2])) * 100
        price_change_5d = ((current_price - float(close.iloc[-6])) / float(close.iloc[-6])) * 100 if len(close) >= 6 else None
        price_change_20d = ((current_price - float(close.iloc[-21])) / float(close.iloc[-21])) * 100 if len(close) >= 21 else None
        
        # Moving averages
        ma_5 = float(close.rolling(5).mean().iloc[-1])
        ma_10 = float(close.rolling(10).mean().iloc[-1])
        ma_20 = float(close.rolling(20).mean().iloc[-1])
        ma_50 = float(close.rolling(50).mean().iloc[-1])
        ma_100 = float(close.rolling(100).mean().iloc[-1]) if len(close) >= 100 else None
        ma_200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        
        # Exponential moving averages
        ema_12 = float(close.ewm(span=12).mean().iloc[-1])
        ema_26 = float(close.ewm(span=26).mean().iloc[-1])
        
        # Technical indicators
        rsi = float(calculate_rsi(close).iloc[-1])
        macd_data = calculate_macd(close)
        bb_data = calculate_bollinger_bands(close)
        stoch_data = calculate_stochastic(high, low, close)
        atr = calculate_atr(high, low, close)
        williams_r = calculate_williams_r(high, low, close)
        cci = calculate_cci(high, low, close)
        support_resistance = get_support_resistance(close)
        
        # Volume analysis
        avg_volume_20 = float(volume.rolling(20).mean().iloc[-1])
        current_volume = float(volume.iloc[-1])
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1
        
        # Price position analysis
        price_vs_ma20 = ((current_price - ma_20) / ma_20) * 100
        price_vs_ma50 = ((current_price - ma_50) / ma_50) * 100
        
        # Generate comprehensive signals
        signals = []
        strength_score = 0
        
        # Trend signals
        if current_price > ma_5 > ma_10 > ma_20 > ma_50:
            signals.append("STRONG_UPTREND")
            strength_score += 3
        elif current_price > ma_20 > ma_50:
            signals.append("UPTREND")
            strength_score += 2
        elif current_price < ma_5 < ma_10 < ma_20 < ma_50:
            signals.append("STRONG_DOWNTREND")
            strength_score -= 3
        elif current_price < ma_20 < ma_50:
            signals.append("DOWNTREND")
            strength_score -= 2
        
        # RSI signals
        if rsi < 20:
            signals.append("EXTREMELY_OVERSOLD")
            strength_score += 2
        elif rsi < 30:
            signals.append("OVERSOLD")
            strength_score += 1
        elif rsi > 80:
            signals.append("EXTREMELY_OVERBOUGHT")
            strength_score -= 2
        elif rsi > 70:
            signals.append("OVERBOUGHT")
            strength_score -= 1
        
        # MACD signals
        if macd_data['macd'] > macd_data['signal'] and macd_data['histogram'] > 0:
            signals.append("MACD_BULLISH")
            strength_score += 1
        elif macd_data['macd'] < macd_data['signal'] and macd_data['histogram'] < 0:
            signals.append("MACD_BEARISH")
            strength_score -= 1
        
        # Bollinger Bands signals
        if bb_data['position'] > 0.8:
            signals.append("BB_OVERBOUGHT")
        elif bb_data['position'] < 0.2:
            signals.append("BB_OVERSOLD")
        if bb_data['squeeze']:
            signals.append("BB_SQUEEZE")
        
        # Stochastic signals
        if stoch_data['k'] < 20 and stoch_data['d'] < 20:
            signals.append("STOCH_OVERSOLD")
        elif stoch_data['k'] > 80 and stoch_data['d'] > 80:
            signals.append("STOCH_OVERBOUGHT")
        
        # Volume signals
        if volume_ratio > 2:
            signals.append("HIGH_VOLUME")
            strength_score += 1
        elif volume_ratio < 0.5:
            signals.append("LOW_VOLUME")
        
        # Williams %R signals
        if williams_r < -80:
            signals.append("WILLIAMS_OVERSOLD")
        elif williams_r > -20:
            signals.append("WILLIAMS_OVERBOUGHT")
        
        # CCI signals
        if cci > 100:
            signals.append("CCI_OVERBOUGHT")
        elif cci < -100:
            signals.append("CCI_OVERSOLD")
        
        # Overall signal based on strength score
        if strength_score >= 4:
            overall_signal = "STRONG_BUY"
        elif strength_score >= 2:
            overall_signal = "BUY"
        elif strength_score <= -4:
            overall_signal = "STRONG_SELL"
        elif strength_score <= -2:
            overall_signal = "SELL"
        else:
            overall_signal = "HOLD"
        
        return {
            "ticker": ticker.upper(),
            "current_price": round(current_price, 2),
            "price_change_1d": round(price_change_1d, 2),
            "price_change_5d": round(price_change_5d, 2) if price_change_5d else None,
            "price_change_20d": round(price_change_20d, 2) if price_change_20d else None,
            
            # Moving averages
            "ma_5": round(ma_5, 2),
            "ma_10": round(ma_10, 2),
            "ma_20": round(ma_20, 2),
            "ma_50": round(ma_50, 2),
            "ma_100": round(ma_100, 2) if ma_100 else None,
            "ma_200": round(ma_200, 2) if ma_200 else None,
            "ema_12": round(ema_12, 2),
            "ema_26": round(ema_26, 2),
            
            # Technical indicators
            "rsi": round(rsi, 2),
            "macd": round(macd_data['macd'], 4),
            "macd_signal": round(macd_data['signal'], 4),
            "macd_histogram": round(macd_data['histogram'], 4),
            
            # Bollinger Bands
            "bb_upper": round(bb_data['upper'], 2),
            "bb_middle": round(bb_data['middle'], 2),
            "bb_lower": round(bb_data['lower'], 2),
            "bb_position": round(bb_data['position'], 3),
            "bb_squeeze": bool(bb_data['squeeze']),
            
            # Stochastic
            "stoch_k": round(float(stoch_data['k']), 2),
            "stoch_d": round(float(stoch_data['d']), 2),
            
            # Other indicators
            "atr": round(float(atr), 2),
            "williams_r": round(float(williams_r), 2),
            "cci": round(float(cci), 2),
            
            # Support/Resistance
            "resistance": round(support_resistance['resistance'], 2),
            "support": round(support_resistance['support'], 2),
            
            # Volume
            "volume_ratio": round(float(volume_ratio), 2),
            "avg_volume_20": int(float(avg_volume_20)),
            
            # Position analysis
            "price_vs_ma20": round(price_vs_ma20, 2),
            "price_vs_ma50": round(price_vs_ma50, 2),
            
            # Signals
            "signals": signals,
            "overall_signal": overall_signal,
            "strength_score": strength_score
        }
        
    except Exception as e:
        return {"error": str(e)}

# Keep the old function for backward compatibility
def get_technical_signals(ticker: str, period: str = "6mo") -> Dict:
    return get_comprehensive_technical_analysis(ticker, period)

def get_multi_timeframe_signals(ticker: str) -> Dict:
    """Get signals across multiple timeframes"""
    timeframes = {
        "1mo": "Short Term",
        "3mo": "Medium Term", 
        "1y": "Long Term"
    }
    
    results = {}
    for period, name in timeframes.items():
        signals = get_comprehensive_technical_analysis(ticker, period)
        if "error" not in signals:
            results[name] = {
                "signal": signals["overall_signal"],
                "rsi": signals["rsi"],
                "trend": "UP" if signals["current_price"] > signals["ma_20"] else "DOWN"
            }
    
    return results
