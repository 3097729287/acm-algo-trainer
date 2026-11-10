"""Save the local editor before closing; cloud synchronization is not a barrier."""
import logging
import threading

SAVE_AND_CLOSE = """(request=>{const waits=[];window.dispatchEvent(new CustomEvent('tb-before-update',{detail:{waitUntil:p=>waits.push(p)}}));Promise.all(waits).then(values=>{const saved=!values.some(value=>value===false);if(saved)window.dispatchEvent(new Event('tb-desktop-closing'));window.pywebview.api.desktop_close_ready(saved,request);},()=>window.pywebview.api.desktop_close_ready(false,request));return true;})(__TB_CLOSE_REQUEST__)"""


class CloseCoordinator:
    def __init__(self,window,before_stop=lambda:None,*,frontend_alive=lambda:True):
        self.window,self.before_stop=window,before_stop
        self.frontend_alive=frontend_alive
        self.lock=threading.Lock();self.requesting=False;self.approved=False
        self.request_id=0;self.stopping=False
        window.expose(self.desktop_close_ready)

    def on_closing(self,*_):
        try:
            unavailable=self.frontend_alive() is False
        except Exception:
            # A failed optional health probe is not evidence that it is safe
            # to skip an editor save.
            unavailable=False
        with self.lock:
            if unavailable or self.window.events.loaded.is_set() is False:
                # Before the local UI loads there is no mounted editor to
                # drain. After an actual process exit no JS save can complete;
                # leave the synchronously journaled drafts intact instead.
                self.approved=True
                self.requesting=False
                self.request_id+=1
            if self.approved:
                stop=not self.stopping
                self.stopping=True
            else:
                if self.requesting:return False
                self.requesting=True
                self.request_id+=1
                request_id=self.request_id
                stop=False
        if self.approved:
            if stop:
                try:self.before_stop()
                except Exception:
                    logging.getLogger('tb.desktop').exception('Native close cleanup failed; final cleanup will retry')
            return True
        def save():
            try:
                self.window.evaluate_js(SAVE_AND_CLOSE.replace('__TB_CLOSE_REQUEST__',str(request_id)))
            except Exception:
                with self.lock:
                    if self.request_id==request_id:self.requesting=False
                logging.getLogger('tb.desktop').warning('Close deferred until the local editor can save')
        # WinForms invokes a cancellable closing event on its UI thread. Do
        # not evaluate JavaScript there while WebView2 is waiting for a return.
        self.saver=threading.Thread(target=save,name='tb-close-save',daemon=True)
        self.saver.start()
        return False

    def desktop_close_ready(self,saved,request_id=None):
        with self.lock:
            if not self.requesting or request_id!=self.request_id:return
            self.requesting=False
            if saved is not True:return
            self.approved=True
        self._close_native()

    def frontend_failed(self):
        """Finish an already requested close when its JS process has exited."""
        with self.lock:
            if not self.requesting:return
            self.requesting=False
            self.request_id+=1
            self.approved=True
        self._close_native()

    def _close_native(self):
        # The native event must return False before the approved second close.
        timer=threading.Timer(.05,self.window.destroy);timer.daemon=True;timer.start()
