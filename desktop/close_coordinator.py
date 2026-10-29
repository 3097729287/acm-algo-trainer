"""Save the local editor before closing; cloud synchronization is not a barrier."""
import logging
import threading

SAVE_AND_CLOSE = """(()=>{const waits=[];window.dispatchEvent(new CustomEvent('tb-before-update',{detail:{waitUntil:p=>waits.push(p)}}));Promise.all(waits).then(values=>window.pywebview.api.desktop_close_ready(!values.some(value=>value===false)),()=>window.pywebview.api.desktop_close_ready(false));return true;})()"""


class CloseCoordinator:
    def __init__(self,window,before_stop=lambda:None):
        self.window,self.before_stop=window,before_stop
        self.lock=threading.Lock();self.requesting=False;self.approved=False
        window.expose(self.desktop_close_ready)

    def on_closing(self,*_):
        with self.lock:
            if self.window.events.loaded.is_set() is False:
                # Before the local UI loads there is no mounted editor to
                # drain, and the JS bridge may not exist yet.
                self.approved=True
            if self.approved:
                self.before_stop()
                return True
            if self.requesting:return False
            self.requesting=True
        def save():
            try:
                self.window.evaluate_js(SAVE_AND_CLOSE)
            except Exception:
                with self.lock:self.requesting=False
                logging.getLogger('tb.desktop').warning('Close deferred until the local editor can save')
        # WinForms invokes a cancellable closing event on its UI thread. Do
        # not evaluate JavaScript there while WebView2 is waiting for a return.
        self.saver=threading.Thread(target=save,name='tb-close-save',daemon=True)
        self.saver.start()
        return False

    def desktop_close_ready(self,saved):
        with self.lock:
            if not self.requesting:return
            self.requesting=False
            if saved is not True:return
            self.approved=True
        # The native event must return False before the approved second close.
        timer=threading.Timer(.05,self.window.destroy);timer.daemon=True;timer.start()
