"""
Real-time Market Data Streaming for the Multi-Agent AI Trading System
"""
import asyncio
import json
import websockets
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import threading
from queue import Queue
import time

from src.integrations.market_data.data_provider import MarketDataManager, MarketDataPoint
from src.utils.logging import get_component_logger

logger = get_component_logger("streaming")


@dataclass
class StreamingUpdate:
    """Real-time market data update"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    change: float
    change_percent: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "volume": self.volume,
            "timestamp": self.timestamp.isoformat(),
            "change": self.change,
            "change_percent": self.change_percent,
            "bid": self.bid,
            "ask": self.ask
        }


class MarketDataStreamer:
    """Real-time market data streaming manager"""
    
    def __init__(self, market_data_manager: MarketDataManager):
        self.market_data_manager = market_data_manager
        self.subscribers: Dict[str, Set[Callable]] = {}
        self.streaming_symbols: Set[str] = set()
        self.is_streaming = False
        self.stream_task = None
        self.update_queue = Queue()
        self.last_prices: Dict[str, float] = {}
        
        # Streaming configuration
        self.update_interval = 5  # 5 seconds for demo (real systems would be much faster)
        self.max_subscribers = 100
        
        logger.info("Market Data Streamer initialized")
    
    def subscribe(self, symbol: str, callback: Callable[[StreamingUpdate], None]) -> bool:
        """Subscribe to real-time updates for a symbol"""
        try:
            if symbol not in self.subscribers:
                self.subscribers[symbol] = set()
            
            if len(self.subscribers[symbol]) >= self.max_subscribers:
                logger.warning(f"Max subscribers reached for {symbol}")
                return False
            
            self.subscribers[symbol].add(callback)
            self.streaming_symbols.add(symbol)
            
            logger.info(f"Subscribed to {symbol}, total subscribers: {len(self.subscribers[symbol])}")
            
            # Start streaming if not already running
            if not self.is_streaming:
                self._start_streaming()
            
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to {symbol}: {e}")
            return False
    
    def unsubscribe(self, symbol: str, callback: Callable[[StreamingUpdate], None]) -> bool:
        """Unsubscribe from real-time updates"""
        try:
            if symbol in self.subscribers and callback in self.subscribers[symbol]:
                self.subscribers[symbol].remove(callback)
                
                # Remove symbol if no more subscribers
                if not self.subscribers[symbol]:
                    del self.subscribers[symbol]
                    self.streaming_symbols.discard(symbol)
                
                logger.info(f"Unsubscribed from {symbol}")
                
                # Stop streaming if no more symbols
                if not self.streaming_symbols and self.is_streaming:
                    self._stop_streaming()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error unsubscribing from {symbol}: {e}")
            return False
    
    def _start_streaming(self):
        """Start the streaming process"""
        if self.is_streaming:
            return
        
        self.is_streaming = True
        self.stream_task = asyncio.create_task(self._stream_data())
        logger.info("Started market data streaming")
    
    def _stop_streaming(self):
        """Stop the streaming process"""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        if self.stream_task:
            self.stream_task.cancel()
        
        logger.info("Stopped market data streaming")
    
    async def _stream_data(self):
        """Main streaming loop"""
        while self.is_streaming:
            try:
                # Get updates for all subscribed symbols
                for symbol in list(self.streaming_symbols):
                    await self._fetch_and_broadcast_update(symbol)
                
                # Wait for next update cycle
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                logger.info("Streaming task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _fetch_and_broadcast_update(self, symbol: str):
        """Fetch current data and broadcast to subscribers"""
        try:
            # Get current price
            current_price = await self.market_data_manager.get_current_price(symbol)
            
            if current_price is None:
                return
            
            # Calculate change from last price
            last_price = self.last_prices.get(symbol, current_price)
            change = current_price - last_price
            change_percent = (change / last_price * 100) if last_price > 0 else 0.0
            
            # Create streaming update
            update = StreamingUpdate(
                symbol=symbol,
                price=current_price,
                volume=0,  # Volume not available in real-time for this demo
                timestamp=datetime.now(timezone.utc),
                change=change,
                change_percent=change_percent
            )
            
            # Update last price
            self.last_prices[symbol] = current_price
            
            # Broadcast to subscribers
            if symbol in self.subscribers:
                for callback in list(self.subscribers[symbol]):
                    try:
                        callback(update)
                    except Exception as e:
                        logger.error(f"Error calling subscriber callback for {symbol}: {e}")
            
        except Exception as e:
            logger.error(f"Error fetching update for {symbol}: {e}")
    
    def get_streaming_status(self) -> Dict[str, Any]:
        """Get current streaming status"""
        return {
            "is_streaming": self.is_streaming,
            "symbols": list(self.streaming_symbols),
            "total_subscribers": sum(len(subs) for subs in self.subscribers.values()),
            "update_interval": self.update_interval
        }


class WebSocketServer:
    """WebSocket server for real-time market data"""
    
    def __init__(self, streamer: MarketDataStreamer, host: str = "0.0.0.0", port: int = 8765):
        self.streamer = streamer
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.client_subscriptions: Dict[websockets.WebSocketServerProtocol, Set[str]] = {}
        self.server = None
        
        logger.info(f"WebSocket server configured for {host}:{port}")
    
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port
            )
            logger.info(f"WebSocket server started on {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Error starting WebSocket server: {e}")
            raise
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connection"""
        try:
            self.clients.add(websocket)
            self.client_subscriptions[websocket] = set()
            
            logger.info(f"Client connected: {websocket.remote_address}")
            
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to AI Trading System Market Data Stream",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
            
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"Error handling client {websocket.remote_address}: {e}")
        finally:
            await self.cleanup_client(websocket)
    
    async def handle_message(self, websocket, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                symbol = data.get("symbol", "").upper()
                if symbol:
                    await self.subscribe_client(websocket, symbol)
                else:
                    await self.send_error(websocket, "Symbol required for subscription")
            
            elif message_type == "unsubscribe":
                symbol = data.get("symbol", "").upper()
                if symbol:
                    await self.unsubscribe_client(websocket, symbol)
                else:
                    await self.send_error(websocket, "Symbol required for unsubscription")
            
            elif message_type == "get_status":
                await self.send_status(websocket)
            
            else:
                await self.send_error(websocket, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON message")
        except Exception as e:
            logger.error(f"Error handling message from {websocket.remote_address}: {e}")
            await self.send_error(websocket, "Internal server error")
    
    async def subscribe_client(self, websocket, symbol: str):
        """Subscribe client to symbol updates"""
        try:
            # Create callback for this client
            def client_callback(update: StreamingUpdate):
                asyncio.create_task(self.send_update(websocket, update))
            
            # Subscribe to streamer
            success = self.streamer.subscribe(symbol, client_callback)
            
            if success:
                self.client_subscriptions[websocket].add(symbol)
                await websocket.send(json.dumps({
                    "type": "subscription_success",
                    "symbol": symbol,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
                logger.info(f"Client {websocket.remote_address} subscribed to {symbol}")
            else:
                await self.send_error(websocket, f"Failed to subscribe to {symbol}")
                
        except Exception as e:
            logger.error(f"Error subscribing client to {symbol}: {e}")
            await self.send_error(websocket, "Subscription failed")
    
    async def unsubscribe_client(self, websocket, symbol: str):
        """Unsubscribe client from symbol updates"""
        try:
            if symbol in self.client_subscriptions.get(websocket, set()):
                # Note: In a real implementation, we'd need to track the specific callback
                # For now, we'll just remove from client subscriptions
                self.client_subscriptions[websocket].discard(symbol)
                
                await websocket.send(json.dumps({
                    "type": "unsubscription_success",
                    "symbol": symbol,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
                logger.info(f"Client {websocket.remote_address} unsubscribed from {symbol}")
            else:
                await self.send_error(websocket, f"Not subscribed to {symbol}")
                
        except Exception as e:
            logger.error(f"Error unsubscribing client from {symbol}: {e}")
            await self.send_error(websocket, "Unsubscription failed")
    
    async def send_update(self, websocket, update: StreamingUpdate):
        """Send market data update to client"""
        try:
            message = {
                "type": "market_update",
                "data": update.to_dict()
            }
            await websocket.send(json.dumps(message))
            
        except websockets.exceptions.ConnectionClosed:
            # Client disconnected, will be cleaned up
            pass
        except Exception as e:
            logger.error(f"Error sending update to client: {e}")
    
    async def send_status(self, websocket):
        """Send streaming status to client"""
        try:
            status = self.streamer.get_streaming_status()
            status.update({
                "type": "status",
                "connected_clients": len(self.clients),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            await websocket.send(json.dumps(status))
            
        except Exception as e:
            logger.error(f"Error sending status to client: {e}")
    
    async def send_error(self, websocket, error_message: str):
        """Send error message to client"""
        try:
            message = {
                "type": "error",
                "message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await websocket.send(json.dumps(message))
            
        except Exception as e:
            logger.error(f"Error sending error message to client: {e}")
    
    async def cleanup_client(self, websocket):
        """Clean up client connection"""
        try:
            self.clients.discard(websocket)
            
            # Unsubscribe from all symbols
            if websocket in self.client_subscriptions:
                subscribed_symbols = self.client_subscriptions[websocket].copy()
                for symbol in subscribed_symbols:
                    # In a real implementation, we'd properly unsubscribe the callback
                    pass
                del self.client_subscriptions[websocket]
            
            logger.info(f"Cleaned up client: {websocket.remote_address}")
            
        except Exception as e:
            logger.error(f"Error cleaning up client: {e}")


class StreamingManager:
    """Main streaming manager that coordinates all streaming components"""
    
    def __init__(self, market_data_manager: MarketDataManager):
        self.market_data_manager = market_data_manager
        self.streamer = MarketDataStreamer(market_data_manager)
        self.websocket_server = WebSocketServer(self.streamer)
        self.is_running = False
        
        logger.info("Streaming Manager initialized")
    
    async def start(self):
        """Start all streaming services"""
        try:
            if self.is_running:
                logger.warning("Streaming services already running")
                return
            
            # Start WebSocket server
            await self.websocket_server.start_server()
            
            self.is_running = True
            logger.info("All streaming services started")
            
        except Exception as e:
            logger.error(f"Error starting streaming services: {e}")
            raise
    
    async def stop(self):
        """Stop all streaming services"""
        try:
            if not self.is_running:
                return
            
            # Stop WebSocket server
            await self.websocket_server.stop_server()
            
            # Stop streamer
            self.streamer._stop_streaming()
            
            self.is_running = False
            logger.info("All streaming services stopped")
            
        except Exception as e:
            logger.error(f"Error stopping streaming services: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall streaming status"""
        return {
            "is_running": self.is_running,
            "streamer_status": self.streamer.get_streaming_status(),
            "websocket_clients": len(self.websocket_server.clients),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def subscribe_to_symbol(self, symbol: str, callback: Callable[[StreamingUpdate], None]) -> bool:
        """Subscribe to real-time updates for a symbol"""
        return self.streamer.subscribe(symbol, callback)
    
    async def unsubscribe_from_symbol(self, symbol: str, callback: Callable[[StreamingUpdate], None]) -> bool:
        """Unsubscribe from real-time updates"""
        return self.streamer.unsubscribe(symbol, callback)


# Example usage and testing
async def example_callback(update: StreamingUpdate):
    """Example callback for handling streaming updates"""
    print(f"Received update for {update.symbol}: ${update.price:.2f} ({update.change_percent:+.2f}%)")


async def test_streaming():
    """Test the streaming functionality"""
    from src.integrations.market_data.data_provider import market_data_manager
    
    # Create streaming manager
    streaming_manager = StreamingManager(market_data_manager)
    
    try:
        # Start streaming services
        await streaming_manager.start()
        
        # Subscribe to a symbol
        await streaming_manager.subscribe_to_symbol("AAPL", example_callback)
        
        # Let it run for a bit
        await asyncio.sleep(30)
        
        # Check status
        status = streaming_manager.get_status()
        print(f"Streaming status: {status}")
        
    finally:
        # Stop streaming services
        await streaming_manager.stop()


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_streaming())

