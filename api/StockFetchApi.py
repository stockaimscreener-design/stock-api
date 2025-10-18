from flask import Flask, jsonify, request
import yfinance as yf
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from Supabase

def get_stock_data(symbol):
    """Fetch data for a single symbol"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not price:
            return None
        
        volume = info.get('volume') or info.get('regularMarketVolume')
        avg_volume = info.get('averageDailyVolume10Day')
        prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
        
        # Calculate change percent
        change_percent = None
        if price and prev_close and prev_close != 0:
            change_percent = round(((price - prev_close) / prev_close) * 100, 4)
        
        # Calculate relative volume
        relative_volume = None
        if volume and avg_volume and avg_volume != 0:
            relative_volume = round(volume / avg_volume, 2)
        
        return {
            'symbol': symbol,
            'name': info.get('longName') or info.get('shortName'),
            'price': price,
            'open': info.get('open') or info.get('regularMarketOpen'),
            'high': info.get('dayHigh') or info.get('regularMarketDayHigh'),
            'low': info.get('dayLow') or info.get('regularMarketDayLow'),
            'volume': volume,
            'change_percent': change_percent,
            'market_cap': info.get('marketCap'),
            'shares_float': info.get('floatShares'),
            'relative_volume': relative_volume,
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'endpoints': {
            '/quote': 'GET with ?symbols=AAPL,MSFT,GOOGL',
            '/health': 'GET for health check'
        }
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/quote', methods=['GET'])
def get_quote():
    """
    Get quotes for multiple symbols
    Usage: /quote?symbols=AAPL,MSFT,GOOGL
    """
    symbols_param = request.args.get('symbols', '')
    
    if not symbols_param:
        return jsonify({'error': 'Missing symbols parameter'}), 400
    
    symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
    
    if not symbols:
        return jsonify({'error': 'No valid symbols provided'}), 400
    
    # Limit to 100 symbols per request
    if len(symbols) > 100:
        return jsonify({'error': 'Maximum 100 symbols per request'}), 400
    
    results = []
    errors = []
    
    for symbol in symbols:
        data = get_stock_data(symbol)
        if data:
            results.append(data)
        else:
            errors.append(symbol)
    
    response = {
        'success': True,
        'count': len(results),
        'data': results
    }
    
    if errors:
        response['errors'] = {
            'count': len(errors),
            'symbols': errors
        }
    
    return jsonify(response)

#commented out to prevent auto-execution during imports and vercel deployments
# if __name__ == '__main__':
#     # For local testing
#     app.run(debug=True, host='0.0.0.0', port=5000)