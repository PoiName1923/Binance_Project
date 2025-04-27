import websocket
import json
import time
from kafka import KafkaProducer
import logging
from datetime import datetime

curr_time = datetime.now()
# Cấu hình Kafka
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    retries=3
)
# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def process_kline_data(kline_data, symbol=None):
    """Xử lý dữ liệu kline thành dictionary chuẩn"""
    return {
        'symbol': symbol or kline_data.get('s'),
        'open_time': kline_data['t'],
        'close_time': kline_data['T'],
        'interval': kline_data['i'],
        'open_price': float(kline_data['o']),
        'close_price': float(kline_data['c']),
        'high_price': float(kline_data['h']),
        'low_price': float(kline_data['l']),
        'volume': float(kline_data['v']),
        'quote_volume': float(kline_data['q']),
        'number_of_trades': kline_data['n'],
        'is_closed': kline_data['x']
    }

def on_message(ws, message):
    try:
        data = json.loads(message)
        # Xử lý combined stream
        if 'stream' in data:
            stream_data = data['data']
            if 'k' not in stream_data:
                return
            processed_data = process_kline_data(stream_data['k'], stream_data['s'])
        else:
            if 'k' not in data:
                return
            processed_data = process_kline_data(data['k'])
        # Gửi đến Kafka
        try:
            future = producer.send('crypto-trades', value=processed_data)
            future.get(timeout=10)
        except Exception as kafka_error:
            logging.error(f"Kafka send failed: {kafka_error}")
            
    except Exception as e:
        logging.error(f"Message processing error: {e}", exc_info=True)


def on_error(ws, error):
    logging.error(f"WebSocket error: {error}")
def on_close(ws, close_status_code, close_msg):
    logging.info(f"WebSocket closed: {close_msg}")

# Các ticker quan sát
streams = ["btcusdt@kline_1m","ethusdt@kline_1m","bnbusdt@kline_1m"]
stream_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"

# Tạo client websocket
ws = websocket.WebSocketApp(
    stream_url,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

# Chạy WebSocket client
try:
    logging.info("Connecting to WebSocket...")
    ws.run_forever()
except Exception as e:
    logging.error(f"WebSocket error: {e}. Reconnecting in 5s...")
    time.sleep(5)


"""file này có nhiệm vụ thu thập dữ liệu streaming từ websocket
 và lưu trữ tạm thời vào kafka. Có thể tạm coi đây là bước Extract"""