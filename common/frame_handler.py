from tornado import websocket

ui_clients = []


class FrameHandler(websocket.WebSocketHandler):
    def check_origin(self, origin) -> bool:
        return True

    # overridden method from WebsocketHandler
    def open(self) -> None:
        # Set a no-wait indication when receiving messages
        if self not in ui_clients:
            ui_clients.append(self)
        self.set_nodelay(True)

    # overridden method from WebsocketHandler
    def on_close(self) -> None:
        if self in ui_clients:
            ui_clients.remove(self)
        pass

    def get_compression_options(self):
        # compression level 6 is the default compression level..
        return {"compression_level": 6, "mem_level": 5}

    # overridden method from WebsocketHandler
    def on_message(self, message: str) -> None:
        """Handler action when an incoming message is received

        message (str): incoming message from the UI Component
        """
        pass


class FrameHandlerInternal(websocket.WebSocketHandler):
    def check_origin(self, origin) -> bool:
        return True

    # overridden method from WebsocketHandler
    def open(self) -> None:
        # Set a no-wait indication when receiving messages
        self.set_nodelay(True)

    # overridden method from WebsocketHandler
    def on_close(self) -> None:
        pass

    def get_compression_options(self):
        # compression level 6 is the default compression level..
        return {"compression_level": 6, "mem_level": 5}

    # overridden method from WebsocketHandler
    def on_message(self, message: str) -> None:
        """Handler action when an incoming message is received

        message (str): incoming message from the UI Component
        """
        for ui in ui_clients:
            ui.write_message(message)
